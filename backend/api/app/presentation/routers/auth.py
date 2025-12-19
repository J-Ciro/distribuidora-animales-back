"""
Authentication router: Register, Login, Logout, Token refresh
Handles HU_REGISTER_USER and HU_LOGIN_USER

Refactored following SOLID principles:
- Thin controller layer - only handles HTTP concerns
- Delegates business logic to AuthService
- Uses custom exceptions for better error handling
- Follows Dependency Inversion Principle
"""
from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from sqlalchemy.orm import Session
from typing import Optional
import logging

from app.presentation.schemas import (
    RegisterRequest, 
    LoginRequest, 
    TokenResponse, 
    VerificationCodeRequest,
    ResendCodeRequest,
    StandardResponse,
    LoginSuccessResponse,
    CartMergeInfo,
    UsuarioPublicResponse,
    ForgotPasswordRequest,
    ResetPasswordRequest
)
from app.core.database import get_db
from app.domain.models import Usuario
from app.application.services.auth_service import AuthService
from app.infrastructure.repositories.user_repository import (
    SQLAlchemyUserRepository,
    SQLAlchemyVerificationCodeRepository,
    SQLAlchemyRefreshTokenRepository
)
from app.domain.interfaces.message_broker import MessageBroker
from app.infrastructure.external.rabbitmq import rabbitmq_producer
from app.infrastructure.security.security import security_utils
from app.domain.exceptions import AuthenticationError
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(tags=["auth"])


# Dependency Injection helpers
def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    """Factory function for AuthService - Dependency Injection"""
    user_repo = SQLAlchemyUserRepository(db)
    verification_repo = SQLAlchemyVerificationCodeRepository(db)
    token_repo = SQLAlchemyRefreshTokenRepository(db)
    message_broker = rabbitmq_producer  # Using existing RabbitMQ producer as MessageBroker
    
    return AuthService(
        db=db,
        user_repo=user_repo,
        verification_repo=verification_repo,
        token_repo=token_repo,
        message_broker=message_broker
    )


def handle_auth_error(e: Exception) -> HTTPException:
    """
    Centralized error handler for authentication errors
    Converts domain exceptions to HTTP exceptions
    """
    if isinstance(e, AuthenticationError):
        return HTTPException(
            status_code=e.status_code,
            detail={"status": "error", "message": e.message}
        )
    elif isinstance(e, ValueError):
        # Handle password validation errors
        error_msg = str(e)
        if "contraseña" in error_msg.lower() or "password" in error_msg.lower():
            error_msg = "La contraseña debe tener al menos 10 caracteres, incluir una mayúscula, un número y un carácter especial."
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"status": "error", "message": error_msg}
        )
    else:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        return HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"status": "error", "message": "Error interno del servidor. Por favor, intenta más tarde."}
        )


# ==================== ENDPOINTS ====================

@router.post("/register", response_model=StandardResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: RegisterRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Register new user with email verification
    
    Requirements (HU_REGISTER_USER):
    - Email must be unique and verified via 6-digit code
    - Password: 10+ chars, uppercase, digit, special char
    - Sends verification email with 6-digit code (10 min expiry)
    """
    try:
        created_user, success_message = auth_service.register_user(request)
        return {"status": "success", "message": success_message}
    except Exception as e:
        raise handle_auth_error(e)


@router.post("/verify-email", response_model=StandardResponse, status_code=status.HTTP_200_OK)
async def verify_email(
    request: VerificationCodeRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Verify user email with 6-digit code
    
    Requirements:
    - Code must match stored verification code
    - Code expires after 10 minutes
    - Mark usuario as is_active=True after verification
    """
    try:
        verified_user, success_message = auth_service.verify_email(request.email, request.code)
        return {"status": "success", "message": success_message}
    except Exception as e:
        raise handle_auth_error(e)


@router.post("/resend-code", response_model=StandardResponse, status_code=status.HTTP_200_OK)
async def resend_code(
    request: ResendCodeRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Resend verification code
    
    Requirements:
    - Email exists and user is not already active
    - Respect rate-limit: max 3 reenvíos in 60 minutes
    """
    try:
        success_message = auth_service.resend_verification_code(request.email)
        return {"status": "success", "message": success_message}
    except Exception as e:
        raise handle_auth_error(e)


@router.post("/login", response_model=LoginSuccessResponse, status_code=status.HTTP_200_OK)
async def login(
    request: LoginRequest,
    response: Response,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    User login with credentials, handling account lockout and token generation.
    """
    try:
        # Call auth service for login logic
        access_token, refresh_token, usuario = auth_service.login(
            email=request.email,
            password=request.password,
            session_id=request.session_id
        )
        
        # Set refresh token in secure HttpOnly cookie
        from datetime import datetime, timedelta, timezone
        refresh_token_expires = datetime.now(timezone.utc) + timedelta(
            minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES
        )
        
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=not settings.DEBUG,
            samesite="lax",
            expires=refresh_token_expires,
            path="/api/auth"
        )
        
        # Handle cart merging (placeholder)
        cart_merge_info = CartMergeInfo(merged=False, items_adjusted=[])
        if request.session_id:
            logger.info(f"Cart merge requested for session_id: {request.session_id}")
            cart_merge_info.merged = True  # Simulate merge
        
        return LoginSuccessResponse(
            status="success",
            message="Inicio de sesión exitoso",
            access_token=access_token,
            cart_merge=cart_merge_info
        )
    except Exception as e:
        raise handle_auth_error(e)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: Request,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Refresh access token using refresh token from HttpOnly cookie.
    """
    refresh_token_value = request.cookies.get("refresh_token")
    if not refresh_token_value:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not found"
        )
    
    try:
        access_token = auth_service.refresh_access_token(refresh_token_value)
        
        return TokenResponse(
            access_token=access_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
    except Exception as e:
        raise handle_auth_error(e)


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(
    response: Response,
    request: Request,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    User logout by revoking the refresh token.
    """
    refresh_token_value = request.cookies.get("refresh_token")
    
    # Revoke refresh token via service (accepts optional refresh token)
    auth_service.logout(usuario_id=None, refresh_token=refresh_token_value)
    
    # Clear the cookie on the client side
    response.delete_cookie(key="refresh_token", path="/api/auth")
    
    return {"status": "success", "message": "Cierre de sesión exitoso"}


@router.get("/me", response_model=UsuarioPublicResponse)
async def get_me(current_user: UsuarioPublicResponse = Depends(get_current_user)):
    """Get current authenticated user profile"""
    return current_user


@router.post("/forgot-password", response_model=StandardResponse, status_code=status.HTTP_200_OK)
async def forgot_password(
    request: ForgotPasswordRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Password recovery endpoint (US-ERROR-02 CP-21 to CP-22)
    
    Security requirements:
    - Returns uniform message regardless of email existence (prevents user enumeration)
    - Generates JWT token valid for 30 minutes
    - Sends password recovery email with reset link
    - Non-blocking: Always returns 200 OK with success message
    """
    try:
        # Request password reset - service handles all logic
        auth_service.request_password_reset(request.email)
        
        # Always return success message for security (prevent email enumeration)
        return {
            "status": "success",
            "message": "Se ha enviado a tu correo el enlace de recuperación"
        }
    except Exception as e:
        # Log error but still return success for security
        logger.error(f"Error during password recovery: {str(e)}", exc_info=True)
        return {
            "status": "success",
            "message": "Se ha enviado a tu correo el enlace de recuperación"
        }


@router.post("/reset-password", response_model=StandardResponse, status_code=status.HTTP_200_OK)
async def reset_password(
    request: ResetPasswordRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Password reset endpoint (US-ERROR-02 CP-24 to CP-27)
    
    Security requirements:
    - Validates JWT token (30 min expiry)
    - Prevents token reuse (CP-27)
    - Updates password and invalidates all existing tokens
    """
    try:
        # Delegate to service
        usuario = auth_service.reset_password(request.token, request.new_password)
        
        return {
            "status": "success",
            "message": "Contraseña actualizada exitosamente. Ya puedes iniciar sesión con tu nueva contraseña."
        }
    except Exception as e:
        raise handle_auth_error(e)


# ==================== AUTH MIDDLEWARE & DEPENDENCIES ====================

def get_current_user(request: Request, db: Session = Depends(get_db)) -> UsuarioPublicResponse:
    """
    Extract authenticated user from JWT Bearer token
    Used as dependency for protected endpoints
    """
    auth_header = request.headers.get("authorization")
    if not auth_header or not auth_header.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="No autenticado")
    
    token = auth_header.split(" ", 1)[1]
    payload = security_utils.verify_jwt_token(token)
    user_id = payload.get("sub")
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Token inválido")
    
    from app.infrastructure.repositories.user_repository import SQLAlchemyUserRepository
    user_repo = SQLAlchemyUserRepository(db)
    usuario = user_repo.find_by_id(int(user_id))
    
    if not usuario:
        raise HTTPException(status_code=403, detail="Usuario no encontrado")
    
    rol = "admin" if usuario.es_admin else "cliente"
    return UsuarioPublicResponse(
        id=usuario.id,
        nombre_completo=usuario.nombre_completo,
        email=usuario.email,
        rol=rol
    )


def require_admin(current_user: UsuarioPublicResponse = Depends(get_current_user)) -> UsuarioPublicResponse:
    """
    Dependency to require admin privileges
    
    Usage:
        @router.get("/admin-only")
        def admin_endpoint(current_user: UsuarioPublicResponse = Depends(require_admin)):
            # Only admins can access
            pass
    """
    if current_user.rol != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"status": "error", "message": "Privilegios insuficientes."}
        )
    return current_user


# ==================== USER PROFILE ====================
