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
