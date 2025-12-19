"""
Image service - Handles all image-related operations
Single Responsibility: Image file management
"""
import os
import time
import base64
import logging
from typing import Optional, Tuple
from fastapi import UploadFile
from fastapi.responses import JSONResponse
from fastapi import status
from sqlalchemy.orm import Session
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings

logger = logging.getLogger(__name__)


class ImageService:
    """Handles all image file operations"""

    @staticmethod
    def save_image_file(file_contents: bytes, filename: str, producto_id: int) -> Tuple[Optional[str], Optional[str]]:
        """
        Save image file to disk
        Returns: (file_path, error_message)
        """
        try:
            upload_dir = os.path.abspath(settings.UPLOAD_DIR)
            product_dir = os.path.join(upload_dir, 'productos', str(producto_id))
            os.makedirs(product_dir, exist_ok=True)
            
            safe_name = f"{int(time.time())}_{''.join(c if c.isalnum() or c in '._-' else '_' for c in filename)}"
            file_path = os.path.join(product_dir, safe_name)
            
            with open(file_path, 'wb') as f:
                f.write(file_contents)
            
            return file_path, None
        except Exception as e:
            logger.exception("Error saving image file: %s", e)
            return None, "Error interno al guardar la imagen."

    @staticmethod
    def delete_image_file(file_path: str) -> bool:
        """Delete image file from disk"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
        except Exception:
            logger.exception("Failed to remove image file: %s", file_path)
        return False

    @staticmethod
    def encode_image_to_base64(file_contents: bytes) -> str:
        """Encode image to base64 string"""
        return base64.b64encode(file_contents).decode('utf-8')

    @staticmethod
    def generate_image_url(file_path: str) -> str:
        """Generate public URL for image"""
        upload_dir = os.path.abspath(settings.UPLOAD_DIR)
        relative_path = os.path.relpath(file_path, upload_dir)
        # Convert Windows backslashes to forward slashes for URL
        relative_path = relative_path.replace('\\', '/')
        return f"/app/uploads/{relative_path}"

    @staticmethod
    def get_product_images_from_db(db: Session, producto_id: int):
        """Get all images for a product from database"""
        try:
            query = text("""
                SELECT id, producto_id, ruta_imagen, es_principal, orden, fecha_creacion 
                FROM ProductoImagenes 
                WHERE producto_id = :id 
                ORDER BY orden ASC
            """)
            return db.execute(query, {"id": producto_id}).fetchall()
        except Exception as e:
            logger.exception("Error querying product images: %s", e)
            raise

    @staticmethod
    def get_product_image_by_id(db: Session, imagen_id: int, producto_id: int):
        """Get specific product image"""
        try:
            query = text("""
                SELECT id, producto_id, ruta_imagen, es_principal, orden, fecha_creacion 
                FROM ProductoImagenes 
                WHERE id = :imagen_id AND producto_id = :producto_id
            """)
            return db.execute(query, {"imagen_id": imagen_id, "producto_id": producto_id}).first()
        except Exception as e:
            logger.exception("Error querying product image: %s", e)
            raise

    @staticmethod
    def insert_product_image(db: Session, producto_id: int, ruta_imagen: str):
        """Insert product image into database"""
        try:
            query = text("""
                INSERT INTO ProductoImagenes (producto_id, ruta_imagen, es_principal, orden) 
                VALUES (:producto_id, :ruta_imagen, 1, 0)
            """)
            db.execute(query, {"producto_id": producto_id, "ruta_imagen": ruta_imagen})
            db.commit()
        except SQLAlchemyError as e:
            logger.exception("Error inserting product image: %s", e)
            db.rollback()
            raise

    @staticmethod
    def update_product_image(db: Session, imagen_id: int, producto_id: int, update_data: dict):
        """Update product image in database"""
        set_clauses = []
        params = {"imagen_id": imagen_id, "producto_id": producto_id}
        
        if 'ruta_imagen' in update_data:
            set_clauses.append("ruta_imagen = :ruta_imagen")
            params['ruta_imagen'] = update_data['ruta_imagen']
        if 'es_principal' in update_data:
            set_clauses.append("es_principal = :es_principal")
            params['es_principal'] = 1 if update_data['es_principal'] else 0
        if 'orden' in update_data:
            set_clauses.append("orden = :orden")
            params['orden'] = update_data['orden']

        if not set_clauses:
            return None

        set_sql = ", ".join(set_clauses) + ", fecha_creacion = fecha_creacion"
        query = text(f"""
            UPDATE ProductoImagenes SET {set_sql} 
            OUTPUT inserted.id, inserted.producto_id, inserted.ruta_imagen, 
                   inserted.es_principal, inserted.orden, inserted.fecha_creacion 
            WHERE id = :imagen_id AND producto_id = :producto_id
        """)

        try:
            res = db.execute(query, params)
            row = res.fetchone()
            db.commit()
            return row
        except Exception as e:
            logger.exception("Error updating product image: %s", e)
            db.rollback()
            raise

    @staticmethod
    def delete_product_image_from_db(db: Session, imagen_id: int, producto_id: int) -> int:
        """Delete product image from database"""
        try:
            query = text("DELETE FROM ProductoImagenes WHERE id = :imagen_id AND producto_id = :producto_id")
            res = db.execute(query, {"imagen_id": imagen_id, "producto_id": producto_id})
            db.commit()
            try:
                return res.rowcount
            except Exception:
                return 1  # Assume success if rowcount not available
        except Exception as e:
            logger.exception("Error deleting product image from DB: %s", e)
            db.rollback()
            raise

    @staticmethod
    def delete_all_product_images(db: Session, producto_id: int):
        """Delete all images for a product from database"""
        try:
            query = text("DELETE FROM ProductoImagenes WHERE producto_id = :id")
            db.execute(query, {"id": producto_id})
            db.commit()
        except Exception as e:
            logger.exception("Error deleting all product images: %s", e)
            db.rollback()
            raise
