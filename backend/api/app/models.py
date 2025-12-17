"""
SQLAlchemy models for database tables
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Index, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import uuid


class Usuario(Base):
    """
    Modelo para la tabla Usuarios
    Almacena información de los usuarios/clientes
    """
    __tablename__ = "usuarios"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nombre_completo = Column(String(200), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    cedula = Column(String(50), nullable=False)
    password_hash = Column(String(255), nullable=False)
    es_admin = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=False, nullable=False)
    fecha_registro = Column(DateTime, server_default=func.getdate(), nullable=True)
    ultimo_login = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)

    # Additional fields
    telefono = Column(String(20), nullable=True)
    direccion_envio = Column(String(500), nullable=True)
    preferencia_mascotas = Column(String(20), nullable=True)
    
    # Campos para bloqueo de cuenta (si existen en la BD)
    failed_login_attempts = Column(Integer, default=0, nullable=False)
    locked_until = Column(DateTime, nullable=True)

    # Relationships (other tables may still reference usuarios.id)
    verification_codes = relationship("VerificationCode", back_populates="usuario", cascade="all, delete-orphan")
    refresh_tokens = relationship("RefreshToken", back_populates="usuario", cascade="all, delete-orphan")
    
    # Note: Email uniqueness is enforced at application level with case-insensitive comparison
    # SQL Server collation can be set to case-insensitive, or we use LOWER() in queries
    
    def __repr__(self):
        return f"<Usuario(id={self.id}, email={self.email}, is_active={self.is_active})>"


class VerificationCode(Base):
    """
    Modelo para la tabla VerificationCodes
    Almacena códigos de verificación de email (solo hash, nunca texto plano)
    """
    __tablename__ = "verification_codes"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False, index=True)
    code_hash = Column(String(255), nullable=False)  # Hash del código, nunca texto plano
    expires_at = Column(DateTime, nullable=False, index=True)
    attempts = Column(Integer, default=0, nullable=False)  # Intentos de verificación
    sent_count = Column(Integer, default=0, nullable=False)  # Cantidad de reenvíos
    created_at = Column(DateTime, server_default=func.getdate(), nullable=False)
    is_used = Column(Boolean, default=False, nullable=False)  # Si ya fue usado para verificar
    
    # Relationships
    usuario = relationship("Usuario", back_populates="verification_codes")
    
    def __repr__(self):
        return f"<VerificationCode(id={self.id}, usuario_id={self.usuario_id}, expires_at={self.expires_at})>"


class RefreshToken(Base):
    """
    Modelo para la tabla RefreshTokens
    Almacena los refresh tokens de los usuarios para la persistencia de sesión
    """
    __tablename__ = "refresh_tokens"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash = Column(String(255), nullable=False, unique=True, index=True)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, server_default=func.getdate(), nullable=False)
    revoked = Column(Boolean, default=False, nullable=False)
    ip = Column(String(50), nullable=True)
    user_agent = Column(String(255), nullable=True)
    
    # Relationships
    usuario = relationship("Usuario", back_populates="refresh_tokens")
    
    def __repr__(self):
        return f"<RefreshToken(id={self.id}, usuario_id={self.usuario_id}, revoked={self.revoked})>"


class CarruselImagen(Base):
    __tablename__ = 'CarruselImagenes'

    id = Column(Integer, primary_key=True, index=True)
    imagen_url = Column('ruta_imagen', String(1024), nullable=False)  # Maps to ruta_imagen in DB
    orden = Column(Integer, nullable=False, index=True)
    link_url = Column(String(2048), nullable=True)
    activo = Column(Boolean, nullable=False, default=True)
    fecha_creacion = Column('fecha_creacion', DateTime(timezone=True), server_default=func.now())
    fecha_actualizacion = Column('fecha_actualizacion', DateTime(timezone=True), onupdate=func.now(), server_default=func.now())


# Orders models
class Pedido(Base):
    __tablename__ = 'Pedidos'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    usuario_id = Column(Integer, nullable=False, index=True)
    estado = Column(String(50), nullable=False, default='Pendiente')
    estado_pago = Column(String(50), nullable=False, default='Pendiente de Pago', index=True)  # Payment status: Pendiente de Pago, Pagado, Fallido
    total = Column(Numeric(10, 2), nullable=False, default=0)
    subtotal = Column(Numeric(10, 2), nullable=False, default=0)
    costo_envio = Column(Numeric(10, 2), nullable=False, default=0)
    metodo_pago = Column(String(50), nullable=True)
    direccion_entrega = Column(String(500), nullable=False)
    municipio = Column(String(100), nullable=True)
    departamento = Column(String(100), nullable=True)
    pais = Column(String(100), nullable=True, default='Colombia')
    telefono_contacto = Column(String(20), nullable=False)
    nota_especial = Column(String(500), nullable=True)
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    detalles = relationship("PedidoItem", back_populates="pedido", lazy="joined")


class PedidoItem(Base):
    __tablename__ = 'PedidoItems'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    pedido_id = Column(Integer, ForeignKey('Pedidos.id', ondelete='CASCADE'), nullable=False, index=True)
    producto_id = Column(Integer, nullable=False)
    cantidad = Column(Integer, nullable=False)
    precio_unitario = Column(Numeric(10, 2), nullable=False)
    
    # Relationships
    pedido = relationship("Pedido", back_populates="detalles")


class PedidosHistorialEstado(Base):
    __tablename__ = 'PedidosHistorialEstado'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    pedido_id = Column(Integer, ForeignKey('Pedidos.id', ondelete='CASCADE'), nullable=False, index=True)
    estado_anterior = Column(String(50), nullable=True)
    estado_nuevo = Column(String(50), nullable=False)
    usuario_id = Column(Integer, nullable=True)
    nota = Column(String(300), nullable=True)
    fecha = Column(DateTime(timezone=True), server_default=func.now())


# Address model (DireccionesUsuario) - using existing table
class Direccion(Base):
    __tablename__ = 'DireccionesUsuario'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    usuario_id = Column(Integer, ForeignKey('usuarios.id', ondelete='CASCADE'), nullable=False, index=True)
    direccion_completa = Column(String(500), nullable=False)
    municipio = Column(String(100), nullable=True)
    departamento = Column(String(100), nullable=True)
    pais = Column(String(100), nullable=True, default='Colombia')
    es_principal = Column(Boolean, nullable=False, default=False)
    alias = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Optional relationship back to Usuario
    # Not strictly required for this HU, but keeps ORM consistent
    # usuario = relationship('Usuario', backref='direcciones')


# Ratings models
class Calificacion(Base):
    """
    Modelo para la tabla Calificaciones
    Almacena las calificaciones (ratings) de productos por usuarios
    """
    __tablename__ = 'Calificaciones'
    __table_args__ = {'implicit_returning': False}  # Disable OUTPUT clause for SQL Server triggers

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    producto_id = Column(Integer, nullable=False, index=True)
    usuario_id = Column(Integer, nullable=False, index=True)
    pedido_id = Column(Integer, nullable=True, index=True)
    calificacion = Column('puntuacion', Integer, nullable=False)  # Maps to 'puntuacion' in DB
    comentario = Column(String(500), nullable=True)
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now())
    fecha_actualizacion = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())
    aprobado = Column(Boolean, default=True, nullable=False)
    visible = Column(Boolean, default=True, nullable=False)


class ProductoStats(Base):
    """
    Modelo para la tabla ProductoStats
    Almacena estadísticas precalculadas de calificaciones por producto
    """
    __tablename__ = 'ProductoStats'

    producto_id = Column(Integer, primary_key=True)
    promedio_calificacion = Column(Numeric(3, 2), default=0, nullable=False)
    total_calificaciones = Column(Integer, default=0, nullable=False)
    total_5_estrellas = Column(Integer, default=0, nullable=False)
    total_4_estrellas = Column(Integer, default=0, nullable=False)
    total_3_estrellas = Column(Integer, default=0, nullable=False)
    total_2_estrellas = Column(Integer, default=0, nullable=False)
    total_1_estrella = Column(Integer, default=0, nullable=False)
    fecha_actualizacion = Column(DateTime(timezone=True), server_default=func.now())

# Payment Transaction Models (US-FUNC-01: Stripe Integration)
class TransaccionPago(Base):
    """
    Modelo para la tabla TransaccionPago
    Almacena transacciones de pago procesadas por Stripe
    """
    __tablename__ = 'TransaccionPago'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    pedido_id = Column(Integer, ForeignKey('Pedidos.id', ondelete='CASCADE'), nullable=False, index=True)
    payment_intent_id = Column(String(100), unique=True, nullable=False, index=True)
    usuario_id = Column(Integer, nullable=False, index=True)
    monto = Column(Numeric(10, 2), nullable=False)
    moneda = Column(String(3), nullable=False, default='USD')
    estado = Column(String(50), nullable=False, default='pending', index=True)  # pending, succeeded, failed, canceled
    metodo_pago = Column(String(50), nullable=True)  # card, link, etc
    detalles_error = Column(String(500), nullable=True)
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    fecha_actualizacion = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())
    fecha_confirmacion = Column(DateTime(timezone=True), nullable=True)


class EstadoPagoHistorial(Base):
    """
    Modelo para la tabla EstadoPagoHistorial
    Registra el historial de cambios de estado en transacciones de pago
    """
    __tablename__ = 'EstadoPagoHistorial'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    transaccion_id = Column(Integer, ForeignKey('TransaccionPago.id', ondelete='CASCADE'), nullable=False, index=True)
    estado_anterior = Column(String(50), nullable=True)
    estado_nuevo = Column(String(50), nullable=False)
    razon_cambio = Column(String(300), nullable=True)
    fecha = Column(DateTime(timezone=True), server_default=func.now(), index=True)


class EventoWebhookStripe(Base):
    """
    Modelo para la tabla EventoWebhookStripe
    Auditoría de eventos webhook recibidos de Stripe
    """
    __tablename__ = 'EventoWebhookStripe'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    event_id = Column(String(100), unique=True, nullable=False, index=True)  # Stripe webhook ID
    event_type = Column(String(100), nullable=False, index=True)  # payment_intent.succeeded, etc
    payload = Column(String(4000), nullable=True)  # JSON payload (truncated if needed)
    transaccion_id = Column(Integer, ForeignKey('TransaccionPago.id', ondelete='SET NULL'), nullable=True, index=True)
    procesado = Column(Boolean, default=False, nullable=False)
    resultado = Column(String(300), nullable=True)
    fecha_recibido = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    fecha_procesado = Column(DateTime(timezone=True), nullable=True)