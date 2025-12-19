"""
Product validation logic - Single Responsibility Principle
Centralizes all product-related validation logic
"""
import os
from typing import Dict, Any, Optional
from fastapi import HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
import logging

from app.core.constants import (
    MIN_PRODUCT_NAME_LENGTH,
    MIN_PRODUCT_DESCRIPTION_LENGTH,
    MIN_PRODUCT_PRICE,
    MIN_PRODUCT_WEIGHT_GRAMS,
)
from app.core.config import settings

logger = logging.getLogger(__name__)


class ProductValidator:
    """Handles all product validation logic"""

    @staticmethod
    def validate_required_fields(payload: Dict[str, Any]) -> Optional[JSONResponse]:
        """Validate that all required fields are present"""
        nombre = payload.get('nombre')
        descripcion = payload.get('descripcion')
        precio = payload.get('precio')
        peso_gramos = payload.get('peso_gramos') or payload.get('peso')
        categoria_id = payload.get('categoria_id') or payload.get('categoria')
        subcategoria_id = payload.get('subcategoria_id') or payload.get('subcategoria')

        required_fields = [nombre, descripcion, precio, peso_gramos, categoria_id, subcategoria_id]
        if any(f is None for f in required_fields):
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"status": "error", "message": "Por favor, completa todos los campos obligatorios."}
            )
        return None

    @staticmethod
    def validate_nombre(nombre: Any) -> Optional[JSONResponse]:
        """Validate product name"""
        if not isinstance(nombre, str) or len(nombre.strip()) < MIN_PRODUCT_NAME_LENGTH:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "status": "error",
                    "message": f"El nombre debe tener al menos {MIN_PRODUCT_NAME_LENGTH} caracteres."
                }
            )
        return None

    @staticmethod
    def validate_descripcion(descripcion: Any) -> Optional[JSONResponse]:
        """Validate product description"""
        if not isinstance(descripcion, str) or len(descripcion.strip()) < MIN_PRODUCT_DESCRIPTION_LENGTH:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "status": "error",
                    "message": f"La descripción debe tener al menos {MIN_PRODUCT_DESCRIPTION_LENGTH} caracteres."
                }
            )
        return None

    @staticmethod
    def validate_precio(precio: Any) -> Optional[JSONResponse]:
        """Validate product price"""
        try:
            precio_val = float(precio)
            if precio_val < MIN_PRODUCT_PRICE:
                raise ValueError()
        except Exception:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "status": "error",
                    "message": f"El precio debe ser un número mayor a {MIN_PRODUCT_PRICE}."
                }
            )
        return None

    @staticmethod
    def validate_peso_gramos(peso_gramos: Any) -> Optional[JSONResponse]:
        """Validate product weight"""
        try:
            peso_val = int(peso_gramos)
            if peso_val < MIN_PRODUCT_WEIGHT_GRAMS:
                raise ValueError()
        except Exception:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "status": "error",
                    "message": f"El peso debe ser un entero mayor a {MIN_PRODUCT_WEIGHT_GRAMS} (gramos)."
                }
            )
        return None

    @staticmethod
    def validate_cantidad(cantidad: Any) -> Optional[JSONResponse]:
        """Validate stock quantity"""
        try:
            cantidad_val = int(cantidad)
            if cantidad_val <= 0:
                raise ValueError()
        except Exception:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"status": "error", "message": "La cantidad debe ser un número positivo."}
            )
        return None

    @staticmethod
    def validate_image_file(filename: str, file_size: int) -> Optional[JSONResponse]:
        """Validate image file extension and size"""
        _, ext = os.path.splitext(filename.lower())
        if ext not in settings.ALLOWED_IMAGE_EXTENSIONS:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"status": "error", "message": "Formato o tamaño de imagen no válido."}
            )

        if file_size > settings.MAX_FILE_SIZE:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"status": "error", "message": "Formato o tamaño de imagen no válido."}
            )
        return None

    @staticmethod
    def check_duplicate_product(db: Session, nombre: str) -> Optional[JSONResponse]:
        """Check if product with same name already exists"""
        try:
            existing = db.execute(
                text("SELECT id FROM Productos WHERE LOWER(nombre) = :name"),
                {"name": nombre.strip().lower()}
            ).first()
            if existing:
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={"status": "error", "message": "Ya existe un producto con ese nombre."}
                )
        except SQLAlchemyError as err:
            logger.exception("Error checking existing product name: %s", err)
            db.rollback()
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"status": "error", "message": "Error interno al verificar duplicados."}
            )
        return None

    @staticmethod
    def validate_product_exists(db: Session, producto_id: int, include_inactive: bool = False) -> Optional[JSONResponse]:
        """Validate that product exists"""
        try:
            if include_inactive:
                query = text("SELECT id FROM Productos WHERE id = :id")
            else:
                query = text("SELECT id FROM Productos WHERE id = :id AND activo = 1")
            
            prod = db.execute(query, {"id": producto_id}).first()
            if not prod:
                return JSONResponse(
                    status_code=status.HTTP_404_NOT_FOUND,
                    content={"status": "error", "message": "Producto no encontrado."}
                )
        except Exception as e:
            logger.exception("Error checking product existence: %s", e)
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"status": "error", "message": "Error interno al verificar producto."}
            )
        return None
