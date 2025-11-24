"""
Admin Users router: View customer profiles and order history
Handles HU_MANAGE_USERS
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from typing import List, Optional
from app.schemas import (
    UsuarioDetailResponse,
    PedidoResponse,
    UsuariosListResponse,
    UsuarioDetailWrapper,
    PedidosListResponse,
)
from app.database import get_db
from app.models import Usuario, Pedido, PedidoItem
from app.utils import security_utils
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/admin/usuarios",
    tags=["admin-users"]
)


def require_admin(request: Request, db: Session = Depends(get_db)) -> Usuario:
    """
    Dependency that verifies JWT and that the user is admin.
    Raises 401/403 accordingly.
    """
    auth_header = request.headers.get("authorization")
    if not auth_header or not auth_header.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail={"status": "error", "message": "No autenticado"})
    token = auth_header.split(" ", 1)[1]
    try:
        payload = security_utils.verify_jwt_token(token)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail={"status": "error", "message": "Token inválido"})
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail={"status": "error", "message": "Token inválido"})
    usuario = db.query(Usuario).filter(Usuario.id == int(user_id)).first()
    if not usuario or not usuario.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail={"status": "error", "message": "Cuenta no activa"})
    if not usuario.es_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail={"status": "error", "message": "Acceso denegado"})
    return usuario


@router.get("", response_model=UsuariosListResponse)
async def list_users(
    q: Optional[str] = Query(None, description="Búsqueda libre por id, nombre, cedula o email"),
    page: int = Query(1, ge=1),
    pageSize: int = Query(20, ge=1, le=100),
    sort: str = Query("fecha_registro", description="Campo para ordenar: nombre o fecha_registro"),
    db: Session = Depends(get_db),
    _admin: Usuario = Depends(require_admin)
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
    query = db.query(Usuario)
    if q:
        q_lower = q.lower()
        # If q is numeric, allow matching id directly
        filters = []
        if q.isdigit():
            filters.append(Usuario.id == int(q))
        filters.append(func.lower(Usuario.nombre_completo).like(f"%{q_lower}%"))
        filters.append(func.lower(Usuario.email).like(f"%{q_lower}%"))
        filters.append(func.lower(Usuario.cedula).like(f"%{q_lower}%"))
        query = query.filter(or_(*filters))

    # Total for pagination
    total = query.count()

    # Sorting
    if sort == "nombre":
        query = query.order_by(Usuario.nombre_completo.asc())
    else:
        query = query.order_by(Usuario.fecha_registro.desc())

    # Pagination
    offset = (page - 1) * pageSize
    users = query.offset(offset).limit(pageSize).all()

    data = []
    for u in users:
        data.append({
            "id": u.id,
            "nombre_completo": u.nombre_completo,
            "cedula": u.cedula,
            "email": u.email,
            "direccion_envio": u.direccion_envio,
            "fecha_registro": u.fecha_registro,
        })

    return {
        "status": "success",
        "data": data,
        "meta": {"page": page, "pageSize": pageSize, "total": total}
    }


@router.get("/{usuario_id}", response_model=UsuarioDetailWrapper)
async def get_user(usuario_id: int, db: Session = Depends(get_db), _admin: Usuario = Depends(require_admin)):
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
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"status": "error", "message": "Usuario no encontrado."})

    # Build pedidosResumen
    pedidos_query = db.query(Pedido).filter(Pedido.usuario_id == usuario.id)
    total_pedidos = pedidos_query.count()
    ultimo = pedidos_query.order_by(Pedido.fecha_creacion.desc()).first()
    ultimo_pedido = None
    if ultimo:
        ultimo_pedido = {"id": ultimo.id, "fecha": ultimo.fecha_creacion, "total": float(ultimo.total), "estado": ultimo.estado}

    result = {
        "id": usuario.id,
        "nombre_completo": usuario.nombre_completo,
        "cedula": usuario.cedula,
        "email": usuario.email,
        "telefono": usuario.telefono,
        "direccion_envio": usuario.direccion_envio,
        "preferencia_mascotas": usuario.preferencia_mascotas,
        "fecha_registro": usuario.fecha_registro,
        "ultimo_login": usuario.ultimo_login,
        "rol": "admin" if usuario.es_admin else "cliente",
        "pedidosResumen": {"totalPedidos": total_pedidos, "ultimoPedido": ultimo_pedido}
    }

    return {"status": "success", "data": result}


@router.get("/{usuario_id}/pedidos", response_model=PedidosListResponse)
async def get_user_orders(
    usuario_id: int,
    page: int = Query(1, ge=1),
    pageSize: int = Query(20, ge=1, le=100),
    estado: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    _admin: Usuario = Depends(require_admin)
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
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"status": "error", "message": "Usuario no encontrado."})

    query = db.query(Pedido).filter(Pedido.usuario_id == usuario_id)
    if estado:
        query = query.filter(Pedido.estado == estado)

    total = query.count()
    offset = (page - 1) * pageSize
    pedidos = query.order_by(Pedido.fecha_creacion.desc()).offset(offset).limit(pageSize).all()

    data = []
    for p in pedidos:
        items = db.query(PedidoItem).filter(PedidoItem.pedido_id == p.id).all()
        items_list = []
        for it in items:
            items_list.append({
                "id": it.id,
                "producto_id": it.producto_id,
                "cantidad": it.cantidad,
                "precio_unitario": float(it.precio_unitario)
            })

        data.append({
            "id": p.id,
            "usuario_id": p.usuario_id,
            "estado": p.estado,
            "total": float(p.total),
            "fecha_creacion": p.fecha_creacion,
            "items": items_list
        })

    return {"status": "success", "data": data, "meta": {"page": page, "pageSize": pageSize, "total": total}}


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
    # Simple implementation returning basic stats
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"status": "error", "message": "Usuario no encontrado."})

    total_pedidos = db.query(Pedido).filter(Pedido.usuario_id == usuario_id).count()
    total_spent = db.query(func.coalesce(func.sum(Pedido.total), 0)).filter(Pedido.usuario_id == usuario_id).scalar() or 0
    last = db.query(Pedido).filter(Pedido.usuario_id == usuario_id).order_by(Pedido.fecha_creacion.desc()).first()
    last_date = last.fecha_creacion if last else None

    # Preferred category calculation requires join with order items and products; omitted for now
    return {
        "status": "success",
        "data": {
            "totalPedidos": total_pedidos,
            "totalGastado": float(total_spent),
            "ultimoPedidoFecha": last_date,
            "preferenciaCategoria": None
        }
    }
