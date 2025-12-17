"""
Dependency injection providers
Centralizes creation of service and repository instances
"""
from fastapi import Depends
from sqlalchemy.orm import Session
from typing import Generator

from app.core.database import get_db
from app.infrastructure.repositories.user_repository import (
    SQLAlchemyUserRepository,
    SQLAlchemyVerificationCodeRepository,
    SQLAlchemyRefreshTokenRepository
)
from app.application.services.auth_service import AuthService
from app.infrastructure.external.rabbitmq import rabbitmq_producer
from app.domain.interfaces.message_broker import MessageBroker


# Repository providers
def get_user_repository(db: Session = Depends(get_db)) -> SQLAlchemyUserRepository:
    """Provide user repository instance"""
    return SQLAlchemyUserRepository(db)


def get_verification_code_repository(db: Session = Depends(get_db)) -> SQLAlchemyVerificationCodeRepository:
    """Provide verification code repository instance"""
    return SQLAlchemyVerificationCodeRepository(db)


def get_refresh_token_repository(db: Session = Depends(get_db)) -> SQLAlchemyRefreshTokenRepository:
    """Provide refresh token repository instance"""
    return SQLAlchemyRefreshTokenRepository(db)


# Message broker provider
def get_message_broker() -> MessageBroker:
    """Provide message broker instance"""
    return rabbitmq_producer


# Service providers
def get_auth_service(
    db: Session = Depends(get_db),
    user_repo: SQLAlchemyUserRepository = Depends(get_user_repository),
    verification_repo: SQLAlchemyVerificationCodeRepository = Depends(get_verification_code_repository),
    token_repo: SQLAlchemyRefreshTokenRepository = Depends(get_refresh_token_repository),
    message_broker: MessageBroker = Depends(get_message_broker)
) -> AuthService:
    """Provide auth service instance with all dependencies injected"""
    return AuthService(
        db=db,
        user_repo=user_repo,
        verification_repo=verification_repo,
        token_repo=token_repo,
        message_broker=message_broker
    )
