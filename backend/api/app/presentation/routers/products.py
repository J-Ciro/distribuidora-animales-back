"""
Products router: Create, Read, Update products for admin
Handles HU_CREATE_PRODUCT
Refactored to follow SOLID principles with separated concerns
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Body, Request, Form
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from app.presentation.schemas import ProductoCreate, ProductoResponse, ProductoUpdate, ProductoImagenResponse
from app.core.database import get_db
import logging
import base64
import json
import os
from app.core.config import settings
from app.application.services.product_service import ProductService
from app.application.services.image_service import ImageService
from app.application.validators.product_validator import ProductValidator
from app.infrastructure.repositories.product_repository import ProductRepository
from app.core.constants import (
    MIN_PRODUCT_NAME_LENGTH,
    MIN_PRODUCT_DESCRIPTION_LENGTH,
    MIN_PRODUCT_PRICE,
    MIN_PRODUCT_WEIGHT_GRAMS,
    MAX_PAGE_SIZE
)
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
import time
import uuid

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/admin/productos",
    tags=["products"]
)


@router.post("")
async def create_product(
    request: Request,
    file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    """
    Create new product with details
    
    Requirements (HU_CREATE_PRODUCT):
    - Validates product name, price, weight, category, subcategory
    - Price > 0, weight > 0
    - Category and subcategory must exist
    - Publishes productos.crear queue message
    - Handles image uploads separately
    """
    # Initialize services
    validator = ProductValidator()
    product_service = ProductService(db)
    image_service = ImageService()
    
    # Parse request payload (multipart or JSON)
    content_type = request.headers.get('content-type', '')
    payload = None
    
    if content_type.startswith('multipart/form-data'):
        form = await request.form()
        raw = form.get('payload')
        if raw:
            try:
                payload = json.loads(raw if isinstance(raw, str) else str(raw))
            except Exception:
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={"status": "error", "message": "El campo 'payload' debe ser JSON válido."}
                )
        else:
            payload = {k: v for k, v in form.multi_items() if k != 'file'}
    else:
        try:
            payload = await request.json()
        except Exception:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "status": "error",
                    "message": "Validation error",
                    "errors": [{"field": "body -> payload", "message": "Input should be a valid dictionary", "type": "dict_type"}]
                }
            )

    # Validate required fields
    if error := validator.validate_required_fields(payload):
        return error

    nombre = payload.get('nombre')
    descripcion = payload.get('descripcion')
    precio = payload.get('precio')
    peso_gramos = payload.get('peso_gramos') or payload.get('peso')
    categoria_id = payload.get('categoria_id') or payload.get('categoria')
    subcategoria_id = payload.get('subcategoria_id') or payload.get('subcategoria')

    # Field validations
    if error := validator.validate_nombre(nombre):
        return error
    if error := validator.validate_descripcion(descripcion):
        return error
    if error := validator.validate_precio(precio):
        return error
    if error := validator.validate_peso_gramos(peso_gramos):
        return error

    # Handle image file upload
    imagen_b64 = None
    imagen_filename = None
    
    if file is not None:
        imagen_filename = file.filename or ""
        contents = await file.read()
        
        if error := validator.validate_image_file(imagen_filename, len(contents)):
            await file.close()
            return error
        
        try:
            imagen_b64 = image_service.encode_image_to_base64(contents)
        finally:
            await file.close()

    # Check for duplicates
    if error := validator.check_duplicate_product(db, nombre):
        return error

    # Resolve category and subcategory IDs
    cat_id, subcat_id, error = product_service.resolve_category_and_subcategory(categoria_id, subcategoria_id)
    if error:
        return error

    # Add image data to payload if present
    if imagen_b64 and imagen_filename:
        payload['imagen_b64'] = imagen_b64
        payload['imagen_filename'] = imagen_filename

    # Prepare and publish message
    message = product_service.prepare_product_message(payload, cat_id, subcat_id)
    product_service.publish_product_created(message)

    return JSONResponse(
        status_code=status.HTTP_202_ACCEPTED,
        content={"status": "success", "message": "Producto creado exitosamente"}
    )


@router.get("", response_model=List[ProductoResponse])
async def list_products(
    categoria_id: int = Query(None, ge=1),
    subcategoria_id: int = Query(None, ge=1),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    List products with optional filtering by category/subcategory
    
    Requirements:
    - Filter by category_id and/or subcategory_id
    - Pagination support
    - Return active products
    """
    # Initialize services
    product_service = ProductService(db)
    repository = ProductRepository(db)
    
    try:
        # Fetch products from repository
        rows = repository.list_products(categoria_id, subcategoria_id, skip, limit)
        if not rows:
            return []

        # Build product response objects
        products = [product_service.build_product_response(r) for r in rows]
        
        # Enrich with relations (categories, subcategories, images)
        products = product_service.enrich_products_with_relations(products)
        
        # Enrich with ratings
        products = product_service.enrich_products_with_ratings(products)

        return products
        
    except Exception as e:
        logger.exception("Error listing products: %s", e)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"status": "error", "message": "Error interno al listar productos."}
        )


@router.get("/{producto_id}", response_model=ProductoResponse)
async def get_product(producto_id: int, include_inactive: bool = Query(False), db: Session = Depends(get_db)):
    """
    Get product details

    - Returns full product information including images, category and subcategory
    - By default only active products are returned (activo = 1). Set `include_inactive=true` to allow fetching inactive products for admin purposes.
    """
    # Initialize services
    validator = ProductValidator()
    product_service = ProductService(db)
    repository = ProductRepository(db)
    
    # Validate product exists
    if error := validator.validate_product_exists(db, producto_id, include_inactive):
        return error

    try:
        # Fetch product
        row = repository.get_product_by_id(producto_id, include_inactive)
        if not row:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"status": "error", "message": "Producto no encontrado."}
            )

        # Build product response
        producto = product_service.build_product_response(row)
        
        # Enrich with relations
        producto = product_service.enrich_product_with_relations(producto)

        return producto
        
    except Exception as e:
        logger.exception("Error getting product: %s", e)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"status": "error", "message": "Error interno al obtener el producto."}
        )


@router.put("/{producto_id}", response_model=ProductoResponse, tags=["Inventory","Products"])
async def update_product(
    producto_id: int,
    request: ProductoUpdate,
    db: Session = Depends(get_db)
):
    """
    Update product information
    
    Requirements (HU_CREATE_PRODUCT):
    - Update name, price, weight, category, subcategory
    - Validates all fields
    - Publishes productos.actualizar queue message
    """
    # Initialize services
    validator = ProductValidator()
    product_service = ProductService(db)
    repository = ProductRepository(db)
    image_service = ImageService()
    
    # Validate product exists
    if error := validator.validate_product_exists(db, producto_id, include_inactive=True):
        return error

    # Extract update data
    data = request.model_dump(exclude_unset=True) if hasattr(request, 'model_dump') else request.dict(exclude_unset=True)
    if not data:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"status": "error", "message": "No se proporcionaron campos para actualizar."}
        )

    # Validate fields if provided
    if 'nombre' in data and data.get('nombre'):
        if error := validator.validate_nombre(data['nombre']):
            return error

    if 'precio' in data:
        if error := validator.validate_precio(data['precio']):
            return error

    if 'peso_gramos' in data:
        if error := validator.validate_peso_gramos(data['peso_gramos']):
            return error

    if 'cantidad_disponible' in data:
        try:
            cant = int(data['cantidad_disponible'])
            if cant < 0:
                raise ValueError()
        except Exception:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"status": "error", "message": "La cantidad disponible debe ser un entero >= 0."}
            )

    # Validate categories if provided
    existing = repository.get_product_by_id(producto_id, include_inactive=True)
    
    if 'categoria_id' in data:
        try:
            cat = db.execute(
                text("SELECT id FROM Categorias WHERE id = :id AND activo = 1"),
                {"id": int(data['categoria_id'])}
            ).first()
            if not cat:
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={"status": "error", "message": "Categoría no encontrada."}
                )
        except Exception as e:
            logger.exception("Error checking categoria: %s", e)
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"status": "error", "message": "Error interno al verificar categoría."}
            )

    if 'subcategoria_id' in data:
        try:
            sub = db.execute(
                text("SELECT id, categoria_id FROM Subcategorias WHERE id = :id AND activo = 1"),
                {"id": int(data['subcategoria_id'])}
            ).first()
            if not sub:
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={"status": "error", "message": "Subcategoría no encontrada."}
                )
            
            target_cat = data.get('categoria_id') if 'categoria_id' in data else existing.categoria_id
            if int(sub.categoria_id) != int(target_cat):
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={"status": "error", "message": "La subcategoría no pertenece a la categoría indicada."}
                )
        except Exception as e:
            logger.exception("Error checking subcategoria: %s", e)
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"status": "error", "message": "Error interno al verificar subcategoría."}
            )

    # Update product
    try:
        row = repository.update_product(producto_id, data)
        if not row:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"status": "error", "message": "Producto no encontrado."}
            )

        producto = product_service.build_product_response(row)
        producto['fecha_actualizacion'] = row.fecha_actualizacion
        
        # Handle image changes
        if 'imagenUrl' in data:
            imagen_url = data.get('imagenUrl', '').strip() if data.get('imagenUrl') else ''
            try:
                image_service.delete_all_product_images(db, producto_id)
                if imagen_url:
                    image_service.insert_product_image(db, producto_id, imagen_url)
                    logger.info(f"Updated product {producto_id} with imagen URL: {imagen_url}")
                else:
                    logger.info(f"Removed all images for product {producto_id}")
            except Exception as e:
                logger.exception(f"Error updating product image URL: {e}")

        # Enrich with relations
        producto = product_service.enrich_product_with_relations(producto)
        
        # Publish update message
        product_service.publish_product_updated(producto_id, producto)

        return producto

    except Exception as e:
        logger.exception("Error updating product: %s", e)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"status": "error", "message": "Error interno al actualizar el producto."}
        )
 

@router.put("/{producto_id}/stock", tags=["Inventory","Products"])
async def update_product_stock(producto_id: int, request_obj: Request, db: Session = Depends(get_db)):
    """
    Producer endpoint: manually update product stock (only publishes message to RabbitMQ)

    Validations and exact messages required by the HU:
    - Missing required fields -> "Por favor, completa todos los campos obligatorios."
    - cantidad must be positive -> "La cantidad debe ser un número positivo."
    - If product missing -> "Producto no encontrado."
    - On success -> "Existencias actualizadas exitosamente"
    """
    # Initialize services
    validator = ProductValidator()
    product_service = ProductService(db)
    
    # Parse request body
    try:
        payload = await request_obj.json()
    except Exception:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"status": "error", "message": "Por favor, completa todos los campos obligatorios."}
        )

    cantidad = payload.get('cantidad') if isinstance(payload, dict) else None
    if cantidad is None:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"status": "error", "message": "Por favor, completa todos los campos obligatorios."}
        )

    # Validate cantidad
    if error := validator.validate_cantidad(cantidad):
        return error

    # Validate product exists
    if error := validator.validate_product_exists(db, producto_id):
        return error

    # Publish message to RabbitMQ
    if not product_service.publish_inventory_replenished(producto_id, int(cantidad)):
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"status": "error", "message": "Error interno al procesar la solicitud."}
        )

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"status": "success", "message": "Existencias actualizadas exitosamente"}
    )


@router.post("/{producto_id}/images")
async def upload_product_image(
    producto_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload product image
    
    Requirements (HU_CREATE_PRODUCT):
    - Max 10 MB file size
    - Allowed formats: jpg, jpeg, png, svg, webp
    - Stores in uploads/productos/{producto_id}/
    - Publishes productos.imagen.crear queue message
    """
    # Initialize services
    validator = ProductValidator()
    image_service = ImageService()
    product_service = ProductService(db)
    
    # Validate product exists
    if error := validator.validate_product_exists(db, producto_id):
        return error

    # Read and validate file
    filename = file.filename or ""
    try:
        contents = await file.read()
    except Exception as e:
        logger.exception("Error reading uploaded file: %s", e)
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"status": "error", "message": "Error al leer el archivo de imagen."}
        )

    if error := validator.validate_image_file(filename, len(contents)):
        return error

    # Save file
    file_path, error_msg = image_service.save_image_file(contents, filename, producto_id)
    if not file_path:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"status": "error", "message": error_msg}
        )

    # Save to database
    try:
        image_service.insert_product_image(db, producto_id, file_path)
    except Exception as e:
        logger.exception("Error inserting image record: %s", e)
        # Cleanup saved file
        image_service.delete_image_file(file_path)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"status": "error", "message": "Error interno al guardar la imagen en la base de datos."}
        )

    # Publish message (non-blocking)
    message = {"producto_id": producto_id, "ruta_imagen": file_path}
    from app.infrastructure.external.rabbitmq import publish_message_safe
    published = publish_message_safe("productos.imagen.crear", message, retry=True)
    if not published:
        logger.warning(f"Failed to publish productos.imagen.crear message for product {producto_id}")

    # Generate public URL
    imagen_url = image_service.generate_image_url(file_path)

    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={
            "status": "success",
            "message": "Imagen subida correctamente",
            "ruta_imagen": file_path,
            "path": file_path,
            "imagen_url": imagen_url
        }
    )


@router.get("/{producto_id}/images")
async def list_product_images(producto_id: int, db: Session = Depends(get_db)):
    """List all images for a product

    Returns an array of image records with `id`, `ruta_imagen`, `es_principal` and `orden`.
    """
    # Initialize services
    validator = ProductValidator()
    image_service = ImageService()
    
    # Validate product exists
    if error := validator.validate_product_exists(db, producto_id):
        return error

    try:
        rows = image_service.get_product_images_from_db(db, producto_id)
        images = []
        for r in rows:
            images.append({
                "id": int(r.id),
                "producto_id": int(r.producto_id),
                "ruta_imagen": r.ruta_imagen,
                "es_principal": bool(r.es_principal),
                "orden": int(r.orden)
            })
        return images
    except Exception as e:
        logger.exception("Error listing product images: %s", e)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"status": "error", "message": "Error interno al listar imágenes."}
        )


@router.get("/{producto_id}/images/{imagen_id}", response_model=ProductoImagenResponse)
async def get_product_image(producto_id: int, imagen_id: int, db: Session = Depends(get_db)):
    """Get a single product image by id

    - Validates that the product exists and is active
    - Validates that the image exists and belongs to the given product
    - Returns a `ProductoImagenResponse` object
    """
    # Initialize services
    validator = ProductValidator()
    image_service = ImageService()
    
    # Validate product exists
    if error := validator.validate_product_exists(db, producto_id):
        return error

    try:
        row = image_service.get_product_image_by_id(db, imagen_id, producto_id)
        if not row:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"status": "error", "message": "Imagen no encontrada."}
            )

        return {
            "id": int(row.id),
            "producto_id": int(row.producto_id),
            "ruta_imagen": row.ruta_imagen,
            "es_principal": bool(row.es_principal),
            "orden": int(row.orden),
        }
    except Exception as e:
        logger.exception("Error getting product image: %s", e)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"status": "error", "message": "Error interno al obtener la imagen."}
        )


@router.put("/{producto_id}/images/{imagen_id}")
async def update_product_image(
    producto_id: int,
    imagen_id: int,
    file: UploadFile = File(...),
    es_principal: Optional[str] = Form(None),
    orden: Optional[int] = Form(None),
    db: Session = Depends(get_db)
):
    """Update product image (replace file and/or metadata)

    - Accepts multipart/form-data with optional `file` and optional fields `es_principal` and `orden`.
    - Validates product and image existence, validates file extension and size, saves new file, updates DB, deletes old file on success, and publishes `productos.imagen.actualizar`.
    """
    # Initialize services
    validator = ProductValidator()
    image_service = ImageService()
    
    # Validate product exists
    if error := validator.validate_product_exists(db, producto_id):
        return error

    # Fetch existing image
    try:
        img_row = image_service.get_product_image_by_id(db, imagen_id, producto_id)
        if not img_row:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"status": "error", "message": "Imagen no encontrada."}
            )
        old_path = img_row.ruta_imagen
    except Exception as e:
        logger.exception("Error fetching image: %s", e)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"status": "error", "message": "Error interno al obtener la imagen."}
        )

    # Process new file if provided
    new_path = None
    if file is not None:
        filename = getattr(file, 'filename', '') or ''
        try:
            contents = await file.read()
        except Exception as e:
            logger.exception("Error reading file: %s", e)
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"status": "error", "message": "Error al leer el archivo de imagen."}
            )

        if error := validator.validate_image_file(filename, len(contents)):
            return error

        # Save new file
        new_path, error_msg = image_service.save_image_file(contents, filename, producto_id)
        if not new_path:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"status": "error", "message": error_msg}
            )

    # Normalize es_principal
    if es_principal is not None:
        es_principal = es_principal.lower() in ('1', 'true', 'yes') if isinstance(es_principal, str) else bool(es_principal)

    # Validate orden
    if orden is not None:
        try:
            orden = int(orden)
            if orden < 0:
                if new_path:
                    image_service.delete_image_file(new_path)
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={"status": "error", "message": "El campo 'orden' debe ser un entero >= 0."}
                )
        except Exception:
            if new_path:
                image_service.delete_image_file(new_path)
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"status": "error", "message": "El campo 'orden' debe ser un entero."}
            )

    # Build update data
    update_data = {}
    if new_path:
        update_data['ruta_imagen'] = new_path
    if es_principal is not None:
        update_data['es_principal'] = es_principal
    if orden is not None:
        update_data['orden'] = orden

    if not update_data:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"status": "error", "message": "No se proporcionaron campos para actualizar."}
        )

    # Update database
    try:
        row = image_service.update_product_image(db, imagen_id, producto_id, update_data)
        if not row:
            if new_path:
                image_service.delete_image_file(new_path)
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"status": "error", "message": "Imagen no encontrada."}
            )

        # Remove old file if new one was saved
        if new_path and old_path and old_path != new_path:
            image_service.delete_image_file(old_path)

        # Publish message (non-blocking)
        message = {
            "producto_id": producto_id,
            "imagen_id": imagen_id,
            "ruta_imagen": row.ruta_imagen,
            "es_principal": bool(row.es_principal),
            "orden": int(row.orden)
        }
        from app.infrastructure.external.rabbitmq import publish_message_safe
        published = publish_message_safe("productos.imagen.actualizar", message, retry=True)
        if not published:
            logger.warning(f"Failed to publish productos.imagen.actualizar message")

        return {
            "id": int(row.id),
            "producto_id": int(row.producto_id),
            "ruta_imagen": row.ruta_imagen,
            "es_principal": bool(row.es_principal),
            "orden": int(row.orden)
        }

    except Exception as e:
        logger.exception("Error updating image: %s", e)
        if new_path:
            image_service.delete_image_file(new_path)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"status": "error", "message": "Error interno al actualizar la imagen en la base de datos."}
        )


@router.delete("/{producto_id}/images/{imagen_id}")
async def delete_product_image(
    producto_id: int,
    imagen_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete product image
    
    Requirements (HU_CREATE_PRODUCT):
    - Delete image file and database record
    - Publishes productos.imagen.eliminar queue message
    """
    # Initialize services
    validator = ProductValidator()
    image_service = ImageService()
    
    # Validate product exists
    if error := validator.validate_product_exists(db, producto_id):
        return error

    # Fetch image record
    try:
        img = image_service.get_product_image_by_id(db, imagen_id, producto_id)
        if not img:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"status": "error", "message": "Imagen no encontrada."}
            )
        
        ruta = img.ruta_imagen if hasattr(img, 'ruta_imagen') else None
        
        # Delete from database
        rowcount = image_service.delete_product_image_from_db(db, imagen_id, producto_id)
        if rowcount == 0:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"status": "error", "message": "Imagen no encontrada."}
            )
        
        # Delete physical file
        if ruta:
            image_service.delete_image_file(ruta)
        
        # Publish message (non-blocking)
        message = {"producto_id": int(producto_id), "imagen_id": int(imagen_id), "ruta_imagen": ruta}
        from app.infrastructure.external.rabbitmq import publish_message_safe
        published = publish_message_safe("productos.imagen.eliminar", message, retry=True)
        if not published:
            logger.warning(f"Failed to publish productos.imagen.eliminar message for product {producto_id}")
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"status": "success", "message": "Imagen eliminada correctamente"}
        )
        
    except Exception as e:
        logger.exception("Error deleting product image: %s", e)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"status": "error", "message": "Error interno al eliminar la imagen."}
        )


@router.delete("/{producto_id}", tags=["Inventory","Products"])
async def delete_product(producto_id: int, db: Session = Depends(get_db)):
    """
    Soft delete product (mark as inactive)
    
    Requirements:
    - Set activo=False instead of deleting
    - Publishes productos.eliminar queue message
    """
    # Initialize services
    validator = ProductValidator()
    product_service = ProductService(db)
    repository = ProductRepository(db)
    
    # Validate product exists
    if error := validator.validate_product_exists(db, producto_id, include_inactive=True):
        return error

    # Check inventory history
    try:
        if repository.check_inventory_history(producto_id):
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"status": "error", "message": "No se puede eliminar el producto porque tiene movimientos registrados."}
            )
    except Exception as e:
        logger.exception("Error checking inventory history: %s", e)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"status": "error", "message": "Error interno al verificar historial de inventario."}
        )

    # Publish deletion message
    product_service.publish_product_deleted(producto_id)

    # Soft delete
    repository.soft_delete_product(producto_id)

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"status": "success", "message": "Producto eliminado exitosamente"}
    )
