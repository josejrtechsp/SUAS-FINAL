# app/routers/suas_encaminhamentos.py
from __future__ import annotations

from datetime import datetime
import json
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session, select
from sqlalchemy import or_

from app.core.db import get_session
from app.core.security import decodificar_token
from app.models.usuario import Usuario
from app.models.suas_encaminhamento import SuasEncaminhamento, SuasEncaminhamentoEvento

router = APIRouter(prefix="/suas/encaminhamentos", tags=["suas_encaminhamentos"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

STATUS_VALIDOS = {
    "enviado",
    "recebido",
    "em_atendimento",
    "retorno_enviado",
    "concluido",
    "cancelado",
}

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

def _norm_modulo(m: str) -> str:
    s = (m or "").strip().upper()
    if s in ("POP RUA", "POP_RUA", "POP-RUA", "POP"):
        return "POPRUA"
    if s in ("CRAS", "CREAS", "POPRUA"):
        return s
    return s or "CRAS"

def _norm_view(v: str) -> str:
    s = (v or "inbox").strip().lower()
    return s if s in ("inbox", "outbox", "all") else "inbox"

def _append_event(session: Session, enc_id: int, tipo: str, detalhe: Optional[str], usuario: Usuario):
    ev = SuasEncaminhamentoEvento(
        encaminhamento_id=enc_id,
        tipo=tipo,
        detalhe=detalhe,
        por_usuario_id=usuario.id,
        por_nome=usuario.nome,
        em=_agora(),
    )
    session.add(ev)

def _load_events(session: Session, enc_id: int, limit: int = 20) -> List[dict]:
    rows = session.exec(
        select(SuasEncaminhamentoEvento)
        .where(SuasEncaminhamentoEvento.encaminhamento_id == enc_id)
        .order_by(SuasEncaminhamentoEvento.em.desc())
        .limit(limit)
    ).all()
    return [
        {
            "id": r.id,
            "tipo": r.tipo,
            "detalhe": r.detalhe,
            "por_id": r.por_usuario_id,
            "por_nome": r.por_nome,
            "em": r.em.isoformat() if r.em else None,
        }
        for r in rows
    ]

def _to_dict(session: Session, enc: SuasEncaminhamento, with_events: bool = True) -> dict:
    d = enc.model_dump()
    for k in ("status_em", "retorno_em", "cobranca_ultimo_em", "criado_em", "atualizado_em"):
        v = d.get(k)
        if isinstance(v, datetime):
            d[k] = v.isoformat()
    if with_events:
        d["timeline"] = _load_events(session, enc.id, limit=50) if enc.id else []
    return d

@router.get("/")
def listar(
    modulo: str = Query(..., description="CRAS|CREAS|POPRUA"),
    view: str = Query("inbox", description="inbox|outbox|all"),
    municipio_id: Optional[int] = Query(None),
    pessoa_id: Optional[int] = Query(None),
    familia_id: Optional[int] = Query(None),
    caso_id: Optional[int] = Query(None, description="Filtra por origem_caso_id OU destino_caso_id"),
    status: Optional[str] = Query(None),
    include_events: bool = Query(True),
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    mod = _norm_modulo(modulo)
    vw = _norm_view(view)

    mid = municipio_id or getattr(usuario, "municipio_id", None)
    if mid is None and not _is_admin_or_consorcio(usuario):
        raise HTTPException(status_code=400, detail="municipio_id é obrigatório para este usuário.")
    if not _is_admin_or_consorcio(usuario):
        mid = getattr(usuario, "municipio_id", None)

    q = select(SuasEncaminhamento)
    if mid is not None:
        q = q.where(SuasEncaminhamento.municipio_id == int(mid))

    if vw == "inbox":
        q = q.where(SuasEncaminhamento.destino_modulo == mod)
    elif vw == "outbox":
        q = q.where(SuasEncaminhamento.origem_modulo == mod)
    else:
        q = q.where(or_(SuasEncaminhamento.origem_modulo == mod, SuasEncaminhamento.destino_modulo == mod))

    extra_ors = []
    if pessoa_id is not None:
        try: extra_ors.append(SuasEncaminhamento.pessoa_id == int(pessoa_id))
        except Exception: pass
    if familia_id is not None:
        try: extra_ors.append(SuasEncaminhamento.familia_id == int(familia_id))
        except Exception: pass
    if caso_id is not None:
        try:
            cid = int(caso_id)
            extra_ors.append(SuasEncaminhamento.origem_caso_id == cid)
            extra_ors.append(SuasEncaminhamento.destino_caso_id == cid)
        except Exception:
            pass
    if extra_ors:
        q = q.where(or_(*extra_ors))

    if status:
        st = str(status).strip().lower()
        if st in STATUS_VALIDOS:
            q = q.where(SuasEncaminhamento.status == st)

    q = q.order_by(SuasEncaminhamento.status_em.desc(), SuasEncaminhamento.atualizado_em.desc())
    rows = session.exec(q).all()
    return [_to_dict(session, r, with_events=include_events) for r in rows]

@router.post("/{enc_id}/status")
def atualizar_status(
    enc_id: int,
    payload: dict,
    municipio_id: Optional[int] = Query(None),
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    mid = municipio_id or getattr(usuario, "municipio_id", None)
    if not _is_admin_or_consorcio(usuario):
        mid = getattr(usuario, "municipio_id", None)

    enc = session.get(SuasEncaminhamento, enc_id)
    if not enc:
        raise HTTPException(status_code=404, detail="Encaminhamento não encontrado")

    if mid is not None and enc.municipio_id != int(mid) and not _is_admin_or_consorcio(usuario):
        raise HTTPException(status_code=403, detail="Acesso negado")

    st = (payload.get("status") or "").strip().lower()
    if st not in STATUS_VALIDOS:
        raise HTTPException(status_code=400, detail="Status inválido")

    detalhe = payload.get("detalhe")

    cobranca_txt = None
    if payload.get("cobranca"):
        cobranca_txt = payload.get("cobranca_texto") or payload.get("cobranca")
        try:
            enc.cobranca_total = int(enc.cobranca_total or 0) + 1
        except Exception:
            enc.cobranca_total = 1
        enc.cobranca_ultimo_em = _agora()
        enc.cobranca_ultimo_texto = str(cobranca_txt) if cobranca_txt is not None else None

    if st == "retorno_enviado":
        enc.retorno_texto = payload.get("retorno_texto") or payload.get("retorno") or enc.retorno_texto
        enc.retorno_detalhe = payload.get("retorno_detalhe") or enc.retorno_detalhe
        raw_modelo = payload.get("retorno_modelo_json") or payload.get("retorno_modelo")
        if raw_modelo is not None:
            try:
                enc.retorno_modelo_json = raw_modelo if isinstance(raw_modelo, str) else json.dumps(raw_modelo, ensure_ascii=False)
            except Exception:
                enc.retorno_modelo_json = str(raw_modelo)
        enc.retorno_em = _agora()

    if st in ("recebido", "em_atendimento"):
        if payload.get("destino_caso_id") is not None:
            try: enc.destino_caso_id = int(payload.get("destino_caso_id"))
            except Exception: pass

    enc.status = st
    enc.status_em = _agora()
    enc.atualizado_em = _agora()
    enc.atualizado_por_nome = usuario.nome

    session.add(enc)
    if cobranca_txt:
        _append_event(session, enc.id, "cobranca", str(cobranca_txt), usuario)
    _append_event(session, enc.id, st, detalhe, usuario)
    session.commit()
    session.refresh(enc)
    return _to_dict(session, enc, with_events=True)
