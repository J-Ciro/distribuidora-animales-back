from pydantic import BaseModel, Field
from typing import Optional
import uuid

class ProductoOut(BaseModel):
    id: int
    nombre: str
    descripcion: Optional[str]
    precio: float
    stock: int

class ReabastecerIn(BaseModel):
    cantidad: int = Field(..., description="Cantidad a reabastecer")

    class Config:
        schema_extra = {
            "example": {"cantidad": 10}
        }

class InventarioHistorialOut(BaseModel):
    id: int
    producto_id: int
    cantidad: int
    accion: str
    request_id: Optional[str]
    created_at: Optional[str]

class MessagePublished(BaseModel):
    requestId: str
    productoId: int
    cantidad: int
