"""
Payment Service for handling payment processing logic
Manages transactions, order status updates, and stock deductions
"""
import logging
from decimal import Decimal
from typing import Optional, Dict, Any
from datetime import datetime
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.services.stripe_service import stripe_service
import app.models as models

logger = logging.getLogger(__name__)


class PaymentService:
    """Service for payment processing and transaction management"""
    
    @staticmethod
    def register_transaction(
        db: Session,
        pedido_id: int,
        payment_intent_id: str,
        usuario_id: int,
        monto: float,
        moneda: str = "USD",
        estado: str = "pending",
        metodo_pago: Optional[str] = None,
        detalles_error: Optional[str] = None
    ) -> models.TransaccionPago:
        """
        Register a payment transaction in the database
        
        Args:
            db: Database session
            pedido_id: Associated order ID
            payment_intent_id: Stripe Payment Intent ID
            usuario_id: User ID
            monto: Transaction amount
            moneda: Currency code
            estado: Transaction status (pending, succeeded, failed)
            metodo_pago: Payment method (card, link, etc)
            detalles_error: Error details if failed
            
        Returns:
            TransaccionPago model instance
        """
        try:
            logger.info(f"Registering transaction: pedido_id={pedido_id}, intent={payment_intent_id}")
            
            # Check if transaction already exists (idempotency)
            existing_tx = db.query(models.TransaccionPago).filter(
                models.TransaccionPago.payment_intent_id == payment_intent_id
            ).first()
            
            if existing_tx:
                logger.info(f"Transaction already exists: {existing_tx.id}")
                return existing_tx
            
            # Create new transaction record
            transaccion = models.TransaccionPago(
                pedido_id=pedido_id,
                payment_intent_id=payment_intent_id,
                usuario_id=usuario_id,
                monto=Decimal(str(monto)),
                moneda=moneda,
                estado=estado,
                metodo_pago=metodo_pago,
                detalles_error=detalles_error,
            )
            
            db.add(transaccion)
            db.flush()  # Get the ID without committing
            
            # Record state change in history
            historial = models.EstadoPagoHistorial(
                transaccion_id=transaccion.id,
                estado_anterior=None,
                estado_nuevo=estado,
                razon_cambio="Transacción creada"
            )
            db.add(historial)
            
            logger.info(f"Transaction registered: {transaccion.id}")
            return transaccion
            
        except Exception as e:
            logger.exception(f"Error registering transaction: {str(e)}")
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error registrando transacción"
            )
    
    @staticmethod
    def update_payment_status(
        db: Session,
        transaccion_id: int,
        new_status: str,
        razon: Optional[str] = None,
        detalles_error: Optional[str] = None
    ) -> models.TransaccionPago:
        """
        Update payment transaction status
        
        Args:
            db: Database session
            transaccion_id: Transaction ID
            new_status: New status (pending, succeeded, failed, canceled)
            razon: Reason for status change
            detalles_error: Error details if applicable
            
        Returns:
            Updated TransaccionPago instance
        """
        try:
            logger.info(f"Updating transaction {transaccion_id} to status: {new_status}")
            
            transaccion = db.query(models.TransaccionPago).filter(
                models.TransaccionPago.id == transaccion_id
            ).first()
            
            if not transaccion:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Transacción no encontrada"
                )
            
            old_status = transaccion.estado
            
            # Update transaction
            transaccion.estado = new_status
            if detalles_error:
                transaccion.detalles_error = detalles_error
            transaccion.fecha_actualizacion = datetime.utcnow()
            
            if new_status == "succeeded":
                transaccion.fecha_confirmacion = datetime.utcnow()
            
            db.add(transaccion)
            db.flush()
            
            # Record state change in history
            historial = models.EstadoPagoHistorial(
                transaccion_id=transaccion_id,
                estado_anterior=old_status,
                estado_nuevo=new_status,
                razon_cambio=razon or f"Status change to {new_status}"
            )
            db.add(historial)
            
            logger.info(f"Transaction {transaccion_id} updated: {old_status} -> {new_status}")
            return transaccion
            
        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"Error updating transaction status: {str(e)}")
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error actualizando estado de transacción"
            )
    
    @staticmethod
    def verify_stock_availability(
        db: Session,
        pedido_id: int
    ) -> bool:
        """
        Verify that stock is available for all items in the order
        
        Args:
            db: Database session
            pedido_id: Order ID
            
        Returns:
            True if all items have sufficient stock
            
        Raises:
            HTTPException: If any item lacks stock
        """
        try:
            # Get all items in the order
            items = db.query(models.PedidoItem).filter(
                models.PedidoItem.pedido_id == pedido_id
            ).all()
            
            for item in items:
                # Check stock for each product
                result = db.execute(
                    text("SELECT cantidad_disponible FROM Productos WHERE id = :id"),
                    {"id": item.producto_id}
                ).fetchone()
                
                if not result or result.cantidad_disponible < item.cantidad:
                    available = result.cantidad_disponible if result else 0
                    logger.warning(
                        f"Stock insufficient for producto {item.producto_id}: "
                        f"needed {item.cantidad}, available {available}"
                    )
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Stock insuficiente para producto {item.producto_id}"
                    )
            
            return True
            
        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"Error verifying stock: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error verificando disponibilidad"
            )
    
    @staticmethod
    def deduct_stock(
        db: Session,
        pedido_id: int
    ) -> bool:
        """
        Deduct stock from inventory for all order items
        Should only be called after successful payment confirmation
        
        Args:
            db: Database session
            pedido_id: Order ID
            
        Returns:
            True if stock deduction successful
        """
        try:
            logger.info(f"Deducting stock for order {pedido_id}")
            
            # First verify stock is available
            PaymentService.verify_stock_availability(db, pedido_id)
            
            # Get all items in the order
            items = db.query(models.PedidoItem).filter(
                models.PedidoItem.pedido_id == pedido_id
            ).all()
            
            # Deduct stock for each item
            for item in items:
                update_stmt = text("""
                    UPDATE Productos 
                    SET cantidad_disponible = cantidad_disponible - :cantidad
                    WHERE id = :id
                """)
                db.execute(update_stmt, {
                    "cantidad": item.cantidad,
                    "id": item.producto_id
                })
                
                logger.info(f"Stock deducted for producto {item.producto_id}: {item.cantidad} units")
            
            return True
            
        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"Error deducting stock: {str(e)}")
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error actualizando inventario"
            )
    
    @staticmethod
    def process_payment(
        db: Session,
        pedido_id: int,
        payment_intent_id: str,
        usuario_id: int
    ) -> Dict[str, Any]:
        """
        Complete payment processing: verify intent, deduct stock, update order status
        
        Args:
            db: Database session
            pedido_id: Order ID
            payment_intent_id: Stripe Payment Intent ID
            usuario_id: User ID
            
        Returns:
            Dictionary with payment confirmation details
        """
        try:
            logger.info(f"Processing payment: pedido_id={pedido_id}, intent={payment_intent_id}")
            
            # Get the order
            pedido = db.query(models.Pedido).filter(
                models.Pedido.id == pedido_id
            ).first()
            
            if not pedido:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Pedido no encontrado"
                )
            
            if pedido.usuario_id != usuario_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Acceso denegado"
                )
            
            # Verify payment intent with Stripe
            intent_status = stripe_service.get_payment_intent_status(payment_intent_id)
            
            if intent_status['status'] != 'succeeded':
                logger.warning(f"Payment intent not succeeded: {intent_status['status']}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Pago no confirmado por Stripe"
                )
            
            # Check for existing transaction (idempotency)
            existing_tx = db.query(models.TransaccionPago).filter(
                models.TransaccionPago.payment_intent_id == payment_intent_id,
                models.TransaccionPago.estado == "succeeded"
            ).first()
            
            if existing_tx:
                logger.info(f"Payment already processed: {existing_tx.id}")
                return {
                    "status": "success",
                    "message": "Pago ya ha sido procesado",
                    "transaccion_id": existing_tx.id,
                    "pedido_id": pedido_id
                }
            
            # Verify stock availability
            PaymentService.verify_stock_availability(db, pedido_id)
            
            # Deduct stock
            PaymentService.deduct_stock(db, pedido_id)
            
            # Update order status
            pedido.estado = "Pagado"
            pedido.estado_pago = "Pagado"
            db.add(pedido)
            db.flush()
            
            # Update transaction status to succeeded
            transaccion = PaymentService.update_payment_status(
                db,
                # Get the transaction ID
                db.query(models.TransaccionPago).filter(
                    models.TransaccionPago.payment_intent_id == payment_intent_id
                ).first().id,
                "succeeded",
                "Pago confirmado exitosamente"
            )
            
            logger.info(f"Payment processed successfully: pedido_id={pedido_id}")
            
            return {
                "status": "success",
                "message": "Pago confirmado exitosamente",
                "transaccion_id": transaccion.id,
                "pedido_id": pedido_id,
                "payment_intent_id": payment_intent_id
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"Error processing payment: {str(e)}")
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error procesando pago"
            )


# Singleton instance
payment_service = PaymentService()
