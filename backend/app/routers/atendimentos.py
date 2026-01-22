from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.core.db import get_session
from app.core.auth import get_current_user, pode_acesso_global, perfil_eh_maximo
from app.models.usuario import Usuario
from app.models.atendimento import Atendimento, AtendimentoBase
from app.models.pessoa import PessoaRua

router = APIRouter(prefix="/pessoas", tags=["atendimentos"])

# Texto padrão para mascarar campos sensíveis (LGPD)
REDACTION_TEXT = "🔒 Restrito (LGPD)"

# Campos que normalmente carregam informação sensível (principalmente texto livre)
# Obs: colocamos vários nomes possíveis pra funcionar mesmo se seu model tiver variações.
CAMPOS_SENSIVEIS_ATENDIMENTO = {
    "descricao",
    "descricao_resumida",
    "descricao_completa",
    "relato",
    "anotacoes",
    "observacoes",
    "observacoes_gerais",
    "diagnostico",
    "pia",
    "saude",
    "uso_substancias",
    "encaminhamentos",
    "encaminhamentos_realizados",
    "enc_saude",
    "enc_habitacao",
    "enc_trabalho",
    "enc_justica",
    "enc_outros",
    "profissional_responsavel",
    "servico_responsavel",
}


def _model_to_dict(obj: Any) -> Dict[str, Any]:
    """
    Converte SQLModel/Pydantic em dict (compatível com pydantic v1/v2).
    """
    if isinstance(obj, dict):
        return dict(obj)

    if hasattr(obj, "dict") and callable(getattr(obj, "dict")):
        return obj.dict()

    if hasattr(obj, "model_dump") and callable(getattr(obj, "model_dump")):
        return obj.model_dump()

    return dict(obj)


def _mascarar_atendimento_para_usuario(atendimento: Atendimento, usuario: Usuario) -> Dict[str, Any]:
    """
    Regra LGPD:
    - Somente ADMIN (perfil máximo) vê atendimento completo
    - Outros perfis recebem campos sensíveis mascarados
    """
    data = _model_to_dict(atendimento)

    # Admin vê tudo
    if perfil_eh_maximo(getattr(usuario, "perfil", None)):
        return data

    # Mascarar textos livres e outros campos sensíveis
    for campo in CAMPOS_SENSIVEIS_ATENDIMENTO:
        if campo in data and data[campo] not in (None, "", []):
            # Se for texto, substitui por placeholder.
            # Se não for texto, define como None (mais seguro).
            if isinstance(data[campo], str):
                data[campo] = REDACTION_TEXT
            else:
                data[campo] = None

    return data


@router.post("/{pessoa_id}/atendimentos", response_model=Atendimento, status_code=status.HTTP_201_CREATED)
def criar_atendimento(
    pessoa_id: int,
    dados: AtendimentoBase,
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    """
    Cria um atendimento para uma pessoa.

    Segurança/LGPD:
    - exige usuário logado (token)
    - se NÃO for perfil global, força municipio_id = usuario.municipio_id
    - só admin recebe o atendimento completo no retorno; demais recebem mascarado
    """

    # Confere se a pessoa existe
    pessoa = session.get(PessoaRua, pessoa_id)
    if not pessoa:
        raise HTTPException(status_code=404, detail="Pessoa não encontrada.")

    payload = _model_to_dict(dados)
    payload["pessoa_id"] = pessoa_id

    # Controle por município:
    # - Gestor consórcio/admin podem enviar municipio_id livremente
    # - Outros perfis: municipio_id vem do usuário logado (e sobrescreve o do frontend)
    if not pode_acesso_global(usuario):
        user_mun = getattr(usuario, "municipio_id", None)
        if user_mun is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Usuário sem município associado. Não é possível registrar atendimento.",
            )
        payload["municipio_id"] = int(user_mun)
    else:
        # Perfis globais: se não vier municipio_id, tenta usar o do usuário (se existir)
        if payload.get("municipio_id") is None and getattr(usuario, "municipio_id", None) is not None:
            payload["municipio_id"] = int(usuario.municipio_id)

    atendimento = Atendimento(**payload)

    session.add(atendimento)
    session.commit()
    session.refresh(atendimento)

    # LGPD: só admin vê completo
    if perfil_eh_maximo(getattr(usuario, "perfil", None)):
        return atendimento

    return _mascarar_atendimento_para_usuario(atendimento, usuario)


@router.get("/{pessoa_id}/atendimentos", response_model=List[Atendimento])
def listar_atendimentos(
    pessoa_id: int,
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    """
    Lista atendimentos de uma pessoa.

    Segurança/LGPD:
    - exige usuário logado (token)
    - se NÃO for perfil global, lista somente atendimentos do municipio_id do usuário
    - só admin recebe atendimento completo; demais recebem mascarado
    """

    # (Opcional, mas bom): confere se a pessoa existe
    pessoa = session.get(PessoaRua, pessoa_id)
    if not pessoa:
        raise HTTPException(status_code=404, detail="Pessoa não encontrada.")

    stmt = select(Atendimento).where(Atendimento.pessoa_id == pessoa_id)

    # Se não for perfil global, restringe por município
    if not pode_acesso_global(usuario):
        user_mun = getattr(usuario, "municipio_id", None)
        if user_mun is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Usuário sem município associado. Acesso negado.",
            )

        # Só adiciona esse filtro se o model realmente tiver municipio_id
        if hasattr(Atendimento, "municipio_id"):
            stmt = stmt.where(Atendimento.municipio_id == int(user_mun))

    resultados = list(session.exec(stmt))

    # Admin vê tudo
    if perfil_eh_maximo(getattr(usuario, "perfil", None)):
        return resultados

    # Outros perfis: mascarar
    return [_mascarar_atendimento_para_usuario(a, usuario) for a in resultados]