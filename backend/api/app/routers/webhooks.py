"""
Webhooks Router: Handle Stripe webhook events
Processes asynchronous payment events from Stripe
"""
from fastapi import APIRouter, Request, HTTPException, status
from sqlalchemy.orm import Session
import json
import logging

from app.database import get_db
from app.services.stripe_service import stripe_service
from app.services.payment_service import payment_service
from app.config import settings
import app.models as models

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/webhooks",
    tags=["webhooks"]
)


@router.post(
    "/stripe",
    status_code=status.HTTP_200_OK,
    summary="Stripe Webhook",
    description="Handle webhook events from Stripe"
)
async def stripe_webhook(request: Request):
    """
    Handle Stripe webhook events
    
    Events processed:
    - payment_intent.succeeded: Payment confirmed
    - payment_intent.payment_failed: Payment failed
    - charge.dispute.created: Payment dispute
    
    Note: Returns 200 immediately, processing happens asynchronously
    
    In development without STRIPE_WEBHOOK_SECRET configured,
    this endpoint skips signature verification for testing purposes.
    """
    try:
        # Get raw body for signature verification
        body = await request.body()
        sig_header = request.headers.get("stripe-signature")
        
        if not sig_header:
            logger.warning("Missing stripe-signature header")
            # In dev/test mode, allow missing signature
            if not settings.STRIPE_WEBHOOK_SECRET:
                logger.info("Webhook signature verification skipped (dev mode)")
                try:
                    event = json.loads(body)
                except Exception as e:
                    logger.error(f"Invalid JSON payload: {str(e)}")
                    return {"status": "received"}
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Missing signature"
                )
        else:
            logger.info(f"Received webhook with signature: {sig_header[:20]}...")
            
            # Verify and construct event (if webhook secret is configured)
            if settings.STRIPE_WEBHOOK_SECRET:
                event = stripe_service.construct_webhook_event(
                    body,
                    sig_header,
                    settings.STRIPE_WEBHOOK_SECRET
                )
            else:
                # Dev mode: skip verification
                try:
                    event = json.loads(body)
                except Exception as e:
                    logger.error(f"Invalid JSON payload: {str(e)}")
                    return {"status": "received"}
        
        logger.info(f"Webhook verified: type={event['type']}, id={event['id']}")
        
        # Get database session
        db: Session = next(get_db())
        
        try:
            # Record webhook event for auditing
            evento = models.EventoWebhookStripe(
                event_id=event['id'],
                event_type=event['type'],
                payload=json.dumps(event)[:4000],  # Truncate if needed
                procesado=False
            )
            db.add(evento)
            db.flush()
            
            # Process event based on type
            if event['type'] == 'payment_intent.succeeded':
                _handle_payment_intent_succeeded(db, event, evento)
            elif event['type'] == 'payment_intent.payment_failed':
                _handle_payment_intent_failed(db, event, evento)
            elif event['type'] == 'charge.dispute.created':
                _handle_charge_dispute(db, event, evento)
            else:
                logger.info(f"Unhandled event type: {event['type']}")
                evento.procesado = True
                evento.resultado = "Unhandled event type"
            
            db.commit()
            
            logger.info(f"Webhook processed successfully: {event['type']}")
            
        except Exception as e:
            logger.exception(f"Error processing webhook: {str(e)}")
            db.rollback()
            # Still return 200 to avoid Stripe retrying
        finally:
            db.close()
        
        # Always return 200 to Stripe to confirm receipt
        return {"received": True}
        
    except HTTPException:
        # Stripe signature verification failed
        return {"received": False}
    except Exception as e:
        logger.exception(f"Unexpected error in webhook handler: {str(e)}")
        # Still return 200 to avoid Stripe retrying
        return {"received": True}


def _handle_payment_intent_succeeded(db: Session, event: dict, evento: models.EventoWebhookStripe):
    """Handle payment_intent.succeeded event"""
    try:
        payment_intent = event['data']['object']
        payment_intent_id = payment_intent['id']
        
        logger.info(f"Processing succeeded payment: {payment_intent_id}")
        
        # Get transaction
        transaccion = db.query(models.TransaccionPago).filter(
            models.TransaccionPago.payment_intent_id == payment_intent_id
        ).first()
        
        if not transaccion:
            logger.warning(f"Transaction not found: {payment_intent_id}")
            evento.procesado = True
            evento.resultado = "Transaction not found"
            return
        
        # Check if already processed
        if transaccion.estado == "succeeded":
            logger.info(f"Payment already processed: {payment_intent_id}")
            evento.procesado = True
            evento.resultado = "Already processed"
            return
        
        # Update transaction status
        payment_service.update_payment_status(
            db,
            transaccion.id,
            "succeeded",
            "Pago confirmado por webhook"
        )
        
        # Update order status
        pedido = db.query(models.Pedido).filter(
            models.Pedido.id == transaccion.pedido_id
        ).first()
        
        if pedido:
            pedido.estado = "Pagado"
            pedido.estado_pago = "Pagado"
            db.add(pedido)
        
        evento.procesado = True
        evento.transaccion_id = transaccion.id
        evento.resultado = "Payment confirmed"
        
        logger.info(f"Payment succeeded processed: {payment_intent_id}")
        
    except Exception as e:
        logger.exception(f"Error handling payment succeeded: {str(e)}")
        evento.resultado = f"Error: {str(e)}"


def _handle_payment_intent_failed(db: Session, event: dict, evento: models.EventoWebhookStripe):
    """Handle payment_intent.payment_failed event"""
    try:
        payment_intent = event['data']['object']
        payment_intent_id = payment_intent['id']
        
        logger.info(f"Processing failed payment: {payment_intent_id}")
        
        # Get transaction
        transaccion = db.query(models.TransaccionPago).filter(
            models.TransaccionPago.payment_intent_id == payment_intent_id
        ).first()
        
        if not transaccion:
            logger.warning(f"Transaction not found: {payment_intent_id}")
            evento.procesado = True
            evento.resultado = "Transaction not found"
            return
        
        # Get error message
        error_msg = ""
        if payment_intent.get('last_payment_error'):
            error_msg = payment_intent['last_payment_error'].get('message', '')
        
        # Update transaction status
        payment_service.update_payment_status(
            db,
            transaccion.id,
            "failed",
            "Pago rechazado",
            error_msg
        )
        
        # Order remains in "Pendiente de Pago"
        evento.procesado = True
        evento.transaccion_id = transaccion.id
        evento.resultado = f"Payment failed: {error_msg}"
        
        logger.info(f"Payment failed processed: {payment_intent_id}")
        
    except Exception as e:
        logger.exception(f"Error handling payment failed: {str(e)}")
        evento.resultado = f"Error: {str(e)}"


def _handle_charge_dispute(db: Session, event: dict, evento: models.EventoWebhookStripe):
    """Handle charge.dispute.created event"""
    try:
        dispute = event['data']['object']
        charge_id = dispute.get('charge')
        
        logger.warning(f"Dispute created for charge: {charge_id}")
        
        # Find transaction by charge ID (if we stored it)
        # For now, just log it
        evento.procesado = True
        evento.resultado = f"Dispute created - charge: {charge_id}"
        
        logger.warning(f"Dispute handled: {charge_id}")
        
    except Exception as e:
        logger.exception(f"Error handling dispute: {str(e)}")
        evento.resultado = f"Error: {str(e)}"
