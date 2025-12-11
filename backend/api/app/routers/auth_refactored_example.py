"""
EXAMPLE: Refactored auth router using AuthService
This file demonstrates how to use the new service layer

TO MIGRATE:
1. Backup current app/routers/auth.py
2. Replace with this file
3. Test all endpoints
4. Keep this as auth_router_refactored.py until fully tested
"""
from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from sqlalchemy.orm import Session
from typing import Optional
import logging

from app.schemas import (
    RegisterRequest,
    LoginRequest,
    VerificationCodeRequest,
    ResendCodeRequest,
    StandardResponse,
    LoginSuccessResponse,
    UsuarioPublicResponse
)
from app.database import get_db
from app.services.auth_service import AuthService
from app.dependencies import get_auth_service
from app.constants import SuccessMessages

logger = logging.getLogger(__name__)

router = APIRouter(tags=["auth"])


@router.post("/register", response_model=StandardResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: RegisterRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Register new user with email verification
    
    NOW: Uses AuthService instead of inline business logic
    - Cleaner router code
    - Testable service layer
    - Reusable business logic
    """
    try:
        user, message = auth_service.register_user(request)
        return StandardResponse(status="success", message=message)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during registration: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"status": "error", "message": "Error interno del servidor."}
        )


@router.post("/verify-email", response_model=StandardResponse)
async def verify_email(
    request: VerificationCodeRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Verify user email with code
    
    NOW: Delegates to AuthService
    """
    try:
        user, message = auth_service.verify_email(request.email, request.code)
        return StandardResponse(status="success", message=message)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during verification: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"status": "error", "message": "Error interno del servidor."}
        )


@router.post("/resend-code", response_model=StandardResponse)
async def resend_code(
    request: ResendCodeRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Resend verification code
    
    NOW: Delegates to AuthService
    """
    try:
        message = auth_service.resend_verification_code(request.email)
        return StandardResponse(status="success", message=message)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during resend: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"status": "error", "message": "Error interno del servidor."}
        )


@router.post("/login", response_model=LoginSuccessResponse)
async def login(
    request: LoginRequest,
    response: Response,
    http_request: Request,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Login user and return tokens
    
    NOW: Uses AuthService for authentication logic
    Router only handles HTTP concerns (cookies, response)
    """
    try:
        # Get IP and user agent for audit
        ip = http_request.client.host if http_request.client else None
        user_agent = http_request.headers.get("user-agent")
        
        # Authenticate via service
        access_token, refresh_token, user = auth_service.login(
            email=request.email,
            password=request.password,
            session_id=request.session_id,
            ip=ip,
            user_agent=user_agent
        )
        
        # Set refresh token in HTTP-only cookie
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=True,  # Only over HTTPS in production
            samesite="strict",
            max_age=60 * 60 * 24 * 7  # 7 days
        )
        
        # TODO: Implement cart merging logic here
        # For now, return empty cart_merge
        cart_merge = {"merged": False, "items_adjusted": []}
        
        return LoginSuccessResponse(
            status="success",
            message=SuccessMessages.LOGIN_EXITOSO,
            access_token=access_token,
            cart_merge=cart_merge
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during login: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"status": "error", "message": "Error interno del servidor."}
        )


@router.post("/logout", response_model=StandardResponse)
async def logout(
    response: Response,
    request: Request,
    auth_service: AuthService = Depends(get_auth_service),
    current_user = Depends(get_current_user)  # Assumes you have this dependency
):
    """
    Logout user and revoke tokens
    
    NOW: Uses AuthService
    """
    try:
        # Get refresh token from cookie
        refresh_token = request.cookies.get("refresh_token")
        
        # Revoke via service
        message = auth_service.logout(current_user.id, refresh_token)
        
        # Clear cookie
        response.delete_cookie("refresh_token")
        
        return StandardResponse(status="success", message=message)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during logout: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"status": "error", "message": "Error interno del servidor."}
        )


# TODO: Add get_current_user dependency
# This should also be refactored to use the service layer
def get_current_user():
    """Placeholder - implement based on your auth middleware"""
    pass


"""
BENEFITS OF THIS REFACTORED VERSION:

1. SINGLE RESPONSIBILITY
   - Router: HTTP concerns only (requests, responses, cookies)
   - Service: Business logic (validation, DB operations, messaging)

2. TESTABILITY
   - Can unit test AuthService without HTTP layer
   - Can mock AuthService in router tests

3. REUSABILITY
   - Same AuthService can be used by:
     * REST API
     * GraphQL API
     * CLI tools
     * Background jobs

4. MAINTAINABILITY
   - Business logic changes don't affect router
   - Easier to understand and modify
   - Better separation of concerns

5. DEPENDENCY INVERSION
   - Router depends on AuthService interface
   - Can swap implementations (mock, different DB, etc.)

MIGRATION STEPS:

1. Test current functionality thoroughly
2. Rename current auth.py to auth_old.py
3. Rename this file to auth.py
4. Update imports in main.py if needed
5. Test all auth endpoints
6. Fix any issues
7. Delete auth_old.py when confident

"""
