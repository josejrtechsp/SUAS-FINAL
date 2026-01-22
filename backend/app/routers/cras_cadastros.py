from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select

from app.core.db import get_session
from app.core.auth import get_current_user, pode_acesso_global
from app.models.usuario import Usuario

from app.models.pessoa_suas import PessoaSUAS
from app.models.familia_suas import FamiliaSUAS, FamiliaMembro

router = APIRouter(prefix="/cras/cadastros", tags=["cras-cadastros"])


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


@router.get("/pessoas")
def listar_pessoas(
    q: Optional[str] = Query(default=None),
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
) -> List[PessoaSUAS]:
    stmt = select(PessoaSUAS).order_by(PessoaSUAS.id.desc())
    if not pode_acesso_global(usuario):
        um = _mun_id(usuario)
        if um is None:
            raise HTTPException(status_code=403, detail="Usuário sem município.")
        stmt = stmt.where(PessoaSUAS.municipio_id == um)

    pessoas = session.exec(stmt).all()

    qn = (q or "").strip().lower()
    if not qn:
        return pessoas

    out = []
    for p in pessoas:
        hay = " ".join([p.nome or "", p.nome_social or "", p.cpf or "", p.nis or "", p.bairro or "", p.territorio or ""]).lower()
        if qn in hay:
            out.append(p)
    return out


@router.post("/pessoas")
def criar_pessoa(
    payload: Dict[str, Any],
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
) -> PessoaSUAS:
    nome = (payload.get("nome") or "").strip()
    if not nome:
        raise HTTPException(status_code=400, detail="nome é obrigatório.")

    municipio_id = payload.get("municipio_id")
    if municipio_id is None:
        municipio_id = _mun_id(usuario)
    if municipio_id is None:
        raise HTTPException(status_code=400, detail="municipio_id não informado e usuário sem município.")

    _check_municipio(usuario, int(municipio_id))

    p = PessoaSUAS(
        municipio_id=int(municipio_id),
        nome=nome,
        nome_social=payload.get("nome_social"),
        cpf=payload.get("cpf"),
        nis=payload.get("nis"),
        data_nascimento=payload.get("data_nascimento"),
        sexo=payload.get("sexo"),
        telefone=payload.get("telefone"),
        email=payload.get("email"),
        endereco=payload.get("endereco"),
        bairro=payload.get("bairro"),
        territorio=payload.get("territorio"),
        observacoes=payload.get("observacoes"),
        criado_em=_now(),
        atualizado_em=_now(),
    )
    session.add(p)
    session.commit()
    session.refresh(p)
    return p


@router.patch("/pessoas/{pessoa_id}")
def atualizar_pessoa(
    pessoa_id: int,
    payload: Dict[str, Any],
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
) -> PessoaSUAS:
    p = session.get(PessoaSUAS, pessoa_id)
    if not p:
        raise HTTPException(status_code=404, detail="Pessoa não encontrada.")
    _check_municipio(usuario, int(p.municipio_id))

    campos = [
        "nome","nome_social","cpf","nis","data_nascimento","sexo","telefone","email",
        "endereco","bairro","territorio","observacoes"
    ]
    for c in campos:
        if c in payload:
            setattr(p, c, payload.get(c))

    p.atualizado_em = _now()
    session.add(p)
    session.commit()
    session.refresh(p)
    return p


@router.get("/familias")
def listar_familias(
    q: Optional[str] = Query(default=None),
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
) -> List[FamiliaSUAS]:
    stmt = select(FamiliaSUAS).order_by(FamiliaSUAS.id.desc())
    if not pode_acesso_global(usuario):
        um = _mun_id(usuario)
        if um is None:
            raise HTTPException(status_code=403, detail="Usuário sem município.")
        stmt = stmt.where(FamiliaSUAS.municipio_id == um)

    familias = session.exec(stmt).all()

    qn = (q or "").strip().lower()
    if not qn:
        return familias

    out = []
    for f in familias:
        hay = " ".join([f.nis_familia or "", f.bairro or "", f.territorio or "", f.endereco or ""]).lower()
        if qn in hay:
            out.append(f)
    return out


@router.post("/familias")
def criar_familia(
    payload: Dict[str, Any],
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
) -> FamiliaSUAS:
    municipio_id = payload.get("municipio_id")
    if municipio_id is None:
        municipio_id = _mun_id(usuario)
    if municipio_id is None:
        raise HTTPException(status_code=400, detail="municipio_id não informado e usuário sem município.")

    _check_municipio(usuario, int(municipio_id))

    f = FamiliaSUAS(
        municipio_id=int(municipio_id),
        nis_familia=payload.get("nis_familia"),
        endereco=payload.get("endereco"),
        bairro=payload.get("bairro"),
        territorio=payload.get("territorio"),
        referencia_pessoa_id=payload.get("referencia_pessoa_id"),
        observacoes=payload.get("observacoes"),
        criado_em=_now(),
        atualizado_em=_now(),
    )
    session.add(f)
    session.commit()
    session.refresh(f)
    return f


@router.get("/familias/{familia_id}/membros")
def listar_membros(
    familia_id: int,
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
) -> List[FamiliaMembro]:
    f = session.get(FamiliaSUAS, familia_id)
    if not f:
        raise HTTPException(status_code=404, detail="Família não encontrada.")
    _check_municipio(usuario, int(f.municipio_id))

    return session.exec(select(FamiliaMembro).where(FamiliaMembro.familia_id == familia_id)).all()


@router.post("/familias/{familia_id}/membros")
def adicionar_membro(
    familia_id: int,
    payload: Dict[str, Any],
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
) -> FamiliaMembro:
    f = session.get(FamiliaSUAS, familia_id)
    if not f:
        raise HTTPException(status_code=404, detail="Família não encontrada.")
    _check_municipio(usuario, int(f.municipio_id))

    pessoa_id = payload.get("pessoa_id")
    if not pessoa_id:
        raise HTTPException(status_code=400, detail="pessoa_id é obrigatório.")

    # evita duplicidade
    existing = session.exec(
        select(FamiliaMembro).where(
            (FamiliaMembro.familia_id == familia_id) & (FamiliaMembro.pessoa_id == int(pessoa_id))
        )
    ).first()
    if existing:
        return existing

    m = FamiliaMembro(
        familia_id=int(familia_id),
        pessoa_id=int(pessoa_id),
        parentesco=payload.get("parentesco"),
        responsavel_bool=bool(payload.get("responsavel_bool") or False),
        criado_em=_now(),
    )
    session.add(m)
    session.commit()
    session.refresh(m)
    return m
