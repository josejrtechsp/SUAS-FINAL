from __future__ import annotations

from datetime import date, datetime
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from sqlalchemy.inspection import inspect as sa_inspect
from sqlmodel import Session, select

from app.core.db import get_session
from app.core.auth import get_current_user, pode_acesso_global
from app.models.usuario import Usuario

from app.models.caso_cras import CasoCras, CasoCrasHistorico
from app.models.cras_pia import CrasPiaPlano, CrasPiaAcao

router = APIRouter(prefix="/cras", tags=["cras-pia"])


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


def _usuario_nome(usuario: Usuario) -> str:
    return getattr(usuario, "nome", None) or "Usuário"


def _parse_date(v: Any) -> Optional[date]:
    """Aceita date/datetime/ISO string. Retorna date ou None."""
    if v is None or v == "":
        return None
    if isinstance(v, datetime):
        return v.date()
    if isinstance(v, date):
        return v
    try:
        # garante YYYY-MM-DD
        return date.fromisoformat(str(v)[:10])
    except Exception:
        return None


def _dump(obj: Any) -> Any:
    """Converte modelos (SQLModel/Pydantic/SQLAlchemy) para dict.

    Motivo: alguns modelos ORM podem serializar como {} se não forem convertidos.
    """
    if obj is None:
        return None

    # Pydantic v2
    if hasattr(obj, "model_dump"):
        try:
            d = obj.model_dump()  # type: ignore[attr-defined]
            if isinstance(d, dict) and d:
                return d
        except Exception:
            pass

    # Pydantic v1
    if hasattr(obj, "dict"):
        try:
            d = obj.dict()  # type: ignore[attr-defined]
            if isinstance(d, dict) and d:
                return d
        except Exception:
            pass

    # SQLAlchemy/SQLModel fallback (colunas mapeadas)
    try:
        insp = sa_inspect(obj)
        if insp is not None and getattr(insp, "mapper", None) is not None:
            return {attr.key: getattr(obj, attr.key) for attr in insp.mapper.column_attrs}
    except Exception:
        pass

    # Último recurso: __dict__ sem estado interno
    try:
        d = dict(getattr(obj, "__dict__", {}) or {})
        d.pop("_sa_instance_state", None)
        return d
    except Exception:
        return str(obj)


def _encode(obj: Any) -> Any:
    """Garante JSON serializável (date/datetime -> ISO)."""
    return jsonable_encoder(_dump(obj))


def _log(session: Session, caso_id: int, etapa: str, tipo_acao: str, usuario: Usuario, obs: Optional[str] = None) -> None:
    session.add(
        CasoCrasHistorico(
            caso_id=int(caso_id),
            etapa=str(etapa),
            tipo_acao=str(tipo_acao),
            usuario_id=getattr(usuario, "id", None),
            usuario_nome=_usuario_nome(usuario),
            observacoes=obs,
            criado_em=_now(),
        )
    )
    session.commit()


def _get_caso(session: Session, caso_id: int, usuario: Usuario) -> CasoCras:
    caso = session.get(CasoCras, caso_id)
    if not caso:
        raise HTTPException(status_code=404, detail="Caso CRAS não encontrado.")
    _check_municipio(usuario, int(caso.municipio_id))
    return caso


def _get_plano(session: Session, caso_id: int) -> Optional[CrasPiaPlano]:
    return session.exec(select(CrasPiaPlano).where(CrasPiaPlano.caso_id == caso_id)).first()


@router.get("/casos/{caso_id}/pia/plano", response_model=None)
def obter_plano(
    caso_id: int,
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
) -> Dict[str, Any]:
    _ = _get_caso(session, caso_id, usuario)
    plano = _get_plano(session, caso_id)
    if not plano:
        return {"plano": None, "acoes": []}

    acoes = session.exec(
        select(CrasPiaAcao).where(CrasPiaAcao.plano_id == plano.id).order_by(CrasPiaAcao.id.desc())
    ).all()
    return {"plano": _encode(plano), "acoes": [_encode(a) for a in acoes]}


@router.post("/casos/{caso_id}/pia/plano", response_model=None)
def upsert_plano(
    caso_id: int,
    payload: Dict[str, Any],
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
) -> Dict[str, Any]:
    caso = _get_caso(session, caso_id, usuario)

    plano = _get_plano(session, caso_id)
    creating = False
    if not plano:
        creating = True
        plano = CrasPiaPlano(
            municipio_id=int(caso.municipio_id),
            unidade_id=int(caso.unidade_id),
            caso_id=int(caso_id),
            status="ativo",
            data_inicio=date.today(),
            criado_em=_now(),
            atualizado_em=_now(),
        )

    if "resumo_diagnostico" in payload:
        plano.resumo_diagnostico = payload.get("resumo_diagnostico")
    if "objetivos" in payload:
        plano.objetivos = payload.get("objetivos")
    if "status" in payload and payload.get("status") in ("ativo", "finalizado"):
        plano.status = payload.get("status")

    if "data_revisao" in payload:
        raw = payload.get("data_revisao")
        dr = _parse_date(raw)
        if raw and dr is None:
            raise HTTPException(status_code=400, detail="data_revisao inválida (use YYYY-MM-DD).")
        plano.data_revisao = dr

    plano.atualizado_em = _now()
    session.add(plano)
    session.commit()
    session.refresh(plano)

    obs = "Plano criado" if creating else "Plano atualizado"
    _log(session, caso_id=caso_id, etapa="PIA", tipo_acao="pia_plano", usuario=usuario, obs=obs)

    return _encode(plano)


@router.post("/casos/{caso_id}/pia/acoes", response_model=None)
def criar_acao(
    caso_id: int,
    payload: Dict[str, Any],
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
) -> Dict[str, Any]:
    caso = _get_caso(session, caso_id, usuario)
    plano = _get_plano(session, caso_id)
    if not plano:
        plano = CrasPiaPlano(
            municipio_id=int(caso.municipio_id),
            unidade_id=int(caso.unidade_id),
            caso_id=int(caso_id),
            status="ativo",
            data_inicio=date.today(),
            criado_em=_now(),
            atualizado_em=_now(),
        )
        session.add(plano)
        session.commit()
        session.refresh(plano)
        _log(session, caso_id=caso_id, etapa="PIA", tipo_acao="pia_plano", usuario=usuario, obs="Plano criado")

    desc = (payload.get("descricao") or "").strip()
    if not desc:
        raise HTTPException(status_code=400, detail="descricao é obrigatória.")

    raw_prazo = payload.get("prazo")
    prazo = _parse_date(raw_prazo)
    if raw_prazo and prazo is None:
        raise HTTPException(status_code=400, detail="prazo inválido (use YYYY-MM-DD).")

    acao = CrasPiaAcao(
        plano_id=int(plano.id),
        descricao=desc,
        responsavel_usuario_id=payload.get("responsavel_usuario_id"),
        prazo=prazo,
        status=payload.get("status") or "pendente",
        evidencias_texto=payload.get("evidencias_texto"),
        criado_em=_now(),
        atualizado_em=_now(),
    )
    session.add(acao)
    session.commit()
    session.refresh(acao)

    _log(session, caso_id=caso_id, etapa="PIA", tipo_acao="pia_acao_criada", usuario=usuario, obs=f"Ação criada: {desc[:180]}")

    return _encode(acao)


@router.patch("/pia/acoes/{acao_id}", response_model=None)
def atualizar_acao(
    acao_id: int,
    payload: Dict[str, Any],
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
) -> Dict[str, Any]:
    acao = session.get(CrasPiaAcao, acao_id)
    if not acao:
        raise HTTPException(status_code=404, detail="Ação não encontrada.")

    plano = session.get(CrasPiaPlano, acao.plano_id)
    if not plano:
        raise HTTPException(status_code=404, detail="Plano não encontrado.")
    _check_municipio(usuario, int(plano.municipio_id))

    if "descricao" in payload and payload.get("descricao"):
        acao.descricao = str(payload.get("descricao"))
    if "status" in payload and payload.get("status"):
        acao.status = str(payload.get("status"))

    if "prazo" in payload:
        raw = payload.get("prazo")
        pr = _parse_date(raw)
        if raw and pr is None:
            raise HTTPException(status_code=400, detail="prazo inválido (use YYYY-MM-DD).")
        acao.prazo = pr

    if "responsavel_usuario_id" in payload:
        acao.responsavel_usuario_id = payload.get("responsavel_usuario_id")
    if "evidencias_texto" in payload:
        acao.evidencias_texto = payload.get("evidencias_texto")

    acao.atualizado_em = _now()
    session.add(acao)
    session.commit()
    session.refresh(acao)

    caso_id = plano.caso_id
    _log(session, caso_id=caso_id, etapa="PIA", tipo_acao="pia_acao_atualizada", usuario=usuario, obs=f"Ação atualizada: {acao.descricao[:180]}")

    return _encode(acao)


@router.post("/pia/acoes/{acao_id}/concluir", response_model=None)
def concluir_acao(
    acao_id: int,
    payload: Dict[str, Any],
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
) -> Dict[str, Any]:
    acao = session.get(CrasPiaAcao, acao_id)
    if not acao:
        raise HTTPException(status_code=404, detail="Ação não encontrada.")

    plano = session.get(CrasPiaPlano, acao.plano_id)
    if not plano:
        raise HTTPException(status_code=404, detail="Plano não encontrado.")
    _check_municipio(usuario, int(plano.municipio_id))

    acao.status = "concluida"
    if payload.get("evidencias_texto"):
        acao.evidencias_texto = payload.get("evidencias_texto")
    acao.atualizado_em = _now()

    session.add(acao)
    session.commit()
    session.refresh(acao)

    _log(session, caso_id=plano.caso_id, etapa="PIA", tipo_acao="pia_acao_concluida", usuario=usuario, obs=f"Ação concluída: {acao.descricao[:180]}")

    return _encode(acao)

# --- inclui sub-rotas do CRAS (automações)
try:
    from app.routers.cras_automacoes import router as cras_automacoes_router  # type: ignore
    router.include_router(cras_automacoes_router)
except Exception:
    pass
