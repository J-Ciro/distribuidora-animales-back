"""
Ratings API Router
Endpoints para gestionar calificaciones de productos
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional

from app.database import get_db
from app.schemas import (
    CalificacionCreate,
    CalificacionUpdate,
    CalificacionResponse,
    ProductoStatsResponse,
    CalificacionesListResponse,
    SuccessResponse,
    MetaPage,
    UsuarioPublicResponse
)
from app.services.ratings_service import RatingsService
from app.models import Usuario, Calificacion
from app.routers.auth import get_current_user, require_admin

# Router público (clientes)
public_router = APIRouter(prefix="/api/calificaciones")

# Router admin
admin_router = APIRouter(prefix="/api/admin/calificaciones")


# ============================================================
# PUBLIC ENDPOINTS (Clientes autenticados)
# ============================================================

@public_router.post("", response_model=CalificacionResponse, status_code=201)
def create_rating(
    rating_data: CalificacionCreate,
    db: Session = Depends(get_db),
    current_user: UsuarioPublicResponse = Depends(get_current_user)
):
    """
    Crear una nueva calificación para un producto
    - El usuario debe haber recibido el pedido (estado: Entregado)
    - Solo se puede calificar una vez por producto por pedido
    """
    calificacion = RatingsService.create_rating(db, current_user.id, rating_data)
    
    # Obtener nombre del usuario para la respuesta
    response = CalificacionResponse.from_orm(calificacion)
    response.usuario_nombre = current_user.nombre_completo
    
    return response


@public_router.get("/mis-calificaciones", response_model=List[CalificacionResponse])
def get_my_ratings(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: UsuarioPublicResponse = Depends(get_current_user)
):
    """Obtener todas las calificaciones del usuario autenticado"""
    calificaciones = RatingsService.get_all_ratings(
        db, 
        skip=skip, 
        limit=limit,
        usuario_id=current_user.id
    )
    
    result = []
    for cal in calificaciones:
        response = CalificacionResponse.from_orm(cal)
        response.usuario_nombre = current_user.nombre_completo
        result.append(response)
    
    return result


@public_router.get("/producto/{producto_id}", response_model=List[CalificacionResponse])
def get_product_ratings(
    producto_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Obtener todas las calificaciones visibles de un producto"""
    calificaciones = RatingsService.get_product_ratings(
        db, 
        producto_id, 
        visible_only=True,
        skip=skip, 
        limit=limit
    )
    
    result = []
    for cal in calificaciones:
        usuario = db.query(Usuario).filter(Usuario.id == cal.usuario_id).first()
        response = CalificacionResponse.from_orm(cal)
        response.usuario_nombre = usuario.nombre_completo if usuario else "Usuario"
        result.append(response)
    
    return result


@public_router.get("/producto/{producto_id}/stats", response_model=ProductoStatsResponse)
def get_product_stats(
    producto_id: int,
    db: Session = Depends(get_db)
):
    """Obtener estadísticas de calificaciones de un producto"""
    stats = RatingsService.get_product_stats(db, producto_id)
    
    if not stats:
        # Retornar stats vacías si no hay calificaciones
        return ProductoStatsResponse(
            producto_id=producto_id,
            promedio_calificacion=0.0,
            total_calificaciones=0,
            total_5_estrellas=0,
            total_4_estrellas=0,
            total_3_estrellas=0,
            total_2_estrellas=0,
            total_1_estrella=0,
            fecha_actualizacion=None
        )
    
    return ProductoStatsResponse.from_orm(stats)


@public_router.put("/{rating_id}", response_model=CalificacionResponse)
def update_my_rating(
    rating_id: int,
    rating_update: CalificacionUpdate,
    db: Session = Depends(get_db),
    current_user: UsuarioPublicResponse = Depends(get_current_user)
):
    """Actualizar una calificación propia"""
    calificacion = RatingsService.update_rating(
        db, 
        rating_id, 
        current_user.id, 
        rating_update,
        is_admin=False
    )
    
    response = CalificacionResponse.from_orm(calificacion)
    response.usuario_nombre = current_user.nombre_completo
    
    return response


@public_router.delete("/{rating_id}", response_model=SuccessResponse)
def delete_my_rating(
    rating_id: int,
    db: Session = Depends(get_db),
    current_user: UsuarioPublicResponse = Depends(get_current_user)
):
    """Eliminar una calificación propia"""
    RatingsService.delete_rating(db, rating_id, current_user.id, is_admin=False)
    
    return SuccessResponse(
        status="success",
        message="Calificación eliminada exitosamente"
    )


@public_router.get("/productos-pendientes", response_model=List[dict])
def get_ratable_products(
    db: Session = Depends(get_db),
    current_user: UsuarioPublicResponse = Depends(get_current_user)
):
    """Obtener productos que el usuario puede calificar"""
    productos = RatingsService.get_user_ratable_products(db, current_user.id)
    return productos


# ============================================================
# ADMIN ENDPOINTS
# ============================================================

@admin_router.get("", response_model=CalificacionesListResponse)
def get_all_ratings_admin(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    producto_id: Optional[int] = Query(None),
    usuario_id: Optional[int] = Query(None),
    visible_only: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
    current_admin: UsuarioPublicResponse = Depends(require_admin)
):
    """Obtener todas las calificaciones (admin)"""
    calificaciones = RatingsService.get_all_ratings(
        db,
        skip=skip,
        limit=limit,
        producto_id=producto_id,
        usuario_id=usuario_id,
        visible_only=visible_only
    )
    
    total = RatingsService.count_ratings(
        db,
        producto_id=producto_id,
        usuario_id=usuario_id,
        visible_only=visible_only
    )
    
    result = []
    for cal in calificaciones:
        usuario = db.query(Usuario).filter(Usuario.id == cal.usuario_id).first()
        producto = db.execute(
            text("SELECT id, nombre FROM Productos WHERE id = :producto_id"),
            {"producto_id": cal.producto_id}
        ).fetchone()
        
        response = CalificacionResponse.from_orm(cal)
        response.usuario_nombre = usuario.nombre_completo if usuario else "Usuario"
        response.producto_nombre = producto.nombre if producto else f"Producto #{cal.producto_id}"
        result.append(response)
    
    return CalificacionesListResponse(
        status="success",
        data=result,
        meta=MetaPage(
            page=skip // limit + 1,
            pageSize=limit,
            total=total
        )
    )


@admin_router.get("/{rating_id}", response_model=CalificacionResponse)
def get_rating_by_id_admin(
    rating_id: int,
    db: Session = Depends(get_db),
    current_admin: UsuarioPublicResponse = Depends(require_admin)
):
    """Obtener una calificación por ID (admin)"""
    calificacion = RatingsService.get_rating_by_id(db, rating_id)
    
    if not calificacion:
        raise HTTPException(status_code=404, detail="Calificación no encontrada")
    
    usuario = db.query(Usuario).filter(Usuario.id == calificacion.usuario_id).first()
    producto = db.execute(
        text("SELECT id, nombre FROM Productos WHERE id = :producto_id"),
        {"producto_id": calificacion.producto_id}
    ).fetchone()
    
    response = CalificacionResponse.from_orm(calificacion)
    response.usuario_nombre = usuario.nombre_completo if usuario else "Usuario"
    response.producto_nombre = producto.nombre if producto else f"Producto #{calificacion.producto_id}"
    
    return response


@admin_router.put("/{rating_id}", response_model=CalificacionResponse)
def update_rating_admin(
    rating_id: int,
    rating_update: CalificacionUpdate,
    db: Session = Depends(get_db),
    current_admin: UsuarioPublicResponse = Depends(require_admin)
):
    """Actualizar cualquier calificación (admin)"""
    calificacion = RatingsService.update_rating(
        db, 
        rating_id, 
        current_admin.id, 
        rating_update,
        is_admin=True
    )
    
    usuario = db.query(Usuario).filter(Usuario.id == calificacion.usuario_id).first()
    response = CalificacionResponse.from_orm(calificacion)
    response.usuario_nombre = usuario.nombre_completo if usuario else "Usuario"
    
    return response


@admin_router.delete("/{rating_id}", response_model=SuccessResponse)
def delete_rating_admin(
    rating_id: int,
    db: Session = Depends(get_db),
    current_admin: UsuarioPublicResponse = Depends(require_admin)
):
    """Eliminar cualquier calificación (admin)"""
    RatingsService.delete_rating(db, rating_id, current_admin.id, is_admin=True)
    
    return SuccessResponse(
        status="success",
        message="Calificación eliminada exitosamente"
    )


@admin_router.patch("/{rating_id}/toggle-visibility", response_model=CalificacionResponse)
def toggle_rating_visibility(
    rating_id: int,
    db: Session = Depends(get_db),
    current_admin: UsuarioPublicResponse = Depends(require_admin)
):
    """Cambiar visibilidad de una calificación (admin)"""
    calificacion = RatingsService.get_rating_by_id(db, rating_id)
    
    if not calificacion:
        raise HTTPException(status_code=404, detail="Calificación no encontrada")
    
    # Toggle visibility
    update = CalificacionUpdate(visible=not calificacion.visible)
    
    calificacion = RatingsService.update_rating(
        db, 
        rating_id, 
        current_admin.id, 
        update,
        is_admin=True
    )
    
    usuario = db.query(Usuario).filter(Usuario.id == calificacion.usuario_id).first()
    response = CalificacionResponse.from_orm(calificacion)
    response.usuario_nombre = usuario.nombre_completo if usuario else "Usuario"
    
    return response
