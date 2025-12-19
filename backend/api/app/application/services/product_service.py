"""
Product service - Business Logic Layer
Centralizes all product-related business logic
Follows Single Responsibility and Dependency Inversion principles
"""
import uuid
import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from fastapi.responses import JSONResponse
from fastapi import status

from app.infrastructure.repositories.product_repository import ProductRepository
from app.application.validators.product_validator import ProductValidator
from app.application.services.ratings_service import RatingsService
from app.infrastructure.external.rabbitmq import publish_message_safe

logger = logging.getLogger(__name__)


class ProductService:
    """Handles product business logic"""

    def __init__(self, db: Session):
        self.db = db
        self.repository = ProductRepository(db)
        self.validator = ProductValidator()

    def build_product_response(self, row: Any) -> Dict[str, Any]:
        """Build product response dict from database row"""
        return {
            "id": int(row.id),
            "nombre": row.nombre,
            "descripcion": row.descripcion,
            "precio": float(row.precio),
            "peso_gramos": int(row.peso_gramos),
            "cantidad_disponible": int(row.cantidad_disponible or 0),
            "categoria_id": int(row.categoria_id) if row.categoria_id is not None else None,
            "subcategoria_id": int(row.subcategoria_id) if row.subcategoria_id is not None else None,
            "activo": bool(row.activo),
            "fecha_creacion": row.fecha_creacion
        }

    def enrich_product_with_relations(self, producto: Dict[str, Any]) -> Dict[str, Any]:
        """Add category, subcategory and images to product"""
        # Fetch category
        if producto['categoria_id']:
            cat_row = self.repository.get_category_by_id(producto['categoria_id'])
            if cat_row:
                producto['categoria'] = {
                    "id": cat_row.id,
                    "nombre": cat_row.nombre,
                    "created_at": cat_row.created_at,
                    "updated_at": cat_row.updated_at
                }
            else:
                producto['categoria'] = None
        else:
            producto['categoria'] = None

        # Fetch subcategory
        if producto['subcategoria_id']:
            sub_row = self.repository.get_subcategory_by_id(producto['subcategoria_id'])
            if sub_row:
                producto['subcategoria'] = {
                    "id": sub_row.id,
                    "categoria_id": sub_row.categoria_id,
                    "nombre": sub_row.nombre,
                    "created_at": sub_row.created_at,
                    "updated_at": sub_row.created_at
                }
            else:
                producto['subcategoria'] = None
        else:
            producto['subcategoria'] = None

        # Fetch images
        images_map = self.repository.get_product_images([producto['id']])
        producto['imagenes'] = images_map.get(producto['id'], [])

        return producto

    def enrich_products_with_relations(self, products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Add categories, subcategories and images to multiple products"""
        if not products:
            return products

        # Collect IDs
        cat_ids = set()
        subcat_ids = set()
        prod_ids = []
        
        for p in products:
            prod_ids.append(p['id'])
            if p['categoria_id']:
                cat_ids.add(p['categoria_id'])
            if p['subcategoria_id']:
                subcat_ids.add(p['subcategoria_id'])

        # Fetch in batch
        cats = self.repository.get_categories_by_ids(cat_ids)
        subcats = self.repository.get_subcategories_by_ids(subcat_ids)
        images_map = self.repository.get_product_images(prod_ids)

        # Attach to products
        for p in products:
            p['categoria'] = cats.get(p['categoria_id'])
            p['subcategoria'] = subcats.get(p['subcategoria_id'])
            p['imagenes'] = images_map.get(p['id'], [])

        return products

    def enrich_products_with_ratings(self, products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Add rating stats to products"""
        if not products:
            return products

        prod_ids = [p['id'] for p in products]
        
        try:
            stats_map = RatingsService.get_products_with_ratings(self.db, prod_ids)
            for p in products:
                stats = stats_map.get(p['id'])
                if stats:
                    p['promedio_calificacion'] = stats.get('promedio_calificacion', 0.0)
                    p['total_calificaciones'] = int(stats.get('total_calificaciones', 0))
                else:
                    p['promedio_calificacion'] = 0.0
                    p['total_calificaciones'] = 0
        except Exception:
            logger.exception('Error fetching ratings stats for products')
            for p in products:
                p['promedio_calificacion'] = 0.0
                p['total_calificaciones'] = 0

        return products

    def resolve_category_and_subcategory(self, categoria_value: Any, subcategoria_value: Any) -> tuple:
        """
        Resolve category and subcategory IDs from values
        Returns: (categoria_id, subcategoria_id, error_response)
        """
        categoria_id = self.repository.resolve_category_id(categoria_value)
        if categoria_id is None:
            return None, None, JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"status": "error", "message": "Categoría no encontrada o id inválido."}
            )

        subcategoria_id = self.repository.resolve_subcategory_id(subcategoria_value)
        if subcategoria_id is None:
            return None, None, JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"status": "error", "message": "Subcategoría no encontrada o id inválido."}
            )

        return categoria_id, subcategoria_id, None

    def prepare_product_message(self, payload: Dict[str, Any], categoria_id: int, subcategoria_id: int) -> Dict[str, Any]:
        """Prepare message for RabbitMQ product creation"""
        message = {
            "nombre": payload['nombre'].strip(),
            "descripcion": payload['descripcion'].strip(),
            "precio": float(payload['precio']),
            "peso_gramos": int(payload.get('peso_gramos') or payload.get('peso')),
            "categoria_id": int(categoria_id),
            "subcategoria_id": int(subcategoria_id),
            "cantidad_disponible": int(payload.get('cantidad_disponible', 0)),
        }

        # Add image data if present
        if payload.get('imagen_b64') and payload.get('imagen_filename'):
            message['imagen_filename'] = payload['imagen_filename']
            message['imagen_b64'] = payload['imagen_b64']

        # Add external image URL if present
        imagen_url = payload.get('imagenUrl') or payload.get('imagen_url')
        if imagen_url and isinstance(imagen_url, str) and imagen_url.strip():
            message['imagen_url'] = imagen_url.strip()

        return message

    def publish_product_created(self, message: Dict[str, Any]) -> bool:
        """Publish product created message to RabbitMQ"""
        published = publish_message_safe("productos.crear", message, retry=True)
        if not published:
            logger.error(f"Failed to publish message to productos.crear. Message: {message}")
        return published

    def publish_product_updated(self, producto_id: int, producto: Dict[str, Any]) -> bool:
        """Publish product updated message to RabbitMQ"""
        message = {"producto_id": producto_id, "producto": producto}
        published = publish_message_safe("productos.actualizar", message, retry=True)
        if not published:
            logger.warning(f"Failed to publish productos.actualizar message for product {producto_id}")
        return published

    def publish_product_deleted(self, producto_id: int) -> bool:
        """Publish product deleted message to RabbitMQ"""
        message = {"requestId": str(uuid.uuid4()), "productoId": int(producto_id)}
        published = publish_message_safe("productos.eliminar", message, retry=True)
        if not published:
            logger.warning(f"Failed to publish productos.eliminar message for product {producto_id}")
        return published

    def publish_inventory_replenished(self, producto_id: int, cantidad: int) -> bool:
        """Publish inventory replenishment message to RabbitMQ"""
        message = {
            "requestId": str(uuid.uuid4()),
            "productoId": int(producto_id),
            "cantidad": int(cantidad)
        }
        published = publish_message_safe("inventario.reabastecer", message, retry=True)
        if not published:
            logger.error(f"Failed to publish inventario.reabastecer message for product {producto_id}")
        return published
