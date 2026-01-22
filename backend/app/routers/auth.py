# app/routers/auth.py
from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import func
from sqlmodel import Session, select

from app.core.db import DATABASE_URL, get_session
from app.core.security import verificar_senha, criar_token_acesso, decodificar_token
from app.models.usuario import Usuario, UsuarioRead

router = APIRouter(prefix="/auth", tags=["auth"])

# Para /auth/me (Bearer)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def _to_dict(obj: Any) -> Dict[str, Any]:
    """Compatível com Pydantic v1/v2 e SQLModel."""
    if obj is None:
        return {}
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    if hasattr(obj, "dict"):
        return obj.dict()
    return dict(obj)


def _debug_enabled() -> bool:
    return (os.getenv("POPRUA_DEBUG_DIAGNOSTICO", "").strip().lower() in {"1", "true", "yes"})


def _sqlite_file_from_url(url: str) -> Optional[str]:
    if not url.startswith("sqlite"):
        return None
    # sqlite:///relative.db  OR sqlite:////abs/path.db
    if "sqlite:///" in url:
        path_part = url.split("sqlite:///", 1)[1]
        # Se vier relativo, tentamos ancorar no diretório do backend (app/.. -> backend)
        if not path_part.startswith("/"):
            backend_dir = Path(__file__).resolve().parents[2]  # app/routers -> app -> backend
            return str((backend_dir / path_part).resolve())
        return path_part
    return None


def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: Session = Depends(get_session),
) -> Usuario:
    """Valida o JWT e retorna o usuário do banco."""
    try:
        payload = decodificar_token(token)
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Token inválido.")
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado.")

    usuario = session.get(Usuario, int(user_id))
    if not usuario or not getattr(usuario, "ativo", True):
        raise HTTPException(status_code=401, detail="Usuário inválido/inativo.")
    return usuario


@router.post("/login")
async def login(
    request: Request,
    session: Session = Depends(get_session),
):
    """Login (aceita form OU JSON).

    - Form (padrão OAuth2): username/email + password
    - JSON (fallback): {"username"|"email": ..., "password"|"senha": ...}

    Isso evita 422 quando o front manda JSON e o backend esperava form.
    """

    content_type = (request.headers.get("content-type") or "").lower()
    email = ""
    senha = ""

    try:
        if "application/json" in content_type:
            data = await request.json()
            if isinstance(data, dict):
                email = str(data.get("username") or data.get("email") or "").strip().lower()
                senha = str(data.get("password") or data.get("senha") or "").strip()
        else:
            form = await request.form()
            email = str(form.get("username") or form.get("email") or "").strip().lower()
            senha = str(form.get("password") or form.get("senha") or "").strip()
    except Exception:
        # fallback simples
        pass

    if not email or not senha:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Informe username/email e password/senha.",
        )

    stmt = select(Usuario).where(Usuario.email == email)
    usuario = session.exec(stmt).first()

    if not usuario or not getattr(usuario, "ativo", True):
        if _debug_enabled():
            print(f"[auth] login falhou: usuário inexistente/inativo ({email})")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário ou senha inválidos.",
        )

    if not verificar_senha(senha, usuario.senha_hash):
        if _debug_enabled():
            print(f"[auth] login falhou: senha inválida ({email})")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário ou senha inválidos.",
        )

    usuario_read = UsuarioRead(
        id=usuario.id,
        nome=usuario.nome,
        email=usuario.email,
        perfil=usuario.perfil,
        municipio_id=usuario.municipio_id,
        ativo=usuario.ativo,
    )

    access_token = criar_token_acesso(usuario_read)

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "usuario": _to_dict(usuario_read),
    }


@router.get("/me")
def me(usuario: Usuario = Depends(get_current_user)):
    usuario_read = UsuarioRead(
        id=usuario.id,
        nome=usuario.nome,
        email=usuario.email,
        perfil=usuario.perfil,
        municipio_id=usuario.municipio_id,
        ativo=usuario.ativo,
    )
    return _to_dict(usuario_read)


@router.get("/diagnostico")
def diagnostico(session: Session = Depends(get_session)):
    """Diagnóstico de login (somente em modo debug).

    Ative com:
      export POPRUA_DEBUG_DIAGNOSTICO=true

    Retorna apenas sinais básicos para descobrir:
    - se você está apontando para o banco correto
    - se existe usuário admin
    """

    if not _debug_enabled():
        raise HTTPException(status_code=404, detail="Not Found")

    total_users = session.exec(select(func.count(Usuario.id))).one()
    admin = session.exec(select(Usuario.id).where(Usuario.email == "admin@poprua.local")).first()

    sqlite_file = _sqlite_file_from_url(DATABASE_URL)
    sqlite_exists = Path(sqlite_file).exists() if sqlite_file else None

    return {
        "database_url": DATABASE_URL,
        "sqlite_file": sqlite_file,
        "sqlite_exists": sqlite_exists,
        "usuarios_total": int(total_users or 0),
        "admin_exists": bool(admin),
        "hint": "Se admin_exists=false: rode backend/app/seed_usuarios.py. Se admin_exists=true mas senha falha: rode backend/app/reset_senhas.py.",
    }
