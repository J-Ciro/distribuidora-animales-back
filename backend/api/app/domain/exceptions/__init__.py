"""
Domain exceptions package
"""
from app.domain.exceptions.auth_exceptions import (
    AuthenticationError,
    ValidationError,
    EmailAlreadyExistsError,
    CedulaAlreadyExistsError,
    UserNotFoundError,
    InvalidCredentialsError,
    AccountLockedError,
    AccountNotVerifiedError,
    AccountAlreadyVerifiedError,
    VerificationCodeExpiredError,
    InvalidVerificationCodeError,
    TooManyVerificationAttemptsError,
    TooManyResendAttemptsError,
    InvalidTokenError,
    TokenExpiredError,
    RefreshTokenNotFoundError,
    RefreshTokenRevokedError,
    PasswordResetTokenInvalidError,
)

__all__ = [
    "AuthenticationError",
    "ValidationError",
    "EmailAlreadyExistsError",
    "CedulaAlreadyExistsError",
    "UserNotFoundError",
    "InvalidCredentialsError",
    "AccountLockedError",
    "AccountNotVerifiedError",
    "AccountAlreadyVerifiedError",
    "VerificationCodeExpiredError",
    "InvalidVerificationCodeError",
    "TooManyVerificationAttemptsError",
    "TooManyResendAttemptsError",
    "InvalidTokenError",
    "TokenExpiredError",
    "RefreshTokenNotFoundError",
    "RefreshTokenRevokedError",
    "PasswordResetTokenInvalidError",
]
