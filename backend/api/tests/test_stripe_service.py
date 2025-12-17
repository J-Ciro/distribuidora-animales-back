"""
Unit tests for stripe_service
Tests Stripe API integration: create, confirm, retrieve payment intents
"""
import pytest
from unittest.mock import patch, MagicMock
from fastapi import HTTPException
import stripe

from app.application.services.stripe_service import stripe_service
from app.core.config import settings


class TestStripeService:
    """Unit tests for StripeService"""
    
    @pytest.mark.unit
    def test_create_payment_intent_success(self, mock_stripe_payment_intent, patch_stripe_create_payment_intent):
        """
        CP-56: Create payment intent successfully
        Validates: Stripe API integration, response contains client_secret
        """
        # Arrange
        amount = 9999
        currency = "USD"
        customer_email = "test@example.com"
        
        # Act
        result = stripe_service.create_payment_intent(
            amount=amount,
            currency=currency,
            customer_email=customer_email
        )
        
        # Assert
        assert result is not None
        assert result['id'] == 'pi_test_12345'
        assert result['status'] == 'requires_payment_method'
        assert result['client_secret'] == 'pi_test_12345_secret_xyz'
        assert result['amount'] == 9999
        assert result['currency'] == 'usd'
    
    @pytest.mark.unit
    def test_create_payment_intent_invalid_amount(self):
        """
        Validates: Amount must be greater than 0
        """
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            stripe_service.create_payment_intent(
                amount=-10,
                currency="USD",
                customer_email="test@example.com"
            )
        
        assert exc_info.value.status_code == 400
        assert "greater than 0" in exc_info.value.detail.lower() or "invalido" in exc_info.value.detail.lower()
    
    @pytest.mark.unit
    def test_create_payment_intent_card_error(self):
        """
        CP-57: CardError when card details invalid
        Validates: HTTP 402 for card errors
        """
        # Arrange
        with patch('app.services.stripe_service.stripe.PaymentIntent.create') as mock_create:
            mock_create.side_effect = stripe.error.CardError(
                message="Your card was declined",
                param="",
                code="card_declined"
            )
            
            # Act & Assert
            with pytest.raises(HTTPException) as exc_info:
                stripe_service.create_payment_intent(
                    amount=9999,
                    currency="USD",
                    customer_email="test@example.com"
                )
            
            assert exc_info.value.status_code == 402
            assert "declined" in exc_info.value.detail.lower() or "tarjeta" in exc_info.value.detail.lower()
    
    @pytest.mark.unit
    def test_create_payment_intent_rate_limit_error(self):
        """
        CP-59: RateLimitError when API limit reached
        Validates: HTTP 429 for rate limit errors
        """
        # Arrange
        with patch('app.services.stripe_service.stripe.PaymentIntent.create') as mock_create:
            mock_create.side_effect = stripe.error.RateLimitError(
                message="Rate limit reached"
            )
            
            # Act & Assert
            with pytest.raises(HTTPException) as exc_info:
                stripe_service.create_payment_intent(
                    amount=9999,
                    currency="USD",
                    customer_email="test@example.com"
                )
            
            assert exc_info.value.status_code == 429
    
    @pytest.mark.unit
    def test_create_payment_intent_api_connection_error(self):
        """
        CP-59: APIConnectionError when Stripe API unreachable
        Validates: HTTP 503 for connection errors
        """
        # Arrange
        with patch('app.services.stripe_service.stripe.PaymentIntent.create') as mock_create:
            mock_create.side_effect = stripe.error.APIConnectionError(
                message="Connection error"
            )
            
            # Act & Assert
            with pytest.raises(HTTPException) as exc_info:
                stripe_service.create_payment_intent(
                    amount=9999,
                    currency="USD",
                    customer_email="test@example.com"
                )
            
            assert exc_info.value.status_code == 503
    
    @pytest.mark.unit
    def test_confirm_payment_intent_success(self, mock_stripe_payment_intent_succeeded, patch_stripe_retrieve_payment_intent_succeeded):
        """
        CP-56: Confirm payment intent successfully
        Validates: Payment status retrieved correctly
        """
        # Arrange
        payment_intent_id = "pi_test_12345"
        
        # Act
        result = stripe_service.confirm_payment_intent(payment_intent_id)
        
        # Assert
        assert result is not None
        assert result['id'] == 'pi_test_12345'
        assert result['status'] == 'succeeded'
    
    @pytest.mark.unit
    def test_confirm_payment_intent_not_found(self):
        """
        Validates: 404 when payment intent not found
        """
        # Arrange
        with patch('app.services.stripe_service.stripe.PaymentIntent.retrieve') as mock_retrieve:
            mock_retrieve.side_effect = stripe.error.InvalidRequestError(
                message="No such payment_intent",
                param="id"
            )
            
            # Act & Assert
            with pytest.raises(HTTPException) as exc_info:
                stripe_service.confirm_payment_intent("pi_nonexistent")
            
            assert exc_info.value.status_code == 404
    
    @pytest.mark.unit
    def test_get_payment_intent_status_success(self, mock_stripe_payment_intent_succeeded, patch_stripe_retrieve_payment_intent_succeeded):
        """
        Validates: Get payment status from Stripe
        """
        # Arrange
        payment_intent_id = "pi_test_12345"
        
        # Act
        result = stripe_service.get_payment_intent_status(payment_intent_id)
        
        # Assert
        assert result is not None
        assert result['id'] == 'pi_test_12345'
        assert result['status'] == 'succeeded'
        assert result['amount'] == 9999
    
    @pytest.mark.unit
    def test_construct_webhook_event_success(self, mock_stripe_webhook_event_succeeded):
        """
        CP-60: Validate webhook signature successfully
        Validates: Webhook event parsed correctly
        """
        # Arrange
        body = b'{"type": "payment_intent.succeeded"}'
        sig_header = "t=123456789,v1=abc123"
        webhook_secret = "whsec_test_secret"
        
        with patch('app.services.stripe_service.stripe.Webhook.construct_event') as mock_construct:
            mock_construct.return_value = mock_stripe_webhook_event_succeeded
            
            # Act
            result = stripe_service.construct_webhook_event(
                body,
                sig_header,
                webhook_secret
            )
            
            # Assert
            assert result is not None
            assert result['type'] == 'payment_intent.succeeded'
            assert result['id'] == 'evt_test_succeeded_123'
    
    @pytest.mark.unit
    def test_construct_webhook_event_invalid_signature(self):
        """
        Validates: 403 when webhook signature invalid
        """
        # Arrange
        body = b'{"type": "payment_intent.succeeded"}'
        sig_header = "invalid_signature"
        webhook_secret = "whsec_test_secret"
        
        with patch('app.services.stripe_service.stripe.Webhook.construct_event') as mock_construct:
            mock_construct.side_effect = stripe.error.SignatureVerificationError(
                message="Invalid signature",
                sig_header=sig_header
            )
            
            # Act & Assert
            with pytest.raises(HTTPException) as exc_info:
                stripe_service.construct_webhook_event(
                    body,
                    sig_header,
                    webhook_secret
                )
            
            assert exc_info.value.status_code == 403
    
    @pytest.mark.unit
    def test_construct_webhook_event_invalid_json(self):
        """
        Validates: 400 when webhook payload invalid JSON
        """
        # Arrange
        body = b'invalid json {'
        sig_header = "t=123456789,v1=abc123"
        webhook_secret = "whsec_test_secret"
        
        with patch('app.services.stripe_service.stripe.Webhook.construct_event') as mock_construct:
            mock_construct.side_effect = ValueError("Expecting value")
            
            # Act & Assert
            with pytest.raises(HTTPException) as exc_info:
                stripe_service.construct_webhook_event(
                    body,
                    sig_header,
                    webhook_secret
                )
            
            assert exc_info.value.status_code == 400


class TestStripeServiceEdgeCases:
    """Edge cases and error scenarios"""
    
    @pytest.mark.unit
    def test_create_payment_intent_zero_amount(self):
        """
        Validates: Zero amount is rejected
        """
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            stripe_service.create_payment_intent(
                amount=0,
                currency="USD",
                customer_email="test@example.com"
            )
        
        assert exc_info.value.status_code == 400
    
    @pytest.mark.unit
    def test_create_payment_intent_very_large_amount(self, patch_stripe_create_payment_intent):
        """
        CP-56: Handle very large amounts (up to $999,999.99)
        """
        # Arrange
        large_amount = 99999999  # $999,999.99 in cents
        
        with patch('app.services.stripe_service.stripe.PaymentIntent.create') as mock_create:
            mock = MagicMock()
            mock.id = 'pi_large'
            mock.status = 'requires_payment_method'
            mock.client_secret = 'secret'
            mock.amount = large_amount
            mock.currency = 'usd'
            mock_create.return_value = mock
            
            # Act
            result = stripe_service.create_payment_intent(
                amount=large_amount,
                currency="USD",
                customer_email="test@example.com"
            )
            
            # Assert
            assert result['amount'] == large_amount
    
    @pytest.mark.unit
    def test_create_payment_intent_minimum_amount(self, patch_stripe_create_payment_intent):
        """
        CP-56: Handle minimum amount ($0.01)
        """
        # Arrange
        min_amount = 1  # $0.01 in cents
        
        with patch('app.services.stripe_service.stripe.PaymentIntent.create') as mock_create:
            mock = MagicMock()
            mock.id = 'pi_min'
            mock.status = 'requires_payment_method'
            mock.client_secret = 'secret'
            mock.amount = min_amount
            mock.currency = 'usd'
            mock_create.return_value = mock
            
            # Act
            result = stripe_service.create_payment_intent(
                amount=min_amount,
                currency="USD",
                customer_email="test@example.com"
            )
            
            # Assert
            assert result['amount'] == min_amount
