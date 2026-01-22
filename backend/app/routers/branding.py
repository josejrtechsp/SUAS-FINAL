from __future__ import annotations

import base64
import os
import re
from datetime import datetime, timezone
from io import BytesIO
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlmodel import Session, select

from app.core.auth import exigir_minimo_perfil, get_current_user, pode_acesso_global
from app.core.db import get_session
from app.models.usuario import Usuario
from app.models.municipio_branding import MunicipioBranding


router = APIRouter(prefix="/config/branding", tags=["config"])


# =========================================================
# Storage helpers
# =========================================================

def _now_utc_naive() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _backend_dir() -> str:
    # routers -> app -> backend
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def _storage_dir() -> str:
    return os.getenv("POPRUA_STORAGE_DIR", os.path.join(_backend_dir(), "storage"))


def _to_relpath(abs_path: str) -> str:
    try:
        return os.path.relpath(abs_path, _backend_dir())
    except Exception:
        return abs_path


def _branding_dir(municipio_id: int) -> str:
    base_dir = _storage_dir()
    return os.path.join(base_dir, "branding", str(municipio_id))


def _public_url_path(municipio_id: int) -> str:
    return os.path.join(_branding_dir(municipio_id), "public_base_url.txt")


def _read_public_base_url(municipio_id: int) -> Optional[str]:
    try:
        p = _public_url_path(municipio_id)
        if os.path.exists(p):
            with open(p, "r", encoding="utf-8") as f:
                u = (f.read() or "").strip()
            u = u.rstrip("/")
            return u or None
    except Exception:
        pass
    return None


def _write_public_base_url(municipio_id: int, url: Optional[str]) -> None:
    os.makedirs(_branding_dir(municipio_id), exist_ok=True)
    p = _public_url_path(municipio_id)

    if url is None:
        return  # não altera

    u = (url or "").strip()
    if not u:
        # limpar
        try:
            if os.path.exists(p):
                os.remove(p)
        except Exception:
            pass
        return

    if not re.match(r"^https?://", u, flags=re.IGNORECASE):
        raise HTTPException(
            status_code=422,
            detail="public_base_url deve começar com http:// ou https://",
        )
    u = u.rstrip("/")

    with open(p, "w", encoding="utf-8") as f:
        f.write(u)


# =========================================================
# Auth / municipio
# =========================================================

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


def _decode_logo_base64(logo_base64: str) -> bytes:
    s = (logo_base64 or "").strip()
    m = re.match(r"^data:(image/[^;]+);base64,(.+)$", s, flags=re.IGNORECASE)
    if m:
        s = m.group(2)
    try:
        return base64.b64decode(s)
    except Exception:
        raise HTTPException(status_code=422, detail="Logo inválido. Envie um PNG/JPG válido em base64.")


def _save_logo_png(municipio_id: int, raw: bytes) -> str:
    try:
        from PIL import Image  # type: ignore
    except Exception:
        raise HTTPException(status_code=500, detail="Dependência Pillow não encontrada.")

    try:
        img = Image.open(BytesIO(raw))
        img.verify()  # valida/CRC
        img = Image.open(BytesIO(raw))  # reabrir após verify()
    except Exception:
        raise HTTPException(status_code=422, detail="Logo inválido. Envie um PNG/JPG válido em base64.")

    os.makedirs(_branding_dir(municipio_id), exist_ok=True)
    abs_path = os.path.join(_branding_dir(municipio_id), "logo.png")

    try:
        # Normaliza para PNG
        if img.mode not in ("RGB", "RGBA"):
            img = img.convert("RGBA")
        img.save(abs_path, format="PNG")
    except Exception:
        raise HTTPException(status_code=422, detail="Não foi possível salvar o logo. Tente outro arquivo.")

    return _to_relpath(abs_path)


# =========================================================
# Schemas
# =========================================================

class BrandingUpsert(BaseModel):
    municipio_id: Optional[int] = None

    nome_instituicao: Optional[str] = None
    header_text: Optional[str] = None
    footer_text: Optional[str] = None

    margin_top_mm: Optional[float] = None
    margin_bottom_mm: Optional[float] = None
    margin_left_mm: Optional[float] = None
    margin_right_mm: Optional[float] = None

    logo_width_mm: Optional[float] = None
    logo_height_mm: Optional[float] = None

    font_name: Optional[str] = None
    font_size: Optional[int] = None

    # Upload opcional (compatibilidade)
    logo_base64: Optional[str] = None
    logo_filename: Optional[str] = None  # mantido (não usado aqui; salvamos como logo.png)

    # NOVO (3.2.8): URL pública oficial para verificação (ex.: https://verifica.prefeitura.gov.br)
    public_base_url: Optional[str] = None


class LogoUpload(BaseModel):
    municipio_id: Optional[int] = None
    logo_base64: str
    logo_filename: Optional[str] = None


# =========================================================
# Endpoints
# =========================================================

@router.get("", dependencies=[Depends(exigir_minimo_perfil("operador"))])
def get_branding(
    municipio_id: Optional[int] = Query(default=None),
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    mid = _resolver_municipio(usuario, municipio_id)
    branding = session.exec(
        select(MunicipioBranding).where(MunicipioBranding.municipio_id == mid)
    ).first()
    if not branding:
        branding = MunicipioBranding(municipio_id=mid)

    data = branding.model_dump()
    data["public_base_url"] = _read_public_base_url(mid)
    return data


@router.post("", dependencies=[Depends(exigir_minimo_perfil("coord_municipal"))])
def upsert_branding(
    payload: BrandingUpsert,
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    mid = _resolver_municipio(usuario, payload.municipio_id)

    branding = session.exec(
        select(MunicipioBranding).where(MunicipioBranding.municipio_id == mid)
    ).first()

    now = _now_utc_naive()
    if not branding:
        branding = MunicipioBranding(municipio_id=mid, criado_em=now, atualizado_em=now)
        session.add(branding)

    for field in (
        "nome_instituicao",
        "header_text",
        "footer_text",
        "margin_top_mm",
        "margin_bottom_mm",
        "margin_left_mm",
        "margin_right_mm",
        "logo_width_mm",
        "logo_height_mm",
        "font_name",
        "font_size",
    ):
        v = getattr(payload, field, None)
        if v is not None:
            setattr(branding, field, v)

    # Logo via upsert (compat)
    if payload.logo_base64:
        raw = _decode_logo_base64(payload.logo_base64)
        branding.logo_path = _save_logo_png(mid, raw)

    # NOVO: base URL pública
    _write_public_base_url(mid, payload.public_base_url)

    branding.atualizado_em = now
    session.add(branding)
    session.commit()
    session.refresh(branding)

    data = branding.model_dump()
    data["public_base_url"] = _read_public_base_url(mid)
    return data


@router.post("/logo", dependencies=[Depends(exigir_minimo_perfil("coord_municipal"))])
def upload_logo(
    payload: LogoUpload,
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    mid = _resolver_municipio(usuario, payload.municipio_id)

    branding = session.exec(
        select(MunicipioBranding).where(MunicipioBranding.municipio_id == mid)
    ).first()

    now = _now_utc_naive()
    if not branding:
        branding = MunicipioBranding(municipio_id=mid, criado_em=now, atualizado_em=now)
        session.add(branding)

    raw = _decode_logo_base64(payload.logo_base64)
    branding.logo_path = _save_logo_png(mid, raw)

    branding.atualizado_em = now
    session.add(branding)
    session.commit()
    session.refresh(branding)

    data = branding.model_dump()
    data["public_base_url"] = _read_public_base_url(mid)
    return data
