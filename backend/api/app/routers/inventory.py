"""
Inventory router: Manage product stock and restocking
Handles HU_MANAGE_INVENTORY
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List
from app.schemas import ReabastecimientoRequest, InventarioHistorialResponse
from app.database import get_db
import logging
import uuid

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/admin/productos",
    tags=["inventory"]
)


@router.post("/{producto_id}/reabastecer")
async def restock_product(
    producto_id: int,
    request: ReabastecimientoRequest,
    db: Session = Depends(get_db)
):
    """
    Restock product inventory
    
    Requirements (HU_MANAGE_INVENTORY):
    - Add stock quantity to product
    - cantidad > 0
    - Create audit entry in InventarioHistorial
    - Record usuario_id, timestamp, tipo_movimiento='REABASTECIMIENTO'
    - Publishes inventario.actualizar queue message
    - Rate limiting: max 10 restock operations per product per hour
    """
    # 1. Validate producto exists and cantidad
    try:
        prod = db.execute(text("SELECT id, cantidad_disponible FROM Productos WHERE id = :id"), {"id": producto_id}).first()
    except Exception as e:
        logger.exception("Error checking product for restock: %s", e)
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"status": "error", "message": "Error interno al verificar producto."})

    if not prod:
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"status": "error", "message": "Producto no encontrado."})

    cantidad = request.cantidad
    if cantidad is None or int(cantidad) <= 0:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"status": "error", "message": "La cantidad debe ser un número mayor a 0."})

    # 2. Rate limiting: max 10 reabastecimientos por producto en la última hora
    try:
        qcount = text("SELECT COUNT(1) AS cnt FROM InventarioHistorial WHERE producto_id = :id AND tipo_movimiento = 'REABASTECIMIENTO' AND fecha >= DATEADD(hour, -1, GETUTCDATE())")
        cnt_row = db.execute(qcount, {"id": producto_id}).first()
        cnt = int(getattr(cnt_row, 'cnt', 0) or 0)
        if cnt >= 10:
            return JSONResponse(status_code=status.HTTP_429_TOO_MANY_REQUESTS, content={"status": "error", "message": "Límite de reabastecimientos por hora alcanzado para este producto."})
    except Exception:
        logger.exception("Error checking rate limit for restock")

    # 3. Perform update and historial insert inside a transaction
    try:
        cantidad_anterior = int(getattr(prod, 'cantidad_disponible', 0) or 0)
        cantidad_nueva = cantidad_anterior + int(cantidad)

        upd = text("UPDATE Productos SET cantidad_disponible = :nueva, fecha_actualizacion = GETUTCDATE() WHERE id = :id")
        db.execute(upd, {"nueva": cantidad_nueva, "id": producto_id})

        ins = text("INSERT INTO InventarioHistorial (producto_id, cantidad_anterior, cantidad_nueva, tipo_movimiento, referencia, usuario_id) VALUES (:producto_id, :cantidad_anterior, :cantidad_nueva, 'REABASTECIMIENTO', :referencia, NULL)")
        db.execute(ins, {"producto_id": producto_id, "cantidad_anterior": cantidad_anterior, "cantidad_nueva": cantidad_nueva, "referencia": request.referencia})

        db.commit()
    except Exception as e:
        logger.exception("Error performing restock transaction: %s", e)
        db.rollback()
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"status": "error", "message": "Error interno al reabastecer el producto."})

    # 4. Publish inventario.actualizar message (best-effort)
    try:
        from app.utils.rabbitmq import rabbitmq_producer
        msg = {"requestId": str(uuid.uuid4()), "productoId": int(producto_id), "cantidad_anterior": int(cantidad_anterior), "cantidad_nueva": int(cantidad_nueva)}
        rabbitmq_producer.connect()
        rabbitmq_producer.publish(queue_name="inventario.actualizar", message=msg)
    except Exception:
        logger.exception("Error publishing inventario.actualizar message")
    finally:
        try:
            rabbitmq_producer.close()
        except Exception:
            pass

    return JSONResponse(status_code=status.HTTP_200_OK, content={"status": "success", "message": "Reabastecimiento realizado correctamente", "cantidad_anterior": cantidad_anterior, "cantidad_nueva": cantidad_nueva})


@router.get("/{producto_id}/historial", response_model=List[InventarioHistorialResponse])
async def get_inventory_history(
    producto_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """
    Get inventory history for product
    
    Requirements (HU_MANAGE_INVENTORY):
    - Returns all inventory movements (restock, sales, adjustments)
    - Sorted by date descending (newest first)
    - Includes usuario_id, tipo_movimiento, cantidad changes
    - Pagination support
    """
    # 1. Validate producto exists
    try:
        prod = db.execute(text("SELECT id FROM Productos WHERE id = :id"), {"id": producto_id}).first()
    except Exception as e:
        logger.exception("Error checking product for historial: %s", e)
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"status": "error", "message": "Error interno al verificar producto."})

    if not prod:
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"status": "error", "message": "Producto no encontrado."})

    # 2. Query InventarioHistorial
    try:
        q = text("SELECT id, producto_id, cantidad_anterior, cantidad_nueva, tipo_movimiento, referencia, usuario_id, fecha FROM InventarioHistorial WHERE producto_id = :id ORDER BY fecha DESC OFFSET :skip ROWS FETCH NEXT :limit ROWS ONLY")
        rows = db.execute(q, {"id": producto_id, "skip": int(skip), "limit": int(limit)}).fetchall()
    except Exception as e:
        logger.exception("Error querying InventarioHistorial: %s", e)
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"status": "error", "message": "Error interno al obtener el historial de inventario."})

    result = []
    for r in rows:
        result.append({
            "id": int(r.id),
            "producto_id": int(r.producto_id),
            "cantidad_anterior": int(r.cantidad_anterior),
            "cantidad_nueva": int(r.cantidad_nueva),
            "tipo_movimiento": r.tipo_movimiento,
            "referencia": r.referencia,
            "usuario_id": int(r.usuario_id) if getattr(r, 'usuario_id', None) is not None else None,
            "fecha": r.fecha
        })

    return result


@router.get("/{producto_id}/stock")
async def get_stock(producto_id: int, db: Session = Depends(get_db)):
    """
    Get current stock for product
    
    Requirements:
    - Return current cantidad_disponible
    - Return last restock date/time
    - Return total movements count
    """
    try:
        prod = db.execute(text("SELECT cantidad_disponible FROM Productos WHERE id = :id"), {"id": producto_id}).first()
    except Exception as e:
        logger.exception("Error checking product for stock: %s", e)
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"status": "error", "message": "Error interno al verificar producto."})

    if not prod:
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"status": "error", "message": "Producto no encontrado."})

    cantidad_disponible = int(getattr(prod, 'cantidad_disponible', 0) or 0)

    try:
        qlast = text("SELECT TOP 1 fecha FROM InventarioHistorial WHERE producto_id = :id AND tipo_movimiento = 'REABASTECIMIENTO' ORDER BY fecha DESC")
        last_row = db.execute(qlast, {"id": producto_id}).first()
        last_restock = last_row.fecha if last_row else None

        qcount = text("SELECT COUNT(1) AS cnt FROM InventarioHistorial WHERE producto_id = :id")
        cnt_row = db.execute(qcount, {"id": producto_id}).first()
        movimientos_total = int(getattr(cnt_row, 'cnt', 0) or 0)
    except Exception:
        logger.exception("Error fetching stock metadata")
        last_restock = None
        movimientos_total = 0

    return {"cantidad_disponible": cantidad_disponible, "last_restock": last_restock, "movimientos_total": movimientos_total}
