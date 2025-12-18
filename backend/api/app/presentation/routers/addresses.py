"""
User addresses router: CRUD for user shipping addresses
Implements 1:N relation Usuario:Direcciones for checkout flow
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.presentation.routers.auth import get_current_user, UsuarioPublicResponse
from app.presentation.schemas import DireccionCreate, DireccionResponse
import app.domain.models as models

router = APIRouter(
    prefix="/api/usuarios/direcciones",
    tags=["user-addresses"],
)


@router.get("/", response_model=List[DireccionResponse])
async def list_my_addresses(
    current_user: UsuarioPublicResponse = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(models.Direccion)
        .filter(models.Direccion.usuario_id == current_user.id)
        .order_by(models.Direccion.es_principal.desc(), models.Direccion.created_at.desc())
        .all()
    )
    return rows


@router.post("/", response_model=DireccionResponse, status_code=status.HTTP_201_CREATED)
async def create_my_address(
    payload: DireccionCreate,
    current_user: UsuarioPublicResponse = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Ensure a single primary address at a time if es_principal=True
    if payload.es_principal:
        db.query(models.Direccion).filter(models.Direccion.usuario_id == current_user.id).update({"es_principal": False})

    row = models.Direccion(
        usuario_id=current_user.id,
        direccion_completa=payload.direccion_completa.strip(),
        municipio=payload.municipio,
        departamento=payload.departamento,
        pais=payload.pais or 'Colombia',
        es_principal=bool(payload.es_principal or False),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.delete("/{direccion_id}", status_code=status.HTTP_200_OK)
async def delete_my_address(
    direccion_id: int,
    current_user: UsuarioPublicResponse = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = (
        db.query(models.Direccion)
        .filter(models.Direccion.id == direccion_id, models.Direccion.usuario_id == current_user.id)
        .first()
    )
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={
            "status": "error",
            "message": "Dirección no encontrada."
        })
    db.delete(row)
    db.commit()
    return {"status": "success", "message": "Dirección eliminada"}
