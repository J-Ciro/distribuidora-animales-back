"""
Authentication router: Register, Login, Logout, Token refresh
Presentation layer router moved from app/routers
"""
from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timedelta, timezone
from typing import Optional
import uuid
import logging

import hashlib
from app.presentation.schemas import (
    RegisterRequest, 
    LoginRequest, 
    TokenResponse, 
    VerificationCodeRequest,
    ResendCodeRequest,
    StandardResponse,
    LoginSuccessResponse,
    CartMergeInfo,
    UsuarioPublicResponse
)
from app.database import get_db
from app.models import Usuario, VerificationCode, RefreshToken
from app.utils import security_utils
from app.utils.rabbitmq import rabbitmq_producer
from app.utils.email_service import email_service
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(
    tags=["auth"]
)


def _check_email_exists(db: Session, email: str, exclude_user_id: Optional[int] = None) -> bool:
    """Check if email exists (case-insensitive)"""
    query = db.query(Usuario).filter(func.lower(Usuario.email) == func.lower(email))
    if exclude_user_id:
        query = query.filter(Usuario.id != exclude_user_id)
    return query.first() is not None


def _check_cedula_exists(db: Session, cedula: str, exclude_user_id: Optional[int] = None) -> bool:
    """Check if cedula exists in usuarios table"""
    if not cedula:
        return False
    query = db.query(Usuario).filter(Usuario.cedula == cedula)
    if exclude_user_id:
        query = query.filter(Usuario.id != exclude_user_id)
    return query.first() is not None


@router.post("/register", response_model=StandardResponse, status_code=status.HTTP_201_CREATED)
async def register(request: RegisterRequest, db: Session = Depends(get_db)):
    """
    Register new user with email verification
    
    Requirements (HU_REGISTER_USER):
    - Email must be unique and verified via 6-digit code
    - Password: 10+ chars, uppercase, digit, special char
    - Sends verification email with 6-digit code (10 min expiry)
    - Publishes to email.verification queue
    """
    try:
        # 1. Validate required fields - Pydantic handles validation, but check for empty
        if not request.email or not request.password or not request.nombre:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"status": "error", "message": "Por favor, completa todos los campos obligatorios."}
            )
        
        # 2. Check email uniqueness (case-insensitive)
        query = db.query(Usuario).filter(func.lower(Usuario.email) == func.lower(request.email))
        if query.first() is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"status": "error", "message": "El correo ya está registrado. ¿Deseas iniciar sesión o recuperar tu contraseña?"}
            )

        # 2b. Check cedula uniqueness (if provided)
        if request.cedula:
            q2 = db.query(Usuario).filter(Usuario.cedula == request.cedula)
            if q2.first() is not None:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail={"status": "error", "message": "La cédula ya está registrada."}
                )
        
        # 3. Password validation is handled by Pydantic field_validator
        # It will raise ValueError with the exact message if invalid
        
        # 4. Hash password using bcrypt
        password_hash = security_utils.hash_password(request.password)
        
        # 5. Create usuario entry (is_active=False) - Requiere verificación de email
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
        db.add(nuevo_usuario)
        try:
            db.flush()
        except IntegrityError as ie:
            db.rollback()
            msg = str(ie.orig) if hasattr(ie, 'orig') else str(ie)
            if 'duplicate' in msg.lower() or 'violation' in msg.lower() or 'unique' in msg.lower():
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail={"status": "error", "message": "El correo o la cédula ya están registrados."}
                )
            raise
        
        # 6. Generate verification code (6 digits)
        verification_code = security_utils.generate_verification_code()
        code_hash = security_utils.hash_verification_code(verification_code)
        
        # 7. Create VerificationCode with expires_at = now + 10 minutes
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.VERIFICATION_CODE_EXPIRE_MINUTES)
        
        db.query(VerificationCode).filter(
            and_(
                VerificationCode.usuario_id == nuevo_usuario.id,
                VerificationCode.is_used == False
            )
        ).update({"is_used": True})
        
        verification_record = VerificationCode(
            usuario_id=nuevo_usuario.id,
            code_hash=code_hash,
            expires_at=expires_at,
            sent_count=1,
            attempts=0,
            is_used=False
        )
        db.add(verification_record)
        
        db.commit()
        db.refresh(nuevo_usuario)
        
        logger.info(f"📧 Intentando enviar código de verificación a {request.email}")
        logger.info(f"🔑 Código generado: {verification_code}")
        try:
            email_sent = email_service.send_verification_code(request.email, verification_code)
            if email_sent:
                logger.info(f"✅ Código enviado exitosamente a {request.email}")
            else:
                logger.warning(f"⚠️ No se pudo enviar email a {request.email} - revisar configuración SMTP")
        except Exception as e:
            logger.error(f"❌ Error al enviar email: {str(e)}")
        
        return {
            "status": "success",
            "message": "¡Registro exitoso! Revisa tu correo para verificar tu cuenta. El código expira en 10 minutos."
        }
        
    except HTTPException:
        db.rollback()
        raise
    except ValueError as e:
        db.rollback()
        error_msg = str(e)
        if "contraseña" in error_msg.lower() or "password" in error_msg.lower():
            error_msg = "La contraseña debe tener al menos 10 caracteres, incluir una mayúscula, un número y un carácter especial."
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"status": "error", "message": error_msg}
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Error during registration: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"status": "error", "message": "Error interno del servidor. Por favor, intenta más tarde."}
        )