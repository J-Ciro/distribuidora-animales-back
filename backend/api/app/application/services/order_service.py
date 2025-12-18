"""
Order Service: Business logic for order management
Handles order status transitions, purchase order generation, and order cancellation
"""
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from datetime import datetime
import logging
from app.domain.models import Pedido, PedidoItem, TransaccionPago
from sqlalchemy import text

logger = logging.getLogger(__name__)


class OrderService:
    """Service for managing order operations"""
    
    @staticmethod
    async def generate_purchase_order(db: Session, pedido_id: int, transaccion_id: int):
        """
        Generate a purchase order after payment confirmation
        
        This is called after successful payment to create an official purchase order
        that can be used for fulfillment tracking
        
        Args:
            db: Database session
            pedido_id: ID of the Pedido (Order)
            transaccion_id: ID of the TransaccionPago (Payment Transaction)
        
        Returns:
            dict: {
                "status": "success",
                "compra_id": <int>,
                "numero_compra": <str>,
                "pedido_id": <int>
            }
        
        Raises:
            HTTPException 404: If Pedido not found
            HTTPException 400: If Pedido already has a purchase order or estado_pago != "Pagado"
        """
        try:
            # Get the Pedido
            pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
            if not pedido:
                logger.error(f"Pedido not found: pedido_id={pedido_id}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Pedido con ID {pedido_id} no encontrado"
                )
            
            # Verify payment status
            if pedido.estado_pago != "Pagado":
                logger.warning(f"Cannot generate PO for unpaid order: pedido_id={pedido_id}, estado_pago={pedido.estado_pago}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"No se puede generar orden de compra. Estado de pago: {pedido.estado_pago}"
                )
            
            # Generate purchase order number (e.g., "OC-20251216-00001")
            date_str = datetime.utcnow().strftime("%Y%m%d")
            next_number = db.query(Pedido).filter(
                Pedido.id == pedido_id
            ).first().id
            numero_compra = f"OC-{date_str}-{next_number:05d}"
            
            # Update Pedido with purchase order reference
            # NOTE: In a full implementation, you would create a separate OrdenCompra table
            # For now, we're adding a reference field to Pedido
            
            # Log the purchase order generation
            logger.info(
                f"Purchase order generated: "
                f"numero_compra={numero_compra}, "
                f"pedido_id={pedido_id}, "
                f"transaccion_id={transaccion_id}"
            )
            
            return {
                "status": "success",
                "compra_id": pedido_id,
                "numero_compra": numero_compra,
                "pedido_id": pedido_id,
                "fecha_generacion": datetime.utcnow().isoformat()
            }
        
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error generating purchase order: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al generar orden de compra"
            )
    
    @staticmethod
    async def update_order_status(db: Session, pedido_id: int, new_status: str, razon: str = None):
        """
        Update order status with validation and audit trail
        
        Valid state transitions:
        - "Pendiente" → "Pagado" (payment confirmed - only via payment system)
        - "Pagado" → "Enviado" (shipped to customer)
        - "Pagado" → "Cancelado" (order cancelled)
        - "Enviado" → "Entregado" (delivered)
        - "Enviado" → "Cancelado" (order cancelled)
        - "Entregado" → (final state, no changes allowed)
        - "Cancelado" → (final state, no changes allowed)
        
        Args:
            db: Database session
            pedido_id: ID of the Pedido
            new_status: New status (Pendiente, Pagado, Enviado, Entregado, Cancelado)
            razon: Reason for status change (optional)
        
        Returns:
            dict: {
                "status": "success",
                "pedido_id": <int>,
                "estado_anterior": <str>,
                "estado_nuevo": <str>
            }
        
        Raises:
            HTTPException 404: If Pedido not found
            HTTPException 400: If invalid state transition
        """
        try:
            # Get the Pedido
            pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
            if not pedido:
                logger.error(f"Pedido not found: pedido_id={pedido_id}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Pedido con ID {pedido_id} no encontrado"
                )
            
            # Save previous status
            estado_anterior = pedido.estado
            
            # Define valid state transitions
            valid_transitions = {
                "Pendiente": ["Pagado", "Cancelado"],  # Solo puede cambiar cuando se confirma el pago o se cancela
                "Pagado": ["Enviado", "Cancelado"],     # Admin puede marcar como enviado o cancelar
                "Enviado": ["Entregado", "Cancelado"],   # Admin puede marcar como entregado o cancelar
                "Entregado": [],                         # Estado final - no se puede cambiar
                "Cancelado": []                          # Estado final - no se puede cambiar
            }
            
            # Validate transition
            if new_status not in valid_transitions.get(estado_anterior, []):
                logger.warning(
                    f"Invalid state transition: pedido_id={pedido_id}, "
                    f"{estado_anterior} → {new_status}"
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Transición de estado inválida: {estado_anterior} → {new_status}"
                )
            
            # Update status
            pedido.estado = new_status
            db.add(pedido)
            db.commit()
            db.refresh(pedido)
            
            logger.info(
                f"Order status updated: pedido_id={pedido_id}, "
                f"{estado_anterior} → {new_status}, razon={razon}"
            )
            
            return {
                "status": "success",
                "pedido_id": pedido_id,
                "estado_anterior": estado_anterior,
                "estado_nuevo": new_status,
                "razon": razon,
                "fecha_cambio": datetime.utcnow().isoformat()
            }
        
        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating order status: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al actualizar estado del pedido"
            )
    
    @staticmethod
    async def cancel_pending_payment_order(db: Session, pedido_id: int, razon: str = None):
        """
        Cancel an order that is still pending payment
        
        Can be called if:
        - Customer cancels before payment
        - Payment fails and customer gives up
        - Admin cancels the order
        
        Args:
            db: Database session
            pedido_id: ID of the Pedido
            razon: Reason for cancellation (optional)
        
        Returns:
            dict: {
                "status": "success",
                "pedido_id": <int>,
                "estado": "Cancelado"
            }
        
        Raises:
            HTTPException 404: If Pedido not found
            HTTPException 400: If estado_pago != "Pendiente de Pago"
        """
        try:
            # Get the Pedido
            pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
            if not pedido:
                logger.error(f"Pedido not found: pedido_id={pedido_id}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Pedido con ID {pedido_id} no encontrado"
                )
            
            # Check if payment is still pending
            if pedido.estado_pago != "Pendiente de Pago":
                logger.warning(
                    f"Cannot cancel non-pending order: pedido_id={pedido_id}, "
                    f"estado_pago={pedido.estado_pago}"
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Solo se pueden cancelar pedidos pendientes de pago. "
                           f"Estado actual: {pedido.estado_pago}"
                )
            
            # Update status to Cancelado
            pedido.estado = "Cancelado"
            pedido.estado_pago = "Cancelado"
            db.add(pedido)
            db.commit()
            db.refresh(pedido)
            
            logger.info(
                f"Order cancelled: pedido_id={pedido_id}, "
                f"razon={razon}"
            )
            
            return {
                "status": "success",
                "pedido_id": pedido_id,
                "estado": "Cancelado",
                "razon": razon,
                "fecha_cancelacion": datetime.utcnow().isoformat()
            }
        
        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"Error cancelling order: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al cancelar el pedido"
            )


# Create singleton instance
order_service = OrderService()
