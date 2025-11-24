"""
Admin Users router: View customer profiles and order history
Handles HU_MANAGE_USERS
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List
from app.schemas import UsuarioDetailResponse, PedidoResponse
from app.database import get_db
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/admin/usuarios",
    tags=["admin-users"]
)


@router.get("", response_model=List[UsuarioDetailResponse])
async def list_users(
    nombre: str = Query(None),
    email: str = Query(None),
    cedula: str = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    List all customers with optional search
    
    Requirements (HU_MANAGE_USERS):
    - Search by nombre, email, or cedula (case-insensitive)
    - Sort by fecha_registro DESC (newest first)
    - Return user details but NO password
    - Pagination support
    - Database indexes on email, cedula, nombre for performance
    """
    try:
        where_clauses = []
        params = {"skip": skip, "limit": limit}

        if nombre:
            where_clauses.append("nombre_completo LIKE :nombre")
            params["nombre"] = f"%{nombre}%"
        if email:
            where_clauses.append("email LIKE :email")
            params["email"] = f"%{email}%"
        if cedula:
            where_clauses.append("cedula = :cedula")
            params["cedula"] = cedula

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

        q = text(f"SELECT id, nombre_completo, email, cedula, fecha_registro, ultimo_login, CASE WHEN es_admin = 1 THEN 'admin' ELSE 'customer' END as rol FROM Usuarios WHERE {where_sql} ORDER BY fecha_registro DESC OFFSET :skip ROWS FETCH NEXT :limit ROWS ONLY")
        result = db.execute(q, params)
        rows = result.fetchall()

        users = []
        for r in rows:
            users.append(UsuarioDetailResponse(
                id=r.id,
                nombre_completo=r.nombre_completo,
                email=r.email,
                cedula=r.cedula,
                fecha_registro=r.fecha_registro,
                ultimo_login=r.ultimo_login,
                rol=r.rol
            ))

        return users
    except Exception as e:
        logger.exception("Error listing users")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail={"status": "error", "message": "Error al listar usuarios."})


@router.get("/{usuario_id}", response_model=UsuarioDetailResponse)
async def get_user(usuario_id: int, db: Session = Depends(get_db)):
    """
    Get customer profile details
    
    Requirements (HU_MANAGE_USERS):
    - Return full user information
    - Include fecha_registro and ultimo_login
    - Do NOT include password
    - Return 404 if user not found
    """
    try:
        q = text("SELECT id, nombre_completo, email, cedula, fecha_registro, ultimo_login, CASE WHEN es_admin = 1 THEN 'admin' ELSE 'customer' END as rol FROM Usuarios WHERE id = :id")
        row = db.execute(q, {"id": usuario_id}).first()
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"status": "error", "message": "Usuario no encontrado."})

        user = UsuarioDetailResponse(
            id=row.id,
            nombre_completo=row.nombre_completo,
            email=row.email,
            cedula=row.cedula,
            fecha_registro=row.fecha_registro,
            ultimo_login=row.ultimo_login,
            rol=row.rol
        )

        return user
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error fetching user %s", usuario_id)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail={"status": "error", "message": "Error al obtener el usuario."})


@router.get("/{usuario_id}/pedidos", response_model=List[PedidoResponse])
async def get_user_orders(
    usuario_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Get order history for customer
    
    Requirements (HU_MANAGE_USERS):
    - Return all pedidos for usuario_id
    - Sort by fecha_creacion DESC (newest first)
    - Include all pedido items
    - Pagination support
    """
    try:
        # Validate user exists
        exists_q = text("SELECT id FROM Usuarios WHERE id = :id")
        user_res = db.execute(exists_q, {"id": usuario_id}).fetchone()
        if not user_res:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"status": "error", "message": "Usuario no encontrado."})

        orders_q = text("SELECT id, usuario_id, estado, total, fecha_creacion FROM Pedidos WHERE usuario_id = :usuario_id ORDER BY fecha_creacion DESC OFFSET :skip ROWS FETCH NEXT :limit ROWS ONLY")
        orders_res = db.execute(orders_q, {"usuario_id": usuario_id, "skip": skip, "limit": limit}).fetchall()

        pedidos = []
        for o in orders_res:
            items_q = text("SELECT id, producto_id, cantidad, precio_unitario FROM PedidoItems WHERE pedido_id = :pedido_id")
            items_res = db.execute(items_q, {"pedido_id": o.id}).fetchall()
            items = []
            for it in items_res:
                items.append({"id": it.id, "producto_id": it.producto_id, "cantidad": it.cantidad, "precio_unitario": float(it.precio_unitario)})

            pedido = PedidoResponse(
                id=o.id,
                usuario_id=o.usuario_id,
                estado=o.estado,
                total=float(o.total),
                fecha_creacion=o.fecha_creacion,
                items=[
                    # Pydantic will convert dicts to PedidoItemResponse via from_attributes if necessary
                    item for item in items
                ]
            )
            pedidos.append(pedido)

        return pedidos
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error fetching orders for user %s", usuario_id)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail={"status": "error", "message": "Error al obtener los pedidos del usuario."})


@router.get("/{usuario_id}/stats")
async def get_user_stats(usuario_id: int, db: Session = Depends(get_db)):
    """
    Get customer statistics
    
    Requirements:
    - Total orders count
    - Total spent (sum of pedido totals)
    - Last order date
    - Preferred category (most purchased)
    """
    try:
        # Verify user exists
        exists_q = text("SELECT id FROM Usuarios WHERE id = :id")
        user_res = db.execute(exists_q, {"id": usuario_id}).fetchone()
        if not user_res:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"status": "error", "message": "Usuario no encontrado."})

        stats_q = text("""
            SELECT
                (SELECT COUNT(*) FROM Pedidos WHERE usuario_id = :id) as total_pedidos,
                (SELECT ISNULL(SUM(total),0) FROM Pedidos WHERE usuario_id = :id) as total_gastado,
                (SELECT MAX(fecha_creacion) FROM Pedidos WHERE usuario_id = :id) as ultimo_pedido
        """)
        stats_res = db.execute(stats_q, {"id": usuario_id}).fetchone()

        # Preferred category: most spent
        pref_q = text("""
            SELECT TOP 1 c.id as categoria_id, c.nombre as categoria_nombre, SUM(pi.cantidad * pi.precio_unitario) as total_spent
            FROM PedidoItems pi
            INNER JOIN Pedidos p ON pi.pedido_id = p.id
            INNER JOIN Productos prod ON pi.producto_id = prod.id
            INNER JOIN Categorias c ON prod.categoria_id = c.id
            WHERE p.usuario_id = :id
            GROUP BY c.id, c.nombre
            ORDER BY total_spent DESC
        """)
        pref_res = db.execute(pref_q, {"id": usuario_id}).fetchone()

        return {
            "total_pedidos": int(stats_res.total_pedidos) if stats_res else 0,
            "total_gastado": float(stats_res.total_gastado) if stats_res else 0.0,
            "ultimo_pedido": stats_res.ultimo_pedido if stats_res else None,
            "preferida": {"categoria_id": pref_res.categoria_id, "nombre": pref_res.categoria_nombre} if pref_res else None
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error computing stats for user %s", usuario_id)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail={"status": "error", "message": "Error al calcular estadísticas del usuario."})
