from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select

from app.core.db import get_session
from app.core.auth import get_current_user, pode_acesso_global
from app.models.usuario import Usuario

from app.models.cadunico_precadastro import CadunicoPreCadastro

router = APIRouter(prefix="/cras/cadunico", tags=["cras-cadunico"])

def _now() -> datetime:
    return datetime.utcnow()

def _mun_id(usuario: Usuario) -> Optional[int]:
    mid = getattr(usuario, "municipio_id", None)
    return int(mid) if mid is not None else None

def _check_municipio(usuario: Usuario, municipio_id: int) -> None:
    if pode_acesso_global(usuario):
        return
    um = _mun_id(usuario)
    if um is None or int(municipio_id) != int(um):
        raise HTTPException(status_code=403, detail="Acesso negado (município).")

@router.get("/precadastros")
def listar_precadastros(
    status: Optional[str] = Query(default=None),
    unidade_id: Optional[int] = Query(default=None),
    pessoa_id: Optional[int] = Query(default=None),
    familia_id: Optional[int] = Query(default=None),
    caso_id: Optional[int] = Query(default=None),
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
) -> List[CadunicoPreCadastro]:
    stmt = select(CadunicoPreCadastro).order_by(CadunicoPreCadastro.id.desc())

    if not pode_acesso_global(usuario):
        um = _mun_id(usuario)
        if um is None:
            raise HTTPException(status_code=403, detail="Usuário sem município.")
        stmt = stmt.where(CadunicoPreCadastro.municipio_id == um)

    if status:
        stmt = stmt.where(CadunicoPreCadastro.status == status)
    if unidade_id:
        stmt = stmt.where(CadunicoPreCadastro.unidade_id == unidade_id)
    if pessoa_id:
        stmt = stmt.where(CadunicoPreCadastro.pessoa_id == pessoa_id)
    if familia_id:
        stmt = stmt.where(CadunicoPreCadastro.familia_id == familia_id)
    if caso_id:
        stmt = stmt.where(CadunicoPreCadastro.caso_id == caso_id)

    return session.exec(stmt).all()

@router.post("/precadastros")
def criar_precadastro(
    payload: Dict[str, Any],
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
) -> CadunicoPreCadastro:
    unidade_id = payload.get("unidade_id")
    if not unidade_id:
        raise HTTPException(status_code=400, detail="unidade_id é obrigatório.")

    municipio_id = payload.get("municipio_id") or _mun_id(usuario)
    if municipio_id is None:
        raise HTTPException(status_code=400, detail="municipio_id não informado e usuário sem município.")
    _check_municipio(usuario, int(municipio_id))

    pc = CadunicoPreCadastro(
        municipio_id=int(municipio_id),
        unidade_id=int(unidade_id),
        pessoa_id=payload.get("pessoa_id"),
        familia_id=payload.get("familia_id"),
        caso_id=payload.get("caso_id"),
        status="pendente",
        data_agendada=None,
        observacoes=payload.get("observacoes"),
        criado_em=_now(),
        atualizado_em=_now(),
    )
    session.add(pc)
    session.commit()
    session.refresh(pc)
    return pc

@router.post("/precadastros/{pc_id}/agendar")
def agendar(
    pc_id: int,
    payload: Dict[str, Any],
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
) -> CadunicoPreCadastro:
    pc = session.get(CadunicoPreCadastro, pc_id)
    if not pc:
        raise HTTPException(status_code=404, detail="Pré-cadastro não encontrado.")
    _check_municipio(usuario, pc.municipio_id)

    data_agendada = payload.get("data_agendada")
    if not data_agendada:
        raise HTTPException(status_code=400, detail="data_agendada é obrigatório (ISO).")

    pc.data_agendada = datetime.fromisoformat(data_agendada)
    pc.status = "agendado"
    pc.atualizado_em = _now()
    session.add(pc)
    session.commit()
    session.refresh(pc)
    return pc

@router.post("/precadastros/{pc_id}/finalizar")
def finalizar(
    pc_id: int,
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
) -> CadunicoPreCadastro:
    pc = session.get(CadunicoPreCadastro, pc_id)
    if not pc:
        raise HTTPException(status_code=404, detail="Pré-cadastro não encontrado.")
    _check_municipio(usuario, pc.municipio_id)

    pc.status = "finalizado"
    pc.atualizado_em = _now()
    session.add(pc)
    session.commit()
    session.refresh(pc)
    return pc

@router.post("/precadastros/{pc_id}/nao-compareceu")
def nao_compareceu(
    pc_id: int,
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
) -> CadunicoPreCadastro:
    pc = session.get(CadunicoPreCadastro, pc_id)
    if not pc:
        raise HTTPException(status_code=404, detail="Pré-cadastro não encontrado.")
    _check_municipio(usuario, pc.municipio_id)

    pc.status = "nao_compareceu"
    pc.atualizado_em = _now()
    session.add(pc)
    session.commit()
    session.refresh(pc)
    return pc
