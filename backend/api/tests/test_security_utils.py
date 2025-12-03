"""
Pruebas unitarias para el módulo de seguridad
Tests para SecurityUtils: password hashing, JWT, verification codes
"""
import pytest
from datetime import datetime, timedelta, timezone
from app.utils.security import SecurityUtils
from jose import jwt
from app.config import settings


class TestPasswordHashing:
    """Pruebas para hash y verificación de contraseñas"""
    
    def test_password_hash_and_verify_success(self):
        """Debe hashear y verificar correctamente una contraseña válida"""
        password = "TestPassword123!"
        hashed = SecurityUtils.hash_password(password)
        
        assert hashed != password
        assert hashed.startswith("$2b$")  # bcrypt prefix
        assert SecurityUtils.verify_password(password, hashed) is True
    
    def test_password_verify_wrong_password(self):
        """Debe rechazar una contraseña incorrecta"""
        password = "TestPassword123!"
        wrong_password = "WrongPassword456!"
        hashed = SecurityUtils.hash_password(password)
        
        assert SecurityUtils.verify_password(wrong_password, hashed) is False
    
    def test_different_passwords_different_hashes(self):
        """Contraseñas diferentes deben generar hashes diferentes"""
        password1 = "Password1!"
        password2 = "Password2!"
        
        hash1 = SecurityUtils.hash_password(password1)
        hash2 = SecurityUtils.hash_password(password2)
        
        assert hash1 != hash2


class TestJWTTokens:
    """Pruebas para creación y verificación de tokens JWT"""
    
    def test_create_access_token(self):
        """Debe crear un token de acceso válido"""
        data = {"sub": "test@example.com", "user_id": 123}
        token = SecurityUtils.create_access_token(data)
        
        assert isinstance(token, str)
        assert len(token) > 0
        
        # Decodificar el token para verificar el contenido
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        assert payload["sub"] == "test@example.com"
        assert payload["user_id"] == 123
        assert "exp" in payload
        assert "iat" in payload
        assert payload["token_type"] == "access"
    
    def test_verify_jwt_token_valid(self):
        """Debe verificar correctamente un token válido"""
        data = {"sub": "test@example.com", "user_id": 456}
        token = SecurityUtils.create_access_token(data)
        
        payload = SecurityUtils.verify_jwt_token(token)
        
        assert payload["sub"] == "test@example.com"
        assert payload["user_id"] == 456
        assert payload["token_type"] == "access"
    
    def test_verify_jwt_token_invalid(self):
        """Debe rechazar un token inválido"""
        from fastapi import HTTPException
        
        with pytest.raises(HTTPException) as exc_info:
            SecurityUtils.verify_jwt_token("invalid.token.here")
        
        assert exc_info.value.status_code == 401
    
    def test_verify_jwt_token_expired(self):
        """Debe rechazar un token expirado"""
        from fastapi import HTTPException
        
        # Crear token que ya expiró
        data = {"sub": "test@example.com"}
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) - timedelta(minutes=1)  # Expirado hace 1 minuto
        to_encode.update({"exp": expire})
        
        expired_token = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        
        with pytest.raises(HTTPException) as exc_info:
            SecurityUtils.verify_jwt_token(expired_token)
        
        assert exc_info.value.status_code == 401


class TestRefreshTokens:
    """Pruebas para tokens de refresco"""
    
    def test_create_refresh_token(self):
        """Debe crear un token de refresco con hash y fecha de expiración"""
        token, token_hash, expire = SecurityUtils.create_refresh_token()
        
        assert isinstance(token, str)
        assert len(token) > 0
        assert isinstance(token_hash, str)
        assert len(token_hash) == 64  # SHA256 produces 64 hex characters
        assert isinstance(expire, datetime)
        assert expire > datetime.now(timezone.utc)
    
    def test_refresh_tokens_are_unique(self):
        """Tokens de refresco consecutivos deben ser únicos"""
        token1, hash1, _ = SecurityUtils.create_refresh_token()
        token2, hash2, _ = SecurityUtils.create_refresh_token()
        
        assert token1 != token2
        assert hash1 != hash2


class TestVerificationCodes:
    """Pruebas para códigos de verificación"""
    
    def test_generate_verification_code(self):
        """Debe generar un código de 6 dígitos"""
        code = SecurityUtils.generate_verification_code()
        
        assert isinstance(code, str)
        assert len(code) == 6
        assert code.isdigit()
        assert 100000 <= int(code) <= 999999
    
    def test_verification_codes_are_random(self):
        """Códigos consecutivos deben ser diferentes (con alta probabilidad)"""
        codes = [SecurityUtils.generate_verification_code() for _ in range(100)]
        unique_codes = set(codes)
        
        # Con 100 códigos y 900,000 posibilidades, es muy probable que sean únicos
        assert len(unique_codes) > 90  # Al menos 90% únicos
    
    def test_hash_verification_code(self):
        """Debe hashear un código de verificación"""
        code = "123456"
        code_hash = SecurityUtils.hash_verification_code(code)
        
        assert isinstance(code_hash, str)
        assert len(code_hash) == 64  # HMAC-SHA256
        assert code_hash != code
    
    def test_verify_verification_code_valid(self):
        """Debe verificar correctamente un código válido"""
        code = "123456"
        code_hash = SecurityUtils.hash_verification_code(code)
        
        assert SecurityUtils.verify_verification_code(code, code_hash) is True
    
    def test_verify_verification_code_invalid(self):
        """Debe rechazar un código inválido"""
        code = "123456"
        wrong_code = "654321"
        code_hash = SecurityUtils.hash_verification_code(code)
        
        assert SecurityUtils.verify_verification_code(wrong_code, code_hash) is False
    
    def test_same_code_same_hash(self):
        """El mismo código debe generar el mismo hash"""
        code = "999888"
        hash1 = SecurityUtils.hash_verification_code(code)
        hash2 = SecurityUtils.hash_verification_code(code)
        
        assert hash1 == hash2
