"""
Payments Router: REST endpoints for payment processing with Stripe
Handles creation of payment intents, confirmation, and status checks
Refactored to follow SOLID principles with separated concerns
"""
from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session
from typing import List
import logging

from app.core.database import get_db
from app.presentation.routers.auth import get_current_user
from app.presentation.schemas import (
    CreatePaymentIntentRequest,
    PaymentIntentResponse,
    PaymentConfirmationRequest,
    PaymentStatusResponse,
    PaymentStatusQueryResponse,
    TransaccionPagoResponse,
    TransaccionPagoListResponse,
)
from app.application.services.stripe_service import stripe_service
from app.application.services.payment_service import payment_service
from app.application.validators.payment_validator import PaymentValidator
from app.infrastructure.repositories.payment_repository import PaymentRepository
import app.domain.models as models

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/pagos",
    tags=["payments"]
)


@router.post(
    "/create-payment-intent",
    response_model=PaymentIntentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Payment Intent",
    description="Create a Stripe Payment Intent for order payment"
)
async def create_payment_intent(
    request: CreatePaymentIntentRequest,
    current_user: models.Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a Stripe Payment Intent for an order
    
    Requirements:
    - User must be authenticated
    - Order must exist and belong to user
    - Order must be in "Pendiente de Pago" status
    - All items must have sufficient stock
    
    Returns Payment Intent with client_secret for frontend
    """
    try:
        logger.info(f"Creating payment intent for order {request.pedido_id}, user {current_user.id}")
        
        # Initialize services
        validator = PaymentValidator()
        repository = PaymentRepository(db)
        
        # Validate request data
        validator.validate_amount(request.amount)
        validator.validate_currency(request.currency)
        
        # Get and validate order
        pedido = validator.validate_order_exists(db, request.pedido_id)
        validator.validate_user_owns_order(pedido, current_user.id)
        validator.validate_order_payment_pending(pedido)
        
        # Verify stock availability
        payment_service.verify_stock_availability(db, request.pedido_id)
        
        # Create payment intent with Stripe
        intent = stripe_service.create_payment_intent(
            amount=request.amount,
            currency=request.currency,
            customer_email=current_user.email,
            description=f"Order #{request.pedido_id}",
            metadata={
                "pedido_id": str(request.pedido_id),
                "usuario_id": str(current_user.id),
                "email": current_user.email
            }
        )
        
        # Register transaction in database (initial pending state)
        transaccion = payment_service.register_transaction(
            db=db,
            pedido_id=request.pedido_id,
            payment_intent_id=intent['id'],
            usuario_id=current_user.id,
            monto=request.amount / 100,  # Convert cents to dollars
            moneda=request.currency,
            estado="pending",
            metodo_pago=None  # Not known until payment processed
        )
        
        db.commit()
        
        logger.info(f"Payment intent created: {intent['id']}, transaction: {transaccion.id}")
        
        return PaymentIntentResponse(
            id=intent['id'],
            client_secret=intent['client_secret'],
            amount=intent['amount'],
            currency=intent['currency'],
            status=intent['status'],
            stripe_public_key=intent['publishable_key']
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error creating payment intent: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creando intención de pago"
        )


@router.post(
    "/confirm-payment",
    response_model=PaymentStatusResponse,
    summary="Confirm Payment",
    description="Confirm payment and update order status"
)
async def confirm_payment(
    request: PaymentConfirmationRequest,
    current_user: models.Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Confirm payment and complete order processing
    
    Requirements:
    - User must be authenticated
    - Payment Intent must be in succeeded status
    - Order must belong to user
    - Stock must be available
    
    Returns:
    - Confirmation of payment
    - Updated order status
    - Transaction ID
    """
    try:
        logger.info(f"Confirming payment for order {request.pedido_id}, user {current_user.id}")
        
        # Initialize services
        validator = PaymentValidator()
        repository = PaymentRepository(db)
        
        # Validate payment intent ID
        validator.validate_payment_intent_id(request.payment_intent_id)
        
        # Get and validate transaction
        transaccion = validator.validate_transaction_exists(db, request.payment_intent_id)
        validator.validate_user_owns_transaction(transaccion, current_user.id)
        
        # Process the payment
        result = payment_service.process_payment(
            db=db,
            pedido_id=request.pedido_id,
            payment_intent_id=request.payment_intent_id,
            usuario_id=current_user.id
        )
        
        db.commit()
        
        logger.info(f"Payment confirmed: {request.payment_intent_id}")
        
        return PaymentStatusResponse(
            status=result['status'],
            message=result['message'],
            pedido_id=result['pedido_id'],
            transaccion_id=result['transaccion_id'],
            payment_intent_id=request.payment_intent_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error confirming payment: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error confirmando pago"
        )


@router.get(
    "/payment-status/{payment_intent_id}",
    response_model=PaymentStatusQueryResponse,
    summary="Query Payment Status",
    description="Get current status of a payment intent"
)
async def get_payment_status(
    payment_intent_id: str,
    current_user: models.Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Query the current status of a payment intent
    
    Returns current status from Stripe
    """
    try:
        logger.info(f"Querying payment status: {payment_intent_id}")
        
        # Initialize services
        validator = PaymentValidator()
        
        # Validate payment intent ID
        validator.validate_payment_intent_id(payment_intent_id)
        
        # Get and validate transaction
        transaccion = validator.validate_transaction_exists(db, payment_intent_id)
        validator.validate_user_owns_transaction(transaccion, current_user.id)
        
        # Get status from Stripe
        status_info = stripe_service.get_payment_intent_status(payment_intent_id)
        
        return PaymentStatusQueryResponse(
            payment_intent_id=status_info['id'],
            status=status_info['status'],
            amount=status_info['amount'],
            currency=status_info['currency']
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error getting payment status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error obteniendo estado de pago"
        )


@router.get(
    "/transacciones/{pedido_id}",
    response_model=TransaccionPagoListResponse,
    summary="Get Order Payment Transactions",
    description="Get all payment transactions for an order (admin)"
)
async def get_order_transactions(
    pedido_id: int,
    current_user: models.Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get payment transaction history for an order
    
    Can be accessed by:
    - Order owner
    - Admin users
    """
    try:
        logger.info(f"Getting transactions for order {pedido_id}")
        
        # Initialize services
        validator = PaymentValidator()
        repository = PaymentRepository(db)
        
        # Get and validate order
        pedido = validator.validate_order_exists(db, pedido_id)
        validator.validate_user_can_access_order(pedido, current_user)
        
        # Get all transactions for the order
        transacciones = repository.get_order_transactions(pedido_id)
        
        logger.info(f"Found {len(transacciones)} transactions for order {pedido_id}")
        
        return TransaccionPagoListResponse(
            status="success",
            data=[
                TransaccionPagoResponse.from_orm(t) for t in transacciones
            ]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error getting transactions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error obteniendo transacciones"
        )


@router.get(
    "/{pedido_id}/estado-pago",
    summary="Get Payment Status",
    description="Get current payment status for an order"
)
async def get_order_payment_status(
    pedido_id: int,
    current_user: models.Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get the current payment status of an order
    
    Requirements:
    - User must be authenticated
    - User must be order owner or admin
    
    Returns:
    - pedido_id: Order ID
    - estado_pago: Payment status (Pendiente de Pago, Pagado, Fallido, Cancelado)
    - transacciones: List of payment attempts with details
    - mensaje: Descriptive message
    """
    try:
        logger.info(f"Getting payment status for order {pedido_id}, user {current_user.id}")
        
        # Initialize services
        validator = PaymentValidator()
        repository = PaymentRepository(db)
        
        # Get and validate order
        pedido = validator.validate_order_exists(db, pedido_id)
        validator.validate_user_can_access_order(pedido, current_user)
        
        # Get payment status and transactions
        estado_pago = pedido.estado_pago if hasattr(pedido, 'estado_pago') else "No disponible"
        transacciones = repository.get_order_transactions(pedido_id)
        
        # Map transaction status to descriptive message
        mensajes = {
            "Pendiente de Pago": "El pago está pendiente de confirmación",
            "Pagado": "Pago confirmado exitosamente",
            "Fallido": "El pago ha fallado. Por favor, intenta de nuevo",
            "Cancelado": "El pago ha sido cancelado"
        }
        
        mensaje = mensajes.get(estado_pago, f"Estado de pago: {estado_pago}")
        
        logger.info(
            f"Payment status retrieved: pedido_id={pedido_id}, "
            f"estado_pago={estado_pago}, transacciones={len(transacciones)}"
        )
        
        return {
            "status": "success",
            "pedido_id": pedido_id,
            "estado_pago": estado_pago,
            "transacciones": [
                {
                    "transaccion_id": t.id,
                    "payment_intent_id": t.payment_intent_id,
                    "estado": t.estado,
                    "monto": float(t.monto),
                    "moneda": t.moneda,
                    "metodo_pago": t.metodo_pago or "Desconocido",
                    "fecha_creacion": t.fecha_creacion.isoformat() if t.fecha_creacion else None,
                    "fecha_confirmacion": t.fecha_confirmacion.isoformat() if t.fecha_confirmacion else None,
                    "detalles_error": t.detalles_error
                }
                for t in transacciones
            ],
            "mensaje": mensaje,
            "total_intentos": len(transacciones)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error getting payment status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error obteniendo estado de pago"
        )
