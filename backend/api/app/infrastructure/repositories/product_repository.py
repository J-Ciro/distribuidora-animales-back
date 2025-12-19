"""
Product repository - Data Access Layer
Handles all database operations for products
"""
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
import logging

logger = logging.getLogger(__name__)


class ProductRepository:
    """Handles all database operations for products"""

    def __init__(self, db: Session):
        self.db = db

    def get_product_by_id(self, producto_id: int, include_inactive: bool = False) -> Optional[Any]:
        """Get product by ID"""
        try:
            if include_inactive:
                query = text("""
                    SELECT id, nombre, descripcion, precio, peso_gramos, cantidad_disponible, 
                           categoria_id, subcategoria_id, activo, fecha_creacion, fecha_actualizacion 
                    FROM Productos WHERE id = :id
                """)
            else:
                query = text("""
                    SELECT id, nombre, descripcion, precio, peso_gramos, cantidad_disponible, 
                           categoria_id, subcategoria_id, activo, fecha_creacion, fecha_actualizacion 
                    FROM Productos WHERE id = :id AND activo = 1
                """)
            return self.db.execute(query, {"id": producto_id}).first()
        except Exception as e:
            logger.exception("Error querying product by id: %s", e)
            raise

    def list_products(
        self, 
        categoria_id: Optional[int] = None,
        subcategoria_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 20
    ) -> List[Any]:
        """List products with optional filtering"""
        params = {"skip": int(skip), "limit": int(limit)}
        where_clauses = ["p.activo = 1"]
        
        if categoria_id:
            where_clauses.append("p.categoria_id = :categoria_id")
            params["categoria_id"] = int(categoria_id)
        if subcategoria_id:
            where_clauses.append("p.subcategoria_id = :subcategoria_id")
            params["subcategoria_id"] = int(subcategoria_id)

        where_sql = " AND ".join(where_clauses)

        try:
            query = text(f"""
                SELECT p.id, p.nombre, p.descripcion, p.precio, p.peso_gramos, 
                       p.cantidad_disponible, p.categoria_id, p.subcategoria_id, 
                       p.activo, p.fecha_creacion 
                FROM Productos p 
                WHERE {where_sql} 
                ORDER BY p.fecha_creacion DESC 
                OFFSET :skip ROWS FETCH NEXT :limit ROWS ONLY
            """)
            return self.db.execute(query, params).fetchall()
        except Exception as e:
            logger.exception("Error querying products: %s", e)
            raise

    def get_categories_by_ids(self, cat_ids: set) -> Dict[int, Dict]:
        """Get categories by IDs"""
        if not cat_ids:
            return {}
        
        try:
            cat_ids_list = [int(x) for x in cat_ids]
            placeholders = ','.join([f':cat_id_{i}' for i in range(len(cat_ids_list))])
            params = {f'cat_id_{i}': cat_id for i, cat_id in enumerate(cat_ids_list)}
            query = text(f"""
                SELECT id, nombre, fecha_creacion AS created_at, fecha_actualizacion AS updated_at 
                FROM Categorias WHERE id IN ({placeholders})
            """)
            
            cats = {}
            for c in self.db.execute(query, params).fetchall():
                cats[c.id] = {
                    "id": c.id, 
                    "nombre": c.nombre, 
                    "created_at": c.created_at, 
                    "updated_at": c.updated_at
                }
            return cats
        except SQLAlchemyError:
            logger.exception("Error fetching category names")
            return {}

    def get_subcategories_by_ids(self, subcat_ids: set) -> Dict[int, Dict]:
        """Get subcategories by IDs"""
        if not subcat_ids:
            return {}
        
        try:
            subcat_ids_list = [int(x) for x in subcat_ids]
            placeholders = ','.join([f':subcat_id_{i}' for i in range(len(subcat_ids_list))])
            params = {f'subcat_id_{i}': subcat_id for i, subcat_id in enumerate(subcat_ids_list)}
            query = text(f"""
                SELECT id, categoria_id, nombre, fecha_creacion AS created_at 
                FROM Subcategorias WHERE id IN ({placeholders})
            """)
            
            subcats = {}
            for s in self.db.execute(query, params).fetchall():
                subcats[s.id] = {
                    "id": s.id, 
                    "categoria_id": s.categoria_id, 
                    "nombre": s.nombre, 
                    "created_at": s.created_at, 
                    "updated_at": s.created_at
                }
            return subcats
        except SQLAlchemyError:
            logger.exception("Error fetching subcategory names")
            return {}

    def get_product_images(self, producto_ids: List[int]) -> Dict[int, List[str]]:
        """Get images for multiple products"""
        if not producto_ids:
            return {}
        
        try:
            prod_ids_list = [int(x) for x in producto_ids]
            placeholders = ','.join([f':prod_id_{i}' for i in range(len(prod_ids_list))])
            params = {f'prod_id_{i}': prod_id for i, prod_id in enumerate(prod_ids_list)}
            query = text(f"""
                SELECT producto_id, ruta_imagen 
                FROM ProductoImagenes 
                WHERE producto_id IN ({placeholders}) 
                ORDER BY orden ASC
            """)
            
            images_map = {}
            for img in self.db.execute(query, params).fetchall():
                images_map.setdefault(img.producto_id, []).append(img.ruta_imagen)
            return images_map
        except SQLAlchemyError:
            logger.exception("Error fetching product images")
            return {}

    def get_category_by_id(self, categoria_id: int) -> Optional[Any]:
        """Get category by ID"""
        try:
            query = text("""
                SELECT id, nombre, fecha_creacion AS created_at, fecha_actualizacion AS updated_at 
                FROM Categorias WHERE id = :id
            """)
            return self.db.execute(query, {"id": categoria_id}).first()
        except Exception:
            logger.exception("Error fetching category")
            return None

    def get_subcategory_by_id(self, subcategoria_id: int) -> Optional[Any]:
        """Get subcategory by ID"""
        try:
            query = text("""
                SELECT id, categoria_id, nombre, fecha_creacion AS created_at 
                FROM Subcategorias WHERE id = :id
            """)
            return self.db.execute(query, {"id": subcategoria_id}).first()
        except Exception:
            logger.exception("Error fetching subcategory")
            return None

    def resolve_category_id(self, value: Any) -> Optional[int]:
        """Resolve category ID from either int or name string"""
        try:
            return int(value)
        except Exception:
            pass
        
        try:
            query = text("SELECT id FROM Categorias WHERE LOWER(nombre) = :name")
            res = self.db.execute(query, {"name": str(value).strip().lower()}).fetchone()
            if res:
                return int(res.id)
        except Exception:
            return None
        return None

    def resolve_subcategory_id(self, value: Any) -> Optional[int]:
        """Resolve subcategory ID from either int or name string"""
        try:
            return int(value)
        except Exception:
            pass
        
        try:
            query = text("SELECT id FROM Subcategorias WHERE LOWER(nombre) = :name")
            res = self.db.execute(query, {"name": str(value).strip().lower()}).fetchone()
            if res:
                return int(res.id)
        except Exception:
            return None
        return None

    def update_product(self, producto_id: int, update_data: Dict[str, Any]) -> Optional[Any]:
        """Update product with given data"""
        if not update_data:
            return None

        set_clauses = []
        params = {"id": producto_id}
        column_map = {
            'nombre': 'nombre',
            'descripcion': 'descripcion',
            'precio': 'precio',
            'peso_gramos': 'peso_gramos',
            'categoria_id': 'categoria_id',
            'subcategoria_id': 'subcategoria_id',
            'cantidad_disponible': 'cantidad_disponible',
            'activo': 'activo'
        }

        for key, col in column_map.items():
            if key in update_data:
                set_clauses.append(f"{col} = :{key}")
                params[key] = update_data[key]

        if not set_clauses:
            return None

        set_sql = ", ".join(set_clauses) + ", fecha_actualizacion = GETUTCDATE()"
        query = text(f"""
            UPDATE Productos SET {set_sql} 
            OUTPUT inserted.id, inserted.nombre, inserted.descripcion, inserted.precio, 
                   inserted.peso_gramos, inserted.cantidad_disponible, inserted.categoria_id, 
                   inserted.subcategoria_id, inserted.activo, inserted.fecha_creacion, 
                   inserted.fecha_actualizacion 
            WHERE id = :id
        """)

        try:
            res = self.db.execute(query, params)
            row = res.fetchone()
            self.db.commit()
            return row
        except SQLAlchemyError as e:
            logger.exception("Error updating product: %s", e)
            self.db.rollback()
            raise

    def check_inventory_history(self, producto_id: int) -> bool:
        """Check if product has inventory history"""
        try:
            query = text("SELECT TOP 1 1 AS exists_flag FROM InventarioHistorial WHERE producto_id = :id")
            hist = self.db.execute(query, {"id": producto_id}).first()
            return bool(hist)
        except Exception as e:
            logger.exception("Error checking inventory history: %s", e)
            raise

    def soft_delete_product(self, producto_id: int) -> bool:
        """Soft delete product (mark as inactive)"""
        try:
            query = text("UPDATE Productos SET activo = 0, fecha_actualizacion = GETUTCDATE() WHERE id = :id")
            self.db.execute(query, {"id": producto_id})
            self.db.commit()
            return True
        except SQLAlchemyError as e:
            logger.exception("Error marking product inactive: %s", e)
            self.db.rollback()
            return False

    def delete_product_images(self, producto_id: int) -> None:
        """Delete all images for a product"""
        try:
            query = text("DELETE FROM ProductoImagenes WHERE producto_id = :id")
            self.db.execute(query, {"id": producto_id})
            self.db.commit()
        except Exception as e:
            logger.exception("Error deleting product images: %s", e)
            self.db.rollback()
            raise

    def insert_product_image(self, producto_id: int, ruta_imagen: str) -> None:
        """Insert product image"""
        try:
            query = text("""
                INSERT INTO ProductoImagenes (producto_id, ruta_imagen, es_principal, orden) 
                VALUES (:producto_id, :ruta_imagen, 1, 0)
            """)
            self.db.execute(query, {"producto_id": producto_id, "ruta_imagen": ruta_imagen})
            self.db.commit()
        except Exception as e:
            logger.exception("Error inserting product image: %s", e)
            self.db.rollback()
            raise
