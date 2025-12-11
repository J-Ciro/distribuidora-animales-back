#!/usr/bin/env python3
import sys
sys.path.insert(0, './backend/api')

from app.database import SessionLocal
from app.routers.orders import _pedido_to_response
import app.models as models

db = SessionLocal()

# Get first pedido
pedido = db.query(models.Pedido).first()
if pedido:
    print(f"\n🔍 Testing pedido #{pedido.id}")
    response = _pedido_to_response(db, pedido)
    print(f"\n📦 Pedido Response:")
    print(f"  - ID: {response['id']}")
    print(f"  - Usuario ID: {response['usuario_id']}")
    print(f"  - Cliente: {response.get('clienteNombre', 'N/A')}")
    print(f"  - Total items: {len(response.get('items', []))}")
    
    print(f"\n📋 Items:")
    for item in response.get('items', []):
        print(f"  • Item ID: {item.get('id')}")
        print(f"    - Producto ID: {item.get('producto_id')}")
        print(f"    - Producto Nombre: {item.get('producto_nombre', 'NO ENCONTRADO ❌')}")
        print(f"    - Cantidad: {item.get('cantidad')}")
        print(f"    - Precio: ${item.get('precio_unitario')}")
        print()
else:
    print("❌ No hay pedidos en la base de datos")

db.close()
