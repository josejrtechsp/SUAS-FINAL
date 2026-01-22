# app/routers/cras_pes.py
from __future__ import annotations

from datetime import datetime, date
import json
from typing import Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session, select
from sqlalchemy import or_

from app.core.db import get_session
from app.core.security import decodificar_token
from app.models.usuario import Usuario
from app.models.prontuario_pes import ProntuarioPES

router = APIRouter(prefix="/cras/pes", tags=["cras_pes"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def _agora() -> datetime:
    return datetime.utcnow()

def _is_admin_or_consorcio(usuario: Usuario) -> bool:
    p = (getattr(usuario, "perfil", "") or "").lower()
    return p in ("admin", "gestor_consorcio")

def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: Session = Depends(get_session),
) -> Usuario:
    try:
        payload = decodificar_token(token)
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Token inválido.")
    except Exception:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado.")
    usuario = session.get(Usuario, int(user_id))
    if not usuario or not getattr(usuario, "ativo", True):
        raise HTTPException(status_code=401, detail="Usuário inválido/inativo.")
    return usuario

def _parse_date(v) -> Optional[date]:
    if v in (None, "", 0): return None
    try: return date.fromisoformat(str(v))
    except Exception:
        raise HTTPException(status_code=400, detail=f"Data inválida: {v} (use YYYY-MM-DD)")

@router.get("")
def get_pes(
    pessoa_id: Optional[int] = Query(None),
    familia_id: Optional[int] = Query(None),
    caso_id: Optional[int] = Query(None),
    municipio_id: Optional[int] = Query(None),
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    if pessoa_id is None and familia_id is None and caso_id is None:
        raise HTTPException(status_code=400, detail="Informe pessoa_id, familia_id ou caso_id")

    mid = municipio_id or getattr(usuario, "municipio_id", None)
    if mid is None and not _is_admin_or_consorcio(usuario):
        raise HTTPException(status_code=400, detail="municipio_id é obrigatório para este usuário.")
    if not _is_admin_or_consorcio(usuario):
        mid = getattr(usuario, "municipio_id", None)

    q = select(ProntuarioPES).where(ProntuarioPES.municipio_id == int(mid))
    ors = []
    if pessoa_id is not None: ors.append(ProntuarioPES.pessoa_id == int(pessoa_id))
    if familia_id is not None: ors.append(ProntuarioPES.familia_id == int(familia_id))
    if caso_id is not None: ors.append(ProntuarioPES.caso_id == int(caso_id))
    q = q.where(or_(*ors)).order_by(ProntuarioPES.atualizado_em.desc())

    rec = session.exec(q).first()
    if not rec:
        return {"found": False}

    return {
        "found": True,
        "id": rec.id,
        "pessoa_id": rec.pessoa_id,
        "familia_id": rec.familia_id,
        "caso_id": rec.caso_id,
        "forma_acesso": rec.forma_acesso,
        "primeiro_atendimento_em": rec.primeiro_atendimento_em.isoformat() if rec.primeiro_atendimento_em else None,
        "inserido_paif_em": rec.inserido_paif_em.isoformat() if rec.inserido_paif_em else None,
        "desligado_paif_em": rec.desligado_paif_em.isoformat() if rec.desligado_paif_em else None,
        "observacoes_json": rec.observacoes_json,
    }

@router.post("")
def upsert_pes(
    payload: Dict[str, Any],
    municipio_id: Optional[int] = Query(None),
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    pessoa_id = payload.get("pessoa_id")
    familia_id = payload.get("familia_id")
    caso_id = payload.get("caso_id")

    try: pessoa_id = int(pessoa_id) if pessoa_id not in (None,"",0) else None
    except Exception: pessoa_id = None
    try: familia_id = int(familia_id) if familia_id not in (None,"",0) else None
    except Exception: familia_id = None
    try: caso_id = int(caso_id) if caso_id not in (None,"",0) else None
    except Exception: caso_id = None

    if pessoa_id is None and familia_id is None and caso_id is None:
        raise HTTPException(status_code=400, detail="Informe pessoa_id, familia_id ou caso_id")

    mid = municipio_id or getattr(usuario, "municipio_id", None)
    if mid is None and not _is_admin_or_consorcio(usuario):
        raise HTTPException(status_code=400, detail="municipio_id é obrigatório para este usuário.")
    if not _is_admin_or_consorcio(usuario):
        mid = getattr(usuario, "municipio_id", None)

    unidade_id = payload.get("unidade_id")
    try: unidade_id = int(unidade_id) if unidade_id not in (None,"",0) else None
    except Exception: unidade_id = None

    forma_acesso = (payload.get("forma_acesso") or "").strip().lower() or None
    primeiro = _parse_date(payload.get("primeiro_atendimento_em"))
    ins_paif = _parse_date(payload.get("inserido_paif_em"))
    des_paif = _parse_date(payload.get("desligado_paif_em"))

    obs = payload.get("observacoes")
    obs_json = None
    if obs is not None:
        try: obs_json = obs if isinstance(obs, str) else json.dumps(obs, ensure_ascii=False)
        except Exception: obs_json = str(obs)

    q = select(ProntuarioPES).where(ProntuarioPES.municipio_id == int(mid))
    if pessoa_id is not None: q = q.where(ProntuarioPES.pessoa_id == pessoa_id)
    if familia_id is not None: q = q.where(ProntuarioPES.familia_id == familia_id)
    if caso_id is not None: q = q.where(ProntuarioPES.caso_id == caso_id)

    rec = session.exec(q).first()
    now = _agora()
    if rec:
        rec.unidade_id = unidade_id
        rec.forma_acesso = forma_acesso
        rec.primeiro_atendimento_em = primeiro
        rec.inserido_paif_em = ins_paif
        rec.desligado_paif_em = des_paif
        rec.observacoes_json = obs_json
        rec.atualizado_em = now
        rec.atualizado_por_nome = usuario.nome
        session.add(rec); session.commit(); session.refresh(rec)
        return {"ok": True, "id": rec.id, "updated": True}

    rec = ProntuarioPES(
        municipio_id=int(mid) if mid is not None else 1,
        unidade_id=unidade_id,
        pessoa_id=pessoa_id,
        familia_id=familia_id,
        caso_id=caso_id,
        forma_acesso=forma_acesso,
        primeiro_atendimento_em=primeiro,
        inserido_paif_em=ins_paif,
        desligado_paif_em=des_paif,
        observacoes_json=obs_json,
        criado_em=now,
        atualizado_em=now,
        atualizado_por_nome=usuario.nome,
    )
    session.add(rec); session.commit(); session.refresh(rec)
    return {"ok": True, "id": rec.id, "updated": False}
