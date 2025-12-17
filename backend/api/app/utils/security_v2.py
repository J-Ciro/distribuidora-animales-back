"""
Security utilities - Segregated into specialized classes
Follows Interface Segregation Principle
"""
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status
import logging
import hashlib
import hmac
import random
import os
import base64

from app.config import settings

logger = logging.getLogger(__name__)

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class PasswordHasher:
    """Handles password hashing and verification"""
    
    @staticmethod
    def hash(password: str) -> str:
        """Hash password using bcrypt"""
        return pwd_context.hash(password)
    
    @staticmethod
    def verify(plain_password: str, hashed_password: str) -> bool:
        """Verify plain password against hashed password"""
        return pwd_context.verify(plain_password, hashed_password)


class JWTManager:
    """Handles JWT token creation and verification"""
    
    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """
        Create short-lived JWT access token
        
        Args:
            data: Payload data to encode in token
            expires_delta: Optional custom expiration time
            
        Returns:
            Encoded JWT token string
        """
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "token_type": "access"
        })
        
        try:
            encoded_jwt = jwt.encode(
                to_encode,
                settings.SECRET_KEY,
                algorithm=settings.ALGORITHM
            )
            return encoded_jwt
        except Exception as e:
            logger.error(f"Error creating access token: {str(e)}")
            raise
    
    @staticmethod
    def verify_token(token: str) -> dict:
        """
        Verify JWT token and extract payload
        
        Args:
            token: JWT token string
            
        Returns:
            Decoded payload dictionary
            
        Raises:
            HTTPException: If token is invalid or expired
        """
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            return payload
        except JWTError as e:
            logger.warning(f"Invalid JWT token: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )


class RefreshTokenManager:
    """Handles opaque refresh token creation"""
    
    @staticmethod
    def create() -> Tuple[str, str, datetime]:
        """
        Create long-lived opaque refresh token, its hash, and expiry
        
        Returns:
            Tuple of (token, token_hash, expiry_datetime)
        """
        expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        
        # The refresh token is an opaque, URL-safe random string
        random_bytes = os.urandom(32)
        token = base64.urlsafe_b64encode(random_bytes).decode('utf-8')
        
        # Store the hash of the token in the DB
        token_hash = hashlib.sha256(token.encode('utf-8')).hexdigest()
        
        return token, token_hash, expire


class VerificationCodeGenerator:
    """Handles email verification code generation and hashing"""
    
    @staticmethod
    def generate() -> str:
        """
        Generate a 6-digit verification code
        
        Returns:
            6-digit code as string
        """
        return f"{random.randint(100000, 999999)}"
    
    @staticmethod
    def hash(code: str) -> str:
        """
        Hash verification code using HMAC-SHA256
        
        Args:
            code: Plain verification code
            
        Returns:
            Hashed code
        """
        return hmac.new(
            settings.SECRET_KEY.encode('utf-8'),
            code.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    @staticmethod
    def verify(plain_code: str, hashed_code: str) -> bool:
        """
        Verify plain code against hashed code
        
        Args:
            plain_code: Plain verification code
            hashed_code: Hashed verification code
            
        Returns:
            True if codes match, False otherwise
        """
        expected_hash = VerificationCodeGenerator.hash(plain_code)
        return hmac.compare_digest(expected_hash, hashed_code)


# Backward compatibility - maintain old SecurityUtils class interface
class SecurityUtils:
    """
    Legacy wrapper for backward compatibility
    Delegates to specialized classes
    """
    
    @staticmethod
    def hash_password(password: str) -> str:
        return PasswordHasher.hash(password)
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        return PasswordHasher.verify(plain_password, hashed_password)
    
    @staticmethod
    def create_access_token(data: dict) -> str:
        return JWTManager.create_access_token(data)
    
    @staticmethod
    def create_refresh_token() -> Tuple[str, str, datetime]:
        return RefreshTokenManager.create()
    
    @staticmethod
    def verify_jwt_token(token: str) -> dict:
        return JWTManager.verify_token(token)
    
    @staticmethod
    def generate_verification_code() -> str:
        return VerificationCodeGenerator.generate()
    
    @staticmethod
    def hash_verification_code(code: str) -> str:
        return VerificationCodeGenerator.hash(code)
    
    @staticmethod
    def verify_verification_code(plain_code: str, hashed_code: str) -> bool:
        return VerificationCodeGenerator.verify(plain_code, hashed_code)
    
    @staticmethod
    def create_password_reset_token(data: dict) -> str:
        """Create password reset token with 30 min expiry"""
        expires_delta = timedelta(minutes=30)
        return JWTManager.create_access_token(data, expires_delta)
    
    @staticmethod
    def verify_password_reset_token(token: str) -> dict:
        """Verify and decode password reset token"""
        return JWTManager.verify_token(token)


# Create singleton instances for convenience
password_hasher = PasswordHasher()
jwt_manager = JWTManager()
refresh_token_manager = RefreshTokenManager()
verification_code_generator = VerificationCodeGenerator()

# For backward compatibility
security_utils = SecurityUtils()
