"""
Repository interfaces for data access abstraction
Follows Repository Pattern to decouple business logic from data access
"""
from typing import Optional, List, Protocol
from sqlalchemy.orm import Session
from app.models import Usuario, VerificationCode, RefreshToken


class UserRepository(Protocol):
    """Interface for user data access"""
    
    def find_by_id(self, user_id: int) -> Optional[Usuario]:
        """Find user by ID"""
        ...
    
    def find_by_email(self, email: str) -> Optional[Usuario]:
        """Find user by email (case-insensitive)"""
        ...
    
    def find_by_cedula(self, cedula: str) -> Optional[Usuario]:
        """Find user by cedula"""
        ...
    
    def email_exists(self, email: str, exclude_user_id: Optional[int] = None) -> bool:
        """Check if email exists"""
        ...
    
    def cedula_exists(self, cedula: str, exclude_user_id: Optional[int] = None) -> bool:
        """Check if cedula exists"""
        ...
    
    def create(self, user: Usuario) -> Usuario:
        """Create new user"""
        ...
    
    def update(self, user: Usuario) -> Usuario:
        """Update existing user"""
        ...
    
    def delete(self, user_id: int) -> bool:
        """Delete user"""
        ...
    
    def increment_failed_login(self, user: Usuario) -> None:
        """Increment failed login attempts"""
        ...
    
    def reset_failed_login(self, user: Usuario) -> None:
        """Reset failed login attempts"""
        ...
    
    def lock_account(self, user: Usuario, until_datetime) -> None:
        """Lock user account until specified datetime"""
        ...


class VerificationCodeRepository(Protocol):
    """Interface for verification code data access"""
    
    def create(self, code: VerificationCode) -> VerificationCode:
        """Create verification code"""
        ...
    
    def find_active_by_user(self, user_id: int) -> Optional[VerificationCode]:
        """Find active (non-used, non-expired) code for user"""
        ...
    
    def invalidate_user_codes(self, user_id: int) -> None:
        """Mark all user's codes as used"""
        ...
    
    def mark_as_used(self, code: VerificationCode) -> None:
        """Mark code as used"""
        ...


class RefreshTokenRepository(Protocol):
    """Interface for refresh token data access"""
    
    def create(self, token: RefreshToken) -> RefreshToken:
        """Create refresh token"""
        ...
    
    def find_by_hash(self, token_hash: str) -> Optional[RefreshToken]:
        """Find token by hash"""
        ...
    
    def revoke(self, token: RefreshToken) -> None:
        """Revoke refresh token"""
        ...
    
    def revoke_user_tokens(self, user_id: int) -> None:
        """Revoke all user's tokens"""
        ...
