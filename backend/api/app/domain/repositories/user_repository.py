"""
User Repository - Data Access Layer
Implements Repository Pattern for User-related database operations
"""
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.domain.models import Usuario


class UserRepository:
    """Repository for User entity following Repository Pattern"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def find_by_email(self, email: str, case_sensitive: bool = False) -> Optional[Usuario]:
        """Find user by email address"""
        if case_sensitive:
            return self.db.query(Usuario).filter(Usuario.email == email).first()
        return self.db.query(Usuario).filter(func.lower(Usuario.email) == func.lower(email)).first()
    
    def find_by_id(self, user_id: int) -> Optional[Usuario]:
        """Find user by ID"""
        return self.db.query(Usuario).filter(Usuario.id == user_id).first()
    
    def find_by_cedula(self, cedula: str) -> Optional[Usuario]:
        """Find user by cedula"""
        return self.db.query(Usuario).filter(Usuario.cedula == cedula).first()
    
    def email_exists(self, email: str, exclude_user_id: Optional[int] = None) -> bool:
        """Check if email already exists (case-insensitive)"""
        query = self.db.query(Usuario).filter(func.lower(Usuario.email) == func.lower(email))
        if exclude_user_id:
            query = query.filter(Usuario.id != exclude_user_id)
        return query.first() is not None
    
    def cedula_exists(self, cedula: str, exclude_user_id: Optional[int] = None) -> bool:
        """Check if cedula already exists"""
        if not cedula:
            return False
        query = self.db.query(Usuario).filter(Usuario.cedula == cedula)
        if exclude_user_id:
            query = query.filter(Usuario.id != exclude_user_id)
        return query.first() is not None
    
    def create(self, usuario: Usuario) -> Usuario:
        """Create new user and flush to get ID"""
        self.db.add(usuario)
        self.db.flush()
        return usuario
    
    def save(self) -> None:
        """Commit current transaction"""
        self.db.commit()
    
    def rollback(self) -> None:
        """Rollback current transaction"""
        self.db.rollback()
    
    def refresh(self, usuario: Usuario) -> Usuario:
        """Refresh user instance from database"""
        self.db.refresh(usuario)
        return usuario
