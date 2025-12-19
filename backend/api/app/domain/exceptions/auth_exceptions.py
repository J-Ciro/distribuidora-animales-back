"""
Custom domain exceptions for authentication
Following Domain-Driven Design principles
"""


class AuthenticationError(Exception):
    """Base exception for authentication errors"""
    def __init__(self, message: str, status_code: int = 401):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class ValidationError(AuthenticationError):
    """Raised when input validation fails"""
    def __init__(self, message: str):
        super().__init__(message, status_code=400)


class EmailAlreadyExistsError(AuthenticationError):
    """Raised when email is already registered"""
    def __init__(self):
        super().__init__(
            "El correo ya está registrado. ¿Deseas iniciar sesión o recuperar tu contraseña?",
            status_code=409
        )


class CedulaAlreadyExistsError(AuthenticationError):
    """Raised when cedula is already registered"""
    def __init__(self):
        super().__init__("La cédula ya está registrada.", status_code=409)


class UserNotFoundError(AuthenticationError):
    """Raised when user is not found"""
    def __init__(self, message: str = "Usuario no encontrado."):
        super().__init__(message, status_code=404)


class InvalidCredentialsError(AuthenticationError):
    """Raised when login credentials are invalid"""
    def __init__(self):
        super().__init__("Correo o contraseña incorrectos", status_code=401)


class AccountLockedError(AuthenticationError):
    """Raised when account is temporarily locked"""
    def __init__(self):
        super().__init__(
            "Cuenta bloqueada temporalmente por múltiples intentos fallidos. Intenta más tarde.",
            status_code=423
        )


class AccountNotVerifiedError(AuthenticationError):
    """Raised when account email is not verified"""
    def __init__(self):
        super().__init__(
            "Cuenta no verificada. Revisa tu correo para obtener el código de verificación.",
            status_code=403
        )


class AccountAlreadyVerifiedError(AuthenticationError):
    """Raised when trying to verify already verified account"""
    def __init__(self):
        super().__init__("El usuario ya está verificado.", status_code=400)


class VerificationCodeExpiredError(AuthenticationError):
    """Raised when verification code has expired"""
    def __init__(self):
        super().__init__("El código ha expirado. Solicita un reenvío.", status_code=410)


class InvalidVerificationCodeError(AuthenticationError):
    """Raised when verification code is invalid"""
    def __init__(self):
        super().__init__("Código inválido.", status_code=400)


class TooManyVerificationAttemptsError(AuthenticationError):
    """Raised when max verification attempts exceeded"""
    def __init__(self):
        super().__init__(
            "Has excedido el número máximo de intentos. Solicita un nuevo código.",
            status_code=429
        )


class TooManyResendAttemptsError(AuthenticationError):
    """Raised when max code resend attempts exceeded"""
    def __init__(self):
        super().__init__(
            "Has alcanzado el número máximo de reenvíos. Intenta más tarde.",
            status_code=429
        )


class InvalidTokenError(AuthenticationError):
    """Raised when JWT token is invalid"""
    def __init__(self, message: str = "Token inválido"):
        super().__init__(message, status_code=401)


class TokenExpiredError(AuthenticationError):
    """Raised when token has expired"""
    def __init__(self, message: str = "El token ha expirado"):
        super().__init__(message, status_code=401)


class RefreshTokenNotFoundError(AuthenticationError):
    """Raised when refresh token is not found"""
    def __init__(self):
        super().__init__("Refresh token not found", status_code=401)


class RefreshTokenRevokedError(AuthenticationError):
    """Raised when refresh token has been revoked"""
    def __init__(self):
        super().__init__("Refresh token has been revoked", status_code=401)


class PasswordResetTokenInvalidError(AuthenticationError):
    """Raised when password reset token is invalid or expired"""
    def __init__(self):
        super().__init__(
            "Enlace de recuperación caducado o inválido. Solicita uno nuevo.",
            status_code=400
        )
