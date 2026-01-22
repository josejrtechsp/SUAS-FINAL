from __future__ import annotations

from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from sqlalchemy import or_

from app.core.db import get_session
from app.core.auth import get_current_user, pode_acesso_global, nivel_perfil
from app.models.usuario import Usuario
from app.models.pessoa import PessoaRua
from app.models.acolhimento import Acolhimento, AcolhimentoBase

router = APIRouter(prefix="/pessoas", tags=["acolhimentos"])  # aparece como "acolhimentos" na docs

# Permissão:
# - recepcao/leitura/tecnico/operador/coord... podem VER
# - tecnico/operador/coord... podem CRIAR/EDITAR
NIVEL_VER = max(nivel_perfil("recepcao"), nivel_perfil("leitura"), 1)
NIVEL_OPERAR = max(nivel_perfil("tecnico"), nivel_perfil("operador"), 10)


def _dump(obj: Any) -> dict:
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    if hasattr(obj, "dict"):
        return obj.dict()
    return dict(obj)


def _exigir_nivel(usuario: Usuario, minimo: int, *, acao: str) -> None:
    if int(nivel_perfil(getattr(usuario, "perfil", None))) < int(minimo):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Acesso negado: perfil sem permissão para {acao}.",
        )


def _filtro_municipio_stmt(stmt, usuario: Usuario, pessoa: Optional[PessoaRua] = None):
    """Restringe por município quando não for acesso global."""
    if pode_acesso_global(usuario):
        return stmt

    user_mun = getattr(usuario, "municipio_id", None)
    if user_mun is None:
        raise HTTPException(status_code=403, detail="Usuário sem município associado.")

    # regra segura: só registros do município do usuário.
    # fallback: se municipio_id estiver NULL, permite apenas se pessoa.municipio_origem_id == user_mun
    if pessoa is not None:
        return stmt.where(
            or_(
                Acolhimento.municipio_id == int(user_mun),
                (Acolhimento.municipio_id == None) & (pessoa.municipio_origem_id == int(user_mun)),  # noqa: E711
            )
        )

    return stmt.where(Acolhimento.municipio_id == int(user_mun))


@router.get("/{pessoa_id}/acolhimentos", response_model=List[Acolhimento])
def listar_acolhimentos_da_pessoa(
    pessoa_id: int,
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    """Lista o histórico de acolhimentos de uma pessoa.

    Para não quebrar o front, se a pessoa não existir, devolve lista vazia.
    """
    _exigir_nivel(usuario, NIVEL_VER, acao="listar acolhimentos")

    pessoa = session.get(PessoaRua, pessoa_id)
    if not pessoa:
        return []

    stmt = (
        select(Acolhimento)
        .where(Acolhimento.pessoa_id == pessoa_id)
        .order_by(Acolhimento.data_entrada.desc())
    )
    stmt = _filtro_municipio_stmt(stmt, usuario, pessoa)

    resultados = session.exec(stmt).all()
    return list(resultados)


@router.post("/{pessoa_id}/acolhimentos", response_model=Acolhimento, status_code=status.HTTP_201_CREATED)
def criar_acolhimento_para_pessoa(
    pessoa_id: int,
    dados: AcolhimentoBase,
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    """Registra uma nova entrada em serviço de acolhimento.

    - exige token
    - se não for acesso global, força municipio_id = usuario.municipio_id
    - evita Acolhimento.from_orm (pydantic v2) e usa payload dict
    """
    _exigir_nivel(usuario, NIVEL_OPERAR, acao="criar acolhimento")

    pessoa = session.get(PessoaRua, pessoa_id)
    if not pessoa:
        raise HTTPException(status_code=404, detail="Pessoa em situação de rua não encontrada.")

    payload = _dump(dados)

    # Controle por município
    if not pode_acesso_global(usuario):
        user_mun = getattr(usuario, "municipio_id", None)
        if user_mun is None:
            raise HTTPException(status_code=403, detail="Usuário sem município associado.")
        payload["municipio_id"] = int(user_mun)
    else:
        # global: se não vier municipio_id, tenta usar o do usuário (se existir)
        if payload.get("municipio_id") is None and getattr(usuario, "municipio_id", None) is not None:
            payload["municipio_id"] = int(usuario.municipio_id)

    acolhimento = Acolhimento(**payload)
    acolhimento.pessoa_id = pessoa_id

    session.add(acolhimento)
    session.commit()
    session.refresh(acolhimento)

    return acolhimento


@router.patch("/{pessoa_id}/acolhimentos/{acolhimento_id}", response_model=Acolhimento)
def atualizar_acolhimento_da_pessoa(
    pessoa_id: int,
    acolhimento_id: int,
    payload: dict,
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    """Atualiza um acolhimento (normalmente para registrar a saída).

    Restrições:
    - exige token
    - municipal não pode alterar municipio_id
    - municipal só altera registros do seu município
    """
    _exigir_nivel(usuario, NIVEL_OPERAR, acao="atualizar acolhimento")

    pessoa = session.get(PessoaRua, pessoa_id)
    if not pessoa:
        raise HTTPException(status_code=404, detail="Pessoa em situação de rua não encontrada.")

    acolhimento = session.get(Acolhimento, acolhimento_id)
    if not acolhimento or acolhimento.pessoa_id != pessoa_id:
        raise HTTPException(status_code=404, detail="Acolhimento não encontrado para esta pessoa.")

    # controle por município
    if not pode_acesso_global(usuario):
        user_mun = getattr(usuario, "municipio_id", None)
        if user_mun is None:
            raise HTTPException(status_code=403, detail="Usuário sem município associado.")
        acol_mun = getattr(acolhimento, "municipio_id", None)
        if acol_mun is not None and int(acol_mun) != int(user_mun):
            raise HTTPException(status_code=403, detail="Acesso negado: acolhimento fora do seu município.")

    campos_permitidos = {
        "data_saida",
        "motivo_saida",
        "destino_pos_saida",
        "observacoes",
        "tipo_servico",
        "tipo_vaga",
        "unidade_nome",
        "data_entrada",
    }

    # municipio_id: apenas global
    if pode_acesso_global(usuario) and "municipio_id" in payload:
        campos_permitidos.add("municipio_id")

    for campo, valor in (payload or {}).items():
        if campo in campos_permitidos:
            setattr(acolhimento, campo, valor)

    session.add(acolhimento)
    session.commit()
    session.refresh(acolhimento)

    return acolhimento
