"""
Authentication Service - Business logic for user authentication
Follows Single Responsibility Principle and Service Layer Pattern
"""
from typing import Optional, Tuple
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status
import logging
import uuid

from app.domain.models import Usuario, VerificationCode, RefreshToken
from app.infrastructure.repositories.user_repository import (
    SQLAlchemyUserRepository,
    SQLAlchemyVerificationCodeRepository,
    SQLAlchemyRefreshTokenRepository
)
from app.infrastructure.security.security import (
    PasswordHasher,
    JWTManager,
    RefreshTokenManager,
    VerificationCodeGenerator
)
from app.domain.interfaces.message_broker import MessageBroker
from app.core.constants import QueueNames, ErrorMessages, SuccessMessages
from app.core.config import settings
from app.presentation.schemas import RegisterRequest

logger = logging.getLogger(__name__)


class AuthService:
    """
    Authentication service handling all auth-related business logic
    
    Responsibilities:
    - User registration
    - Email verification
    - Login/logout
    - Token management
    - Account locking
    """
    
    def __init__(
        self,
        db: Session,
        user_repo: SQLAlchemyUserRepository,
        verification_repo: SQLAlchemyVerificationCodeRepository,
        token_repo: SQLAlchemyRefreshTokenRepository,
        message_broker: MessageBroker
    ):
        self.db = db
        self.user_repo = user_repo
        self.verification_repo = verification_repo
        self.token_repo = token_repo
        self.message_broker = message_broker
        self.password_hasher = PasswordHasher()
        self.jwt_manager = JWTManager()
        self.refresh_token_manager = RefreshTokenManager()
        self.code_generator = VerificationCodeGenerator()
    
    def register_user(self, request: RegisterRequest) -> Tuple[Usuario, str]:
        """
        Register new user and send verification email
        
        Args:
            request: Registration request data
            
        Returns:
            Tuple of (created_user, success_message)
            
        Raises:
            HTTPException: If email/cedula already exists or validation fails
        """
        # Validate required fields
        if not request.email or not request.password or not request.nombre:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"status": "error", "message": ErrorMessages.CAMPOS_OBLIGATORIOS}
            )
        
        # Check email uniqueness
        if self.user_repo.email_exists(request.email):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"status": "error", "message": ErrorMessages.EMAIL_YA_REGISTRADO}
            )
        
        # Check cedula uniqueness
        if request.cedula and self.user_repo.cedula_exists(request.cedula):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"status": "error", "message": ErrorMessages.CEDULA_YA_REGISTRADA}
            )
        
        # Hash password
        password_hash = self.password_hasher.hash(request.password)
        
        # Create user (is_active=False until email verified)
        nuevo_usuario = Usuario(
            email=request.email,
            password_hash=password_hash,
            nombre_completo=request.nombre,
            cedula=request.cedula,
            telefono=request.telefono,
            direccion_envio=request.direccion_envio,
            preferencia_mascotas=request.preferencia_mascotas,
            is_active=False
        )
        
        try:
            created_user = self.user_repo.create(nuevo_usuario)
        except IntegrityError as ie:
            self.db.rollback()
            logger.error(f"Integrity error during user creation: {str(ie)}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"status": "error", "message": "El correo o la cédula ya están registrados."}
            )
        
        # Generate verification code
        verification_code = self.code_generator.generate()
        code_hash = self.code_generator.hash(verification_code)
        
        # Create verification code record
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.VERIFICATION_CODE_EXPIRE_MINUTES)
        
        # Invalidate old codes
        self.verification_repo.invalidate_user_codes(created_user.id)
        
        # Create new code
        verification_record = VerificationCode(
            usuario_id=created_user.id,
            code_hash=code_hash,
            expires_at=expires_at,
            sent_count=1,
            attempts=0,
            is_used=False
        )
        self.verification_repo.create(verification_record)
        
        # Commit transaction
        self.db.commit()
        
        # Publish email verification message
        self._send_verification_email(created_user.email, verification_code)
        
        return created_user, SuccessMessages.REGISTRO_EXITOSO
    
    def verify_email(self, email: str, code: str) -> Tuple[Usuario, str]:
        """
        Verify user email with code
        
        Args:
            email: User email
            code: 6-digit verification code
            
        Returns:
            Tuple of (verified_user, success_message)
            
        Raises:
            HTTPException: If code is invalid or expired
        """
        # Find user
        user = self.user_repo.find_by_email(email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"status": "error", "message": "Usuario no encontrado."}
            )
        
        if user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"status": "error", "message": "El email ya está verificado."}
            )
        
        # Find active verification code
        verification_record = self.verification_repo.find_active_by_user(user.id)
        if not verification_record:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"status": "error", "message": "Código expirado o inválido. Solicita un nuevo código."}
            )
        
        # Check attempts
        if verification_record.attempts >= settings.MAX_VERIFICATION_ATTEMPTS:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={"status": "error", "message": "Demasiados intentos. Solicita un nuevo código."}
            )
        
        # Verify code
        if not self.code_generator.verify(code, verification_record.code_hash):
            verification_record.attempts += 1
            self.db.commit()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"status": "error", "message": "Código incorrecto. Intenta de nuevo."}
            )
        
        # Activate user
        user.is_active = True
        self.verification_repo.mark_as_used(verification_record)
        self.db.commit()
        
        return user, SuccessMessages.VERIFICACION_EXITOSA
    
    def login(
        self,
        email: str,
        password: str,
        session_id: Optional[str] = None,
        ip: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Tuple[str, str, Usuario]:
        """
        Authenticate user and generate tokens
        
        Args:
            email: User email
            password: Plain password
            session_id: Optional session ID for cart merging
            ip: Optional IP address
            user_agent: Optional user agent
            
        Returns:
            Tuple of (access_token, refresh_token, user)
            
        Raises:
            HTTPException: If credentials are invalid or account is locked
        """
        # Find user
        user = self.user_repo.find_by_email(email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"status": "error", "message": ErrorMessages.CREDENCIALES_INVALIDAS}
            )
        
        # Check if account is locked
        if user.locked_until and user.locked_until > datetime.now(timezone.utc):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"status": "error", "message": ErrorMessages.CUENTA_BLOQUEADA}
            )
        
        # Verify password
        if not self.password_hasher.verify(password, user.password_hash):
            # Increment failed attempts
            self.user_repo.increment_failed_login(user)
            
            # Lock account if too many failures
            if user.failed_login_attempts >= settings.MAX_LOGIN_ATTEMPTS:
                lock_until = datetime.now(timezone.utc) + timedelta(minutes=settings.LOGIN_LOCKOUT_DURATION_MINUTES)
                self.user_repo.lock_account(user, lock_until)
                self.db.commit()
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={"status": "error", "message": ErrorMessages.CUENTA_BLOQUEADA}
                )
            
            self.db.commit()
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"status": "error", "message": ErrorMessages.CREDENCIALES_INVALIDAS}
            )
        
        # Check if email is verified
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"status": "error", "message": "Por favor, verifica tu email antes de iniciar sesión."}
            )
        
        # Reset failed login attempts
        self.user_repo.reset_failed_login(user)
        
        # Update last login
        user.ultimo_login = datetime.now(timezone.utc)
        
        # Generate tokens
        access_token = self.jwt_manager.create_access_token(
            data={"user_id": user.id, "email": user.email, "es_admin": user.es_admin}
        )
        
        refresh_token, token_hash, expires_at = self.refresh_token_manager.create()
        
        # Store refresh token
        refresh_token_record = RefreshToken(
            usuario_id=user.id,
            token_hash=token_hash,
            expires_at=expires_at,
            ip=ip,
            user_agent=user_agent,
            revoked=False
        )
        self.token_repo.create(refresh_token_record)
        
        self.db.commit()
        
        return access_token, refresh_token, user
    
    def logout(self, user_id: int, refresh_token: Optional[str] = None) -> str:
        """
        Logout user and revoke tokens
        
        Args:
            user_id: User ID
            refresh_token: Optional refresh token to revoke
            
        Returns:
            Success message
        """
        if refresh_token:
            import hashlib
            token_hash = hashlib.sha256(refresh_token.encode('utf-8')).hexdigest()
            token_record = self.token_repo.find_by_hash(token_hash)
            if token_record:
                self.token_repo.revoke(token_record)
        else:
            # Revoke all user tokens
            self.token_repo.revoke_user_tokens(user_id)
        
        self.db.commit()
        return SuccessMessages.LOGOUT_EXITOSO
    
    def resend_verification_code(self, email: str) -> str:
        """
        Resend verification code to user
        
        Args:
            email: User email
            
        Returns:
            Success message
            
        Raises:
            HTTPException: If user not found or too many resend attempts
        """
        user = self.user_repo.find_by_email(email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"status": "error", "message": "Usuario no encontrado."}
            )
        
        if user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"status": "error", "message": "El email ya está verificado."}
            )
        
        # Check rate limiting for resend
        active_code = self.verification_repo.find_active_by_user(user.id)
        if active_code and active_code.sent_count >= settings.MAX_RESEND_CODE_ATTEMPTS:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={"status": "error", "message": "Demasiados reenvíos. Espera un momento antes de volver a intentar."}
            )
        
        # Generate new code
        verification_code = self.code_generator.generate()
        code_hash = self.code_generator.hash(verification_code)
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.VERIFICATION_CODE_EXPIRE_MINUTES)
        
        # Invalidate old codes
        self.verification_repo.invalidate_user_codes(user.id)
        
        # Create new code
        sent_count = (active_code.sent_count + 1) if active_code else 1
        verification_record = VerificationCode(
            usuario_id=user.id,
            code_hash=code_hash,
            expires_at=expires_at,
            sent_count=sent_count,
            attempts=0,
            is_used=False
        )
        self.verification_repo.create(verification_record)
        self.db.commit()
        
        # Send email
        self._send_verification_email(user.email, verification_code)
        
        return "Código de verificación reenviado. Revisa tu correo electrónico."
    
    def _send_verification_email(self, email: str, code: str) -> None:
        """
        Send verification email via message queue
        
        Args:
            email: Recipient email
            code: Verification code
        """
        message = {
            "requestId": str(uuid.uuid4()),
            "to": email,
            "code": code,
            "action": "send_verification_code",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        try:
            self.message_broker.publish(QueueNames.EMAIL_VERIFICATION, message)
            logger.info(f"Verification email queued for {email}")
        except Exception as e:
            logger.error(f"Failed to queue verification email: {str(e)}")
            # Don't fail registration if email queue fails
