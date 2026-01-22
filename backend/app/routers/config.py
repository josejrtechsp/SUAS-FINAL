from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field as PField
from sqlalchemy import or_  # type: ignore
from sqlmodel import Session, select

from app.core.auth import exigir_minimo_perfil, get_current_user, pode_acesso_global
from app.core.db import get_session
from app.models.usuario import Usuario

from app.models.sla_regra import SlaRegra
from app.models.meta_kpi import MetaKpi


router = APIRouter(prefix="/config", tags=["config"])


# =========================
# Helpers
# =========================

def _norm_str(v: Optional[str]) -> Optional[str]:
    if v is None:
        return None
    s = str(v).strip().lower()
    return s or None


def _resolver_municipio(usuario: Usuario, municipio_id: Optional[int]) -> Optional[int]:
    """
    - Usuário municipal: força municipio_id do usuário.
    - Gestor consórcio/admin: pode ver/editar qualquer (inclusive None = regra global).
    """
    if pode_acesso_global(usuario):
        return int(municipio_id) if municipio_id is not None else None
    # municipal
    mid = getattr(usuario, "municipio_id", None)
    if mid is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuário sem município não pode configurar regras municipais.",
        )
    return int(mid)


def _selecionar_regra_sla(
    regras: List[SlaRegra],
    municipio_id: Optional[int],
    unidade_tipo: Optional[str],
    unidade_id: Optional[int],
    modulo: str,
    etapa: str,
) -> Optional[SlaRegra]:
    """Seleciona a melhor regra aplicável (mais específica ganha)."""
    mod = _norm_str(modulo) or ""
    st = _norm_str(etapa) or ""
    ut = _norm_str(unidade_tipo)
    uid = int(unidade_id) if unidade_id is not None else None

    best: Optional[SlaRegra] = None
    best_score = -1

    for r in regras:
        if not getattr(r, "ativo", True):
            continue
        if _norm_str(getattr(r, "modulo", None)) != mod:
            continue
        if _norm_str(getattr(r, "etapa", None)) != st:
            continue

        r_mid = getattr(r, "municipio_id", None)
        if r_mid is not None and municipio_id is not None:
            if int(r_mid) != int(municipio_id):
                continue
        elif r_mid is not None and municipio_id is None:
            # regra municipal não vale para consulta global sem municipio_id
            continue
        # se r_mid is None => global: ok

        r_ut = _norm_str(getattr(r, "unidade_tipo", None))
        r_uid = getattr(r, "unidade_id", None)
        r_uid = int(r_uid) if r_uid is not None else None

        # compat de unidade_tipo
        if r_ut is not None:
            if ut is None:
                continue
            if r_ut != ut:
                continue

        # compat de unidade_id
        if r_uid is not None:
            if uid is None:
                continue
            if int(r_uid) != int(uid):
                continue

        score = 0
        score += 4 if r_mid is not None else 0
        score += 2 if r_ut is not None else 0
        score += 1 if r_uid is not None else 0

        if score > best_score:
            best = r
            best_score = score
        elif score == best_score and best is not None:
            # desempate: mais recente
            b_upd = getattr(best, "atualizado_em", None)
            r_upd = getattr(r, "atualizado_em", None)
            if isinstance(r_upd, datetime) and isinstance(b_upd, datetime):
                if r_upd > b_upd:
                    best = r

    return best


# =========================
# SLA
# =========================

class SlaUpsert(BaseModel):
    municipio_id: Optional[int] = None
    unidade_tipo: Optional[str] = None
    unidade_id: Optional[int] = None

    modulo: str = PField(..., min_length=1)
    etapa: str = PField(..., min_length=1)

    sla_dias: int = PField(..., ge=1, le=365)
    ativo: bool = True


@router.get("/sla", response_model=List[SlaRegra])
def listar_sla(
    municipio_id: Optional[int] = Query(default=None),
    unidade_tipo: Optional[str] = Query(default=None),
    unidade_id: Optional[int] = Query(default=None),
    modulo: Optional[str] = Query(default=None),
    etapa: Optional[str] = Query(default=None),
    ativo: Optional[bool] = Query(default=None),
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    """Lista regras de SLA (com filtros)."""

    mid = _resolver_municipio(usuario, municipio_id)

    stmt = select(SlaRegra)
    if mid is not None:
        stmt = stmt.where(SlaRegra.municipio_id == int(mid))
    else:
        # global: sem filtro (pode listar globais ou tudo se municipio_id vier None)
        # Se o usuário é global e quer APENAS globais, use municipio_id=null + filtro abaixo:
        if municipio_id is None:
            pass

    if unidade_tipo is not None:
        stmt = stmt.where(SlaRegra.unidade_tipo == _norm_str(unidade_tipo))
    if unidade_id is not None:
        stmt = stmt.where(SlaRegra.unidade_id == int(unidade_id))
    if modulo is not None:
        stmt = stmt.where(SlaRegra.modulo == _norm_str(modulo))
    if etapa is not None:
        stmt = stmt.where(SlaRegra.etapa == _norm_str(etapa))
    if ativo is not None:
        stmt = stmt.where(SlaRegra.ativo == bool(ativo))

    rows = list(session.exec(stmt).all())
    rows.sort(key=lambda r: (
        0 if getattr(r, "municipio_id", None) is not None else 1,
        str(getattr(r, "unidade_tipo", "") or ""),
        int(getattr(r, "unidade_id", 0) or 0),
        str(getattr(r, "modulo", "") or ""),
        str(getattr(r, "etapa", "") or ""),
    ))
    return rows


@router.post(
    "/sla",
    response_model=SlaRegra,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(exigir_minimo_perfil("coord_municipal"))],
)
def upsert_sla(
    body: SlaUpsert,
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    """Cria/atualiza uma regra de SLA (upsert por chave lógica)."""

    # valida unidade
    ut = _norm_str(body.unidade_tipo)
    uid = int(body.unidade_id) if body.unidade_id is not None else None
    if uid is not None and ut is None:
        raise HTTPException(status_code=400, detail="unidade_id exige unidade_tipo.")

    mid = _resolver_municipio(usuario, body.municipio_id)

    mod = _norm_str(body.modulo) or ""
    st = _norm_str(body.etapa) or ""

    stmt = select(SlaRegra).where(
        SlaRegra.municipio_id == mid,
        SlaRegra.unidade_tipo == ut,
        SlaRegra.unidade_id == uid,
        SlaRegra.modulo == mod,
        SlaRegra.etapa == st,
    )
    row = session.exec(stmt).first()

    now = datetime.utcnow()

    if row:
        row.sla_dias = int(body.sla_dias)
        row.ativo = bool(body.ativo)
        row.atualizado_em = now
        session.add(row)
        session.commit()
        session.refresh(row)
        return row

    row = SlaRegra(
        municipio_id=mid,
        unidade_tipo=ut,
        unidade_id=uid,
        modulo=mod,
        etapa=st,
        sla_dias=int(body.sla_dias),
        ativo=bool(body.ativo),
        criado_em=now,
        atualizado_em=now,
    )
    session.add(row)
    session.commit()
    session.refresh(row)
    return row


@router.get("/sla/efetivo")
def sla_efetivo(
    municipio_id: Optional[int] = Query(default=None),
    unidade_tipo: Optional[str] = Query(default=None),
    unidade_id: Optional[int] = Query(default=None),
    modulo: str = Query(...),
    etapa: str = Query(...),
    default_dias: int = Query(default=7, ge=1, le=365),
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
) -> Dict[str, Any]:
    """Debug: resolve qual regra efetiva seria aplicada (fallback incluso)."""

    mid = _resolver_municipio(usuario, municipio_id)
    ut = _norm_str(unidade_tipo)
    uid = int(unidade_id) if unidade_id is not None else None
    if uid is not None and ut is None:
        raise HTTPException(status_code=400, detail="unidade_id exige unidade_tipo.")

    mod = _norm_str(modulo) or ""
    st = _norm_str(etapa) or ""

    # carrega candidatas (municipal + global)
    stmt = select(SlaRegra).where(
        SlaRegra.ativo == True,  # noqa: E712
        SlaRegra.modulo == mod,
        SlaRegra.etapa == st,
    )
    if mid is not None:
        # pode aplicar regra municipal ou global
        stmt = stmt.where((SlaRegra.municipio_id == int(mid)) | (SlaRegra.municipio_id == None))  # noqa: E711
    else:
        # sem município (consulta global): só globais
        stmt = stmt.where(SlaRegra.municipio_id == None)  # noqa: E711

    regras = list(session.exec(stmt).all())
    regra = _selecionar_regra_sla(regras, mid, ut, uid, mod, st)

    return {
        "sla_dias": int(getattr(regra, "sla_dias")) if regra else int(default_dias),
        "regra": regra.model_dump() if regra else None,
        "fallback_usado": regra is None,
    }


# =========================
# METAS
# =========================

class MetaUpsert(BaseModel):
    municipio_id: Optional[int] = None
    unidade_tipo: Optional[str] = None
    unidade_id: Optional[int] = None

    modulo: str = PField(..., min_length=1)
    kpi: str = PField(..., min_length=1)
    periodo: str = PField(default="mensal", min_length=1)

    valor_meta: float = 0.0
    ativo: bool = True


@router.get("/metas", response_model=List[MetaKpi])
def listar_metas(
    municipio_id: Optional[int] = Query(default=None),
    include_globais: bool = Query(default=False, description="Se true, inclui metas globais (municipio_id=NULL) como fallback."),
    unidade_tipo: Optional[str] = Query(default=None),
    unidade_id: Optional[int] = Query(default=None),
    modulo: Optional[str] = Query(default=None),
    kpi: Optional[str] = Query(default=None),
    periodo: Optional[str] = Query(default=None),
    ativo: Optional[bool] = Query(default=None),
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    mid = _resolver_municipio(usuario, municipio_id)

    stmt = select(MetaKpi)
    if mid is not None:
        if include_globais:
            stmt = stmt.where(or_(MetaKpi.municipio_id == int(mid), MetaKpi.municipio_id.is_(None)))
        else:
            stmt = stmt.where(MetaKpi.municipio_id == int(mid))
    else:
        if municipio_id is None:
            pass

    if unidade_tipo is not None:
        stmt = stmt.where(MetaKpi.unidade_tipo == _norm_str(unidade_tipo))
    if unidade_id is not None:
        stmt = stmt.where(MetaKpi.unidade_id == int(unidade_id))
    if modulo is not None:
        stmt = stmt.where(MetaKpi.modulo == _norm_str(modulo))
    if kpi is not None:
        stmt = stmt.where(MetaKpi.kpi == _norm_str(kpi))
    if periodo is not None:
        stmt = stmt.where(MetaKpi.periodo == _norm_str(periodo))
    if ativo is not None:
        stmt = stmt.where(MetaKpi.ativo == bool(ativo))

    rows = list(session.exec(stmt).all())
    rows.sort(key=lambda r: (
        0 if getattr(r, "municipio_id", None) is not None else 1,
        str(getattr(r, "unidade_tipo", "") or ""),
        int(getattr(r, "unidade_id", 0) or 0),
        str(getattr(r, "modulo", "") or ""),
        str(getattr(r, "kpi", "") or ""),
        str(getattr(r, "periodo", "") or ""),
    ))
    return rows


@router.post(
    "/metas",
    response_model=MetaKpi,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(exigir_minimo_perfil("coord_municipal"))],
)
def upsert_meta(
    body: MetaUpsert,
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    ut = _norm_str(body.unidade_tipo)
    uid = int(body.unidade_id) if body.unidade_id is not None else None
    if uid is not None and ut is None:
        raise HTTPException(status_code=400, detail="unidade_id exige unidade_tipo.")

    mid = _resolver_municipio(usuario, body.municipio_id)
    mod = _norm_str(body.modulo) or ""
    kpi = _norm_str(body.kpi) or ""
    per = _norm_str(body.periodo) or "mensal"

    stmt = select(MetaKpi).where(
        MetaKpi.municipio_id == mid,
        MetaKpi.unidade_tipo == ut,
        MetaKpi.unidade_id == uid,
        MetaKpi.modulo == mod,
        MetaKpi.kpi == kpi,
        MetaKpi.periodo == per,
    )
    row = session.exec(stmt).first()

    now = datetime.utcnow()

    if row:
        row.valor_meta = float(body.valor_meta or 0.0)
        row.ativo = bool(body.ativo)
        row.atualizado_em = now
        session.add(row)
        session.commit()
        session.refresh(row)
        return row

    row = MetaKpi(
        municipio_id=mid,
        unidade_tipo=ut,
        unidade_id=uid,
        modulo=mod,
        kpi=kpi,
        periodo=per,
        valor_meta=float(body.valor_meta or 0.0),
        ativo=bool(body.ativo),
        criado_em=now,
        atualizado_em=now,
    )
    session.add(row)
    session.commit()
    session.refresh(row)
    return row
