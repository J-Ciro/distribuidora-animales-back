"""
Pytest configuration and fixtures for Stripe payment integration tests
Provides: JWT tokens, test database, HTTP client, Stripe mocks
"""
import pytest
import json
import sys
import os
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from fastapi.testclient import TestClient

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from main import app
from app.core.database import Base, get_db
from app.core.config import settings
from app.domain.models import Usuario, Pedido, PedidoItem, TransaccionPago
from app.infrastructure.security.security import SecurityUtils
import app.domain.models as models


# ============================================================================
# DATABASE FIXTURES
# ============================================================================

@pytest.fixture(scope="function")
def test_db():
    """
    Create a fresh in-memory SQLite test database for each test
    Automatically rolled back after test completes
    """
    # Use SQLite in-memory for tests
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    db = TestingSessionLocal()
    
    yield db
    
    db.close()
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(test_db):
    """Alias for test_db for convenience"""
    return test_db


def override_get_db(db):
    """Dependency override to inject test database"""
    try:
        yield db
    finally:
        pass


@pytest.fixture(scope="function")
def client(test_db):
    """
    FastAPI TestClient with injected test database
    """
    app.dependency_overrides[get_db] = lambda: test_db
    
    client = TestClient(app)
    
    yield client
    
    # Clean up
    app.dependency_overrides.clear()


# ============================================================================
# USER FIXTURES
# ============================================================================

@pytest.fixture(scope="function")
def test_user(test_db: Session) -> Usuario:
    """
    Create a test user in the database
    """
    usuario = Usuario(
        email="test@example.com",
        nombre_completo="Test User",
        cedula="12345678",
        password_hash="hashed_password_123",
        es_admin=False,
        is_active=True,
        fecha_registro=datetime.utcnow(),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    test_db.add(usuario)
    test_db.commit()
    test_db.refresh(usuario)
    return usuario


@pytest.fixture(scope="function")
def test_admin_user(test_db: Session) -> Usuario:
    """
    Create a test admin user in the database
    """
    admin = Usuario(
        email="admin@example.com",
        nombre_completo="Admin User",
        cedula="87654321",
        password_hash="hashed_admin_password",
        es_admin=True,
        is_active=True,
        fecha_registro=datetime.utcnow(),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    test_db.add(admin)
    test_db.commit()
    test_db.refresh(admin)
    return admin


# ============================================================================
# JWT TOKEN FIXTURES
# ============================================================================

@pytest.fixture(scope="function")
def user_token(test_user: Usuario) -> str:
    """
    Generate a valid JWT token for test user
    """
    return SecurityUtils.create_access_token({"sub": str(test_user.id)})


@pytest.fixture(scope="function")
def admin_token(test_admin_user: Usuario) -> str:
    """
    Generate a valid JWT token for admin user
    """
    return SecurityUtils.create_access_token({"sub": str(test_admin_user.id)})


@pytest.fixture(scope="function")
def auth_headers(user_token: str) -> dict:
    """
    Return authorization headers with valid JWT
    """
    return {"Authorization": f"Bearer {user_token}"}


@pytest.fixture(scope="function")
def admin_auth_headers(admin_token: str) -> dict:
    """
    Return authorization headers with admin JWT
    """
    return {"Authorization": f"Bearer {admin_token}"}


# ============================================================================
# PRODUCT FIXTURES
# ============================================================================
# Products are not ORM models in backend/api, so we use SimpleNamespace mocks

from types import SimpleNamespace

@pytest.fixture(scope="function")
def test_products():
    """
    Mock product objects for testing
    Each product has common attributes needed for order tests
    """
    products = [
        SimpleNamespace(
            id=1,
            nombre="Producto Test 1",
            precio=50000,  # COP
            cantidad_disponible=100,
            categoria_id=1
        ),
        SimpleNamespace(
            id=2,
            nombre="Producto Test 2",
            precio=75000,  # COP
            cantidad_disponible=50,
            categoria_id=1
        ),
        SimpleNamespace(
            id=3,
            nombre="Producto Test 3",
            precio=25000,  # COP
            cantidad_disponible=200,
            categoria_id=2
        )
    ]
    return products


# ============================================================================
# ORDER FIXTURES
# ============================================================================

@pytest.fixture(scope="function")
def test_order(test_db: Session, test_user: Usuario, test_products):
    """
    Create a test order with items, status Pendiente de Pago
    """
    pedido = Pedido(
        usuario_id=test_user.id,
        estado="Pendiente",
        estado_pago="Pendiente de Pago",
        total=99.99,
        metodo_pago="Stripe",
        direccion_entrega="123 Test St",
        municipio="Test City",
        departamento="Test State",
        pais="Colombia",
        telefono_contacto="1234567890"
    )
    test_db.add(pedido)
    test_db.flush()
    
    # Add order item with mock producto
    item = PedidoItem(
        pedido_id=pedido.id,
        producto_id=1,
        cantidad=1,
        precio_unitario=99.99
    )
    # Attach mock producto object to item
    item.producto = test_products[0]
    test_db.add(item)
    test_db.commit()
    test_db.refresh(pedido)
    
    return pedido


@pytest.fixture(scope="function")
def test_paid_order(test_db: Session, test_user: Usuario):
    """
    Create a test order with status Pagado
    """
    pedido = Pedido(
        usuario_id=test_user.id,
        estado="Pendiente",
        estado_pago="Pagado",
        total=99.99,
        metodo_pago="Stripe",
        direccion_entrega="123 Test St",
        municipio="Test City",
        departamento="Test State",
        pais="Colombia",
        telefono_contacto="1234567890"
    )
    test_db.add(pedido)
    test_db.flush()
    
    item = PedidoItem(
        pedido_id=pedido.id,
        producto_id=1,
        cantidad=1,
        precio_unitario=99.99
    )
    test_db.add(item)
    test_db.commit()
    test_db.refresh(pedido)
    
    return pedido


@pytest.fixture(scope="function")
def test_order_with_single_item(test_db: Session, test_user: Usuario, test_products):
    """
    Create a test order with a single item (includes detalles property for compatibility)
    """
    pedido = Pedido(
        usuario_id=test_user.id,
        estado="Pendiente",
        estado_pago="Pendiente de Pago",
        total=99.99,
        metodo_pago="Stripe",
        direccion_entrega="123 Test St",
        municipio="Test City",
        departamento="Test State",
        pais="Colombia",
        telefono_contacto="1234567890"
    )
    test_db.add(pedido)
    test_db.flush()
    
    # Create item with mutable properties for test modifications
    item = PedidoItem(
        pedido_id=pedido.id,
        producto_id=1,
        cantidad=1,
        precio_unitario=99.99
    )
    # Attach mock producto
    item.producto = test_products[0]
    test_db.add(item)
    test_db.commit()
    test_db.refresh(pedido)
    test_db.refresh(item)
    
    # Add detalles property for compatibility with tests that expect it
    pedido.detalles = [item]
    
    return pedido


@pytest.fixture(scope="function")
def test_order_with_multiple_items(test_db: Session, test_user: Usuario, test_products):
    """
    Create a test order with multiple items
    """
    pedido = Pedido(
        usuario_id=test_user.id,
        estado="Pendiente",
        estado_pago="Pendiente de Pago",
        total=299.97,
        metodo_pago="Stripe",
        direccion_entrega="123 Test St",
        municipio="Test City",
        departamento="Test State",
        pais="Colombia",
        telefono_contacto="1234567890"
    )
    test_db.add(pedido)
    test_db.flush()
    
    # Create multiple items
    items = []
    for i in range(1, 4):
        item = PedidoItem(
            pedido_id=pedido.id,
            producto_id=i,
            cantidad=i,
            precio_unitario=99.99
        )
        # Attach mock producto
        item.producto = test_products[i-1]
        test_db.add(item)
        items.append(item)
    
    test_db.commit()
    test_db.refresh(pedido)
    for item in items:
        test_db.refresh(item)
    
    # Add detalles property for compatibility
    pedido.detalles = items
    
    return pedido


@pytest.fixture(scope="function")
def test_order_maximum_items(test_db: Session, test_user: Usuario, test_products):
    """
    Create a test order with maximum items (100 items)
    """
    pedido = Pedido(
        usuario_id=test_user.id,
        estado="Pendiente",
        estado_pago="Pendiente de Pago",
        total=9999.00,
        metodo_pago="Stripe",
        direccion_entrega="123 Test St",
        municipio="Test City",
        departamento="Test State",
        pais="Colombia",
        telefono_contacto="1234567890"
    )
    test_db.add(pedido)
    test_db.flush()
    
    # Create 100 items
    items = []
    for i in range(1, 101):
        item = PedidoItem(
            pedido_id=pedido.id,
            producto_id=(i % 3) + 1,  # Cycle through 3 products
            cantidad=1,
            precio_unitario=99.99
        )
        # Attach mock producto
        item.producto = test_products[(i % 3)]
        test_db.add(item)
        items.append(item)
    
    test_db.commit()
    test_db.refresh(pedido)
    for item in items:
        test_db.refresh(item)
    
    # Add detalles property for compatibility
    pedido.detalles = items
    
    return pedido


# ============================================================================
# PAYMENT AMOUNT FIXTURES (PARTITION OF EQUIVALENCE)
# ============================================================================

@pytest.fixture(scope="function")
def payment_amount_minimum():
    """Monto mínimo válido: $0.01 (BOUND-001)"""
    from decimal import Decimal
    return {
        "amount": Decimal("0.01"),
        "amount_cents": 1,
        "description": "Monto mínimo válido"
    }


@pytest.fixture(scope="function")
def payment_amount_standard():
    """Monto estándar de prueba: $99.99"""
    from decimal import Decimal
    return {
        "amount": Decimal("99.99"),
        "amount_cents": 9999,
        "description": "Monto estándar de prueba"
    }


@pytest.fixture(scope="function")
def payment_amount_maximum():
    """Monto máximo válido: $999,999.99 (BOUND-002)"""
    from decimal import Decimal
    return {
        "amount": Decimal("999999.99"),
        "amount_cents": 99999999,
        "description": "Monto máximo válido"
    }


@pytest.fixture(scope="function")
def payment_amount_invalid_negative():
    """Monto inválido negativo para test de validación"""
    from decimal import Decimal
    return {
        "amount": Decimal("-10.00"),
        "amount_cents": -1000,
        "description": "Monto negativo inválido"
    }


@pytest.fixture(scope="function")
def payment_amount_invalid_zero():
    """Monto cero inválido para test de validación"""
    from decimal import Decimal
    return {
        "amount": Decimal("0.00"),
        "amount_cents": 0,
        "description": "Monto cero inválido"
    }


# ============================================================================
# STRIPE CARD TEST NUMBERS FIXTURES
# ============================================================================

@pytest.fixture(scope="function")
def stripe_card_visa_success():
    """Tarjeta Visa exitosa"""
    return {
        "number": "4242424242424242",
        "exp_month": 12,
        "exp_year": 2030,
        "cvc": "123",
        "name": "Test Visa",
        "token": "tok_visa"
    }


@pytest.fixture(scope="function")
def stripe_card_mastercard_success():
    """Tarjeta Mastercard exitosa"""
    return {
        "number": "5555555555554444",
        "exp_month": 6,
        "exp_year": 2029,
        "cvc": "456",
        "name": "Test Mastercard",
        "token": "tok_mastercard"
    }


@pytest.fixture(scope="function")
def stripe_card_declined():
    """Tarjeta declinada genérica"""
    return {
        "number": "4000000000000002",
        "exp_month": 12,
        "exp_year": 2030,
        "cvc": "123",
        "name": "Test Declined",
        "token": "tok_chargeDeclined"
    }


@pytest.fixture(scope="function")
def stripe_card_insufficient_funds():
    """Tarjeta con fondos insuficientes"""
    return {
        "number": "4000000000009995",
        "exp_month": 12,
        "exp_year": 2030,
        "cvc": "123",
        "name": "Test Insufficient",
        "token": "tok_chargeDeclinedInsufficientFunds"
    }


@pytest.fixture(scope="function")
def stripe_card_expired():
    """Tarjeta expirada"""
    return {
        "number": "4000000000000069",
        "exp_month": 1,
        "exp_year": 2020,
        "cvc": "123",
        "name": "Test Expired",
        "token": "tok_chargeDeclinedExpiredCard"
    }


@pytest.fixture(scope="function")
def stripe_card_invalid_cvc():
    """Tarjeta con CVC inválido"""
    return {
        "number": "4000000000000127",
        "exp_month": 12,
        "exp_year": 2030,
        "cvc": "000",
        "name": "Test Invalid CVC",
        "token": "tok_chargeDeclinedIncorrectCvc"
    }


@pytest.fixture(scope="function")
def stripe_card_3ds_required():
    """Tarjeta que requiere autenticación 3D Secure"""
    return {
        "number": "4000002500003155",
        "exp_month": 12,
        "exp_year": 2030,
        "cvc": "123",
        "name": "Test 3DS Required",
        "token": "tok_threeDSecure2Required"
    }


# ============================================================================
# STRIPE ERROR FIXTURES
# ============================================================================

@pytest.fixture(scope="function")
def stripe_error_card_declined():
    """Error: Tarjeta declinada"""
    return {
        "type": "card_error",
        "code": "card_declined",
        "decline_code": "generic_decline",
        "message": "Your card was declined.",
        "param": "card"
    }


@pytest.fixture(scope="function")
def stripe_error_insufficient_funds():
    """Error: Fondos insuficientes"""
    return {
        "type": "card_error",
        "code": "card_declined",
        "decline_code": "insufficient_funds",
        "message": "Your card has insufficient funds.",
        "param": "card"
    }


@pytest.fixture(scope="function")
def stripe_error_expired_card():
    """Error: Tarjeta expirada"""
    return {
        "type": "card_error",
        "code": "expired_card",
        "decline_code": "expired_card",
        "message": "Your card has expired.",
        "param": "exp_year"
    }


@pytest.fixture(scope="function")
def stripe_error_invalid_cvc():
    """Error: CVC incorrecto"""
    return {
        "type": "card_error",
        "code": "incorrect_cvc",
        "decline_code": "incorrect_cvc",
        "message": "Your card's security code is incorrect.",
        "param": "cvc"
    }


@pytest.fixture(scope="function")
def stripe_error_invalid_number():
    """Error: Número de tarjeta inválido"""
    return {
        "type": "card_error",
        "code": "incorrect_number",
        "message": "Your card number is incorrect.",
        "param": "number"
    }


@pytest.fixture(scope="function")
def stripe_error_api_connection():
    """Error: Problema de conexión con Stripe API"""
    return {
        "type": "api_connection_error",
        "message": "Network error communicating with Stripe."
    }


@pytest.fixture(scope="function")
def stripe_error_rate_limit():
    """Error: Rate limit excedido"""
    return {
        "type": "rate_limit_error",
        "message": "Too many requests hit the API too quickly."
    }


@pytest.fixture(scope="function")
def stripe_error_api_error():
    """Error: Error de servidor de Stripe"""
    return {
        "type": "api_error",
        "message": "An error occurred internally with Stripe."
    }


# ============================================================================
# STRIPE MOCK FIXTURES
# ============================================================================

@pytest.fixture(scope="function")
def stripe_test_keys():
    """
    Provide test Stripe API keys
    """
    return {
        "secret_key": "sk_test_4eC39HqLyjWDarhtT657L51",
        "publishable_key": "pk_test_51AbCdEfGhIjKlMnOpQrStUv",
        "webhook_secret": "whsec_test_secret"
    }


@pytest.fixture(scope="function")
def webhook_event_payment_succeeded():
    """
    Mock webhook event for payment_intent.succeeded
    """
    return {
        "id": "evt_test_succeeded_123",
        "type": "payment_intent.succeeded",
        "created": int(datetime.utcnow().timestamp()),
        "data": {
            "object": {
                "id": "pi_test_12345",
                "status": "succeeded",
                "amount": 9999,
                "currency": "usd"
            }
        }
    }


@pytest.fixture(scope="function")
def webhook_event_payment_failed():
    """
    Mock webhook event for payment_intent.payment_failed
    """
    return {
        "id": "evt_test_failed_123",
        "type": "payment_intent.payment_failed",
        "created": int(datetime.utcnow().timestamp()),
        "data": {
            "object": {
                "id": "pi_test_failed",
                "status": "requires_payment_method",
                "amount": 9999,
                "currency": "usd",
                "last_payment_error": {
                    "message": "Card declined"
                }
            }
        }
    }


@pytest.fixture(scope="function")
def mock_stripe_payment_intent():
    """
    Mock Stripe PaymentIntent.create() response
    Returns a mock object with attributes (not dict)
    """
    mock = MagicMock()
    mock.id = 'pi_test_12345'
    mock.status = 'requires_payment_method'
    mock.client_secret = 'pi_test_12345_secret_xyz'
    mock.amount = 9999
    mock.currency = 'usd'
    mock.automatic_payment_methods = {'enabled': True, 'allow_redirects': 'never'}
    return mock


@pytest.fixture(scope="function")
def mock_stripe_payment_intent_succeeded():
    """
    Mock Stripe PaymentIntent.retrieve() response (succeeded)
    Returns a mock object with attributes (not dict)
    """
    mock = MagicMock()
    mock.id = 'pi_test_12345'
    mock.status = 'succeeded'
    mock.client_secret = 'pi_test_12345_secret_xyz'
    mock.amount = 9999
    mock.currency = 'usd'
    charges_mock = MagicMock()
    charge_mock = MagicMock()
    charge_mock.id = 'ch_test_123'
    charge_mock.amount = 9999
    charge_mock.status = 'succeeded'
    charges_mock.data = [charge_mock]
    mock.charges = charges_mock
    return mock


@pytest.fixture(scope="function")
def mock_stripe_payment_intent_failed():
    """
    Mock Stripe PaymentIntent.retrieve() response (failed)
    Returns a mock object with attributes (not dict)
    """
    mock = MagicMock()
    mock.id = 'pi_test_failed'
    mock.status = 'requires_payment_method'
    mock.client_secret = 'pi_test_failed_secret'
    mock.amount = 9999
    mock.currency = 'usd'
    error_mock = MagicMock()
    error_mock.type = 'card_error'
    error_mock.message = 'Your card was declined'
    mock.last_payment_error = error_mock
    return mock


@pytest.fixture(scope="function")
def mock_stripe_webhook_event_succeeded():
    """
    Mock Stripe webhook event for payment_intent.succeeded
    """
    return {
        'id': 'evt_test_succeeded_123',
        'type': 'payment_intent.succeeded',
        'created': int(datetime.utcnow().timestamp()),
        'data': {
            'object': {
                'id': 'pi_test_12345',
                'status': 'succeeded',
                'amount': 9999,
                'currency': 'usd'
            }
        }
    }


@pytest.fixture(scope="function")
def mock_stripe_webhook_event_failed():
    """
    Mock Stripe webhook event for payment_intent.payment_failed
    """
    return {
        'id': 'evt_test_failed_123',
        'type': 'payment_intent.payment_failed',
        'created': int(datetime.utcnow().timestamp()),
        'data': {
            'object': {
                'id': 'pi_test_failed',
                'status': 'requires_payment_method',
                'amount': 9999,
                'currency': 'usd',
                'last_payment_error': {
                    'message': 'Card declined'
                }
            }
        }
    }


# ============================================================================
# REQUEST PAYLOAD FIXTURES
# ============================================================================

@pytest.fixture(scope="function")
def create_payment_intent_payload():
    """
    Payload for POST /api/pagos/create-payment-intent
    """
    return {
        "pedido_id": 1,
        "amount": 99.99,
        "currency": "USD"
    }


@pytest.fixture(scope="function")
def confirm_payment_payload():
    """
    Payload for POST /api/pagos/confirm-payment
    """
    return {
        "payment_intent_id": "pi_test_12345",
        "pedido_id": 1
    }


@pytest.fixture(scope="function")
def create_order_payload():
    """
    Payload for POST /api/admin/pedidos
    """
    return {
        "usuario_id": 1,
        "items": [
            {
                "producto_id": 1,
                "cantidad": 1,
                "precio_unitario": 99.99
            }
        ],
        "direccion_entrega": "123 Test St",
        "municipio": "Test City",
        "departamento": "Test State",
        "pais": "Colombia",
        "telefono_contacto": "1234567890"
    }


# ============================================================================
# PATCH/MOCK FIXTURES
# ============================================================================

@pytest.fixture(scope="function")
def patch_stripe_create_payment_intent(mock_stripe_payment_intent):
    """
    Patch stripe.PaymentIntent.create() to return mock response
    """
    with patch('app.services.stripe_service.stripe.PaymentIntent.create') as mock:
        mock.return_value = mock_stripe_payment_intent
        yield mock


@pytest.fixture(scope="function")
def patch_stripe_retrieve_payment_intent_succeeded(mock_stripe_payment_intent_succeeded):
    """
    Patch stripe.PaymentIntent.retrieve() to return succeeded status
    """
    with patch('app.services.stripe_service.stripe.PaymentIntent.retrieve') as mock:
        mock.return_value = mock_stripe_payment_intent_succeeded
        yield mock


@pytest.fixture(scope="function")
def patch_stripe_retrieve_payment_intent_failed(mock_stripe_payment_intent_failed):
    """
    Patch stripe.PaymentIntent.retrieve() to return failed status
    """
    with patch('app.services.stripe_service.stripe.PaymentIntent.retrieve') as mock:
        mock.return_value = mock_stripe_payment_intent_failed
        yield mock


@pytest.fixture(scope="function")
def patch_stripe_construct_webhook_event():
    """
    Patch stripe.Webhook.construct_event() for signature validation
    """
    with patch('app.services.stripe_service.stripe.Webhook.construct_event') as mock:
        yield mock


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_auth_headers(token: str) -> dict:
    """
    Helper to create auth headers from token
    """
    return {"Authorization": f"Bearer {token}"}


def create_test_payment_intent_id() -> str:
    """
    Generate a test payment intent ID
    """
    return f"pi_test_{int(datetime.utcnow().timestamp() * 1000)}"


def create_test_event_id() -> str:
    """
    Generate a test webhook event ID
    """
    return f"evt_test_{int(datetime.utcnow().timestamp() * 1000)}"


# ============================================================================
# PYTEST CONFIGURATION
# ============================================================================

# ============================================================================
# ADDITIONAL FIXTURES FOR MISSING ITEMS
# ============================================================================

@pytest.fixture(scope="function")
def order_items_multiple():
    """
    Returns a list of order items for multiple item tests
    """
    return [
        {"producto_id": 1, "cantidad": 2, "precio_unitario": 50.00},
        {"producto_id": 2, "cantidad": 1, "precio_unitario": 75.00},
        {"producto_id": 3, "cantidad": 3, "precio_unitario": 25.00}
    ]


@pytest.fixture(scope="function")
def order_items_maximum():
    """
    Returns a list of 100 order items for maximum items tests
    """
    return [{"producto_id": (i % 3) + 1, "cantidad": 1, "precio_unitario": 99.99} for i in range(1, 101)]


@pytest.fixture(scope="function")
def test_product_low_stock(test_db: Session):
    """
    Create a mock product with low stock for testing
    """
    return SimpleNamespace(
        id=4,
        nombre="Producto Stock Bajo",
        precio=50000,
        cantidad_disponible=2,
        categoria_id=1
    )


@pytest.fixture(scope="function")
def capture_logs(caplog):
    """
    Fixture for capturing logs in tests
    """
    import logging
    caplog.set_level(logging.INFO)
    return caplog


@pytest.fixture(scope="function")
def sample_webhook_headers():
    """
    Sample webhook headers for testing webhook validation
    """
    return {
        "stripe-signature": "t=1234567890,v1=test_signature_hash,v0=test_signature_v0"
    }


@pytest.fixture(scope="function")
def webhook_event_duplicate():
    """
    Mock duplicate webhook event for testing idempotency
    """
    return {
        "id": "evt_test_duplicate_123",
        "type": "payment_intent.succeeded",
        "created": int(datetime.utcnow().timestamp()),
        "data": {
            "object": {
                "id": "pi_test_duplicate",
                "status": "succeeded",
                "amount": 9999,
                "currency": "usd"
            }
        }
    }


def pytest_configure(config):
    """Register custom markers"""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "e2e: mark test as an end-to-end test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
