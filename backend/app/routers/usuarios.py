from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select

from app.core.auth import exigir_minimo_perfil, get_current_user, pode_acesso_global
from app.core.db import get_session
from app.models.usuario import Usuario


router = APIRouter(prefix="/usuarios", tags=["Usuários"])


def _user_municipio_id(usuario: Usuario) -> Optional[int]:
    mid = getattr(usuario, "municipio_id", None)
    return int(mid) if mid is not None else None


@router.get("", dependencies=[Depends(exigir_minimo_perfil("operador"))])
def listar_usuarios(
    municipio_id: Optional[int] = Query(default=None, description="(Opcional) Admin/consórcio pode filtrar por município."),
    ativo: Optional[bool] = Query(default=True, description="Filtra usuários ativos (default=true)."),
    incluir_email: bool = Query(default=False, description="Se true, inclui e-mail (para telas internas)."),
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
) -> List[Dict[str, Any]]:
    """Lista usuários para seleção em telas (tarefas/PIA etc.).

    Regras:
    - Usuário municipal: só vê usuários do seu município.
    - Usuário global (admin/gestor_consorcio): pode ver todos ou filtrar por municipio_id.
    """

    mid: Optional[int] = None
    if pode_acesso_global(usuario):
        if municipio_id is not None:
            mid = int(municipio_id)
    else:
        mid = _user_municipio_id(usuario)
        if mid is None:
            raise HTTPException(status_code=403, detail="Usuário sem município associado")
        if municipio_id is not None and int(municipio_id) != int(mid):
            raise HTTPException(status_code=403, detail="Sem permissão para listar usuários de outro município")

    stmt = select(Usuario)
    if ativo is not None:
        stmt = stmt.where(Usuario.ativo == bool(ativo))
    if mid is not None:
        stmt = stmt.where(Usuario.municipio_id == int(mid))

    rows = session.exec(stmt.order_by(Usuario.nome)).all()

    out: List[Dict[str, Any]] = []
    for u in rows:
        d: Dict[str, Any] = {
            "id": getattr(u, "id", None),
            "nome": getattr(u, "nome", None),
            "perfil": getattr(u, "perfil", None),
            "municipio_id": getattr(u, "municipio_id", None),
            "ativo": getattr(u, "ativo", None),
        }
        if incluir_email:
            d["email"] = getattr(u, "email", None)
        out.append(d)
    return out
