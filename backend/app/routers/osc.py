from __future__ import annotations

from datetime import date, datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select

from app.core.auth import exigir_minimo_perfil, get_current_user, pode_acesso_global
from app.core.db import get_session
from app.models.usuario import Usuario
from app.models.osc import Osc, OscParceria, OscPrestacaoContas


router = APIRouter(
    prefix="/osc",
    tags=["Terceiro Setor · OSC"],
    dependencies=[Depends(exigir_minimo_perfil("coord_municipal"))],
)


def _resolver_municipio_id(usuario: Usuario, municipio_id: Optional[int]) -> int:
    """Força município do usuário (exceto admin/consórcio)."""
    if pode_acesso_global(usuario):
        if municipio_id is None:
            raise HTTPException(status_code=400, detail="municipio_id é obrigatório para este perfil.")
        return int(municipio_id)

    mid = getattr(usuario, "municipio_id", None)
    if mid is None:
        raise HTTPException(status_code=403, detail="Usuário sem município associado.")
    if municipio_id is not None and int(municipio_id) != int(mid):
        raise HTTPException(status_code=403, detail="Município não corresponde ao usuário logado.")
    return int(mid)


# =========================
# OSC
# =========================


@router.get("", response_model=List[Osc])
def listar_osc(
    municipio_id: Optional[int] = None,
    q: Optional[str] = Query(default=None, description="Busca por nome/CNPJ"),
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    mid = _resolver_municipio_id(usuario, municipio_id)
    stmt = select(Osc).where(Osc.municipio_id == mid)
    if q:
        qq = f"%{q.strip().lower()}%"
        stmt = stmt.where((Osc.nome.ilike(qq)) | (Osc.cnpj.ilike(qq)))  # type: ignore
    stmt = stmt.order_by(Osc.ativo.desc(), Osc.nome)
    return session.exec(stmt).all()


@router.post("", response_model=Osc)
def criar_osc(
    osc: Osc,
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    mid = _resolver_municipio_id(usuario, getattr(osc, "municipio_id", None))
    osc.municipio_id = mid
    osc.criado_em = datetime.utcnow()
    session.add(osc)
    session.commit()
    session.refresh(osc)
    return osc


@router.get("/{osc_id}", response_model=Osc)
def obter_osc(
    osc_id: int,
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    osc = session.get(Osc, osc_id)
    if not osc:
        raise HTTPException(status_code=404, detail="OSC não encontrada")
    _resolver_municipio_id(usuario, getattr(osc, "municipio_id", None))
    return osc


@router.patch("/{osc_id}", response_model=Osc)
def atualizar_osc(
    osc_id: int,
    payload: dict,
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    osc = session.get(Osc, osc_id)
    if not osc:
        raise HTTPException(status_code=404, detail="OSC não encontrada")
    _resolver_municipio_id(usuario, getattr(osc, "municipio_id", None))

    for k, v in payload.items():
        if k in {"id", "municipio_id", "criado_em"}:
            continue
        if hasattr(osc, k):
            setattr(osc, k, v)
    session.add(osc)
    session.commit()
    session.refresh(osc)
    return osc


# =========================
# Parcerias
# =========================


@router.get("/parcerias", response_model=List[OscParceria])
def listar_parcerias(
    municipio_id: Optional[int] = None,
    osc_id: Optional[int] = None,
    status: Optional[str] = None,
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    mid = _resolver_municipio_id(usuario, municipio_id)
    stmt = select(OscParceria).where(OscParceria.municipio_id == mid)
    if osc_id is not None:
        stmt = stmt.where(OscParceria.osc_id == int(osc_id))
    if status:
        stmt = stmt.where(OscParceria.status == status)
    stmt = stmt.order_by(OscParceria.status, OscParceria.data_fim, OscParceria.data_inicio)
    return session.exec(stmt).all()


@router.post("/parcerias", response_model=OscParceria)
def criar_parceria(
    p: OscParceria,
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    mid = _resolver_municipio_id(usuario, getattr(p, "municipio_id", None))
    p.municipio_id = mid

    # valida OSC pertence ao município
    osc = session.get(Osc, int(p.osc_id))
    if not osc or int(getattr(osc, "municipio_id", 0)) != int(mid):
        raise HTTPException(status_code=400, detail="OSC inválida para este município")

    p.atualizado_em = datetime.utcnow()
    p.criado_em = datetime.utcnow()
    session.add(p)
    session.commit()
    session.refresh(p)
    return p


@router.patch("/parcerias/{parceria_id}", response_model=OscParceria)
def atualizar_parceria(
    parceria_id: int,
    payload: dict,
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    p = session.get(OscParceria, parceria_id)
    if not p:
        raise HTTPException(status_code=404, detail="Parceria não encontrada")
    _resolver_municipio_id(usuario, getattr(p, "municipio_id", None))

    for k, v in payload.items():
        if k in {"id", "municipio_id", "criado_em"}:
            continue
        if hasattr(p, k):
            setattr(p, k, v)

    p.atualizado_em = datetime.utcnow()
    session.add(p)
    session.commit()
    session.refresh(p)
    return p


@router.post("/parcerias/{parceria_id}/encerrar", response_model=OscParceria)
def encerrar_parceria(
    parceria_id: int,
    data_fim: Optional[date] = None,
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    p = session.get(OscParceria, parceria_id)
    if not p:
        raise HTTPException(status_code=404, detail="Parceria não encontrada")
    _resolver_municipio_id(usuario, getattr(p, "municipio_id", None))

    p.status = "encerrada"
    p.data_fim = data_fim or date.today()
    p.atualizado_em = datetime.utcnow()
    session.add(p)
    session.commit()
    session.refresh(p)
    return p


# =========================
# Prestação de contas
# =========================


@router.get("/prestacoes", response_model=List[OscPrestacaoContas])
def listar_prestacoes(
    municipio_id: Optional[int] = None,
    parceria_id: Optional[int] = None,
    status: Optional[str] = None,
    somente_pendentes: bool = False,
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    mid = _resolver_municipio_id(usuario, municipio_id)
    stmt = select(OscPrestacaoContas).where(OscPrestacaoContas.municipio_id == mid)
    if parceria_id is not None:
        stmt = stmt.where(OscPrestacaoContas.parceria_id == int(parceria_id))
    if status:
        stmt = stmt.where(OscPrestacaoContas.status == status)
    if somente_pendentes:
        stmt = stmt.where(OscPrestacaoContas.status.notin_(["aprovado", "reprovado"]))
    stmt = stmt.order_by(OscPrestacaoContas.prazo_entrega, OscPrestacaoContas.status)
    return session.exec(stmt).all()


@router.post("/prestacoes", response_model=OscPrestacaoContas)
def criar_prestacao(
    pc: OscPrestacaoContas,
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    mid = _resolver_municipio_id(usuario, getattr(pc, "municipio_id", None))
    pc.municipio_id = mid

    # valida parceria pertence ao município
    p = session.get(OscParceria, int(pc.parceria_id))
    if not p or int(getattr(p, "municipio_id", 0)) != int(mid):
        raise HTTPException(status_code=400, detail="Parceria inválida para este município")

    pc.criado_em = datetime.utcnow()
    pc.atualizado_em = datetime.utcnow()
    session.add(pc)
    session.commit()
    session.refresh(pc)
    return pc


@router.patch("/prestacoes/{prestacao_id}", response_model=OscPrestacaoContas)
def atualizar_prestacao(
    prestacao_id: int,
    payload: dict,
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    pc = session.get(OscPrestacaoContas, prestacao_id)
    if not pc:
        raise HTTPException(status_code=404, detail="Prestação não encontrada")
    _resolver_municipio_id(usuario, getattr(pc, "municipio_id", None))

    for k, v in payload.items():
        if k in {"id", "municipio_id", "criado_em"}:
            continue
        if hasattr(pc, k):
            setattr(pc, k, v)

    pc.atualizado_em = datetime.utcnow()
    session.add(pc)
    session.commit()
    session.refresh(pc)
    return pc


@router.post("/prestacoes/{prestacao_id}/marcar_entregue", response_model=OscPrestacaoContas)
def marcar_entregue(
    prestacao_id: int,
    entregue_em: Optional[date] = None,
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    pc = session.get(OscPrestacaoContas, prestacao_id)
    if not pc:
        raise HTTPException(status_code=404, detail="Prestação não encontrada")
    _resolver_municipio_id(usuario, getattr(pc, "municipio_id", None))

    pc.status = "entregue"
    pc.entregue_em = entregue_em or date.today()
    pc.atualizado_em = datetime.utcnow()
    session.add(pc)
    session.commit()
    session.refresh(pc)
    return pc
