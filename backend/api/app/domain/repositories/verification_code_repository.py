"""
Verification Code Repository - Data Access Layer
"""
from typing import Optional, List
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.domain.models import VerificationCode


class VerificationCodeRepository:
    """Repository for VerificationCode entity"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def find_active_code(self, usuario_id: int) -> Optional[VerificationCode]:
        """Find active (unused, non-expired) verification code for user"""
        return self.db.query(VerificationCode).filter(
            and_(
                VerificationCode.usuario_id == usuario_id,
                VerificationCode.is_used == False,
                VerificationCode.expires_at > datetime.now(timezone.utc)
            )
        ).order_by(VerificationCode.created_at.desc()).first()
    
    def find_recent_codes(self, usuario_id: int, since: datetime) -> List[VerificationCode]:
        """Find all verification codes created since a given time"""
        return self.db.query(VerificationCode).filter(
            and_(
                VerificationCode.usuario_id == usuario_id,
                VerificationCode.created_at >= since
            )
        ).all()
    
    def invalidate_unused_codes(self, usuario_id: int) -> None:
        """Mark all unused codes for user as used"""
        self.db.query(VerificationCode).filter(
            and_(
                VerificationCode.usuario_id == usuario_id,
                VerificationCode.is_used == False
            )
        ).update({"is_used": True})
    
    def create(self, verification_code: VerificationCode) -> VerificationCode:
        """Create new verification code"""
        self.db.add(verification_code)
        self.db.flush()
        return verification_code
    
    def save(self) -> None:
        """Commit current transaction"""
        self.db.commit()
    
    def rollback(self) -> None:
        """Rollback current transaction"""
        self.db.rollback()
    
    def refresh(self, verification_code: VerificationCode) -> VerificationCode:
        """Refresh verification code from database"""
        self.db.refresh(verification_code)
        return verification_code
