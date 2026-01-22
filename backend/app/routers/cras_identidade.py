from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select
from sqlalchemy import or_

from app.core.db import get_session
from app.core.auth import get_current_user, pode_acesso_global
from app.models.usuario import Usuario

from app.models.pessoa import PessoaRua
from app.models.pessoa_suas import PessoaSUAS
from app.models.pessoa_identidade_link import PessoaIdentidadeLink
from app.models.cras_paif import PaifAcompanhamento
from app.models.cras_triagem import CrasTriagem
from app.models.cras_encaminhamento import CrasEncaminhamento


router = APIRouter(prefix="/cras/identidade", tags=["cras-identidade"])


def _mun_id(usuario: Usuario) -> Optional[int]:
    mid = getattr(usuario, "municipio_id", None)
    return int(mid) if mid is not None else None


def _check_municipio(usuario: Usuario, municipio_id: Optional[int]) -> None:
    if pode_acesso_global(usuario):
        return
    um = _mun_id(usuario)
    if um is None:
        raise HTTPException(status_code=403, detail="Usuário sem município.")
    if municipio_id is not None and int(municipio_id) != int(um):
        raise HTTPException(status_code=403, detail="Acesso negado (município).")


def _norm_doc(doc: Optional[str]) -> Optional[str]:
    if not doc:
        return None
    # mantém apenas dígitos (cpf/nis)
    s = "".join(ch for ch in str(doc) if ch.isdigit())
    return s or None


@router.get("/sugestoes")
def sugestoes(
    pessoarua_id: int = Query(..., ge=1),
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
) -> Dict[str, Any]:
    """Sugere possíveis matches de PessoaSUAS para uma PessoaRua (por CPF/NIS)."""

    pr = session.get(PessoaRua, pessoarua_id)
    if not pr:
        raise HTTPException(status_code=404, detail="PessoaRua não encontrada.")

    # município: em PessoaRua o campo é municipio_origem_id
    _check_municipio(usuario, getattr(pr, "municipio_origem_id", None))

    cpf = _norm_doc(getattr(pr, "cpf", None))
    nis = _norm_doc(getattr(pr, "nis", None))

    if not cpf and not nis:
        return {"pessoarua_id": pessoarua_id, "cpf": None, "nis": None, "sugestoes": []}

    stmt = select(PessoaSUAS)
    conds = []
    if cpf:
        conds.append(PessoaSUAS.cpf == cpf)
    if nis:
        conds.append(PessoaSUAS.nis == nis)

    stmt = stmt.where(or_(*conds)).order_by(PessoaSUAS.id.desc())

    # para usuários não globais, restringe ao município do usuário
    if not pode_acesso_global(usuario):
        um = _mun_id(usuario)
        if um is not None:
            stmt = stmt.where(PessoaSUAS.municipio_id == int(um))

    matches = session.exec(stmt).all()

    return {
        "pessoarua_id": pessoarua_id,
        "cpf": cpf,
        "nis": nis,
        "sugestoes": [m.dict() for m in matches[:25]],
    }


@router.post("/link")
def criar_link(
    payload: Dict[str, Any],
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
) -> Dict[str, Any]:
    """Cria vínculo manual pessoarua_id -> pessoa_suas_id e propaga colunas auxiliares."""

    pessoarua_id = int(payload.get("pessoarua_id") or 0)
    pessoa_suas_id = int(payload.get("pessoa_suas_id") or 0)
    if not pessoarua_id or not pessoa_suas_id:
        raise HTTPException(status_code=400, detail="pessoarua_id e pessoa_suas_id são obrigatórios.")

    pr = session.get(PessoaRua, pessoarua_id)
    if not pr:
        raise HTTPException(status_code=404, detail="PessoaRua não encontrada.")
    ps = session.get(PessoaSUAS, pessoa_suas_id)
    if not ps:
        raise HTTPException(status_code=404, detail="PessoaSUAS não encontrada.")

    # valida município
    _check_municipio(usuario, getattr(ps, "municipio_id", None) or getattr(pr, "municipio_origem_id", None))

    existente = session.exec(select(PessoaIdentidadeLink).where(PessoaIdentidadeLink.pessoarua_id == pessoarua_id)).first()
    if existente:
        existente.pessoa_suas_id = pessoa_suas_id
        session.add(existente)
        session.commit()
        session.refresh(existente)
        link = existente
    else:
        link = PessoaIdentidadeLink(
            pessoarua_id=pessoarua_id,
            pessoa_suas_id=pessoa_suas_id,
            criado_por_id=getattr(usuario, "id", None),
            criado_por_nome=getattr(usuario, "nome", None),
        )
        session.add(link)
        session.commit()
        session.refresh(link)

    _propagar_pessoa_suas_id(session=session, pessoarua_id=pessoarua_id, pessoa_suas_id=pessoa_suas_id)
    session.commit()

    return {"ok": True, "link": link.dict()}


@router.post("/auto")
def auto_link(
    payload: Dict[str, Any],
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
) -> Dict[str, Any]:
    """Tenta vincular automaticamente por CPF/NIS. Se não encontrar, cria PessoaSUAS mínima."""

    pessoarua_id = int(payload.get("pessoarua_id") or 0)
    if not pessoarua_id:
        raise HTTPException(status_code=400, detail="pessoarua_id é obrigatório.")

    pr = session.get(PessoaRua, pessoarua_id)
    if not pr:
        raise HTTPException(status_code=404, detail="PessoaRua não encontrada.")

    cpf = _norm_doc(getattr(pr, "cpf", None))
    nis = _norm_doc(getattr(pr, "nis", None))

    # decide município
    municipio_id = payload.get("municipio_id")
    if municipio_id is not None:
        municipio_id = int(municipio_id)
    else:
        municipio_id = _mun_id(usuario) or getattr(pr, "municipio_origem_id", None)
        municipio_id = int(municipio_id) if municipio_id is not None else None

    _check_municipio(usuario, municipio_id)

    ps: Optional[PessoaSUAS] = None
    if cpf or nis:
        stmt = select(PessoaSUAS)
        conds = []
        if cpf:
            conds.append(PessoaSUAS.cpf == cpf)
        if nis:
            conds.append(PessoaSUAS.nis == nis)
        stmt = stmt.where(or_(*conds)).order_by(PessoaSUAS.id.desc())
        if municipio_id is not None and not pode_acesso_global(usuario):
            stmt = stmt.where(PessoaSUAS.municipio_id == int(municipio_id))
        matches = session.exec(stmt).all()
        if len(matches) == 1:
            ps = matches[0]

    if ps is None:
        # cria PessoaSUAS mínima
        nome = getattr(pr, "nome_social", None) or getattr(pr, "nome_civil", None) or "Pessoa"
        ps = PessoaSUAS(
            municipio_id=municipio_id,
            nome=str(nome)[:200],
            cpf=cpf,
            nis=nis,
        )
        session.add(ps)
        session.commit()
        session.refresh(ps)

    # cria/atualiza link
    existente = session.exec(select(PessoaIdentidadeLink).where(PessoaIdentidadeLink.pessoarua_id == pessoarua_id)).first()
    if existente:
        existente.pessoa_suas_id = int(ps.id)
        session.add(existente)
        session.commit()
        session.refresh(existente)
        link = existente
    else:
        link = PessoaIdentidadeLink(
            pessoarua_id=pessoarua_id,
            pessoa_suas_id=int(ps.id),
            criado_por_id=getattr(usuario, "id", None),
            criado_por_nome=getattr(usuario, "nome", None),
        )
        session.add(link)
        session.commit()
        session.refresh(link)

    _propagar_pessoa_suas_id(session=session, pessoarua_id=pessoarua_id, pessoa_suas_id=int(ps.id))
    session.commit()

    return {"ok": True, "link": link.dict(), "pessoa_suas": ps.dict()}


def _propagar_pessoa_suas_id(*, session: Session, pessoarua_id: int, pessoa_suas_id: int) -> None:
    """Propaga o vínculo para tabelas do universo PopRua (coluna auxiliar pessoa_suas_id)."""
    # PAIF
    rows = session.exec(select(PaifAcompanhamento).where(PaifAcompanhamento.pessoa_id == pessoarua_id)).all()
    for r in rows:
        try:
            r.pessoa_suas_id = pessoa_suas_id
            session.add(r)
        except Exception:
            pass

    # Triagem
    rows = session.exec(select(CrasTriagem).where(CrasTriagem.pessoa_id == pessoarua_id)).all()
    for r in rows:
        try:
            r.pessoa_suas_id = pessoa_suas_id
            session.add(r)
        except Exception:
            pass

    # Encaminhamento externo
    rows = session.exec(select(CrasEncaminhamento).where(CrasEncaminhamento.pessoa_id == pessoarua_id)).all()
    for r in rows:
        try:
            r.pessoa_suas_id = pessoa_suas_id
            session.add(r)
        except Exception:
            pass
