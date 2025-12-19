"""
Public orders router: Create and view orders for authenticated users
Handles user order creation and retrieval
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Dict, Any, Optional, Tuple
from app.presentation.schemas import (
    PedidoResponse,
)
from app.core.database import get_db
from app.presentation.routers.auth import get_current_user
from app.presentation.routers.orders import _pedido_to_response
from app.presentation.routers.auth import UsuarioPublicResponse
import app.domain.models as models
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/pedidos",
    tags=["public-orders"]
)

# Constants
MIN_ADDRESS_LENGTH = 10
MIN_PHONE_DIGITS = 7
MAX_PHONE_DIGITS = 15
DEFAULT_ORDER_STATE = 'Pendiente'
DEFAULT_PAYMENT_METHOD = "No especificado"
DEFAULT_SHIPPING_COST = 0.0

# Error codes
ERROR_EMPTY_CART = "EMPTY_CART"
ERROR_NO_ADDRESS = "NO_ADDRESS"
ERROR_INVALID_ADDRESS = "INVALID_ADDRESS"
ERROR_ADDRESS_NOT_FOUND = "ADDRESS_NOT_FOUND"
ERROR_INVALID_PHONE = "INVALID_PHONE"
ERROR_INVALID_QUANTITY = "INVALID_QUANTITY"
ERROR_INVALID_PRICE = "INVALID_PRICE"


def _normalize_phone(phone: str) -> str:
    """Remove phone formatting characters"""
    return phone.replace("+", "").replace("-", "").replace(" ", "")


def _validate_phone(phone: str) -> None:
    """Validate phone format"""
    normalized = _normalize_phone(phone)
    if not normalized.isdigit():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"status": "error", "message": "El número de teléfono debe contener solo dígitos."}
        )
    if len(normalized) < MIN_PHONE_DIGITS or len(normalized) > MAX_PHONE_DIGITS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"status": "error", "message": f"El número de teléfono debe tener entre {MIN_PHONE_DIGITS} y {MAX_PHONE_DIGITS} dígitos."}
        )


def _get_address_from_payload(payload: Dict[str, Any], user_id: int, db: Session) -> str:
    """
    Extract and validate address from payload.
    Supports both direct address string and address ID reference.
    """
    direccion_entrega = payload.get("direccionEnvio") or payload.get("direccion_entrega")
    direccion_id = payload.get("direccion_id") or payload.get("direccionId")
    
    # If address ID provided, fetch the address
    if direccion_id and not direccion_entrega:
        direccion = (
            db.query(models.Direccion)
            .filter(models.Direccion.id == int(direccion_id), models.Direccion.usuario_id == user_id)
            .first()
        )
        if not direccion:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"status": "error", "message": "La dirección seleccionada no existe.", "code": ERROR_ADDRESS_NOT_FOUND}
            )
        direccion_entrega = direccion.direccion_completa
    
    # Validate address string
    if not direccion_entrega or len(str(direccion_entrega).strip()) < MIN_ADDRESS_LENGTH:
        has_addresses = db.query(models.Direccion).filter(models.Direccion.usuario_id == user_id).count() > 0
        if not has_addresses:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"status": "error", "message": "Debes agregar al menos una dirección de entrega antes de realizar un pedido.", "code": ERROR_NO_ADDRESS}
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"status": "error", "message": "Selecciona una dirección de entrega válida.", "code": ERROR_INVALID_ADDRESS}
            )
    
    return direccion_entrega


def _get_contact_phone(payload: Dict[str, Any], usuario: models.Usuario) -> str:
    """
    Get contact phone from payload or user profile, and validate it.
    """
    telefono_contacto = payload.get("telefonoContacto") or payload.get("telefono_contacto") or usuario.telefono
    
    if not telefono_contacto:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"status": "error", "message": "Debes proporcionar un número de teléfono de contacto."}
        )
    
    _validate_phone(telefono_contacto)
    return _normalize_phone(telefono_contacto)


def _validate_order_items(productos: List[Dict[str, Any]]) -> None:
    """Validate that order has items"""
    if not productos or len(productos) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"status": "error", "message": "El carrito está vacío.", "code": ERROR_EMPTY_CART}
        )


def _parse_product_item(item: Dict[str, Any]) -> Tuple[int, int, float]:
    """
    Parse product item from payload.
    Returns: (producto_id, cantidad, precio_unitario)
    """
    producto_id = int(item.get("sku") or item.get("producto_id") or item.get("id"))
    cantidad = int(item.get("cantidad") or item.get("quantity") or 1)
    precio_unitario = float(item.get("precioUnitario") or item.get("precio_unitario") or item.get("precio") or 0.0)
    
    if cantidad <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"status": "error", "message": f"La cantidad del producto {producto_id} debe ser mayor a 0.", "code": ERROR_INVALID_QUANTITY}
        )
    
    if precio_unitario < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"status": "error", "message": f"El precio del producto {producto_id} no puede ser negativo.", "code": ERROR_INVALID_PRICE}
        )
    
    return producto_id, cantidad, precio_unitario


def _create_order_items(pedido_id: int, productos: List[Dict[str, Any]], db: Session) -> float:
    """
    Create order items and calculate subtotal.
    Returns: subtotal amount
    """
    subtotal = 0.0
    
    for item in productos:
        producto_id, cantidad, precio_unitario = _parse_product_item(item)
        subtotal += cantidad * precio_unitario
        
        pedido_item = models.PedidoItem(
            pedido_id=pedido_id,
            producto_id=producto_id,
            cantidad=cantidad,
            precio_unitario=precio_unitario,
        )
        db.add(pedido_item)
    
    return subtotal


def _get_shipping_and_payment(payload: Dict[str, Any]) -> Tuple[float, str]:
    """
    Extract shipping cost and payment method from payload.
    Returns: (costo_envio, metodo_pago)
    """
    costo_envio = float(payload.get("costoEnvio") or payload.get("costo_envio") or DEFAULT_SHIPPING_COST)
    metodo_pago = payload.get("metodoPago") or payload.get("metodo_pago") or DEFAULT_PAYMENT_METHOD
    return costo_envio, metodo_pago


@router.post("/", response_model=PedidoResponse, status_code=status.HTTP_201_CREATED)
async def create_user_order(
    payload: dict,
    current_user: UsuarioPublicResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new order for the authenticated user
    
    Expected payload format:
    {
        "productos": [
            {
                "sku": int,  # producto_id
                "nombre": str,
                "cantidad": int,
                "precioUnitario": float
            }
        ],
        "direccionEnvio": str,
        "telefonoContacto": str (optional, will use user's phone if not provided),
        "notaEspecial": str (optional),
        "costoEnvio": float (optional),
        "metodoPago": str (optional)
    }
    """
    try:
        # Validate cart is not empty
        productos = payload.get("productos", [])
        _validate_order_items(productos)
        
        # Get and validate address
        direccion_entrega = _get_address_from_payload(payload, current_user.id, db)
        
        # Get user and validate contact phone
        usuario = db.query(models.Usuario).filter(models.Usuario.id == current_user.id).first()
        if not usuario:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"status": "error", "message": "Usuario no encontrado."}
            )
        
        telefono_contacto = _get_contact_phone(payload, usuario)
        
        # Create order
        pedido = models.Pedido(
            usuario_id=current_user.id,
            estado=DEFAULT_ORDER_STATE,
            direccion_entrega=direccion_entrega,
            telefono_contacto=telefono_contacto,
            nota_especial=payload.get("notaEspecial") or payload.get("nota_especial"),
        )
        db.add(pedido)
        db.flush()
        
        # Create order items and calculate subtotal
        subtotal = _create_order_items(pedido.id, productos, db)
        
        # Get shipping and payment information
        costo_envio, metodo_pago = _get_shipping_and_payment(payload)
        
        # Update order with financial information
        pedido.subtotal = subtotal
        pedido.costo_envio = costo_envio
        pedido.metodo_pago = metodo_pago
        pedido.total = subtotal + costo_envio
        
        db.commit()
        db.refresh(pedido)
        
        logger.info(f"Order created: pedido_id={pedido.id}, usuario_id={current_user.id}, total={pedido.total}")
        
        return _pedido_to_response(db, pedido)
        
    except HTTPException:
        db.rollback()
        raise
    except ValueError as e:
        db.rollback()
        logger.error(f"Validation error creating order: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"status": "error", "message": f"Error de validación: {str(e)}"}
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating order: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"status": "error", "message": "Error interno al procesar el pedido."}
        )


@router.get("/", response_model=List[PedidoResponse])
@router.get("/mis-pedidos", response_model=List[PedidoResponse])
async def get_user_orders(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: UsuarioPublicResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get orders for the authenticated user with optional pagination
    
    Returns:
    - All orders for the current user
    - Sorted by fecha_creacion DESC (newest first)
    - Includes order items and product details
    - Optional pagination with skip and limit
    """
    try:
        pedidos = (
            db.query(models.Pedido)
            .filter(models.Pedido.usuario_id == current_user.id)
            .order_by(desc(models.Pedido.fecha_creacion))
            .offset(skip)
            .limit(limit)
            .all()
        )
        
        return [_pedido_to_response(db, p) for p in pedidos]
    except Exception as e:
        logger.error(f"Error fetching user orders: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"status": "error", "message": "Error al obtener los pedidos."}
        )


@router.get("/{pedido_id}", response_model=PedidoResponse)
async def get_user_order(
    pedido_id: int,
    current_user: UsuarioPublicResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific order by ID (only if it belongs to the authenticated user)
    """
    try:
        pedido = db.query(models.Pedido).filter(
            models.Pedido.id == pedido_id,
            models.Pedido.usuario_id == current_user.id
        ).first()
        
        if not pedido:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"status": "error", "message": "Pedido no encontrado."}
            )
        
        return _pedido_to_response(db, pedido)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching order {pedido_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"status": "error", "message": "Error al obtener el pedido."}
        )
