from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select

from app.core.db import get_session
from app.models.municipio import Municipio


# modelo de entrada (corpo da requisição)
class MunicipioCreate(BaseModel):
    nome: str
    uf: str
    codigo_ibge: Optional[str] = None
    ativo: bool = True


# router usado no main.py
router = APIRouter(prefix="/municipios", tags=["municipios"])


@router.post("/", response_model=Municipio)
def criar_municipio(
    dados: MunicipioCreate,
    session: Session = Depends(get_session),
):
    """
    Cria um novo município.
    """
    municipio = Municipio(
        nome=dados.nome,
        uf=dados.uf,
        codigo_ibge=dados.codigo_ibge,
        ativo=dados.ativo,
    )
    session.add(municipio)
    session.commit()
    session.refresh(municipio)
    return municipio


@router.get("/", response_model=List[Municipio])
def listar_municipios(session: Session = Depends(get_session)):
    """
    Lista todos os municípios.
    """
    stmt = select(Municipio).order_by(Municipio.nome)
    return list(session.exec(stmt))


@router.get("/{municipio_id}", response_model=Municipio)
def obter_municipio(
    municipio_id: int,
    session: Session = Depends(get_session),
):
    """
    Busca um município pelo ID.
    """
    municipio = session.get(Municipio, municipio_id)
    if not municipio:
        raise HTTPException(status_code=404, detail="Município não encontrado")
    return municipio