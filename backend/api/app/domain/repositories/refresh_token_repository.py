"""
Refresh Token Repository - Data Access Layer
"""
from typing import Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.domain.models import RefreshToken


class RefreshTokenRepository:
    """Repository for RefreshToken entity"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def find_by_token_hash(self, token_hash: str) -> Optional[RefreshToken]:
        """Find refresh token by its hash"""
        return self.db.query(RefreshToken).filter(RefreshToken.token_hash == token_hash).first()
    
    def create(self, refresh_token: RefreshToken) -> RefreshToken:
        """Create new refresh token"""
        self.db.add(refresh_token)
        self.db.flush()
        return refresh_token
    
    def revoke_all_for_user(self, usuario_id: int) -> None:
        """Revoke all refresh tokens for a user (force logout everywhere)"""
        self.db.query(RefreshToken).filter(RefreshToken.usuario_id == usuario_id).update({"revoked": True})
    
    def save(self) -> None:
        """Commit current transaction"""
        self.db.commit()
    
    def rollback(self) -> None:
        """Rollback current transaction"""
        self.db.rollback()
