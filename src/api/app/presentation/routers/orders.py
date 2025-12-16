"""
Orders router moved to presentation layer with updated schema imports.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from sqlalchemy import desc, text
from app.presentation.schemas import (
	PedidoCreate,
	PedidoResponse,
	PedidoItemResponse,
	PedidoEstadoUpdate,
)
from app.database import get_db
from app.utils.rabbitmq import RabbitMQProducer
from app.routers.auth import get_current_user
import app.models as models
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
	prefix="/api/admin/pedidos",
	tags=["orders"]
)


def _pedido_to_response(db, pedido: models.Pedido):
	items = db.query(models.PedidoItem).filter(models.PedidoItem.pedido_id == pedido.id).all()
	items_resp = []
    
	for item in items:
		producto = db.execute(
			text("""
				SELECT p.id, p.nombre, 
					   (SELECT TOP 1 ruta_imagen FROM ProductoImagenes 
						WHERE producto_id = p.id ORDER BY orden ASC) as imagen
				FROM Productos p 
				WHERE p.id = :producto_id
			"""),
			{"producto_id": item.producto_id}
		).fetchone()
        
		item_data = {
			"id": item.id,
			"producto_id": item.producto_id,
			"cantidad": item.cantidad,
			"precio_unitario": float(item.precio_unitario),
		}
        
		if producto:
			item_data["producto_nombre"] = producto.nombre
			item_data["producto_imagen"] = producto.imagen
        
		items_resp.append(item_data)
    
	usuario = db.query(models.Usuario).filter(models.Usuario.id == pedido.usuario_id).first()
	cliente_nombre = usuario.nombre_completo if usuario else f"Usuario ID: {pedido.usuario_id}"

	return {
		"id": pedido.id,
		"usuario_id": pedido.usuario_id,
		"clienteNombre": cliente_nombre,
		"estado": pedido.estado,
		"total": float(pedido.total),
		"metodo_pago": pedido.metodo_pago or 'Efectivo',
		"direccion_entrega": pedido.direccion_entrega,
		"municipio": pedido.municipio,
		"departamento": pedido.departamento,
		"pais": pedido.pais or 'Colombia',
		"telefono_contacto": pedido.telefono_contacto,
		"fecha_creacion": pedido.fecha_creacion,
		"items": items_resp,
	}


@router.get("/", response_model=List[PedidoResponse])
async def list_orders(
	estado: str = Query(None, regex="^(Pendiente|Enviado|Entregado|Cancelado)$"),
	usuario_id: int = Query(None),
	skip: int = Query(0, ge=0),
	limit: int = Query(20, ge=1, le=100),
	db: Session = Depends(get_db)
):
	q = db.query(models.Pedido)
	if estado:
		q = q.filter(models.Pedido.estado == estado)
	if usuario_id:
		q = q.filter(models.Pedido.usuario_id == usuario_id)

	pedidos = q.order_by(desc(models.Pedido.fecha_creacion)).offset(skip).limit(limit).all()
	return [_pedido_to_response(db, p) for p in pedidos]

@router.post("/", response_model=PedidoResponse, status_code=status.HTTP_201_CREATED)
async def create_order(payload: PedidoCreate, db: Session = Depends(get_db)):
	usuario = db.query(models.Usuario).filter(models.Usuario.id == payload.usuario_id).first()
	if not usuario:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Usuario no existe")

	pedido = models.Pedido(
		usuario_id=payload.usuario_id,
		estado='Pendiente',
		direccion_entrega=payload.direccion_entrega,
		municipio=payload.municipio,
		departamento=payload.departamento,
		pais=payload.pais or 'Colombia',
		telefono_contacto=payload.telefono_contacto,
		metodo_pago=payload.metodo_pago or 'Efectivo',
		nota_especial=payload.nota_especial,
	)
	db.add(pedido)
	db.flush()

	total = 0
	items_payload = getattr(payload, 'items', []) or []
	for it in items_payload:
		producto_id = int(it.get('producto_id'))
		cantidad = int(it.get('cantidad'))
		precio = float(it.get('precio_unitario')) if it.get('precio_unitario') is not None else 0.0
        
		query_producto = text("""
			SELECT id, nombre, cantidad_disponible 
			FROM Productos 
			WHERE id = :producto_id
		""")
		result = db.execute(query_producto, {"producto_id": producto_id})
		producto = result.fetchone()
        
		if not producto:
			db.rollback()
			raise HTTPException(
				status_code=status.HTTP_400_BAD_REQUEST, 
				detail=f"Producto con ID {producto_id} no encontrado"
			)
        
		if producto.cantidad_disponible < cantidad:
			db.rollback()
			raise HTTPException(
				status_code=status.HTTP_400_BAD_REQUEST,
				detail=f"Stock insuficiente para {producto.nombre}. Disponible: {producto.cantidad_disponible}, Solicitado: {cantidad}"
			)
        
		update_stock = text("""
			UPDATE Productos 
			SET cantidad_disponible = cantidad_disponible - :cantidad 
			WHERE id = :producto_id
		""")
		db.execute(update_stock, {"cantidad": cantidad, "producto_id": producto_id})
        
		total += cantidad * precio
		pi = models.PedidoItem(
			pedido_id=pedido.id,
			producto_id=producto_id,
			cantidad=cantidad,
			precio_unitario=precio,
		)
		db.add(pi)

	pedido.total = total
	db.add(pedido)
	db.commit()
	db.refresh(pedido)

	return _pedido_to_response(db, pedido)


@router.put("/{pedido_id}", response_model=PedidoResponse)
async def update_order(pedido_id: int, payload: PedidoCreate, db: Session = Depends(get_db)):
	pedido = db.query(models.Pedido).filter(models.Pedido.id == pedido_id).first()
	if not pedido:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pedido no encontrado")

	pedido.direccion_entrega = payload.direccion_entrega
	pedido.telefono_contacto = payload.telefono_contacto
	pedido.nota_especial = payload.nota_especial
	db.add(pedido)

	db.query(models.PedidoItem).filter(models.PedidoItem.pedido_id == pedido.id).delete()
	total = 0
	items_payload = getattr(payload, 'items', []) or []
	for it in items_payload:
		producto_id = int(it.get('producto_id'))
		cantidad = int(it.get('cantidad'))
		precio = float(it.get('precio_unitario')) if it.get('precio_unitario') is not None else 0.0
		total += cantidad * precio
		pi = models.PedidoItem(
			pedido_id=pedido.id,
			producto_id=producto_id,
			cantidad=cantidad,
			precio_unitario=precio,
		)
		db.add(pi)

	pedido.total = total
	db.commit()
	db.refresh(pedido)
	return _pedido_to_response(db, pedido)


@router.delete("/{pedido_id}")
async def delete_order(pedido_id: int, db: Session = Depends(get_db)):
	pedido = db.query(models.Pedido).filter(models.Pedido.id == pedido_id).first()
	if not pedido:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pedido no encontrado")
	db.delete(pedido)
	db.commit()
	return {"status": "success", "message": "Pedido eliminado"}

@router.get("/{pedido_id}", response_model=PedidoResponse)
async def get_order(pedido_id: int, db: Session = Depends(get_db)):
	pedido = db.query(models.Pedido).filter(models.Pedido.id == pedido_id).first()
	if not pedido:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pedido no encontrado")
	return _pedido_to_response(db, pedido)


@router.put("/{pedido_id}/status", response_model=PedidoResponse)
async def update_order_status(
	pedido_id: int,
	request: PedidoEstadoUpdate,
	db: Session = Depends(get_db)
):
	pedido = db.query(models.Pedido).filter(models.Pedido.id == pedido_id).first()
	if not pedido:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pedido no encontrado")

	estado_anterior = pedido.estado
	pedido.estado = request.estado
	db.add(pedido)

	historial = models.PedidosHistorialEstado(
		pedido_id=pedido.id,
		estado_anterior=estado_anterior,
		estado_nuevo=request.estado,
		usuario_id=None,
		nota=request.nota,
	)
	db.add(historial)
	db.commit()
	db.refresh(pedido)

	try:
		producer = RabbitMQProducer()
		producer.connect()
		message = {
			"pedido_id": pedido.id,
			"estado_anterior": estado_anterior,
			"estado_nuevo": request.estado,
		}
		producer.publish("pedido.estado.cambiado", message)
	except Exception:
		pass
	finally:
		try:
			producer.close()
		except Exception:
			pass

	return _pedido_to_response(db, pedido)


@router.get("/{pedido_id}/history")
async def get_order_history(pedido_id: int, db: Session = Depends(get_db)):
	items = (
		db.query(models.PedidosHistorialEstado)
		.filter(models.PedidosHistorialEstado.pedido_id == pedido_id)
		.order_by(desc(models.PedidosHistorialEstado.fecha))
		.all()
	)

	return [
		{
			"id": it.id,
			"pedido_id": it.pedido_id,
			"estado_anterior": it.estado_anterior,
			"estado_nuevo": it.estado_nuevo,
			"usuario_id": it.usuario_id,
			"nota": it.nota,
			"fecha": it.fecha,
		}
		for it in items
	]
    


@router.get("/user/{usuario_id}", response_model=List[PedidoResponse])
async def get_user_orders(
	usuario_id: int,
	skip: int = Query(0, ge=0),
	limit: int = Query(20, ge=1, le=100),
	db: Session = Depends(get_db)
):
	pedidos = (
		db.query(models.Pedido)
		.filter(models.Pedido.usuario_id == usuario_id)
		.order_by(desc(models.Pedido.fecha_creacion))
		.all()
	)
	return [_pedido_to_response(db, p) for p in pedidos]


public_router = APIRouter(
	prefix="/api/pedidos",
	tags=["pedidos-public"]
)

@public_router.post("/", response_model=PedidoResponse, status_code=status.HTTP_201_CREATED)
async def create_customer_order(payload: PedidoCreate, db: Session = Depends(get_db)):
	usuario = db.query(models.Usuario).filter(models.Usuario.id == payload.usuario_id).first()
	if not usuario:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Usuario no existe")

	pedido = models.Pedido(
		usuario_id=payload.usuario_id,
		estado='Pendiente',
		direccion_entrega=payload.direccion_entrega,
		municipio=payload.municipio,
		departamento=payload.departamento,
		pais=payload.pais or 'Colombia',
		telefono_contacto=payload.telefono_contacto,
		metodo_pago=payload.metodo_pago or 'Efectivo',
		nota_especial=payload.nota_especial,
	)
	db.add(pedido)
	db.flush()

	total = 0
	items_payload = getattr(payload, 'items', []) or []
	for it in items_payload:
		producto_id = int(it.get('producto_id'))
		cantidad = int(it.get('cantidad'))
		precio = float(it.get('precio_unitario')) if it.get('precio_unitario') is not None else 0.0
        
		query_producto = text("""
			SELECT id, nombre, cantidad_disponible 
			FROM Productos 
			WHERE id = :producto_id
		""")
		result = db.execute(query_producto, {"producto_id": producto_id})
		producto = result.fetchone()
        
		if not producto:
			db.rollback()
			raise HTTPException(
				status_code=status.HTTP_400_BAD_REQUEST, 
				detail=f"Producto con ID {producto_id} no encontrado"
			)
        
		if producto.cantidad_disponible < cantidad:
			db.rollback()
			raise HTTPException(
				status_code=status.HTTP_400_BAD_REQUEST,
				detail=f"Stock insuficiente para {producto.nombre}. Disponible: {producto.cantidad_disponible}, Solicitado: {cantidad}"
			)
        
		update_stock = text("""
			UPDATE Productos 
			SET cantidad_disponible = cantidad_disponible - :cantidad 
			WHERE id = :producto_id
		""")
		db.execute(update_stock, {"cantidad": cantidad, "producto_id": producto_id})
        
		total += cantidad * precio
		pi = models.PedidoItem(
			pedido_id=pedido.id,
			producto_id=producto_id,
			cantidad=cantidad,
			precio_unitario=precio,
		)
		db.add(pi)

	pedido.total = total
	db.add(pedido)
	db.commit()
	db.refresh(pedido)

	logger.info(f"Order created: pedido_id={pedido.id}, usuario_id={payload.usuario_id}, total={total}")
	return _pedido_to_response(db, pedido)


@public_router.get("/my-orders", response_model=List[PedidoResponse])
async def get_my_orders(
	skip: int = Query(0, ge=0),
	limit: int = Query(20, ge=1, le=100),
	db: Session = Depends(get_db),
	current_user = Depends(get_current_user)
):
	pedidos = (
		db.query(models.Pedido)
		.filter(models.Pedido.usuario_id == current_user.id)
		.order_by(desc(models.Pedido.fecha_creacion))
		.offset(skip)
		.limit(limit)
		.all()
	)
    
	return [_pedido_to_response(db, p) for p in pedidos]
