"""
Service layer for ratings/calificaciones
Handles business logic for product ratings
"""
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from fastapi import HTTPException
from typing import List, Optional
from datetime import datetime

from app.models import Calificacion, ProductoStats, Usuario, Pedido, PedidoItem
from app.schemas import CalificacionCreate, CalificacionUpdate


class RatingsService:
    """Service for managing product ratings"""
    
    @staticmethod
    def can_user_rate_product(db: Session, usuario_id: int, producto_id: int, pedido_id: int) -> bool:
        """
        Verifica si el usuario puede calificar el producto
        - El pedido debe ser del usuario
        - El pedido debe estar en estado 'Entregado'
        - El producto debe estar en el pedido
        - No debe existir ya una calificación para ese producto en ese pedido
        """
        # Verificar que el pedido sea del usuario y esté entregado
        pedido = db.query(Pedido).filter(
            Pedido.id == pedido_id,
            Pedido.usuario_id == usuario_id,
            Pedido.estado == 'Entregado'
        ).first()
        
        if not pedido:
            return False
        
        # Verificar que el producto esté en el pedido
        pedido_item = db.query(PedidoItem).filter(
            PedidoItem.pedido_id == pedido_id,
            PedidoItem.producto_id == producto_id
        ).first()
        
        if not pedido_item:
            return False
        
        # Verificar que no exista ya una calificación
        existing = db.query(Calificacion).filter(
            Calificacion.usuario_id == usuario_id,
            Calificacion.producto_id == producto_id,
            Calificacion.pedido_id == pedido_id
        ).first()
        
        return existing is None
    
    @staticmethod
    def create_rating(db: Session, usuario_id: int, rating_data: CalificacionCreate) -> Calificacion:
        """Crea una nueva calificación"""
        # Validar que el usuario pueda calificar
        if not RatingsService.can_user_rate_product(
            db, usuario_id, rating_data.producto_id, rating_data.pedido_id
        ):
            raise HTTPException(
                status_code=400,
                detail="No puedes calificar este producto. Verifica que el pedido esté entregado y no hayas calificado antes."
            )
        
        # Crear la calificación
        calificacion = Calificacion(
            producto_id=rating_data.producto_id,
            usuario_id=usuario_id,
            pedido_id=rating_data.pedido_id,
            calificacion=rating_data.calificacion,
            comentario=rating_data.comentario,
            aprobado=True,  # Por defecto aprobado
            visible=True
        )
        
        db.add(calificacion)
        db.flush()  # Flush to get the ID without committing
        db.commit()
        
        # Reload from database to get server-generated values
        db.expire(calificacion)
        db.refresh(calificacion)
        
        return calificacion
    
    @staticmethod
    def get_rating_by_id(db: Session, rating_id: int) -> Optional[Calificacion]:
        """Obtiene una calificación por ID"""
        return db.query(Calificacion).filter(Calificacion.id == rating_id).first()
    
    @staticmethod
    def get_user_rating_for_product(
        db: Session, usuario_id: int, producto_id: int, pedido_id: int
    ) -> Optional[Calificacion]:
        """Obtiene la calificación de un usuario para un producto en un pedido específico"""
        return db.query(Calificacion).filter(
            Calificacion.usuario_id == usuario_id,
            Calificacion.producto_id == producto_id,
            Calificacion.pedido_id == pedido_id
        ).first()
    
    @staticmethod
    def get_product_ratings(
        db: Session, 
        producto_id: int, 
        visible_only: bool = True,
        skip: int = 0,
        limit: int = 100
    ) -> List[Calificacion]:
        """Obtiene todas las calificaciones de un producto"""
        query = db.query(Calificacion).filter(Calificacion.producto_id == producto_id)
        
        if visible_only:
            query = query.filter(Calificacion.visible == True)
        
        return query.order_by(Calificacion.fecha_creacion.desc()).offset(skip).limit(limit).all()
    
    @staticmethod
    def get_all_ratings(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        producto_id: Optional[int] = None,
        usuario_id: Optional[int] = None,
        visible_only: Optional[bool] = None
    ) -> List[Calificacion]:
        """Obtiene todas las calificaciones con filtros opcionales"""
        query = db.query(Calificacion)
        
        if producto_id:
            query = query.filter(Calificacion.producto_id == producto_id)
        
        if usuario_id:
            query = query.filter(Calificacion.usuario_id == usuario_id)
        
        if visible_only is not None:
            query = query.filter(Calificacion.visible == visible_only)
        
        return query.order_by(Calificacion.fecha_creacion.desc()).offset(skip).limit(limit).all()
    
    @staticmethod
    def count_ratings(
        db: Session,
        producto_id: Optional[int] = None,
        usuario_id: Optional[int] = None,
        visible_only: Optional[bool] = None
    ) -> int:
        """Cuenta las calificaciones con filtros opcionales"""
        query = db.query(func.count(Calificacion.id))
        
        if producto_id:
            query = query.filter(Calificacion.producto_id == producto_id)
        
        if usuario_id:
            query = query.filter(Calificacion.usuario_id == usuario_id)
        
        if visible_only is not None:
            query = query.filter(Calificacion.visible == visible_only)
        
        return query.scalar()
    
    @staticmethod
    def update_rating(
        db: Session, 
        rating_id: int, 
        usuario_id: int, 
        rating_update: CalificacionUpdate,
        is_admin: bool = False
    ) -> Calificacion:
        """Actualiza una calificación"""
        calificacion = db.query(Calificacion).filter(Calificacion.id == rating_id).first()
        
        if not calificacion:
            raise HTTPException(status_code=404, detail="Calificación no encontrada")
        
        # Solo el dueño o un admin puede actualizar
        if not is_admin and calificacion.usuario_id != usuario_id:
            raise HTTPException(status_code=403, detail="No autorizado para actualizar esta calificación")
        
        # Usuarios normales solo pueden actualizar calificación y comentario
        if rating_update.calificacion is not None:
            calificacion.calificacion = rating_update.calificacion
        
        if rating_update.comentario is not None:
            calificacion.comentario = rating_update.comentario
        
        # Solo admin puede actualizar visible y aprobado
        if is_admin:
            if rating_update.visible is not None:
                calificacion.visible = rating_update.visible
            
            if rating_update.aprobado is not None:
                calificacion.aprobado = rating_update.aprobado
        
        calificacion.fecha_actualizacion = datetime.utcnow()
        
        db.commit()
        db.refresh(calificacion)
        
        return calificacion
    
    @staticmethod
    def delete_rating(db: Session, rating_id: int, usuario_id: int, is_admin: bool = False):
        """Elimina una calificación"""
        calificacion = db.query(Calificacion).filter(Calificacion.id == rating_id).first()
        
        if not calificacion:
            raise HTTPException(status_code=404, detail="Calificación no encontrada")
        
        # Solo el dueño o un admin puede eliminar
        if not is_admin and calificacion.usuario_id != usuario_id:
            raise HTTPException(status_code=403, detail="No autorizado para eliminar esta calificación")
        
        db.delete(calificacion)
        db.commit()
    
    @staticmethod
    def get_product_stats(db: Session, producto_id: int) -> Optional[ProductoStats]:
        """Obtiene las estadísticas de calificaciones de un producto"""
        return db.query(ProductoStats).filter(ProductoStats.producto_id == producto_id).first()
    
    @staticmethod
    def get_products_with_ratings(db: Session, producto_ids: List[int]) -> dict:
        """
        Obtiene estadísticas de calificaciones para múltiples productos
        Retorna un diccionario {producto_id: stats}
        """
        stats = db.query(ProductoStats).filter(ProductoStats.producto_id.in_(producto_ids)).all()
        
        result = {}
        for stat in stats:
            result[stat.producto_id] = {
                'promedio_calificacion': float(stat.promedio_calificacion),
                'total_calificaciones': stat.total_calificaciones
            }
        
        return result
    
    @staticmethod
    def get_user_ratable_products(db: Session, usuario_id: int) -> List[dict]:
        """
        Obtiene los productos que el usuario puede calificar
        Productos de pedidos entregados que aún no han sido calificados
        """
        # Obtener pedidos entregados del usuario
        pedidos_entregados = db.query(Pedido.id).filter(
            Pedido.usuario_id == usuario_id,
            Pedido.estado == 'Entregado'
        ).all()
        
        pedido_ids = [p.id for p in pedidos_entregados]
        
        if not pedido_ids:
            return []
        
        # Obtener items de esos pedidos
        items = db.query(
            PedidoItem.pedido_id,
            PedidoItem.producto_id
        ).filter(
            PedidoItem.pedido_id.in_(pedido_ids)
        ).all()
        
        # Filtrar los que ya fueron calificados
        result = []
        for item in items:
            existing = db.query(Calificacion).filter(
                Calificacion.usuario_id == usuario_id,
                Calificacion.producto_id == item.producto_id,
                Calificacion.pedido_id == item.pedido_id
            ).first()
            
            if not existing:
                result.append({
                    'pedido_id': item.pedido_id,
                    'producto_id': item.producto_id
                })
        
        return result
