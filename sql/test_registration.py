#!/usr/bin/env python3
"""
Test registration by simulating the register endpoint
"""

import sys
import os
from pathlib import Path
import json

# Change to the API directory
api_dir = Path(__file__).parent.parent / "backend" / "api"
os.chdir(api_dir)
sys.path.insert(0, str(api_dir))

def test_registration():
    from sqlalchemy import text
    from sqlalchemy.orm import Session
    from app.database import SessionLocal
    from app.models import Usuario
    from app.utils import security_utils
    
    print("=" * 60)
    print("TESTING REGISTRATION FLOW")
    print("=" * 60)
    
    db = SessionLocal()
    
    try:
        # Test email
        test_email = "test_registro_002@example.com"
        test_password = "SecurePassword123!"
        test_nombre = "Usuario Test"
        test_cedula = "123456789"
        
        print(f"\nAttempting to register user:")
        print(f"  - Email: {test_email}")
        print(f"  - Nombre: {test_nombre}")
        print(f"  - Cedula: {test_cedula}")
        
        # Check if user exists
        existing = db.query(Usuario).filter(Usuario.email == test_email).first()
        if existing:
            print("\n  WARNING: User already exists, deleting...")
            db.delete(existing)
            db.commit()
        
        # Create new user
        password_hash = security_utils.hash_password(test_password)
        nuevo_usuario = Usuario(
            nombre_completo=test_nombre,
            email=test_email,
            cedula=test_cedula,
            password_hash=password_hash,
            es_admin=False,
            is_active=False,
            telefono=None,
            direccion_envio=None,
            preferencia_mascotas=None,
            failed_login_attempts=0,
            locked_until=None
        )
        
        db.add(nuevo_usuario)
        db.commit()
        
        print("\n✓ User created successfully in database!")
        print(f"  - ID: {nuevo_usuario.id}")
        print(f"  - Email: {nuevo_usuario.email}")
        print(f"  - Is Active: {nuevo_usuario.is_active}")
        
        # Verify we can query it back
        queried_user = db.query(Usuario).filter(Usuario.email == test_email).first()
        if queried_user:
            print("\n✓ Successfully queried user back from database!")
            print(f"  - ID: {queried_user.id}")
            print(f"  - Email: {queried_user.email}")
            print(f"  - Telefono: {queried_user.telefono}")
            print(f"  - Direccion Envio: {queried_user.direccion_envio}")
            print(f"  - Preferencia Mascotas: {queried_user.preferencia_mascotas}")
            print(f"  - Failed Login Attempts: {queried_user.failed_login_attempts}")
            print(f"  - Locked Until: {queried_user.locked_until}")
        
        print("\n" + "=" * 60)
        print("✓ REGISTRATION TEST PASSED!")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    success = test_registration()
    sys.exit(0 if success else 1)
