#!/usr/bin/env python3
"""Test endpoint mis-pedidos directly"""
import sys
import json
sys.path.insert(0, '/app')

from app.database import SessionLocal
from app.routers.orders import get_my_orders
from app.routers.auth import get_current_user
import app.models as models
from fastapi import Depends
from sqlalchemy.orm import Session

# Simulate a request
db = SessionLocal()

# Get a test user (usuario_id=3 from previous tests)
user = db.query(models.Usuario).filter(models.Usuario.id == 3).first()

if not user:
    print("❌ No se encontró usuario con ID 3")
    sys.exit(1)

# Create a mock current_user
class MockUser:
    def __init__(self, user_id):
        self.id = user_id

mock_user = MockUser(3)

# Call the function directly
from app.routers.orders import _pedido_to_response

pedidos = (
    db.query(models.Pedido)
    .filter(models.Pedido.usuario_id == mock_user.id)
    .all()
)

print(f"\n🔍 Usuario #{mock_user.id} tiene {len(pedidos)} pedido(s)\n")

for pedido in pedidos:
    response = _pedido_to_response(db, pedido)
    print(f"📦 Pedido #{response['id']}")
    print(f"   Items: {len(response.get('items', []))}")
    
    for item in response.get('items', []):
        nombre = item.get('producto_nombre', '❌ NO TIENE NOMBRE')
        print(f"   └─ Producto #{item['producto_id']}: {nombre}")

    # Also print the raw JSON to see exactly what's being returned
    print(f"\n   JSON del pedido:")
    print(json.dumps(response, indent=2, ensure_ascii=False, default=str))
    print()

db.close()
