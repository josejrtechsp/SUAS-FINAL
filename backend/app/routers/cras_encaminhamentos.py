from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional, List

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.core.db import get_session
from app.core.auth import get_current_user, pode_acesso_global
from app.models.usuario import Usuario
from app.models.cras_encaminhamento import CrasEncaminhamento, CrasEncaminhamentoEvento

router = APIRouter(prefix="/cras/encaminhamentos", tags=["cras_encaminhamentos"])

# Fluxo simples (MVP). Usuários comuns seguem ordem; admin/gestor global pode pular etapas.
_ALLOWED: Dict[str, List[str]] = {
    "enviado": ["recebido", "agendado", "atendido", "devolutiva", "concluido", "cancelado"],
    "recebido": ["agendado", "atendido", "devolutiva", "concluido", "cancelado"],
    "agendado": ["atendido", "devolutiva", "concluido", "cancelado"],
    "atendido": ["devolutiva", "concluido", "cancelado"],
    "devolutiva": ["concluido", "cancelado"],
    "concluido": [],
    "cancelado": [],
}


def _agora() -> datetime:
    # Mantém compatibilidade com o projeto (timezone-naive em UTC).
    return datetime.utcnow()


def _is_global(usuario: Usuario) -> bool:
    """Admin sempre é global.

    Observação: em alguns projetos `pode_acesso_global(usuario)` não considera `admin`.
    Aqui garantimos que admin/gestor_consorcio tenham permissão de forçar etapas.
    """
    perfil = str(getattr(usuario, "perfil", "") or "").lower()
    if perfil in ("admin", "gestor_consorcio"):
        return True
    try:
        return bool(pode_acesso_global(usuario))
    except Exception:
        return False


def _check_municipio(usuario: Usuario, enc: CrasEncaminhamento) -> None:
    if _is_global(usuario):
        return
    mid = getattr(usuario, "municipio_id", None)
    if mid is None:
        raise HTTPException(status_code=403, detail="Usuário sem município vinculado.")
    enc_mid = getattr(enc, "municipio_id", None)
    if enc_mid is not None and int(enc_mid) != int(mid):
        raise HTTPException(status_code=403, detail="Sem permissão para acessar este encaminhamento.")


def _dump(obj: Any) -> Dict[str, Any]:
    if obj is None:
        return {}
    if hasattr(obj, "model_dump"):
        return obj.model_dump()  # pydantic v2
    if hasattr(obj, "dict"):
        return obj.dict()  # pydantic v1
    return {}


def _eventos(session: Session, enc_id: int) -> List[Dict[str, Any]]:
    stmt = (
        select(CrasEncaminhamentoEvento)
        .where(CrasEncaminhamentoEvento.encaminhamento_id == int(enc_id))
        .order_by(CrasEncaminhamentoEvento.em.desc())
    )
    evs = session.exec(stmt).all()
    return [_dump(e) for e in evs]


def _add_evento(session: Session, enc_id: int, tipo: str, detalhe: Optional[str], por_nome: Optional[str]) -> None:
    ev = CrasEncaminhamentoEvento(
        encaminhamento_id=int(enc_id),
        tipo=tipo,
        detalhe=detalhe,
        por_nome=por_nome,
        em=_agora(),
    )
    session.add(ev)


@router.get("/")
def listar(
    status: Optional[str] = None,
    caso_id: Optional[int] = None,
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    stmt = select(CrasEncaminhamento).order_by(CrasEncaminhamento.id.desc())
    if status:
        stmt = stmt.where(CrasEncaminhamento.status == status)
    if caso_id is not None:
        stmt = stmt.where(CrasEncaminhamento.caso_id == int(caso_id))

    # filtro por município para usuários não-globais
    if not _is_global(usuario):
        mid = getattr(usuario, "municipio_id", None)
        if mid is not None:
            stmt = stmt.where(CrasEncaminhamento.municipio_id == int(mid))

    rows = session.exec(stmt).all()
    out: List[Dict[str, Any]] = []
    for enc in rows:
        d = _dump(enc)
        d["eventos"] = _eventos(session, int(enc.id))
        out.append(d)
    return out


@router.post("/{enc_id}/status")
def atualizar_status(
    enc_id: int,
    payload: Dict[str, Any],
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    enc = session.get(CrasEncaminhamento, int(enc_id))
    if not enc:
        raise HTTPException(status_code=404, detail="Encaminhamento não encontrado.")

    _check_municipio(usuario, enc)

    novo = str(payload.get("status") or "").strip().lower()
    detalhe = (str(payload.get("detalhe") or "").strip() or None)

    if not novo:
        raise HTTPException(status_code=400, detail="status é obrigatório.")

    atual = str(getattr(enc, "status", "") or "enviado").strip().lower() or "enviado"
    if novo == atual:
        d = _dump(enc)
        d["eventos"] = _eventos(session, int(enc.id))
        return d

    # Usuário comum: exige ordem (apenas o próximo passo)
    if not _is_global(usuario):
        allowed = _ALLOWED.get(atual, [])
        proximo = allowed[0] if allowed else None
        if novo not in allowed:
            raise HTTPException(
                status_code=400,
                detail=f"Fora de ordem. Atual={atual}. Próximo permitido={proximo}.",
            )

    # Admin/gestor global pode pular etapa. Registramos isso no detalhe para auditoria.
    if _is_global(usuario):
        allowed = _ALLOWED.get(atual, [])
        if novo not in allowed:
            detalhe = (detalhe or "")
            detalhe = ("FORÇADO (pulo de etapa): " + detalhe).strip()

    now = _agora()
    enc.status = novo
    if hasattr(enc, "atualizado_em"):
        setattr(enc, "atualizado_em", now)

    # timestamps por marco (quando existem no model)
    if novo == "enviado" and hasattr(enc, "enviado_em"):
        setattr(enc, "enviado_em", now)
    if novo == "recebido" and hasattr(enc, "recebido_em"):
        setattr(enc, "recebido_em", now)
    if novo == "agendado" and hasattr(enc, "agendado_em"):
        setattr(enc, "agendado_em", now)
    if novo == "atendido" and hasattr(enc, "atendido_em"):
        setattr(enc, "atendido_em", now)
    if novo == "devolutiva" and hasattr(enc, "devolutiva_em"):
        setattr(enc, "devolutiva_em", now)
    if novo == "concluido" and hasattr(enc, "concluido_em"):
        setattr(enc, "concluido_em", now)

    session.add(enc)
    _add_evento(session, int(enc.id), tipo=novo, detalhe=detalhe, por_nome=getattr(usuario, "nome", None))
    session.commit()
    session.refresh(enc)

    d = _dump(enc)
    d["eventos"] = _eventos(session, int(enc.id))
    return d
