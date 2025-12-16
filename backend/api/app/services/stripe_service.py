"""
Stripe Payment Gateway Service
Handles integration with Stripe API for payment processing
"""
import stripe
import logging
from typing import Optional, Dict, Any
from fastapi import HTTPException, status
from app.config import settings

logger = logging.getLogger(__name__)


class StripeService:
    """Service for Stripe payment operations"""
    
    def __init__(self):
        """Initialize Stripe with API key from configuration"""
        stripe.api_key = settings.STRIPE_SECRET_KEY
        self.publishable_key = settings.STRIPE_PUBLISHABLE_KEY
        
        if not settings.STRIPE_SECRET_KEY:
            logger.warning("STRIPE_SECRET_KEY not configured - Stripe functionality will be disabled")
    
    def create_payment_intent(
        self,
        amount: float,
        currency: str = "USD",
        customer_email: str = "",
        description: str = "",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a Stripe Payment Intent for processing payment
        
        Args:
            amount: Amount in cents (e.g., 9999 for $99.99)
            currency: ISO 4217 currency code (default: USD)
            customer_email: Customer email address
            description: Description for the payment
            metadata: Additional metadata to store with the intent
            
        Returns:
            Dictionary with payment intent details:
            {
                'id': 'pi_xxx',
                'client_secret': 'pi_xxx_secret',
                'status': 'requires_payment_method',
                'amount': 9999,
                'currency': 'usd'
            }
            
        Raises:
            HTTPException: For various Stripe errors
        """
        try:
            # Validate amount is positive
            if amount <= 0:
                logger.warning(f"Invalid amount: {amount}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Amount must be greater than 0"
                )
            
            # Prepare metadata with common fields
            intent_metadata = metadata or {}
            intent_metadata['currency'] = currency
            if customer_email:
                intent_metadata['customer_email'] = customer_email
            
            logger.info(f"Creating payment intent: amount={amount} {currency}, email={customer_email}")
            
            # Create payment intent in Stripe
            payment_intent = stripe.PaymentIntent.create(
                amount=int(amount),  # Ensure it's an integer for Stripe
                currency=currency.lower(),
                description=description or f"Order payment - {currency}",
                metadata=intent_metadata,
                # Enable all payment methods
                automatic_payment_methods={"enabled": True},
            )
            
            logger.info(f"Payment intent created: {payment_intent.id}")
            
            return {
                'id': payment_intent.id,
                'client_secret': payment_intent.client_secret,
                'status': payment_intent.status,
                'amount': payment_intent.amount,
                'currency': payment_intent.currency,
                'publishable_key': self.publishable_key,
            }
            
        except HTTPException:
            # Re-raise HTTPException without modification
            raise
        except stripe.error.CardError as e:
            # Card declined
            logger.warning(f"Card error: {e.user_message}")
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail=e.user_message or "Payment method declined"
            )
        except stripe.error.RateLimitError as e:
            # Too many requests
            logger.error(f"Rate limit error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests to payment gateway. Please try again later."
            )
        except stripe.error.InvalidRequestError as e:
            # Invalid parameters
            logger.error(f"Invalid request error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid payment request: {str(e)}"
            )
        except stripe.error.APIConnectionError as e:
            # Network error
            logger.error(f"API connection error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Error en la pasarela de pago. Por favor, intente más tarde."
            )
        except stripe.error.StripeError as e:
            # Generic Stripe error
            logger.error(f"Stripe error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error en la pasarela de pago. Por favor, intente más tarde."
            )
        except Exception as e:
            # Unexpected error
            logger.exception(f"Unexpected error creating payment intent: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error procesando su solicitud"
            )
    
    def confirm_payment_intent(self, payment_intent_id: str) -> Dict[str, Any]:
        """
        Retrieve and verify payment intent status
        
        Args:
            payment_intent_id: Stripe Payment Intent ID
            
        Returns:
            Dictionary with payment intent details
            
        Raises:
            HTTPException: If payment intent not found or error occurs
        """
        try:
            logger.info(f"Confirming payment intent: {payment_intent_id}")
            
            payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            
            logger.info(f"Payment intent status: {payment_intent.status}")
            
            return {
                'id': payment_intent.id,
                'status': payment_intent.status,
                'amount': payment_intent.amount,
                'currency': payment_intent.currency,
                'client_secret': payment_intent.client_secret,
            }
            
        except stripe.error.InvalidRequestError as e:
            logger.warning(f"Payment intent not found: {payment_intent_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment intent not found"
            )
        except stripe.error.APIConnectionError as e:
            logger.error(f"API connection error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Error en la pasarela de pago. Por favor, intente más tarde."
            )
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error en la pasarela de pago. Por favor, intente más tarde."
            )
    
    def get_payment_intent_status(self, payment_intent_id: str) -> Dict[str, Any]:
        """
        Get current status of a payment intent
        
        Args:
            payment_intent_id: Stripe Payment Intent ID
            
        Returns:
            Dictionary with payment intent details and status
        """
        try:
            logger.info(f"Getting payment intent status: {payment_intent_id}")
            
            payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            
            return {
                'id': payment_intent.id,
                'status': payment_intent.status,
                'amount': payment_intent.amount,
                'currency': payment_intent.currency,
                'charges_count': len(payment_intent.charges.data) if hasattr(payment_intent, 'charges') else 0,
            }
            
        except stripe.error.InvalidRequestError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment intent not found"
            )
        except stripe.error.APIConnectionError:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Error en la pasarela de pago. Por favor, intente más tarde."
            )
        except Exception as e:
            logger.error(f"Error getting payment intent status: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error procesando su solicitud"
            )
    
    @staticmethod
    def construct_webhook_event(body: bytes, sig_header: str, webhook_secret: str) -> Dict[str, Any]:
        """
        Verify and construct webhook event from Stripe
        
        Args:
            body: Raw request body
            sig_header: Signature header from Stripe
            webhook_secret: Webhook secret from Stripe
            
        Returns:
            Verified event dictionary
            
        Raises:
            HTTPException: If signature verification fails
        """
        try:
            event = stripe.Webhook.construct_event(
                body, sig_header, webhook_secret
            )
            logger.info(f"Webhook verified: {event['type']}, ID: {event['id']}")
            return event
        except ValueError as e:
            logger.warning(f"Invalid payload: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid payload"
            )
        except stripe.error.SignatureVerificationError as e:
            logger.warning(f"Invalid signature: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid signature"
            )


# Singleton instance
stripe_service = StripeService()
