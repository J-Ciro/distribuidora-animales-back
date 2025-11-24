from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from ..database import SessionLocal
from .. import models, schemas, rabbitmq

router = APIRouter(prefix="/api/admin/productos", tags=["productos"]) 

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get('/search', response_model=List[schemas.ProductoOut])
def search_productos(q: Optional[str] = Query(None, description="Texto de búsqueda"), db: Session = Depends(get_db)):
    query = db.query(models.Producto)
    if q:
        query = query.filter(models.Producto.nombre.ilike(f"%{q}%"))
    productos = query.limit(50).all()
    return [schemas.ProductoOut.from_orm(p) for p in productos]

@router.get('/{id}', response_model=schemas.ProductoOut)
def get_producto(id: int, db: Session = Depends(get_db)):
    producto = db.query(models.Producto).filter(models.Producto.id == id).first()
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado.")
    return schemas.ProductoOut.from_orm(producto)

@router.get('/{id}/stock')
def get_stock(id: int, db: Session = Depends(get_db)):
    producto = db.query(models.Producto).filter(models.Producto.id == id).first()
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado.")
    resp = {"stock": producto.stock}
    if producto.stock >= 10:
        resp["note"] = "El producto tiene al menos 10 unidades en stock."
    return resp

@router.post('/{id}/reabastecer')
async def reabastecer_producto(id: int, body: schemas.ReabastecerIn = None, db: Session = Depends(get_db)):
    # Validaciones exactas de mensaje
    if body is None:
        raise HTTPException(status_code=400, detail="Por favor, completa todos los campos obligatorios.")
    if body.cantidad is None:
        raise HTTPException(status_code=400, detail="Por favor, completa todos los campos obligatorios.")
    if not isinstance(body.cantidad, int) or body.cantidad <= 0:
        raise HTTPException(status_code=400, detail="La cantidad debe ser un número positivo.")

    producto = db.query(models.Producto).filter(models.Producto.id == id).first()
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado.")

    payload = rabbitmq.build_payload(id, body.cantidad)
    # Publicar (no esperamos respuesta síncrona)
    await rabbitmq.publish_reabastecer(payload)
    return {"message": "Mensaje publicado", "requestId": payload['requestId']} 

@router.get('/{id}/inventario/historial', response_model=List[schemas.InventarioHistorialOut])
def historial_inventario(id: int, db: Session = Depends(get_db)):
    rows = db.query(models.InventarioHistorial).filter(models.InventarioHistorial.producto_id == id).order_by(models.InventarioHistorial.created_at.desc()).limit(100).all()
    return [schemas.InventarioHistorialOut(
        id=r.id,
        producto_id=r.producto_id,
        cantidad=r.cantidad,
        accion=r.accion,
        request_id=r.request_id,
        created_at=r.created_at.isoformat() if r.created_at else None
    ) for r in rows]
