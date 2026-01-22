# app/routers/cras_prontuario.py
from __future__ import annotations

from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session, select
from sqlalchemy import or_

from app.core.db import get_session
from app.core.security import decodificar_token
from app.models.usuario import Usuario
from app.models.ficha_evento import FichaEvento

# opcional: encaminhamentos SUAS (banco)
from app.models.suas_encaminhamento import SuasEncaminhamento

router = APIRouter(prefix="/cras/prontuario", tags=["cras_prontuario"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


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


def _to_item(tipo: str, quando: Optional[datetime], titulo: str, detalhe: str, origem: str) -> dict:
    return {
        "tipo": tipo,
        "quando": quando.isoformat() if quando else None,
        "titulo": titulo,
        "detalhe": detalhe or "",
        "origem": origem,
    }


@router.get("/eventos")
def eventos(
    pessoa_id: Optional[int] = Query(None),
    familia_id: Optional[int] = Query(None),
    include_suas: bool = Query(True),
    municipio_id: Optional[int] = Query(None),
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    mid = municipio_id or getattr(usuario, "municipio_id", None)
    if mid is None and not _is_admin_or_consorcio(usuario):
        raise HTTPException(status_code=400, detail="municipio_id é obrigatório para este usuário.")
    if not _is_admin_or_consorcio(usuario):
        mid = getattr(usuario, "municipio_id", None)

    items: List[dict] = []

    # FichaEvento (pessoa/familia)
    if pessoa_id is not None:
        q = select(FichaEvento).where(
            FichaEvento.municipio_id == int(mid),
            FichaEvento.alvo_tipo == "pessoa",
            FichaEvento.alvo_id == int(pessoa_id),
        ).order_by(FichaEvento.criado_em.desc())
        for e in session.exec(q).all():
            items.append(_to_item(e.tipo, e.criado_em, "Ficha (Pessoa 360)", e.detalhe or "", "ficha"))

    if familia_id is not None:
        q = select(FichaEvento).where(
            FichaEvento.municipio_id == int(mid),
            FichaEvento.alvo_tipo == "familia",
            FichaEvento.alvo_id == int(familia_id),
        ).order_by(FichaEvento.criado_em.desc())
        for e in session.exec(q).all():
            items.append(_to_item(e.tipo, e.criado_em, "Ficha (Família 360)", e.detalhe or "", "ficha"))

    # Encaminhamentos SUAS (se houver)
    if include_suas and (pessoa_id is not None or familia_id is not None):
        ors = []
        if pessoa_id is not None:
            ors.append(SuasEncaminhamento.pessoa_id == int(pessoa_id))
        if familia_id is not None:
            ors.append(SuasEncaminhamento.familia_id == int(familia_id))

        q = select(SuasEncaminhamento).where(SuasEncaminhamento.municipio_id == int(mid)).where(or_(*ors))
        q = q.order_by(SuasEncaminhamento.atualizado_em.desc())
        for e in session.exec(q).all():
            titulo = f"SUAS · {e.origem_modulo} → {e.destino_modulo} · {e.status}".replace("  ", " ").strip()
            detalhe = (e.assunto or "Encaminhamento") + " · " + (e.motivo or "")
            when = e.retorno_em or e.cobranca_ultimo_em or e.status_em or e.atualizado_em or e.criado_em
            items.append(_to_item("suas_encaminhamento", when, titulo, detalhe, "suas"))

    # ordenar
    def ts(it):
        try:
            return datetime.fromisoformat(it["quando"]).timestamp() if it.get("quando") else 0
        except Exception:
            return 0
    items.sort(key=ts, reverse=True)

    return {"municipio_id": int(mid), "pessoa_id": pessoa_id, "familia_id": familia_id, "eventos": items}


@router.get("/export.csv")
def export_csv(
    pessoa_id: Optional[int] = Query(None),
    familia_id: Optional[int] = Query(None),
    include_suas: bool = Query(True),
    municipio_id: Optional[int] = Query(None),
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    data = eventos(pessoa_id=pessoa_id, familia_id=familia_id, include_suas=include_suas, municipio_id=municipio_id, session=session, usuario=usuario)
    items = data["eventos"]

    def gen():
        yield "quando,origem,tipo,titulo,detalhe\n"
        for it in items:
            quando = (it.get("quando") or "")
            origem = (it.get("origem") or "")
            tipo = (it.get("tipo") or "")
            titulo = (it.get("titulo") or "").replace(",", " ")
            detalhe = (it.get("detalhe") or "").replace("\n", " ").replace(",", ";")
            yield f"{quando},{origem},{tipo},{titulo},{detalhe}\n"

    filename = "prontuario.csv"
    if pessoa_id:
        filename = f"prontuario_pessoa_{pessoa_id}.csv"
    if familia_id:
        filename = f"prontuario_familia_{familia_id}.csv"

    return StreamingResponse(gen(), media_type="text/csv", headers={"Content-Disposition": f'attachment; filename="{filename}"'})
