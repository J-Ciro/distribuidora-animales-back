"""
Products router: Create, Read, Update products for admin
Handles HU_CREATE_PRODUCT
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Body, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from app.schemas import ProductoCreate, ProductoResponse, ProductoUpdate
from app.database import get_db
import logging
import base64
import json
import os
from app.config import settings
from app.utils.rabbitmq import rabbitmq_producer
from sqlalchemy import text
import time

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
    # Basic producer-side validations (fields, image format/size, numeric values)
    # AC2: Missing required fields -> specific error message
    # Support both application/json and multipart/form-data with a 'payload' field
    content_type = request.headers.get('content-type', '')
    payload = None
    if content_type.startswith('multipart/form-data'):
        form = await request.form()
        # payload may be a JSON string in the form field 'payload'
        raw = form.get('payload')
        if raw:
            if isinstance(raw, str):
                try:
                    payload = json.loads(raw)
                except Exception:
                    return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"status": "error", "message": "El campo 'payload' debe ser JSON válido."})
            else:
                # Unexpected type, attempt to convert
                try:
                    payload = json.loads(str(raw))
                except Exception:
                    payload = None
        else:
            # Support clients sending fields directly in form without payload wrapper
            payload = {}
            for k, v in form.multi_items():
                # skip file fields
                if k == 'file':
                    continue
                payload[k] = v
    else:
        try:
            payload = await request.json()
        except Exception:
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"status": "error", "message": "Validation error", "errors": [{"field": "body -> payload", "message": "Input should be a valid dictionary", "type": "dict_type"}]})

    # payload is now a dict parsed from JSON or form
    nombre = payload.get('nombre') if isinstance(payload, dict) else None
    descripcion = payload.get('descripcion') if isinstance(payload, dict) else None
    precio = payload.get('precio') if isinstance(payload, dict) else None
    peso_gramos = (payload.get('peso_gramos') or payload.get('peso')) if isinstance(payload, dict) else None
    categoria_id = (payload.get('categoria_id') or payload.get('categoria')) if isinstance(payload, dict) else None
    subcategoria_id = (payload.get('subcategoria_id') or payload.get('subcategoria')) if isinstance(payload, dict) else None

    required_fields = [nombre, descripcion, precio, peso_gramos, categoria_id, subcategoria_id]
    if any(f is None for f in required_fields):
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"status": "error", "message": "Por favor, completa todos los campos obligatorios."})

    # Field-specific validations
    if not isinstance(nombre, str) or len(nombre.strip()) < 2:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"status": "error", "message": "El nombre debe tener al menos 2 caracteres."})

    if not isinstance(descripcion, str) or len(descripcion.strip()) < 10:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"status": "error", "message": "La descripción debe tener al menos 10 caracteres."})

    try:
        precio = float(precio)
        if precio <= 0:
            raise ValueError()
    except Exception:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"status": "error", "message": "El precio debe ser un número mayor a 0."})

    try:
        peso_gramos = int(peso_gramos)
        if peso_gramos <= 0:
            raise ValueError()
    except Exception:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"status": "error", "message": "El peso debe ser un entero mayor a 0 (gramos)."})

    imagen_b64 = None
    imagen_filename = None
    # Prefer file upload; if not provided, allow JSON-embedded base64
    if file is not None:
        # Validate filename and extension
        imagen_filename = file.filename or ""
        _, ext = os.path.splitext(imagen_filename.lower())
        if ext not in settings.ALLOWED_IMAGE_EXTENSIONS:
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"status": "error", "message": "Formato o tamaño de imagen no válido."})

        # Read file content to check size and encode
        contents = await file.read()
        if len(contents) > settings.MAX_FILE_SIZE:
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"status": "error", "message": "Formato o tamaño de imagen no válido."})

        # Base64 encode so the worker can store it
        try:
            imagen_b64 = base64.b64encode(contents).decode('utf-8')
        finally:
            await file.close()

    # Build message payload for RabbitMQ. Consumer will perform uniqueness and category checks.
    cantidad_disponible = payload.get('cantidad_disponible', 0)
    # SKU removed: not accepted in request body per new requirement

    message = {
        "nombre": nombre.strip(),
        "descripcion": descripcion.strip(),
        "precio": float(precio),
        "peso_gramos": int(peso_gramos),
        "categoria_id": int(categoria_id),
        "subcategoria_id": int(subcategoria_id),
        "cantidad_disponible": int(cantidad_disponible or 0),
    }
    # Allow cliente to send imagen_b64 and imagen_filename inside the JSON payload
    if not imagen_b64:
        imagen_b64 = payload.get('imagen_b64')
    if not imagen_filename:
        imagen_filename = payload.get('imagen_filename')

    if imagen_b64 and imagen_filename:
        message.update({"imagen_filename": imagen_filename, "imagen_b64": imagen_b64})

    # Publish message to RabbitMQ
    try:
        # AC5: Prevent duplicate product names (case-insensitive) at Producer level
        try:
            existing = db.execute(text("SELECT id FROM Productos WHERE LOWER(nombre) = :name"), {"name": nombre.strip().lower()}).first()
        except Exception as err:
            logger.exception("Error checking existing product name in DB: %s", err)
            return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"status": "error", "message": "Error interno al verificar duplicados."})

        if existing:
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"status": "error", "message": "Ya existe un producto con ese nombre."})

        rabbitmq_producer.connect()
        rabbitmq_producer.publish(queue_name="productos.crear", message=message)
    except Exception as e:
        logger.exception("Error publishing producto.crear message")
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"status": "error", "message": "Error interno al procesar el producto."})
    finally:
        try:
            rabbitmq_producer.close()
        except Exception:
            pass

    return JSONResponse(status_code=status.HTTP_202_ACCEPTED, content={"status": "success", "message": "Producto creado exitosamente"})


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
    # Build base query with filters
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
        q = text(f"SELECT p.id, p.nombre, p.descripcion, p.precio, p.peso_gramos, p.cantidad_disponible, p.categoria_id, p.subcategoria_id, p.activo, p.fecha_creacion FROM Productos p WHERE {where_sql} ORDER BY p.fecha_creacion DESC OFFSET :skip ROWS FETCH NEXT :limit ROWS ONLY")
        rows = db.execute(q, params).fetchall()
    except Exception as e:
        logger.exception("Error querying products: %s", e)
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"status": "error", "message": "Error interno al listar productos."})

    products = []
    if not rows:
        return []

    # Collect category/subcategory ids to fetch names in batch
    cat_ids = set()
    subcat_ids = set()
    prod_ids = []
    for r in rows:
        prod_ids.append(r.id)
        if r.categoria_id:
            cat_ids.add(r.categoria_id)
        if r.subcategoria_id:
            subcat_ids.add(r.subcategoria_id)

    cats = {}
    subcats = {}
    try:
        if cat_ids:
            qcat = text("SELECT id, nombre FROM Categorias WHERE id IN (:ids)").bindparams(ids=tuple(cat_ids))
            # SQLAlchemy text with IN tuple isn't straightforward; build dynamic list
            qcat = text(f"SELECT id, nombre FROM Categorias WHERE id IN ({', '.join([str(int(x)) for x in cat_ids])})")
            for c in db.execute(qcat).fetchall():
                cats[c.id] = {"id": c.id, "nombre": c.nombre}
        if subcat_ids:
            qsub = text(f"SELECT id, nombre FROM Subcategorias WHERE id IN ({', '.join([str(int(x)) for x in subcat_ids])})")
            for s in db.execute(qsub).fetchall():
                subcats[s.id] = {"id": s.id, "nombre": s.nombre}
    except Exception:
        # Non-fatal: proceed without names
        logger.exception("Error fetching category/subcategory names")

    # Fetch images for products in batch
    images_map = {}
    try:
        if prod_ids:
            qimg = text(f"SELECT producto_id, ruta_imagen FROM ProductoImagenes WHERE producto_id IN ({', '.join([str(int(x)) for x in prod_ids])}) ORDER BY orden ASC")
            for img in db.execute(qimg).fetchall():
                images_map.setdefault(img.producto_id, []).append(img.ruta_imagen)
    except Exception:
        logger.exception("Error fetching product images")

    for r in rows:
        prod = {
            "id": int(r.id),
            "nombre": r.nombre,
            "descripcion": r.descripcion,
            "precio": float(r.precio),
            "peso_gramos": int(r.peso_gramos),
            "cantidad_disponible": int(r.cantidad_disponible or 0),
            "categoria_id": int(r.categoria_id) if r.categoria_id is not None else None,
            "subcategoria_id": int(r.subcategoria_id) if r.subcategoria_id is not None else None,
            "activo": bool(r.activo),
            "fecha_creacion": r.fecha_creacion,
            "categoria": cats.get(r.categoria_id),
            "subcategoria": subcats.get(r.subcategoria_id),
            "imagenes": images_map.get(r.id, [])
        }
        products.append(prod)

    return products


@router.get("/{producto_id}", response_model=ProductoResponse)
async def get_product(producto_id: int, db: Session = Depends(get_db)):
    """
    Get product details
    
    Requirements:
    - Return full product information
    - Include images, category, subcategory
    """
    # TODO: Implement get product logic
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")


@router.put("/{producto_id}", response_model=ProductoResponse)
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
    # TODO: Implement update product logic
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")


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
    # 1. Validate product exists
    try:
        prod = db.execute(text("SELECT id FROM Productos WHERE id = :id AND activo = 1"), {"id": producto_id}).first()
    except Exception as e:
        logger.exception("Error checking product existence: %s", e)
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"status": "error", "message": "Error interno al verificar producto."})

    if not prod:
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"status": "error", "message": "Producto no encontrado."})

    # 2. Validate file size and extension
    filename = file.filename or ""
    _, ext = os.path.splitext(filename.lower())
    if ext not in settings.ALLOWED_IMAGE_EXTENSIONS:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"status": "error", "message": "Formato o tamaño de imagen no válido."})

    try:
        contents = await file.read()
    except Exception as e:
        logger.exception("Error reading uploaded file: %s", e)
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"status": "error", "message": "Error al leer el archivo de imagen."})

    if len(contents) > settings.MAX_FILE_SIZE:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"status": "error", "message": "Formato o tamaño de imagen no válido."})

    # 3. Save file to uploads/productos/{producto_id}/
    try:
        upload_dir = os.path.abspath(settings.UPLOAD_DIR)
        product_dir = os.path.join(upload_dir, 'productos', str(producto_id))
        os.makedirs(product_dir, exist_ok=True)
        safe_name = f"{int(time.time())}_{''.join(c if c.isalnum() or c in '._-' else '_' for c in filename)}"
        file_path = os.path.join(product_dir, safe_name)
        with open(file_path, 'wb') as f:
            f.write(contents)
    except Exception as e:
        logger.exception("Error saving uploaded file: %s", e)
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"status": "error", "message": "Error interno al guardar la imagen."})

    # 4. Create ProductoImagen record
    try:
        db.execute(text("INSERT INTO ProductoImagenes (producto_id, ruta_imagen, es_principal, orden) VALUES (:producto_id, :ruta_imagen, 1, 0)"), {"producto_id": producto_id, "ruta_imagen": file_path})
        db.commit()
    except Exception as e:
        logger.exception("Error inserting ProductoImagenes record: %s", e)
        # attempt to remove saved file on failure
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception:
            pass
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"status": "error", "message": "Error interno al guardar la imagen en la base de datos."})

    # 5. Publish productos.imagen.crear queue message
    try:
        message = {"producto_id": producto_id, "ruta_imagen": file_path}
        rabbitmq_producer.connect()
        rabbitmq_producer.publish(queue_name="productos.imagen.crear", message=message)
    except Exception as e:
        logger.exception("Error publishing productos.imagen.crear message: %s", e)
        # Not critical for upload success; return warning but 201
    finally:
        try:
            rabbitmq_producer.close()
        except Exception:
            pass

    return JSONResponse(status_code=status.HTTP_201_CREATED, content={"status": "success", "message": "Imagen subida correctamente", "ruta": file_path})


@router.get("/{producto_id}/images")
async def list_product_images(producto_id: int, db: Session = Depends(get_db)):
    """List all images for a product

    Returns an array of image records with `id`, `ruta_imagen`, `es_principal` and `orden`.
    """
    # Verify product exists and is active
    try:
        prod = db.execute(text("SELECT id FROM Productos WHERE id = :id AND activo = 1"), {"id": producto_id}).first()
    except Exception as e:
        logger.exception("Error checking product existence for images: %s", e)
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"status": "error", "message": "Error interno al verificar producto."})

    if not prod:
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"status": "error", "message": "Producto no encontrado."})

    try:
        q = text("SELECT id, producto_id, ruta_imagen, es_principal, orden FROM ProductoImagenes WHERE producto_id = :id ORDER BY orden ASC")
        rows = db.execute(q, {"id": producto_id}).fetchall()
    except Exception as e:
        logger.exception("Error querying product images: %s", e)
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"status": "error", "message": "Error interno al listar imágenes."})

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
    # TODO: Implement delete image logic
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")


@router.delete("/{producto_id}")
async def delete_product(producto_id: int, db: Session = Depends(get_db)):
    """
    Soft delete product (mark as inactive)
    
    Requirements:
    - Set activo=False instead of deleting
    - Publishes productos.eliminar queue message
    """
    # 1. Verify product exists and is active
    try:
        prod = db.execute(text("SELECT id, activo FROM Productos WHERE id = :id"), {"id": producto_id}).first()
    except Exception as e:
        logger.exception("Error checking product for delete: %s", e)
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"status": "error", "message": "Error interno al verificar producto."})

    if not prod or not getattr(prod, 'id', None):
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"status": "error", "message": "Producto no encontrado."})

    if getattr(prod, 'activo', 0) == 0:
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"status": "error", "message": "Producto no encontrado."})

    # 2. Perform soft-delete (activo = 0) using OUTPUT to verify the change
    try:
        upd = text("""
        UPDATE Productos
        SET activo = 0
        OUTPUT inserted.id AS id, inserted.activo AS activo
        WHERE id = :id
        """)
        res = db.execute(upd, {"id": producto_id})
        row = res.fetchone()
        db.commit()
        if not row:
            # Nothing updated, return 404
            return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"status": "error", "message": "Producto no encontrado."})
        # row.activo should be 0 now
        updated_activo = int(row.activo)
        if updated_activo != 0:
            logger.warning("Product updated but activo != 0: %s", row)
    except Exception as e:
        logger.exception("Error marking product as inactive: %s", e)
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"status": "error", "message": "Error interno al eliminar el producto."})

    # 3. Publish productos.eliminar message to RabbitMQ
    try:
        message = {"producto_id": int(producto_id)}
        rabbitmq_producer.connect()
        rabbitmq_producer.publish(queue_name="productos.eliminar", message=message)
    except Exception as e:
        logger.exception("Error publishing productos.eliminar message: %s", e)
        # Not fatal for client response
    finally:
        try:
            rabbitmq_producer.close()
        except Exception:
            pass

    return JSONResponse(status_code=status.HTTP_200_OK, content={"status": "success", "message": "Producto eliminado correctamente"})
