# app/routers/cras_rma.py
from __future__ import annotations

from datetime import datetime, date
import json
from typing import Optional, Dict, Any, List

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session, select

from app.core.db import get_session
from app.core.security import decodificar_token
from app.models.usuario import Usuario
from app.models.rma_evento import RmaEvento

from app.models.rma_meta import RmaMeta
router = APIRouter(prefix="/cras/rma", tags=["cras_rma"])
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


def _parse_mes(mes: str) -> tuple[int, int]:
    try:
        y, m = mes.split("-")
        yy = int(y)
        mm = int(m)
        if mm < 1 or mm > 12:
            raise ValueError()
        return yy, mm
    except Exception:
        raise HTTPException(status_code=400, detail="Parâmetro 'mes' deve ser YYYY-MM")


def _in_month(d: date, yy: int, mm: int) -> bool:
    return d.year == yy and d.month == mm


@router.get("/health")
def health():
    return {"status": "ok"}


@router.post("/evento")
def criar_evento(
    payload: Dict[str, Any],
    municipio_id: Optional[int] = Query(None),
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    mid = municipio_id or getattr(usuario, "municipio_id", None)
    if mid is None and not _is_admin_or_consorcio(usuario):
        raise HTTPException(status_code=400, detail="municipio_id é obrigatório para este usuário.")
    if not _is_admin_or_consorcio(usuario):
        mid = getattr(usuario, "municipio_id", None)

    servico = str(payload.get("servico") or "").strip().upper()
    acao = str(payload.get("acao") or "").strip().lower()
    if not servico or not acao:
        raise HTTPException(status_code=400, detail="servico e acao são obrigatórios")

    unidade_id = payload.get("unidade_id")
    try:
        unidade_id = int(unidade_id) if unidade_id is not None else None
    except Exception:
        unidade_id = None

    # alvo
    alvo_tipo = payload.get("alvo_tipo")
    alvo_id = payload.get("alvo_id")
    try:
        alvo_id = int(alvo_id) if alvo_id is not None else None
    except Exception:
        alvo_id = None

    pessoa_id = payload.get("pessoa_id")
    familia_id = payload.get("familia_id")
    caso_id = payload.get("caso_id")
    for k, v in (("pessoa_id", pessoa_id), ("familia_id", familia_id), ("caso_id", caso_id)):
        try:
            locals()[k] = int(v) if v is not None else None
        except Exception:
            locals()[k] = None
    pessoa_id = locals()["pessoa_id"]
    familia_id = locals()["familia_id"]
    caso_id = locals()["caso_id"]

    data_evento = payload.get("data_evento")
    if data_evento:
        try:
            data_evento = date.fromisoformat(str(data_evento))
        except Exception:
            raise HTTPException(status_code=400, detail="data_evento deve ser YYYY-MM-DD")
    else:
        data_evento = date.today()

    meta = payload.get("meta")
    meta_json = None
    if meta is not None:
        try:
            meta_json = meta if isinstance(meta, str) else json.dumps(meta, ensure_ascii=False)
        except Exception:
            meta_json = str(meta)

    ev = RmaEvento(
        municipio_id=int(mid) if mid is not None else 1,
        unidade_id=unidade_id,
        servico=servico[:40],
        acao=acao[:60],
        alvo_tipo=(str(alvo_tipo).lower()[:20] if alvo_tipo else None),
        alvo_id=alvo_id,
        pessoa_id=pessoa_id,
        familia_id=familia_id,
        caso_id=caso_id,
        data_evento=data_evento,
        meta_json=meta_json,
        criado_em=_agora(),
        criado_por_usuario_id=usuario.id,
        criado_por_nome=usuario.nome,
    )
    session.add(ev)
    session.commit()
    session.refresh(ev)
    return {"id": ev.id, "ok": True}


@router.get("/mes")
def resumo_mes(
    mes: str = Query(..., description="YYYY-MM"),
    unidade_id: Optional[int] = Query(None),
    servico: Optional[str] = Query(None),
    municipio_id: Optional[int] = Query(None),
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    yy, mm = _parse_mes(mes)

    mid = municipio_id or getattr(usuario, "municipio_id", None)
    if mid is None and not _is_admin_or_consorcio(usuario):
        raise HTTPException(status_code=400, detail="municipio_id é obrigatório para este usuário.")
    if not _is_admin_or_consorcio(usuario):
        mid = getattr(usuario, "municipio_id", None)

    q = select(RmaEvento).where(RmaEvento.municipio_id == int(mid))
    if unidade_id is not None:
        q = q.where(RmaEvento.unidade_id == int(unidade_id))
    if servico:
        q = q.where(RmaEvento.servico == str(servico).strip().upper())

    rows = session.exec(q).all()
    rows = [r for r in rows if _in_month(r.data_evento, yy, mm)]

    # agregações
    by_servico: Dict[str, Dict[str, int]] = {}
    by_day: Dict[str, int] = {}
    total = 0

    for r in rows:
        total += 1
        s = r.servico
        a = r.acao
        by_servico.setdefault(s, {})
        by_servico[s][a] = by_servico[s].get(a, 0) + 1

        d = r.data_evento.isoformat()
        by_day[d] = by_day.get(d, 0) + 1

    # ordenar dias
    days = [{"dia": k, "qtd": by_day[k]} for k in sorted(by_day.keys())]

    return {
        "mes": mes,
        "municipio_id": int(mid),
        "unidade_id": unidade_id,
        "total_eventos": total,
        "por_servico": by_servico,
        "serie_diaria": days,
    }


@router.get("/export.csv")
def export_csv(
    mes: str = Query(..., description="YYYY-MM"),
    unidade_id: Optional[int] = Query(None),
    municipio_id: Optional[int] = Query(None),
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    yy, mm = _parse_mes(mes)

    mid = municipio_id or getattr(usuario, "municipio_id", None)
    if mid is None and not _is_admin_or_consorcio(usuario):
        raise HTTPException(status_code=400, detail="municipio_id é obrigatório para este usuário.")
    if not _is_admin_or_consorcio(usuario):
        mid = getattr(usuario, "municipio_id", None)

    q = select(RmaEvento).where(RmaEvento.municipio_id == int(mid))
    if unidade_id is not None:
        q = q.where(RmaEvento.unidade_id == int(unidade_id))

    rows = session.exec(q).all()
    rows = [r for r in rows if _in_month(r.data_evento, yy, mm)]

    def gen():
        header = "id,mes,data,servico,acao,unidade_id,pessoa_id,familia_id,caso_id,alvo_tipo,alvo_id,criado_por,meta_json\n"
        yield header
        for r in rows:
            vals = [
                r.id,
                mes,
                r.data_evento.isoformat(),
                r.servico,
                r.acao,
                r.unidade_id or "",
                r.pessoa_id or "",
                r.familia_id or "",
                r.caso_id or "",
                r.alvo_tipo or "",
                r.alvo_id or "",
                (r.criado_por_nome or "").replace(",", " "),
                (r.meta_json or "").replace("\n", " ").replace(",", ";"),
            ]
            yield ",".join([str(v) for v in vals]) + "\n"

    filename = f"rma_{mes}_municipio_{int(mid)}.csv"
    return StreamingResponse(gen(), media_type="text/csv", headers={"Content-Disposition": f'attachment; filename="{filename}"'})

# RMA_METAS_V1

@router.get("/metas")
def listar_metas(
    mes: str = Query(..., description="YYYY-MM"),
    unidade_id: Optional[int] = Query(None),
    servico: Optional[str] = Query(None),
    municipio_id: Optional[int] = Query(None),
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    _parse_mes(mes)
    mid = municipio_id or getattr(usuario, "municipio_id", None)
    if mid is None and not _is_admin_or_consorcio(usuario):
        raise HTTPException(status_code=400, detail="municipio_id é obrigatório para este usuário.")
    if not _is_admin_or_consorcio(usuario):
        mid = getattr(usuario, "municipio_id", None)

    q = select(RmaMeta).where(RmaMeta.municipio_id == int(mid), RmaMeta.mes == mes)
    if unidade_id is not None:
        q = q.where(RmaMeta.unidade_id == int(unidade_id))
    if servico:
        q = q.where(RmaMeta.servico == str(servico).strip().upper())

    rows = session.exec(q).all()
    return [{
        "id": r.id,
        "mes": r.mes,
        "servico": r.servico,
        "unidade_id": r.unidade_id,
        "meta_total": r.meta_total,
        "meta_json": r.meta_json,
        "atualizado_em": r.atualizado_em.isoformat() if r.atualizado_em else None,
        "atualizado_por_nome": r.atualizado_por_nome,
    } for r in rows]


@router.post("/metas")
def upsert_meta(
    payload: Dict[str, Any],
    municipio_id: Optional[int] = Query(None),
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    mes = str(payload.get("mes") or "").strip()
    if not mes or len(mes) != 7:
        raise HTTPException(status_code=400, detail="mes é obrigatório (YYYY-MM)")
    _parse_mes(mes)

    servico = str(payload.get("servico") or "").strip().upper()
    if not servico:
        raise HTTPException(status_code=400, detail="servico é obrigatório")

    unidade_id = payload.get("unidade_id")
    try:
        unidade_id = int(unidade_id) if unidade_id is not None and str(unidade_id).strip() != "" else None
    except Exception:
        unidade_id = None

    meta_total = payload.get("meta_total")
    try:
        meta_total = int(meta_total) if meta_total is not None else 0
    except Exception:
        meta_total = 0

    meta_json = payload.get("meta_json")
    if meta_json is not None and not isinstance(meta_json, str):
        try:
            import json as _json
            meta_json = _json.dumps(meta_json, ensure_ascii=False)
        except Exception:
            meta_json = str(meta_json)

    mid = municipio_id or getattr(usuario, "municipio_id", None)
    if mid is None and not _is_admin_or_consorcio(usuario):
        raise HTTPException(status_code=400, detail="municipio_id é obrigatório para este usuário.")
    if not _is_admin_or_consorcio(usuario):
        mid = getattr(usuario, "municipio_id", None)

    q = select(RmaMeta).where(RmaMeta.municipio_id == int(mid), RmaMeta.mes == mes, RmaMeta.servico == servico)
    if unidade_id is None:
        q = q.where(RmaMeta.unidade_id == None)  # noqa
    else:
        q = q.where(RmaMeta.unidade_id == unidade_id)

    existing = session.exec(q).first()
    now = _agora()

    if existing:
        existing.meta_total = meta_total
        existing.meta_json = meta_json
        existing.atualizado_em = now
        existing.atualizado_por_nome = usuario.nome
        session.add(existing)
        session.commit()
        session.refresh(existing)
        return {"ok": True, "id": existing.id, "updated": True}

    rec = RmaMeta(
        municipio_id=int(mid) if mid is not None else 1,
        unidade_id=unidade_id,
        mes=mes,
        servico=servico[:40],
        meta_total=meta_total,
        meta_json=meta_json,
        criado_em=now,
        atualizado_em=now,
        atualizado_por_nome=usuario.nome,
    )
    session.add(rec)
    session.commit()
    session.refresh(rec)
    return {"ok": True, "id": rec.id, "updated": False}

# RMA_PRESTACAO_V1

@router.get("/prestacao.csv")
def prestacao_csv(
    mes: str = Query(..., description="YYYY-MM"),
    unidade_id: Optional[int] = Query(None),
    municipio_id: Optional[int] = Query(None),
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    yy, mm = _parse_mes(mes)

    mid = municipio_id or getattr(usuario, "municipio_id", None)
    if mid is None and not _is_admin_or_consorcio(usuario):
        raise HTTPException(status_code=400, detail="municipio_id é obrigatório para este usuário.")
    if not _is_admin_or_consorcio(usuario):
        mid = getattr(usuario, "municipio_id", None)

    q = select(RmaEvento).where(RmaEvento.municipio_id == int(mid))
    if unidade_id is not None:
        q = q.where(RmaEvento.unidade_id == int(unidade_id))
    rows = session.exec(q).all()
    rows = [r for r in rows if _in_month(r.data_evento, yy, mm)]

    qm = select(RmaMeta).where(RmaMeta.municipio_id == int(mid), RmaMeta.mes == mes)
    if unidade_id is not None:
        qm = qm.where(RmaMeta.unidade_id == int(unidade_id))
    metas = session.exec(qm).all()
    meta_by_serv = {m.servico: int(m.meta_total or 0) for m in metas}

    real_by_serv = {}
    total_by_day = {}
    for r in rows:
        serv = r.servico
        real_by_serv[serv] = real_by_serv.get(serv, 0) + 1
        d = r.data_evento.isoformat()
        total_by_day[d] = total_by_day.get(d, 0) + 1

    servicos = sorted(set(list(real_by_serv.keys()) + list(meta_by_serv.keys())))

    def gen():
        yield "tipo,mes,unidade_id,servico,meta_total,realizado_total,pct,dia,qtd_dia\n"
        for serv in servicos:
            meta = int(meta_by_serv.get(serv, 0))
            real = int(real_by_serv.get(serv, 0))
            pct = (round((real / meta) * 100) if meta else "")
            yield f"resumo,{mes},{unidade_id or ''},{serv},{meta},{real},{pct},,\n"
        for dia in sorted(total_by_day.keys()):
            yield f"serie,{mes},{unidade_id or ''},TOTAL,,, ,{dia},{total_by_day[dia]}\n"

    filename = f"prestacao_rma_{mes}_municipio_{int(mid)}.csv"
    if unidade_id is not None:
        filename = f"prestacao_rma_{mes}_unidade_{int(unidade_id)}.csv"
    return StreamingResponse(gen(), media_type="text/csv", headers={"Content-Disposition": f'attachment; filename="{filename}"'})
