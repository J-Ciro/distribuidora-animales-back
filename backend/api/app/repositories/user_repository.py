"""
Concrete implementations of repository interfaces
Implements data access logic using SQLAlchemy
"""
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import datetime
from app.models import Usuario, VerificationCode, RefreshToken


class SQLAlchemyUserRepository:
    """SQLAlchemy implementation of UserRepository"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def find_by_id(self, user_id: int) -> Optional[Usuario]:
        """Find user by ID"""
        return self.db.query(Usuario).filter(Usuario.id == user_id).first()
    
    def find_by_email(self, email: str) -> Optional[Usuario]:
        """Find user by email (case-insensitive)"""
        return self.db.query(Usuario).filter(
            func.lower(Usuario.email) == func.lower(email)
        ).first()
    
    def find_by_cedula(self, cedula: str) -> Optional[Usuario]:
        """Find user by cedula"""
        if not cedula:
            return None
        return self.db.query(Usuario).filter(Usuario.cedula == cedula).first()
    
    def email_exists(self, email: str, exclude_user_id: Optional[int] = None) -> bool:
        """Check if email exists (case-insensitive)"""
        query = self.db.query(Usuario).filter(
            func.lower(Usuario.email) == func.lower(email)
        )
        if exclude_user_id:
            query = query.filter(Usuario.id != exclude_user_id)
        return query.first() is not None
    
    def cedula_exists(self, cedula: str, exclude_user_id: Optional[int] = None) -> bool:
        """Check if cedula exists"""
        if not cedula:
            return False
        query = self.db.query(Usuario).filter(Usuario.cedula == cedula)
        if exclude_user_id:
            query = query.filter(Usuario.id != exclude_user_id)
        return query.first() is not None
    
    def create(self, user: Usuario) -> Usuario:
        """Create new user"""
        self.db.add(user)
        self.db.flush()
        return user
    
    def update(self, user: Usuario) -> Usuario:
        """Update existing user"""
        self.db.flush()
        return user
    
    def delete(self, user_id: int) -> bool:
        """Delete user"""
        user = self.find_by_id(user_id)
        if user:
            self.db.delete(user)
            self.db.flush()
            return True
        return False
    
    def increment_failed_login(self, user: Usuario) -> None:
        """Increment failed login attempts"""
        user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
        self.db.flush()
    
    def reset_failed_login(self, user: Usuario) -> None:
        """Reset failed login attempts"""
        user.failed_login_attempts = 0
        user.locked_until = None
        self.db.flush()
    
    def lock_account(self, user: Usuario, until_datetime: datetime) -> None:
        """Lock user account until specified datetime"""
        user.locked_until = until_datetime
        self.db.flush()


class SQLAlchemyVerificationCodeRepository:
    """SQLAlchemy implementation of VerificationCodeRepository"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, code: VerificationCode) -> VerificationCode:
        """Create verification code"""
        self.db.add(code)
        self.db.flush()
        return code
    
    def find_active_by_user(self, user_id: int) -> Optional[VerificationCode]:
        """Find active (non-used, non-expired) code for user"""
        now = datetime.utcnow()
        return self.db.query(VerificationCode).filter(
            and_(
                VerificationCode.usuario_id == user_id,
                VerificationCode.is_used == False,
                VerificationCode.expires_at > now
            )
        ).order_by(VerificationCode.created_at.desc()).first()
    
    def invalidate_user_codes(self, user_id: int) -> None:
        """Mark all user's codes as used"""
        self.db.query(VerificationCode).filter(
            and_(
                VerificationCode.usuario_id == user_id,
                VerificationCode.is_used == False
            )
        ).update({"is_used": True})
        self.db.flush()
    
    def mark_as_used(self, code: VerificationCode) -> None:
        """Mark code as used"""
        code.is_used = True
        self.db.flush()


class SQLAlchemyRefreshTokenRepository:
    """SQLAlchemy implementation of RefreshTokenRepository"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, token: RefreshToken) -> RefreshToken:
        """Create refresh token"""
        self.db.add(token)
        self.db.flush()
        return token
    
    def find_by_hash(self, token_hash: str) -> Optional[RefreshToken]:
        """Find token by hash"""
        return self.db.query(RefreshToken).filter(
            RefreshToken.token_hash == token_hash
        ).first()
    
    def revoke(self, token: RefreshToken) -> None:
        """Revoke refresh token"""
        token.revoked = True
        self.db.flush()
    
    def revoke_user_tokens(self, user_id: int) -> None:
        """Revoke all user's tokens"""
        self.db.query(RefreshToken).filter(
            and_(
                RefreshToken.usuario_id == user_id,
                RefreshToken.revoked == False
            )
        ).update({"revoked": True})
        self.db.flush()


# Factory functions to create repository instances
def get_user_repository(db: Session) -> SQLAlchemyUserRepository:
    """Factory function to get user repository instance"""
    return SQLAlchemyUserRepository(db)


def get_verification_code_repository(db: Session) -> SQLAlchemyVerificationCodeRepository:
    """Factory function to get verification code repository instance"""
    return SQLAlchemyVerificationCodeRepository(db)


def get_refresh_token_repository(db: Session) -> SQLAlchemyRefreshTokenRepository:
    """Factory function to get refresh token repository instance"""
    return SQLAlchemyRefreshTokenRepository(db)
