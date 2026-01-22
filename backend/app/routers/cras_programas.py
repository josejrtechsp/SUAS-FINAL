from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select

from app.core.db import get_session
from app.core.auth import get_current_user, pode_acesso_global
from app.models.usuario import Usuario

from app.models.cras_programa import CrasPrograma, CrasProgramaParticipante
from app.models.pessoa_suas import PessoaSUAS

router = APIRouter(prefix="/cras", tags=["cras-programas"])


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


@router.get("/programas")
def listar_programas(
    unidade_id: Optional[int] = Query(default=None),
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
) -> List[CrasPrograma]:
    stmt = select(CrasPrograma).order_by(CrasPrograma.id.desc())

    if not pode_acesso_global(usuario):
        um = _mun_id(usuario)
        if um is None:
            raise HTTPException(status_code=403, detail="Usuário sem município.")
        stmt = stmt.where(CrasPrograma.municipio_id == um)

    if unidade_id:
        stmt = stmt.where(CrasPrograma.unidade_id == int(unidade_id))

    return session.exec(stmt).all()


@router.post("/programas")
def criar_programa(
    payload: Dict[str, Any],
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
) -> CrasPrograma:
    nome = (payload.get("nome") or "").strip()
    if not nome:
        raise HTTPException(status_code=400, detail="nome é obrigatório.")

    unidade_id = payload.get("unidade_id")
    if not unidade_id:
        raise HTTPException(status_code=400, detail="unidade_id é obrigatório.")

    municipio_id = payload.get("municipio_id")
    if municipio_id is None:
        municipio_id = _mun_id(usuario)
    if municipio_id is None:
        raise HTTPException(status_code=400, detail="municipio_id não informado e usuário sem município.")

    _check_municipio(usuario, int(municipio_id))

    p = CrasPrograma(
        municipio_id=int(municipio_id),
        unidade_id=int(unidade_id),
        nome=nome,
        publico_alvo=payload.get("publico_alvo"),
        descricao=payload.get("descricao"),
        capacidade_max=payload.get("capacidade_max"),
        responsavel_usuario_id=payload.get("responsavel_usuario_id"),
        data_inicio=payload.get("data_inicio"),
        data_fim=payload.get("data_fim"),
        status=payload.get("status") or "em_andamento",
        criado_em=_now(),
        atualizado_em=_now(),
    )
    session.add(p)
    session.commit()
    session.refresh(p)
    return p


@router.get("/programas/{programa_id}/participantes")
def listar_participantes(
    programa_id: int,
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
) -> List[Dict[str, Any]]:
    prog = session.get(CrasPrograma, programa_id)
    if not prog:
        raise HTTPException(status_code=404, detail="Programa não encontrado.")
    _check_municipio(usuario, int(prog.municipio_id))

    parts = session.exec(
        select(CrasProgramaParticipante).where(CrasProgramaParticipante.programa_id == programa_id)
        .order_by(CrasProgramaParticipante.id.desc())
    ).all()

    pessoa_ids = [p.pessoa_id for p in parts]
    pessoas = {}
    if pessoa_ids:
        for pe in session.exec(select(PessoaSUAS).where(PessoaSUAS.id.in_(pessoa_ids))).all():
            pessoas[pe.id] = pe

    out = []
    for pt in parts:
        pe = pessoas.get(pt.pessoa_id)
        out.append(
            {
                "id": pt.id,
                "programa_id": pt.programa_id,
                "pessoa_id": pt.pessoa_id,
                "caso_id": pt.caso_id,
                "status": pt.status,
                "data_inicio": pt.data_inicio,
                "data_fim": pt.data_fim,
                "pessoa": (pe.dict() if pe else None),
            }
        )
    return out


@router.post("/programas/{programa_id}/inscrever")
def inscrever(
    programa_id: int,
    payload: Dict[str, Any],
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
) -> Dict[str, Any]:
    prog = session.get(CrasPrograma, programa_id)
    if not prog:
        raise HTTPException(status_code=404, detail="Programa não encontrado.")
    _check_municipio(usuario, int(prog.municipio_id))

    pessoa_id = payload.get("pessoa_id")
    if not pessoa_id:
        raise HTTPException(status_code=400, detail="pessoa_id é obrigatório.")

    pessoa = session.get(PessoaSUAS, int(pessoa_id))
    if not pessoa:
        raise HTTPException(status_code=404, detail="Pessoa não encontrada.")
    _check_municipio(usuario, int(pessoa.municipio_id))

    # duplicidade (ativo)
    existing = session.exec(
        select(CrasProgramaParticipante).where(
            (CrasProgramaParticipante.programa_id == programa_id)
            & (CrasProgramaParticipante.pessoa_id == int(pessoa_id))
            & (CrasProgramaParticipante.status == "ativo")
        )
    ).first()
    if existing:
        return {"ok": True, "participante_id": existing.id, "detail": "Já inscrito (ativo)."}

    # capacidade
    if prog.capacidade_max is not None:
        ativos = session.exec(
            select(CrasProgramaParticipante).where(
                (CrasProgramaParticipante.programa_id == programa_id)
                & (CrasProgramaParticipante.status == "ativo")
            )
        ).all()
        if len(ativos) >= int(prog.capacidade_max):
            raise HTTPException(status_code=409, detail="Capacidade máxima atingida.")

    pt = CrasProgramaParticipante(
        programa_id=int(programa_id),
        pessoa_id=int(pessoa_id),
        caso_id=payload.get("caso_id"),
        status="ativo",
        data_inicio=payload.get("data_inicio"),
        criado_em=_now(),
    )
    session.add(pt)
    session.commit()
    session.refresh(pt)

    return {"ok": True, "participante_id": pt.id}
