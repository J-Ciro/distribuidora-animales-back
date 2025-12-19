"""
Payment validation logic - Single Responsibility Principle
Centralizes all payment-related validation and authorization logic
"""
import logging
from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
import app.domain.models as models

logger = logging.getLogger(__name__)


class PaymentValidator:
    """Handles all payment validation and authorization logic"""

    @staticmethod
    def validate_order_exists(db: Session, pedido_id: int) -> models.Pedido:
        """
        Validate that order exists
        Returns the order if found, raises HTTPException otherwise
        """
        pedido = db.query(models.Pedido).filter(
            models.Pedido.id == pedido_id
        ).first()
        
        if not pedido:
            logger.warning(f"Order not found: {pedido_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pedido no encontrado"
            )
        
        return pedido

    @staticmethod
    def validate_user_owns_order(pedido: models.Pedido, usuario_id: int) -> None:
        """
        Validate that user owns the order
        Raises HTTPException if not authorized
        """
        if pedido.usuario_id != usuario_id:
            logger.warning(f"Unauthorized access to order {pedido.id} by user {usuario_id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Acceso denegado a este pedido"
            )

    @staticmethod
    def validate_order_payment_pending(pedido: models.Pedido) -> None:
        """
        Validate that order is in pending payment status
        Raises HTTPException if not in correct status
        """
        if pedido.estado_pago != "Pendiente de Pago":
            logger.warning(f"Order {pedido.id} not in pending status: {pedido.estado_pago}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Pedido no está en estado de pago pendiente"
            )

    @staticmethod
    def validate_transaction_exists(db: Session, payment_intent_id: str) -> models.TransaccionPago:
        """
        Validate that transaction exists
        Returns the transaction if found, raises HTTPException otherwise
        """
        transaccion = db.query(models.TransaccionPago).filter(
            models.TransaccionPago.payment_intent_id == payment_intent_id
        ).first()
        
        if not transaccion:
            logger.warning(f"Transaction not found: {payment_intent_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transacción no encontrada"
            )
        
        return transaccion

    @staticmethod
    def validate_user_owns_transaction(transaccion: models.TransaccionPago, usuario_id: int) -> None:
        """
        Validate that user owns the transaction
        Raises HTTPException if not authorized
        """
        if transaccion.usuario_id != usuario_id:
            logger.warning(f"Unauthorized transaction access by user {usuario_id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Acceso denegado"
            )

    @staticmethod
    def validate_user_can_access_order(pedido: models.Pedido, current_user: models.Usuario) -> None:
        """
        Validate that user can access order (owner or admin)
        Raises HTTPException if not authorized
        """
        is_owner = pedido.usuario_id == current_user.id
        is_admin = getattr(current_user, 'es_admin', False)
        
        if not is_owner and not is_admin:
            logger.warning(f"Unauthorized access to order {pedido.id} by user {current_user.id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Acceso denegado"
            )

    @staticmethod
    def validate_payment_intent_id(payment_intent_id: str) -> None:
        """Validate payment intent ID format"""
        if not payment_intent_id or not isinstance(payment_intent_id, str):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="ID de intención de pago inválido"
            )

    @staticmethod
    def validate_amount(amount: int) -> None:
        """Validate payment amount (must be positive)"""
        if not isinstance(amount, int) or amount <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Monto inválido"
            )

    @staticmethod
    def validate_currency(currency: str) -> None:
        """Validate currency code"""
        valid_currencies = ['usd', 'eur', 'gbp', 'cop']
        if currency.lower() not in valid_currencies:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Moneda no soportada. Use: {', '.join(valid_currencies)}"
            )
