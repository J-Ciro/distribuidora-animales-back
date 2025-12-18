"""
Tests for User Addresses CRUD endpoints
HU: Registro sin Dirección - Address management during checkout
"""
import pytest
import requests
import os
from typing import Dict, Any

BACKEND_BASE_URL = os.getenv("BACKEND_BASE_URL", "http://localhost:8000")


@pytest.fixture(scope="module")
def authenticated_user():
    """Setup test user credentials for authentication"""
    # Use a simple test user email that complies with backend validation
    test_credentials = {
        "email": "test.direction@example.com",
        "password": "TestPass123#",
        "nombre": "Test Direcciones User",
        "cedula": "1234567890",
        "telefono": "3001234567", 
        "preferencia_mascotas": "Gatos"
    }
    
    # Step 1: Try to register the user
    reg_response = requests.post(
        f"{BACKEND_BASE_URL}/api/auth/register",
        json=test_credentials,
        timeout=10
    )
    
    # Step 2: If already exists (409), that's OK - means user was created in previous test run
    if reg_response.status_code not in [201, 409]:
        pytest.skip(f"Cannot register test user: {reg_response.text}")
    
    # Step 3: Try to verify email with test code (if not already verified)
    if reg_response.status_code == 201:
        requests.post(
            f"{BACKEND_BASE_URL}/api/auth/verify-email",
            json={
                "email": test_credentials["email"],
                "codigo": "000000"
            },
            timeout=10
        )
    
    # Step 4: Login to get token
    login_response = requests.post(
        f"{BACKEND_BASE_URL}/api/auth/login",
        json={
            "email": test_credentials["email"],
            "password": test_credentials["password"]
        },
        timeout=10
    )
    
    if login_response.status_code != 200:
        pytest.skip(f"Cannot authenticate: {login_response.text}")
    
    data = login_response.json()
    
    return {
        "token": data.get("access_token"),
        "credentials": test_credentials
    }


def test_create_address_success(authenticated_user):
    """Test creating a new address successfully"""
    token = authenticated_user["token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    address_data = {
        "direccion_completa": "Calle 123 #45-67, Apartamento 301",
        "municipio": "Bogotá",
        "departamento": "Cundinamarca",
        "pais": "Colombia",
        "es_principal": True
    }
    
    response = requests.post(
        f"{BACKEND_BASE_URL}/api/usuarios/direcciones/",
        json=address_data,
        headers=headers,
        timeout=10
    )
    
    assert response.status_code == 201, f"Address creation failed: {response.text}"
    
    data = response.json()
    assert "id" in data
    assert data["direccion_completa"] == address_data["direccion_completa"]
    assert data["municipio"] == address_data["municipio"]
    assert data["departamento"] == address_data["departamento"]
    assert data["pais"] == address_data["pais"]
    assert data["es_principal"] is True
    # Verify alias field was removed (should not exist)
    assert "alias" not in data or data.get("alias") is None


def test_create_address_without_optional_fields(authenticated_user):
    """Test creating address with only required field"""
    token = authenticated_user["token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    address_data = {
        "direccion_completa": "Carrera 7 #10-20"
    }
    
    response = requests.post(
        f"{BACKEND_BASE_URL}/api/usuarios/direcciones/",
        json=address_data,
        headers=headers,
        timeout=10
    )
    
    assert response.status_code == 201, f"Address creation failed: {response.text}"
    
    data = response.json()
    assert data["direccion_completa"] == address_data["direccion_completa"]
    assert data["pais"] == "Colombia"  # Default value
    assert data["es_principal"] is False  # Default value


def test_create_address_invalid_direccion_too_short(authenticated_user):
    """Test validation: direccion_completa must be at least 10 characters"""
    token = authenticated_user["token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    address_data = {
        "direccion_completa": "Short"  # Only 5 characters
    }
    
    response = requests.post(
        f"{BACKEND_BASE_URL}/api/usuarios/direcciones/",
        json=address_data,
        headers=headers,
        timeout=10
    )
    
    assert response.status_code == 400, "Should reject short address"


def test_create_address_missing_required_field(authenticated_user):
    """Test validation: direccion_completa is required"""
    token = authenticated_user["token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    address_data = {
        "municipio": "Medellín"
        # Missing direccion_completa
    }
    
    response = requests.post(
        f"{BACKEND_BASE_URL}/api/usuarios/direcciones/",
        json=address_data,
        headers=headers,
        timeout=10
    )
    
    assert response.status_code == 400, "Should reject missing required field"


def test_list_user_addresses(authenticated_user):
    """Test listing user addresses"""
    token = authenticated_user["token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create two addresses
    addresses = [
        {
            "direccion_completa": "Primera dirección de prueba #123",
            "municipio": "Cali",
            "departamento": "Valle del Cauca",
            "es_principal": True
        },
        {
            "direccion_completa": "Segunda dirección diferente #456",
            "municipio": "Barranquilla",
            "departamento": "Atlántico",
            "es_principal": False
        }
    ]
    
    for addr in addresses:
        response = requests.post(
            f"{BACKEND_BASE_URL}/api/usuarios/direcciones/",
            json=addr,
            headers=headers,
            timeout=10
        )
        assert response.status_code == 201
    
    # List addresses
    response = requests.get(
        f"{BACKEND_BASE_URL}/api/usuarios/direcciones/",
        headers=headers,
        timeout=10
    )
    
    assert response.status_code == 200, f"List failed: {response.text}"
    data = response.json()
    
    assert isinstance(data, list)
    assert len(data) >= 2
    
    # Verify primary address is first
    assert data[0]["es_principal"] is True


def test_delete_address(authenticated_user):
    """Test deleting an address"""
    token = authenticated_user["token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create address
    address_data = {
        "direccion_completa": "Dirección a eliminar #789"
    }
    
    create_response = requests.post(
        f"{BACKEND_BASE_URL}/api/usuarios/direcciones/",
        json=address_data,
        headers=headers,
        timeout=10
    )
    
    assert create_response.status_code == 201
    address_id = create_response.json()["id"]
    
    # Delete address
    delete_response = requests.delete(
        f"{BACKEND_BASE_URL}/api/usuarios/direcciones/{address_id}",
        headers=headers,
        timeout=10
    )
    
    assert delete_response.status_code == 200, f"Delete failed: {delete_response.text}"
    
    # Verify it's deleted
    list_response = requests.get(
        f"{BACKEND_BASE_URL}/api/usuarios/direcciones/",
        headers=headers,
        timeout=10
    )
    
    addresses = list_response.json()
    address_ids = [addr["id"] for addr in addresses]
    assert address_id not in address_ids


def test_delete_nonexistent_address(authenticated_user):
    """Test deleting address that doesn't exist"""
    token = authenticated_user["token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.delete(
        f"{BACKEND_BASE_URL}/api/usuarios/direcciones/999999",
        headers=headers,
        timeout=10
    )
    
    assert response.status_code == 404, "Should return 404 for nonexistent address"


def test_addresses_require_authentication():
    """Test that address endpoints require authentication"""
    # Try to list addresses without token
    response = requests.get(
        f"{BACKEND_BASE_URL}/api/usuarios/direcciones/",
        timeout=10
    )
    
    assert response.status_code == 401, "Should require authentication"
    
    # Try to create address without token
    response = requests.post(
        f"{BACKEND_BASE_URL}/api/usuarios/direcciones/",
        json={"direccion_completa": "Test address"},
        timeout=10
    )
    
    assert response.status_code == 401, "Should require authentication"


def test_only_one_primary_address(authenticated_user):
    """Test that only one address can be primary"""
    token = authenticated_user["token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create first primary address
    addr1 = {
        "direccion_completa": "Primera dirección principal",
        "es_principal": True
    }
    
    response1 = requests.post(
        f"{BACKEND_BASE_URL}/api/usuarios/direcciones/",
        json=addr1,
        headers=headers,
        timeout=10
    )
    assert response1.status_code == 201
    
    # Create second primary address
    addr2 = {
        "direccion_completa": "Segunda dirección principal",
        "es_principal": True
    }
    
    response2 = requests.post(
        f"{BACKEND_BASE_URL}/api/usuarios/direcciones/",
        json=addr2,
        headers=headers,
        timeout=10
    )
    assert response2.status_code == 201
    
    # List addresses - only one should be primary
    list_response = requests.get(
        f"{BACKEND_BASE_URL}/api/usuarios/direcciones/",
        headers=headers,
        timeout=10
    )
    
    addresses = list_response.json()
    primary_count = sum(1 for addr in addresses if addr["es_principal"])
    
    assert primary_count == 1, "Only one address should be primary"


def test_user_can_only_access_own_addresses(authenticated_user):
    """Test that users can only see their own addresses"""
    # User 1 creates address
    token1 = authenticated_user["token"]
    headers1 = {"Authorization": f"Bearer {token1}"}
    
    addr_data = {
        "direccion_completa": "Dirección privada del usuario 1"
    }
    
    response = requests.post(
        f"{BACKEND_BASE_URL}/api/usuarios/direcciones/",
        json=addr_data,
        headers=headers1,
        timeout=10
    )
    assert response.status_code == 201
    address_id = response.json()["id"]
    
    # User 2 login with different verified test account
    user2_creds = {
        "email": "ospina3sofka@yopmail.com",  # Different verified test user
        "password": "Sofka2025#"
    }
    
    login2 = requests.post(
        f"{BACKEND_BASE_URL}/api/auth/login",
        json=user2_creds,
        timeout=10
    )
    
    # If user doesn't exist, skip this test
    if login2.status_code != 200:
        pytest.skip("Second test user not available")
    
    token2 = login2.json().get("access_token")
    headers2 = {"Authorization": f"Bearer {token2}"}
    
    # User 2 tries to delete User 1's address
    delete_response = requests.delete(
        f"{BACKEND_BASE_URL}/api/usuarios/direcciones/{address_id}",
        headers=headers2,
        timeout=10
    )
    
    assert delete_response.status_code == 404, "User should not be able to delete other user's address"


def test_addresses_ordered_by_primary_then_created(authenticated_user):
    """Test that addresses are ordered by es_principal DESC, created_at DESC"""
    token = authenticated_user["token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create addresses in specific order
    addresses = [
        {"direccion_completa": "Dirección antigua no principal", "es_principal": False},
        {"direccion_completa": "Dirección reciente no principal", "es_principal": False},
        {"direccion_completa": "Dirección principal", "es_principal": True}
    ]
    
    for addr in addresses:
        response = requests.post(
            f"{BACKEND_BASE_URL}/api/usuarios/direcciones/",
            json=addr,
            headers=headers,
            timeout=10
        )
        assert response.status_code == 201
    
    # List addresses
    list_response = requests.get(
        f"{BACKEND_BASE_URL}/api/usuarios/direcciones/",
        headers=headers,
        timeout=10
    )
    
    result = list_response.json()
    
    # First should be primary
    assert result[0]["es_principal"] is True
    
    # Rest should be non-primary ordered by creation (newest first)
    assert result[1]["es_principal"] is False
    assert result[2]["es_principal"] is False
