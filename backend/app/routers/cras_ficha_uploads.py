from __future__ import annotations

import os
import uuid
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlmodel import Session, select

from app.core.db import get_session
from app.core.auth import get_current_user, pode_acesso_global
from app.models.usuario import Usuario
from app.models.pessoa_suas import PessoaSUAS
from app.models.familia_suas import FamiliaSUAS
from app.models.ficha_anexo import FichaAnexo

router = APIRouter(prefix="/cras/ficha", tags=["cras-ficha-uploads"])

UPLOAD_ROOT = Path(os.getenv("UPLOAD_ROOT", "uploads")).resolve()

def _mun_id(usuario: Usuario) -> Optional[int]:
    mid = getattr(usuario, "municipio_id", None)
    return int(mid) if mid is not None else None

def _check_municipio(usuario: Usuario, municipio_id: int) -> None:
    if pode_acesso_global(usuario):
        return
    um = _mun_id(usuario)
    if um is None or int(municipio_id) != int(um):
        raise HTTPException(status_code=403, detail="Acesso negado (município).")

@router.post("/uploads")
async def upload_anexo(
    alvo_tipo: str = Form(...),   # pessoa|familia
    alvo_id: int = Form(...),
    titulo: str = Form(...),
    tipo: Optional[str] = Form(default=None),
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
) -> Dict[str, Any]:
    if alvo_tipo not in ("pessoa", "familia"):
        raise HTTPException(status_code=400, detail="alvo_tipo inválido (pessoa|familia).")

    # valida município pelo alvo
    if alvo_tipo == "pessoa":
        pe = session.get(PessoaSUAS, int(alvo_id))
        if not pe:
            raise HTTPException(status_code=404, detail="Pessoa não encontrada.")
        _check_municipio(usuario, int(pe.municipio_id))
        municipio_id = int(pe.municipio_id)
    else:
        fa = session.get(FamiliaSUAS, int(alvo_id))
        if not fa:
            raise HTTPException(status_code=404, detail="Família não encontrada.")
        _check_municipio(usuario, int(fa.municipio_id))
        municipio_id = int(fa.municipio_id)

    # salva local (MVP). Depois podemos trocar por MinIO/S3 mantendo a mesma API.
    ext = Path(file.filename or "").suffix.lower()
    safe_name = f"{uuid.uuid4().hex}{ext}"
    rel_dir = Path(str(municipio_id)) / alvo_tipo / str(alvo_id)
    abs_dir = (UPLOAD_ROOT / rel_dir)
    abs_dir.mkdir(parents=True, exist_ok=True)
    abs_path = abs_dir / safe_name

    content = await file.read()
    abs_path.write_bytes(content)

    url = f"/uploads/{rel_dir.as_posix()}/{safe_name}"

    an = FichaAnexo(
        municipio_id=municipio_id,
        alvo_tipo=alvo_tipo,
        alvo_id=int(alvo_id),
        titulo=titulo.strip(),
        url=url,
        tipo=tipo,
        criado_por_usuario_id=getattr(usuario, "id", None),
        criado_por_nome=getattr(usuario, "nome", None),
    )
    session.add(an)
    session.commit()
    session.refresh(an)

    return {"ok": True, "anexo": an}
