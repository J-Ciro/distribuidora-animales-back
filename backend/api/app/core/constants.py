"""
Application constants - Consolidated
Centralizes all constants including queue names, validation rules, and messages
"""


class QueueNames:
    """RabbitMQ queue names used across the application"""
    
    # Email queues
    EMAIL_VERIFICATION = "email.verification"
    EMAIL_NOTIFICATIONS = "email.notifications"
    
    # Category queues
    CATEGORIAS_CREAR = "categorias.crear"
    CATEGORIAS_ACTUALIZAR = "categorias.actualizar"
    SUBCATEGORIAS_CREAR = "subcategorias.crear"
    SUBCATEGORIAS_ACTUALIZAR = "subcategorias.actualizar"
    
    # Product queues
    PRODUCTOS_CREAR = "productos.crear"
    PRODUCTOS_ACTUALIZAR = "productos.actualizar"
    
    # Inventory queues
    INVENTARIO_REABASTECER = "inventario.reabastecer"
    
    # Carousel queues
    CARRUSEL_IMAGEN_CREAR = "carrusel.imagen.crear"
    CARRUSEL_IMAGEN_ELIMINAR = "carrusel.imagen.eliminar"
    CARRUSEL_IMAGEN_REORDENAR = "carrusel.imagen.reordenar"
    
    # Order queues
    PEDIDOS_ACTUALIZAR_ESTADO = "pedidos.actualizar_estado"
    
    # Analytics/Audit queues (optional)
    CART_EVENTS = "cart.events"
    AUTH_EVENTS = "auth.events"


class ErrorMessages:
    """Standardized error messages"""
    
    # Validation errors
    CAMPOS_OBLIGATORIOS = "Por favor, completa todos los campos obligatorios."
    EMAIL_INVALIDO = "El correo electrónico no tiene un formato válido."
    PASSWORD_DEBIL = "La contraseña debe tener al menos 10 caracteres, incluir una mayúscula, un número y un carácter especial."
    
    # Auth errors
    EMAIL_YA_REGISTRADO = "El correo ya está registrado. ¿Deseas iniciar sesión o recuperar tu contraseña?"
    CEDULA_YA_REGISTRADA = "La cédula ya está registrada."
    CREDENCIALES_INVALIDAS = "Credenciales inválidas."
    CUENTA_BLOQUEADA = "Tu cuenta ha sido bloqueada temporalmente. Intenta de nuevo más tarde."
    
    # Resource errors
    RECURSO_NO_ENCONTRADO = "El recurso solicitado no existe."
    CATEGORIA_NO_ENCONTRADA = "La categoría no existe."
    PRODUCTO_NO_ENCONTRADO = "El producto no existe."
    
    # Business logic errors
    STOCK_INSUFICIENTE = "Stock insuficiente para completar la operación."
    IMAGEN_INVALIDA = "Formato o tamaño de imagen no válido."


class SuccessMessages:
    """Standardized success messages"""
    
    # Auth
    REGISTRO_EXITOSO = "Registro exitoso. Hemos enviado un código de verificación a tu correo electrónico."
    LOGIN_EXITOSO = "Inicio de sesión exitoso."
    LOGOUT_EXITOSO = "Sesión cerrada exitosamente."
    VERIFICACION_EXITOSA = "Email verificado exitosamente. Ya puedes iniciar sesión."
    
    # CRUD operations
    CREADO_EXITOSAMENTE = "Creado exitosamente."
    ACTUALIZADO_EXITOSAMENTE = "Actualizado exitosamente."
    ELIMINADO_EXITOSAMENTE = "Eliminado exitosamente."


# Product validation constants
MIN_PRODUCT_NAME_LENGTH = 2
MIN_PRODUCT_DESCRIPTION_LENGTH = 10
MIN_PRODUCT_PRICE = 0.01
MIN_PRODUCT_WEIGHT_GRAMS = 1

# Pagination constants
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100
MIN_PAGE_SIZE = 1

# File upload constants
MAX_FILE_SIZE_BYTES = 10485760  # 10 MB

