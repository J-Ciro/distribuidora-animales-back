"""
Tests unitarios para el repositorio de usuarios
"""
import pytest
from unittest.mock import Mock, MagicMock
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session

from app.infrastructure.repositories.user_repository import (
    SQLAlchemyUserRepository,
    SQLAlchemyVerificationCodeRepository,
    SQLAlchemyRefreshTokenRepository
)
from app.domain.models import Usuario, VerificationCode, RefreshToken


class TestSQLAlchemyUserRepository:
    """Tests para SQLAlchemyUserRepository"""
    
    @pytest.fixture
    def mock_db(self):
        """Mock de sesión de base de datos"""
        return Mock(spec=Session)
    
    @pytest.fixture
    def repository(self, mock_db):
        """Repositorio con DB mockeada"""
        return SQLAlchemyUserRepository(mock_db)
    
    @pytest.fixture
    def sample_user(self):
        """Usuario de ejemplo"""
        return Usuario(
            id=1,
            email="test@example.com",
            nombre_completo="Test User",
            cedula="12345678",
            password_hash="hashed_password",
            is_active=True,
            failed_login_attempts=0
        )
    
    def test_find_by_id_found(self, repository, mock_db, sample_user):
        """Debe encontrar usuario por ID"""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_user
        
        result = repository.find_by_id(1)
        
        assert result == sample_user
        mock_db.query.assert_called_once_with(Usuario)
    
    def test_find_by_id_not_found(self, repository, mock_db):
        """Debe retornar None si no encuentra usuario"""
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        result = repository.find_by_id(999)
        
        assert result is None
    
    def test_find_by_email_found(self, repository, mock_db, sample_user):
        """Debe encontrar usuario por email (case insensitive)"""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_user
        
        result = repository.find_by_email("TEST@EXAMPLE.COM")
        
        assert result == sample_user
    
    def test_email_exists_true(self, repository, mock_db, sample_user):
        """Debe retornar True si email existe"""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_user
        
        result = repository.email_exists("test@example.com")
        
        assert result is True
    
    def test_email_exists_false(self, repository, mock_db):
        """Debe retornar False si email no existe"""
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        result = repository.email_exists("nonexistent@example.com")
        
        assert result is False
    
    def test_email_exists_with_exclusion(self, repository, mock_db):
        """Debe excluir usuario específico al verificar email"""
        mock_db.query.return_value.filter.return_value.filter.return_value.first.return_value = None
        
        result = repository.email_exists("test@example.com", exclude_user_id=1)
        
        assert result is False
    
    def test_cedula_exists_true(self, repository, mock_db, sample_user):
        """Debe retornar True si cédula existe"""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_user
        
        result = repository.cedula_exists("12345678")
        
        assert result is True
    
    def test_cedula_exists_false_empty(self, repository, mock_db):
        """Debe retornar False si cédula está vacía"""
        result = repository.cedula_exists("")
        
        assert result is False
        mock_db.query.assert_not_called()
    
    def test_create_user(self, repository, mock_db, sample_user):
        """Debe crear usuario en la DB"""
        repository.create(sample_user)
        
        mock_db.add.assert_called_once_with(sample_user)
        mock_db.flush.assert_called_once()
    
    def test_update_user(self, repository, mock_db, sample_user):
        """Debe actualizar usuario"""
        sample_user.nombre = "Updated Name"
        
        result = repository.update(sample_user)
        
        assert result.nombre == "Updated Name"
        mock_db.flush.assert_called_once()
    
    def test_delete_user_success(self, repository, mock_db, sample_user):
        """Debe eliminar usuario existente"""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_user
        
        result = repository.delete(1)
        
        assert result is True
        mock_db.delete.assert_called_once_with(sample_user)
        mock_db.flush.assert_called_once()
    
    def test_delete_user_not_found(self, repository, mock_db):
        """Debe retornar False si usuario no existe"""
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        result = repository.delete(999)
        
        assert result is False
        mock_db.delete.assert_not_called()
    
    def test_increment_failed_login(self, repository, mock_db, sample_user):
        """Debe incrementar intentos fallidos de login"""
        sample_user.failed_login_attempts = 2
        
        repository.increment_failed_login(sample_user)
        
        assert sample_user.failed_login_attempts == 3
        mock_db.flush.assert_called_once()
    
    def test_increment_failed_login_from_none(self, repository, mock_db, sample_user):
        """Debe manejar None como 0"""
        sample_user.failed_login_attempts = None
        
        repository.increment_failed_login(sample_user)
        
        assert sample_user.failed_login_attempts == 1
    
    def test_reset_failed_login(self, repository, mock_db, sample_user):
        """Debe resetear intentos fallidos"""
        sample_user.failed_login_attempts = 5
        sample_user.locked_until = datetime.now(timezone.utc)
        
        repository.reset_failed_login(sample_user)
        
        assert sample_user.failed_login_attempts == 0
        assert sample_user.locked_until is None
        mock_db.flush.assert_called_once()
    
    def test_lock_account(self, repository, mock_db, sample_user):
        """Debe bloquear cuenta hasta fecha específica"""
        lock_until = datetime.now(timezone.utc) + timedelta(minutes=15)
        
        repository.lock_account(sample_user, lock_until)
        
        assert sample_user.locked_until == lock_until
        mock_db.flush.assert_called_once()


class TestSQLAlchemyVerificationCodeRepository:
    """Tests para SQLAlchemyVerificationCodeRepository"""
    
    @pytest.fixture
    def mock_db(self):
        return Mock(spec=Session)
    
    @pytest.fixture
    def repository(self, mock_db):
        return SQLAlchemyVerificationCodeRepository(mock_db)
    
    @pytest.fixture
    def sample_code(self):
        return VerificationCode(
            id=1,
            usuario_id=1,
            code_hash="hashed_code",
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=10),
            is_used=False,
            attempts=0
        )
    
    def test_create_verification_code(self, repository, mock_db, sample_code):
        """Debe crear código de verificación"""
        repository.create(sample_code)
        
        mock_db.add.assert_called_once_with(sample_code)
        mock_db.flush.assert_called_once()


class TestSQLAlchemyRefreshTokenRepository:
    """Tests para SQLAlchemyRefreshTokenRepository"""
    
    @pytest.fixture
    def mock_db(self):
        return Mock(spec=Session)
    
    @pytest.fixture
    def repository(self, mock_db):
        return SQLAlchemyRefreshTokenRepository(mock_db)
    
    @pytest.fixture
    def sample_token(self):
        return RefreshToken(
            id=1,
            usuario_id=1,
            token_hash="hashed_token",
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
            revoked=False
        )
    
    def test_create_refresh_token(self, repository, mock_db, sample_token):
        """Debe crear refresh token"""
        repository.create(sample_token)
        
        mock_db.add.assert_called_once_with(sample_token)
        mock_db.flush.assert_called_once()
