"""
Payment repository - Data Access Layer
Handles all database operations for payments, orders and transactions
"""
from typing import List, Optional
from sqlalchemy.orm import Session
import logging
import app.domain.models as models

logger = logging.getLogger(__name__)


class PaymentRepository:
    """Handles all database operations for payments"""

    def __init__(self, db: Session):
        self.db = db

    def get_order_by_id(self, pedido_id: int) -> Optional[models.Pedido]:
        """Get order by ID"""
        try:
            return self.db.query(models.Pedido).filter(
                models.Pedido.id == pedido_id
            ).first()
        except Exception as e:
            logger.exception(f"Error fetching order {pedido_id}: {e}")
            raise

    def get_transaction_by_payment_intent(self, payment_intent_id: str) -> Optional[models.TransaccionPago]:
        """Get transaction by payment intent ID"""
        try:
            return self.db.query(models.TransaccionPago).filter(
                models.TransaccionPago.payment_intent_id == payment_intent_id
            ).first()
        except Exception as e:
            logger.exception(f"Error fetching transaction {payment_intent_id}: {e}")
            raise

    def get_order_transactions(self, pedido_id: int) -> List[models.TransaccionPago]:
        """Get all transactions for an order"""
        try:
            return self.db.query(models.TransaccionPago).filter(
                models.TransaccionPago.pedido_id == pedido_id
            ).order_by(models.TransaccionPago.fecha_creacion.desc()).all()
        except Exception as e:
            logger.exception(f"Error fetching transactions for order {pedido_id}: {e}")
            raise

    def update_order_payment_status(self, pedido_id: int, estado_pago: str) -> None:
        """Update order payment status"""
        try:
            pedido = self.db.query(models.Pedido).filter(
                models.Pedido.id == pedido_id
            ).first()
            
            if pedido:
                pedido.estado_pago = estado_pago
                self.db.flush()
        except Exception as e:
            logger.exception(f"Error updating order payment status: {e}")
            raise

    def update_transaction_status(
        self, 
        transaccion_id: int, 
        estado: str, 
        metodo_pago: Optional[str] = None,
        detalles_error: Optional[str] = None
    ) -> None:
        """Update transaction status"""
        try:
            transaccion = self.db.query(models.TransaccionPago).filter(
                models.TransaccionPago.id == transaccion_id
            ).first()
            
            if transaccion:
                transaccion.estado = estado
                if metodo_pago:
                    transaccion.metodo_pago = metodo_pago
                if detalles_error:
                    transaccion.detalles_error = detalles_error
                self.db.flush()
        except Exception as e:
            logger.exception(f"Error updating transaction status: {e}")
            raise

    def get_order_items_with_products(self, pedido_id: int):
        """Get order items with product information"""
        try:
            return self.db.query(models.DetallePedido).join(
                models.Producto,
                models.DetallePedido.producto_id == models.Producto.id
            ).filter(
                models.DetallePedido.pedido_id == pedido_id
            ).all()
        except Exception as e:
            logger.exception(f"Error fetching order items: {e}")
            raise

    def verify_stock_for_order(self, pedido_id: int) -> bool:
        """
        Verify that all products in order have sufficient stock
        Returns True if all items have stock, False otherwise
        """
        try:
            items = self.get_order_items_with_products(pedido_id)
            
            for item in items:
                producto = item.producto if hasattr(item, 'producto') else None
                if not producto:
                    return False
                
                if producto.cantidad_disponible < item.cantidad:
                    logger.warning(
                        f"Insufficient stock for product {producto.id}: "
                        f"required={item.cantidad}, available={producto.cantidad_disponible}"
                    )
                    return False
            
            return True
        except Exception as e:
            logger.exception(f"Error verifying stock: {e}")
            return False

    def reduce_product_stock(self, producto_id: int, cantidad: int) -> None:
        """Reduce product stock by specified amount"""
        try:
            producto = self.db.query(models.Producto).filter(
                models.Producto.id == producto_id
            ).first()
            
            if producto:
                producto.cantidad_disponible = max(0, producto.cantidad_disponible - cantidad)
                self.db.flush()
        except Exception as e:
            logger.exception(f"Error reducing product stock: {e}")
            raise

    def create_transaction(
        self,
        pedido_id: int,
        payment_intent_id: str,
        usuario_id: int,
        monto: float,
        moneda: str,
        estado: str,
        metodo_pago: Optional[str] = None
    ) -> models.TransaccionPago:
        """Create new payment transaction"""
        try:
            transaccion = models.TransaccionPago(
                pedido_id=pedido_id,
                payment_intent_id=payment_intent_id,
                usuario_id=usuario_id,
                monto=monto,
                moneda=moneda,
                estado=estado,
                metodo_pago=metodo_pago
            )
            self.db.add(transaccion)
            self.db.flush()
            return transaccion
        except Exception as e:
            logger.exception(f"Error creating transaction: {e}")
            raise
