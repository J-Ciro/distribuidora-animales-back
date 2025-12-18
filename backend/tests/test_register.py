import requests
import json

# Test de registro completo
BASE_URL = "http://localhost:8000"

print("=" * 60)
print("TEST DE REGISTRO Y ENVÍO DE EMAIL")
print("=" * 60)
print()

# Datos de prueba
test_user = {
    "email": "test.verificacion@gmail.com",
    "password": "TestPass123!@#",
    "nombre": "Usuario Test",
    "cedula": "9999999999",
    "telefono": "3001234567",
    "direccion_envio": "Calle Test 123",
    "preferencia_mascotas": "Perros"
}

print(f"📝 Registrando usuario: {test_user['email']}")
print()

try:
    response = requests.post(
        f"{BASE_URL}/api/auth/register",
        json=test_user,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print()
    
    if response.status_code == 201:
        print("✅ Registro exitoso")
        print("📧 Revisa los logs del backend para ver si el email se envió")
        print()
        print("Para ver los logs:")
        print("docker logs distribuidora-api --tail 30")
    else:
        print("❌ Error en el registro")
        
except Exception as e:
    print(f"❌ Error: {e}")
