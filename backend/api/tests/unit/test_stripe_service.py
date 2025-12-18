"""
Unit tests for StripeService
Tests Stripe API integration, payment intent management, and webhook handling
"""
import pytest
from unittest.mock import patch, MagicMock
from fastapi import HTTPException
import stripe
from stripe import error as stripe_errors

from app.application.services.stripe_service import stripe_service


@pytest.mark.unit
class TestStripeServiceCreatePaymentIntent:
    """Tests for stripe_service.create_payment_intent()"""
    
    @patch('app.services.stripe_service.stripe.PaymentIntent.create')
    def test_create_payment_intent_success(self, mock_stripe_create, mock_stripe_payment_intent):
        """Test successful payment intent creation"""
        # Arrange
        mock_stripe_create.return_value = mock_stripe_payment_intent
        amount = 9999
        
        # Act
        result = stripe_service.create_payment_intent(
            amount=amount,
            currency="USD",
            customer_email="test@example.com"
        )
        
        # Assert
        assert result['id'] == 'pi_test_12345'
        assert result['amount'] == 9999
        assert result['currency'] == 'usd'
        assert result['status'] == 'requires_payment_method'
        assert 'client_secret' in result
        mock_stripe_create.assert_called_once()
    
    @patch('app.services.stripe_service.stripe.PaymentIntent.create')
    def test_create_payment_intent_with_metadata(self, mock_stripe_create, mock_stripe_payment_intent):
        """Test payment intent creation with custom metadata"""
        # Arrange
        mock_stripe_create.return_value = mock_stripe_payment_intent
        metadata = {"order_id": "123", "customer_id": "456"}
        
        # Act
        result = stripe_service.create_payment_intent(
            amount=5000,
            currency="USD",
            metadata=metadata
        )
        
        # Assert
        assert result is not None
        call_kwargs = mock_stripe_create.call_args[1]
        assert 'metadata' in call_kwargs
        assert call_kwargs['metadata']['order_id'] == "123"
    
    @patch('app.services.stripe_service.stripe.PaymentIntent.create')
    def test_create_payment_intent_invalid_amount(self, mock_stripe_create):
        """Test that negative or zero amount raises HTTPException"""
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            stripe_service.create_payment_intent(
                amount=0,
                currency="USD"
            )
        
        assert exc_info.value.status_code == 400
        assert "must be greater than 0" in exc_info.value.detail
        mock_stripe_create.assert_not_called()
    
    @patch('app.services.stripe_service.stripe.PaymentIntent.create')
    def test_create_payment_intent_card_error(self, mock_stripe_create):
        """Test handling of Stripe CardError"""
        # Arrange
        mock_stripe_create.side_effect = stripe_errors.CardError(
            message="Your card was declined",
            param="card",
            code="card_declined"
        )
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            stripe_service.create_payment_intent(
                amount=9999,
                currency="USD"
            )
        
        assert exc_info.value.status_code == 402
        assert "declined" in exc_info.value.detail.lower()
    
    @patch('app.services.stripe_service.stripe.PaymentIntent.create')
    def test_create_payment_intent_rate_limit_error(self, mock_stripe_create):
        """Test handling of Stripe RateLimitError"""
        # Arrange
        mock_stripe_create.side_effect = stripe_errors.RateLimitError(
            message="Too many requests"
        )
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            stripe_service.create_payment_intent(
                amount=9999,
                currency="USD"
            )
        
        assert exc_info.value.status_code == 429
        assert "too many" in exc_info.value.detail.lower()
    
    @patch('app.services.stripe_service.stripe.PaymentIntent.create')
    def test_create_payment_intent_api_connection_error(self, mock_stripe_create):
        """Test handling of Stripe APIConnectionError"""
        # Arrange
        mock_stripe_create.side_effect = stripe_errors.APIConnectionError(
            message="Network error"
        )
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            stripe_service.create_payment_intent(
                amount=9999,
                currency="USD"
            )
        
        assert exc_info.value.status_code == 503
        assert "pasarela" in exc_info.value.detail.lower()


@pytest.mark.unit
class TestStripeServiceRetrievePaymentIntent:
    """Tests for stripe_service.confirm_payment_intent()"""
    
    @patch('app.services.stripe_service.stripe.PaymentIntent.retrieve')
    def test_retrieve_payment_intent_success(self, mock_retrieve, mock_stripe_payment_intent_succeeded):
        """Test successful payment intent retrieval"""
        # Arrange
        mock_retrieve.return_value = mock_stripe_payment_intent_succeeded
        payment_intent_id = "pi_test_12345"
        
        # Act
        result = stripe_service.confirm_payment_intent(payment_intent_id)
        
        # Assert
        assert result['id'] == 'pi_test_12345'
        assert result['status'] == 'succeeded'
        assert result['amount'] == 9999
        mock_retrieve.assert_called_once_with(payment_intent_id)
    
    @patch('app.services.stripe_service.stripe.PaymentIntent.retrieve')
    def test_retrieve_payment_intent_not_found(self, mock_retrieve):
        """Test retrieving non-existent payment intent raises 404"""
        # Arrange
        mock_retrieve.side_effect = stripe_errors.InvalidRequestError(
            message="No such payment_intent",
            param="id"
        )
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            stripe_service.confirm_payment_intent("pi_nonexistent")
        
        assert exc_info.value.status_code == 404
        assert "not found" in exc_info.value.detail.lower()
    
    @patch('app.services.stripe_service.stripe.PaymentIntent.retrieve')
    def test_retrieve_payment_intent_connection_error(self, mock_retrieve):
        """Test handling connection error when retrieving intent"""
        # Arrange
        mock_retrieve.side_effect = stripe_errors.APIConnectionError(
            message="Network error"
        )
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            stripe_service.confirm_payment_intent("pi_test_12345")
        
        assert exc_info.value.status_code == 503


@pytest.mark.unit
class TestStripeServiceConfirmPayment:
    """Tests for stripe_service.get_payment_intent_status()"""
    
    @patch('app.services.stripe_service.stripe.PaymentIntent.retrieve')
    def test_get_payment_status_succeeded(self, mock_retrieve, mock_stripe_payment_intent_succeeded):
        """Test getting status of succeeded payment"""
        # Arrange
        mock_retrieve.return_value = mock_stripe_payment_intent_succeeded
        
        # Act
        result = stripe_service.get_payment_intent_status("pi_test_12345")
        
        # Assert
        assert result['status'] == 'succeeded'
        assert result['id'] == 'pi_test_12345'
        assert 'charges_count' in result
    
    @patch('app.services.stripe_service.stripe.PaymentIntent.retrieve')
    def test_get_payment_status_not_found(self, mock_retrieve):
        """Test getting status of non-existent payment raises 404"""
        # Arrange
        mock_retrieve.side_effect = stripe_errors.InvalidRequestError(
            message="No such payment_intent",
            param="id"
        )
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            stripe_service.get_payment_intent_status("pi_nonexistent")
        
        assert exc_info.value.status_code == 404


@pytest.mark.unit
class TestStripeServiceErrorHandling:
    """Tests for StripeService error handling"""
    
    @patch('app.services.stripe_service.stripe.PaymentIntent.create')
    def test_invalid_request_error_handling(self, mock_stripe_create):
        """Test handling of InvalidRequestError"""
        # Arrange
        mock_stripe_create.side_effect = stripe_errors.InvalidRequestError(
            message="Invalid currency",
            param="currency"
        )
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            stripe_service.create_payment_intent(
                amount=9999,
                currency="INVALID"
            )
        
        assert exc_info.value.status_code == 400
        assert "invalid" in exc_info.value.detail.lower()
    
    @patch('app.services.stripe_service.stripe.PaymentIntent.create')
    def test_authentication_error_handling(self, mock_stripe_create):
        """Test handling of AuthenticationError (invalid API key)"""
        # Arrange
        mock_stripe_create.side_effect = stripe_errors.AuthenticationError(
            message="Invalid API Key provided"
        )
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            stripe_service.create_payment_intent(
                amount=9999,
                currency="USD"
            )
        
        assert exc_info.value.status_code == 500
    
    @patch('app.services.stripe_service.stripe.PaymentIntent.create')
    def test_generic_stripe_error_handling(self, mock_stripe_create):
        """Test handling of generic StripeError"""
        # Arrange
        mock_stripe_create.side_effect = stripe_errors.StripeError(
            message="Something went wrong"
        )
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            stripe_service.create_payment_intent(
                amount=9999,
                currency="USD"
            )
        
        assert exc_info.value.status_code == 500
        assert "pasarela" in exc_info.value.detail.lower()
    
    @patch('app.services.stripe_service.stripe.PaymentIntent.create')
    def test_unexpected_error_handling(self, mock_stripe_create):
        """Test handling of unexpected non-Stripe errors"""
        # Arrange
        mock_stripe_create.side_effect = ValueError("Unexpected error")
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            stripe_service.create_payment_intent(
                amount=9999,
                currency="USD"
            )
        
        assert exc_info.value.status_code == 500


@pytest.mark.unit
class TestStripeServiceWebhook:
    """Tests for StripeService webhook handling"""
    
    @patch('app.services.stripe_service.stripe.Webhook.construct_event')
    def test_construct_webhook_event_success(self, mock_construct):
        """Test successful webhook event construction"""
        # Arrange
        mock_event = {
            'id': 'evt_test_123',
            'type': 'payment_intent.succeeded',
            'data': {'object': {'id': 'pi_test_12345'}}
        }
        mock_construct.return_value = mock_event
        
        body = b'{"id": "evt_test_123"}'
        sig_header = "t=123456,v1=signature"
        webhook_secret = "whsec_test"
        
        # Act
        result = stripe_service.construct_webhook_event(body, sig_header, webhook_secret)
        
        # Assert
        assert result['id'] == 'evt_test_123'
        assert result['type'] == 'payment_intent.succeeded'
        mock_construct.assert_called_once_with(body, sig_header, webhook_secret)
    
    @patch('app.services.stripe_service.stripe.Webhook.construct_event')
    def test_construct_webhook_invalid_payload(self, mock_construct):
        """Test webhook construction with invalid payload raises 400"""
        # Arrange
        mock_construct.side_effect = ValueError("Invalid payload")
        
        body = b'invalid json'
        sig_header = "t=123456,v1=signature"
        webhook_secret = "whsec_test"
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            stripe_service.construct_webhook_event(body, sig_header, webhook_secret)
        
        assert exc_info.value.status_code == 400
        assert "invalid payload" in exc_info.value.detail.lower()
    
    @patch('app.services.stripe_service.stripe.Webhook.construct_event')
    def test_construct_webhook_invalid_signature(self, mock_construct):
        """Test webhook construction with invalid signature raises 403"""
        # Arrange
        mock_construct.side_effect = stripe_errors.SignatureVerificationError(
            message="Invalid signature",
            sig_header="invalid"
        )
        
        body = b'{"id": "evt_test_123"}'
        sig_header = "invalid_signature"
        webhook_secret = "whsec_test"
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            stripe_service.construct_webhook_event(body, sig_header, webhook_secret)
        
        assert exc_info.value.status_code == 403
        assert "invalid signature" in exc_info.value.detail.lower()
