from sqlalchemy import Column, Integer, String, Numeric, DateTime, func, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base

class Producto(Base):
    __tablename__ = 'Productos'
    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(255), nullable=False)
    descripcion = Column(String(1000), nullable=True)
    precio = Column(Numeric(10,2), nullable=False, default=0)
    stock = Column(Integer, nullable=False, default=0)

class InventarioHistorial(Base):
    __tablename__ = 'InventarioHistorial'
    id = Column(Integer, primary_key=True, autoincrement=True)
    producto_id = Column(Integer, ForeignKey('Productos.id'), nullable=False)
    cantidad = Column(Integer, nullable=False)
    accion = Column(String(50), nullable=False)
    request_id = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    producto = relationship('Producto')
