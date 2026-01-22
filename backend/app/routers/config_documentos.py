from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Dict, Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlmodel import Session, select

from app.core.auth import exigir_minimo_perfil, get_current_user, pode_acesso_global
from app.core.db import get_session
from app.models.usuario import Usuario
from app.models.documento_config import DocumentoConfig
from app.models.documento_sequencia import DocumentoSequencia


router = APIRouter(prefix="/config/documentos", tags=["config"])


def _now_utc_naive() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _resolver_municipio(usuario: Usuario, municipio_id: Optional[int]) -> int:
    if pode_acesso_global(usuario):
        if municipio_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="municipio_id é obrigatório para este usuário (acesso global).",
            )
        return int(municipio_id)

    mid = getattr(usuario, "municipio_id", None)
    if not mid:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuário sem município associado.",
        )
    return int(mid)




# Compat: rotas de sequências usam este helper
def _resolve_municipio_id(usuario: Usuario, municipio_id: Optional[int]) -> int:
    return _resolver_municipio(usuario, municipio_id)
def _cfg_to_dict(cfg: DocumentoConfig) -> Dict[str, Any]:
    # SQLModel: dict() existe; em versões novas pode existir model_dump().
    out = cfg.model_dump() if hasattr(cfg, "model_dump") else cfg.dict()  # type: ignore

    try:
        out["siglas"] = json.loads(cfg.siglas_json) if cfg.siglas_json else {}
    except Exception:
        out["siglas"] = {}

    try:
        out["prefixos"] = json.loads(cfg.prefixos_json) if cfg.prefixos_json else {}
    except Exception:
        out["prefixos"] = {}

    return out


class DocumentosConfigUpsert(BaseModel):
    municipio_id: Optional[int] = None

    numero_estilo_default: Optional[str] = None
    digitos_seq_default: Optional[int] = None

    emissor_padrao: Optional[str] = None
    sequenciar_por_emissor: Optional[bool] = None

    sigla_padrao: Optional[str] = None
    siglas: Optional[Dict[str, str]] = None
    prefixos: Optional[Dict[str, str]] = None


@router.get("", dependencies=[Depends(exigir_minimo_perfil("operador"))])
def get_documentos_config(
    municipio_id: Optional[int] = Query(default=None),
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    mid = _resolver_municipio(usuario, municipio_id)

    cfg = session.exec(
        select(DocumentoConfig).where(DocumentoConfig.municipio_id == mid)
    ).first()

    if not cfg:
        cfg = DocumentoConfig(municipio_id=mid)

    return _cfg_to_dict(cfg)


@router.post("", dependencies=[Depends(exigir_minimo_perfil("coord_municipal"))])
def upsert_documentos_config(
    payload: DocumentosConfigUpsert,
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    mid = _resolver_municipio(usuario, payload.municipio_id)

    cfg = session.exec(
        select(DocumentoConfig).where(DocumentoConfig.municipio_id == mid)
    ).first()

    now = _now_utc_naive()

    if not cfg:
        cfg = DocumentoConfig(municipio_id=mid, criado_em=now, atualizado_em=now)

    if payload.numero_estilo_default is not None:
        cfg.numero_estilo_default = (payload.numero_estilo_default or "").strip().lower() or "prefeitura"

    if payload.digitos_seq_default is not None:
        cfg.digitos_seq_default = int(payload.digitos_seq_default)

    if payload.emissor_padrao is not None:
        cfg.emissor_padrao = (payload.emissor_padrao or "").strip().lower() or "smas"

    if payload.sequenciar_por_emissor is not None:
        cfg.sequenciar_por_emissor = bool(payload.sequenciar_por_emissor)

    if payload.sigla_padrao is not None:
        s = (payload.sigla_padrao or "").strip()
        cfg.sigla_padrao = s or None

    if payload.siglas is not None:
        siglas = {
            str(k).strip().lower(): str(v).strip()
            for k, v in payload.siglas.items()
            if str(k).strip()
        }
        cfg.siglas_json = json.dumps(siglas, ensure_ascii=False)

    if payload.prefixos is not None:
        prefixos = {
            str(k).strip().lower(): str(v).strip().upper()
            for k, v in payload.prefixos.items()
            if str(k).strip()
        }
        cfg.prefixos_json = json.dumps(prefixos, ensure_ascii=False)

    cfg.atualizado_em = now
    session.add(cfg)
    session.commit()
    session.refresh(cfg)

    return _cfg_to_dict(cfg)


@router.get("/emissores", dependencies=[Depends(exigir_minimo_perfil("operador"))])
def listar_emissores_padrao():
    return {
        "emissores": [
            {"key": "smas", "label": "Secretaria de Assistência Social (SMAS)"},
            {"key": "cras", "label": "CRAS"},
            {"key": "creas", "label": "CREAS"},
            {"key": "poprua", "label": "PopRua"},
            {"key": "gestao", "label": "Gestão"},
            {"key": "outro", "label": "Outro (definir sigla)"},
        ]
    }
# --- Sequências de numeração (para ajuste de migração / reset) ---

class SequenciaUpsert(BaseModel):
    municipio_id: Optional[int] = None
    tipo: str
    ano: Optional[int] = None
    emissor: Optional[str] = None  # ex.: smas|cras|creas
    seq_atual: Optional[int] = None  # último número já usado
    proximo: Optional[int] = None  # próximo número a usar (mais fácil para migração)


@router.get("/sequencias", dependencies=[Depends(exigir_minimo_perfil("coord_municipal"))])
def listar_sequencias(
    municipio_id: Optional[int] = Query(default=None),
    tipo: Optional[str] = Query(default=None),
    ano: Optional[int] = Query(default=None),
    emissor: Optional[str] = Query(default=None),
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    mid = _resolve_municipio_id(usuario, municipio_id)
    ano_ref = int(ano or datetime.now(timezone.utc).year)

    q = select(DocumentoSequencia).where(DocumentoSequencia.municipio_id == mid)

    if tipo:
        q = q.where(DocumentoSequencia.tipo == str(tipo).strip().lower())

    if ano_ref:
        q = q.where(DocumentoSequencia.ano == ano_ref)

    if emissor is not None:
        emissor_key = str(emissor or "").strip().lower()
        q = q.where(DocumentoSequencia.emissor_key == emissor_key)

    rows = session.exec(q).all()
    out: List[Dict[str, Any]] = []
    for r in rows:
        d = r.model_dump() if hasattr(r, "model_dump") else r.dict()  # type: ignore
        d["proximo"] = int(getattr(r, "seq_atual", 0)) + 1
        out.append(d)
    return out


@router.post("/sequencias", dependencies=[Depends(exigir_minimo_perfil("coord_municipal"))])
def upsert_sequencia(
    payload: SequenciaUpsert,
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    if not payload.tipo:
        raise HTTPException(status_code=422, detail="tipo é obrigatório.")

    if payload.seq_atual is None and payload.proximo is None:
        raise HTTPException(
            status_code=422,
            detail="Informe seq_atual (último usado) ou proximo (próximo a usar).",
        )

    mid = _resolve_municipio_id(usuario, payload.municipio_id)
    tipo = str(payload.tipo).strip().lower()
    ano_ref = int(payload.ano or datetime.now(timezone.utc).year)

    cfg = session.exec(select(DocumentoConfig).where(DocumentoConfig.municipio_id == mid)).first()
    sequenciar_por_emissor = True if cfg is None else bool(getattr(cfg, "sequenciar_por_emissor", True))
    emissor_padrao = (getattr(cfg, "emissor_padrao", "smas") if cfg else "smas") or "smas"

    emissor_key = (payload.emissor or emissor_padrao or "smas")
    emissor_key = str(emissor_key).strip().lower()

    if not sequenciar_por_emissor:
        emissor_key = ""

    if payload.proximo is not None:
        seq_atual = int(payload.proximo) - 1
    else:
        seq_atual = int(payload.seq_atual or 0)

    if seq_atual < 0:
        raise HTTPException(status_code=422, detail="seq_atual/proximo inválido (negativo).")

    row = session.exec(
        select(DocumentoSequencia).where(
            (DocumentoSequencia.municipio_id == mid)
            & (DocumentoSequencia.tipo == tipo)
            & (DocumentoSequencia.ano == ano_ref)
            & (DocumentoSequencia.emissor_key == emissor_key)
        )
    ).first()

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    if row is None:
        row = DocumentoSequencia(
            municipio_id=mid,
            tipo=tipo,
            ano=ano_ref,
            emissor_key=emissor_key,
            seq_atual=seq_atual,
            atualizado_em=now,
        )
    else:
        row.seq_atual = seq_atual
        row.atualizado_em = now

    session.add(row)
    session.commit()
    session.refresh(row)

    d = row.model_dump() if hasattr(row, "model_dump") else row.dict()  # type: ignore
    d["proximo"] = int(getattr(row, "seq_atual", 0)) + 1
    return d


class SequenciaReset(BaseModel):
    municipio_id: Optional[int] = None
    tipo: str
    ano: Optional[int] = None
    emissor: Optional[str] = None
    proximo: int = 1  # define o próximo número a ser usado (default 1)


@router.post("/sequencias/reset", dependencies=[Depends(exigir_minimo_perfil("coord_municipal"))])
def reset_sequencia(
    payload: SequenciaReset,
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    # reset = setar proximo, por baixo vira seq_atual = proximo-1
    return upsert_sequencia(
        SequenciaUpsert(
            municipio_id=payload.municipio_id,
            tipo=payload.tipo,
            ano=payload.ano,
            emissor=payload.emissor,
            proximo=payload.proximo,
        ),
        session=session,
        usuario=usuario,
    )
