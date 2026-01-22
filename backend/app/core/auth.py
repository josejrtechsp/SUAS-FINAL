# app/core/auth.py

from typing import Any, Callable, Dict, Optional, Set, Union

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session

from app.core.db import get_session
from app.core.security import decodificar_token
from app.models.usuario import Usuario

# URL do endpoint de login (tokenUrl) – bate com /auth/login
# auto_error=False => a gente consegue devolver mensagens mais claras
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)

# =========================================================
# RBAC (Hierarquia de perfis)
# =========================================================
# Quanto MAIOR o número, MAIOR a permissão.
# Ajuste os nomes se no seu banco estiver diferente.
PERFIL_NIVEL: Dict[str, int] = {
    "recepcao": 7,
    "leitura": 8,
    "tecnico": 10,
    "operador": 10,
    "saude": 15,
    "financeiro": 15,
    "beneficios": 15,
    "coord_municipal": 20,
    "gestor": 20,
    "secretario": 22,
    "saude_coord": 25,
    "gestor_consorcio": 30,
    "admin": 40,
}

# Perfis que podem “ver tudo” (acesso global a municípios)
PERFIS_ACESSO_GLOBAL: Set[str] = {"gestor_consorcio", "admin"}

# Somente o perfil máximo vê “tudo” (LGPD: dados completos/sensíveis)
PERFIL_MAXIMO: str = "admin"


def normalizar_perfil(perfil: Optional[str]) -> str:
    """
    Normaliza o perfil para evitar erros por maiúsculas, espaços, etc.
    """
    if not perfil:
        return ""
    return str(perfil).strip().lower()


def nivel_perfil(perfil: Optional[str]) -> int:
    """
    Retorna o nível numérico do perfil; desconhecido => 0.
    """
    return PERFIL_NIVEL.get(normalizar_perfil(perfil), 0)


def perfil_eh_maximo(perfil: Optional[str]) -> bool:
    """
    True somente para o perfil máximo (admin).
    """
    return normalizar_perfil(perfil) == PERFIL_MAXIMO


def pode_acesso_global(usuario: Usuario) -> bool:
    """
    True se o usuário pode acessar dados de qualquer município.
    """
    return normalizar_perfil(getattr(usuario, "perfil", None)) in PERFIS_ACESSO_GLOBAL


# =========================================================
# Auth: usuário atual via JWT
# =========================================================
def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    session: Session = Depends(get_session),
) -> Usuario:
    """
    Recupera o usuário atual a partir do token JWT (Bearer).
    Lança 401 se o token estiver ausente, inválido ou expirado.
    """

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de autenticação não fornecido. Faça login novamente.",
        )

    try:
        payload = decodificar_token(token)
        sub = payload.get("sub")
        if sub is None:
            raise ValueError("Token sem 'sub' (id do usuário).")
        user_id = int(sub)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado. Faça login novamente.",
        )

    usuario = session.get(Usuario, user_id)
    if not usuario or not getattr(usuario, "ativo", False):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário não encontrado ou inativo.",
        )

    return usuario


# =========================================================
# Dependências de autorização (RBAC)
# =========================================================
def exigir_minimo_perfil(min_perfil: str) -> Callable[[Usuario], Usuario]:
    """
    Exige que o usuário logado tenha, no mínimo, um determinado perfil.
    Ex:
      @router.get("/alguma-rota", dependencies=[Depends(exigir_minimo_perfil("gestor_consorcio"))])
    """

    min_nivel = nivel_perfil(min_perfil)

    def _dep(usuario: Usuario = Depends(get_current_user)) -> Usuario:
        user_nivel = nivel_perfil(getattr(usuario, "perfil", None))
        if user_nivel < min_nivel:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Acesso negado: permissão insuficiente para esta operação.",
            )
        return usuario

    return _dep


def exigir_perfis(*perfis: str) -> Callable[[Usuario], Usuario]:
    """
    Exige que o usuário esteja em um dos perfis informados.
    Ex:
      dependencies=[Depends(exigir_perfis("admin", "gestor_consorcio"))]
    """
    permitidos = {normalizar_perfil(p) for p in perfis if p}

    def _dep(usuario: Usuario = Depends(get_current_user)) -> Usuario:
        p = normalizar_perfil(getattr(usuario, "perfil", None))
        if p not in permitidos:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Acesso negado: perfil não autorizado.",
            )
        return usuario

    return _dep


def exigir_municipio_ou_global(
    municipio_id: int,
    usuario: Usuario = Depends(get_current_user),
) -> Usuario:
    """
    LGPD + Governança:
    - Operador/coord municipal só podem acessar recursos do seu município.
    - Gestor consórcio/admin podem acessar qualquer município.

    Use em rotas que tenham municipio_id (path ou query) como parâmetro.
    """
    if pode_acesso_global(usuario):
        return usuario

    user_mun = getattr(usuario, "municipio_id", None)
    if user_mun is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado: usuário sem município associado.",
        )

    try:
        if int(user_mun) != int(municipio_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Acesso negado: município não corresponde ao usuário logado.",
            )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado: município inválido.",
        )

    return usuario


# =========================================================
# LGPD: Redação/Mascaramento de dados antes de devolver
# =========================================================
REDACTION_TEXT = "🔒 Restrito (LGPD)"


def _redigir_valor(valor: Any) -> Any:
    """
    Mantém o tipo o mais seguro possível:
    - se for texto => troca por placeholder
    - se for número/bool => vira None
    - se for None => None
    """
    if valor is None:
        return None
    if isinstance(valor, (int, float, bool)):
        return None
    return REDACTION_TEXT


def _to_dict(obj: Any) -> Dict[str, Any]:
    """
    Converte SQLModel/Pydantic/objeto em dict (quando possível).
    """
    if isinstance(obj, dict):
        return dict(obj)

    # Pydantic v1
    if hasattr(obj, "dict") and callable(getattr(obj, "dict")):
        try:
            return obj.dict()
        except Exception:
            pass

    # Pydantic v2
    if hasattr(obj, "model_dump") and callable(getattr(obj, "model_dump")):
        try:
            return obj.model_dump()
        except Exception:
            pass

    # fallback
    try:
        return dict(obj)
    except Exception:
        return {"value": obj}


def filtrar_dados_lgpd(
    dados: Union[Dict[str, Any], Any],
    usuario: Usuario,
    recurso: str = "geral",
) -> Dict[str, Any]:
    """
    Aplica “minimização” e “redação” (LGPD) conforme o perfil.

    Regra base (segura):
    - Somente ADMIN (perfil máximo) vê dados completos.
    - Outros perfis recebem dados com campos sensíveis mascarados.

    O parâmetro `recurso` ajuda a escolher quais campos redigir:
      - "pessoa"
      - "atendimento"
      - "caso"
      - "geral"
    """
    data = _to_dict(dados)

    # Admin vê tudo
    if perfil_eh_maximo(getattr(usuario, "perfil", None)):
        return data

    # Lista base de campos potencialmente sensíveis (PII + sensíveis + texto livre)
    campos_pii = {
        "cpf",
        "rg",
        "email",
        "telefone",
        "celular",
        "data_nascimento",
        "nome_civil",
        "nome_mae",
        "nome_pai",
        "endereco",
        "logradouro",
        "numero",
        "bairro",
        "cep",
    }

    # Campos de texto livre que frequentemente carregam informação sensível
    campos_texto_livre = {
        "descricao",
        "descricao_completa",
        "observacoes",
        "observacoes_gerais",
        "relato",
        "anotacoes",
        "diagnostico",
        "pia",
        "saude",
        "uso_substancias",
        "encaminhamentos",
        "encaminhamentos_realizados",
    }

    # Regras por tipo de recurso (mais preciso)
    if recurso == "pessoa":
        # Para pessoa: protege PII forte; mantém nome_social (usualmente necessário para operação)
        campos_para_redigir = campos_pii.union({"nome_civil"})
    elif recurso == "atendimento":
        # Para atendimento: texto livre quase sempre tem informação sensível => redigir
        campos_para_redigir = campos_texto_livre.union(campos_pii)
    elif recurso == "caso":
        # Caso: observações e campos livres => redigir
        campos_para_redigir = campos_texto_livre.union(campos_pii)
    else:
        campos_para_redigir = campos_texto_livre.union(campos_pii)

    # Aplicação da redação
    for chave in campos_para_redigir:
        if chave in data:
            data[chave] = _redigir_valor(data.get(chave))

    # Opcional: se for operador, podemos reduzir ainda mais o detalhe
    if normalizar_perfil(getattr(usuario, "perfil", None)) == "operador":
        # Mantém apenas um conjunto mínimo útil para operação
        # (ajuste se quiser deixar ainda mais restrito)
        permitidos_minimos = {
            "id",
            "pessoa_id",
            "caso_id",
            "municipio_id",
            "data_atendimento",
            "tipo_atendimento",
            "resultado",
            "status",
            "etapa_atual",
            "equipamento",
            "local_atendimento",
            "nome_social",
            "nome",  # caso algum model use "nome"
        }
        data = {k: v for k, v in data.items() if k in permitidos_minimos or k.endswith("_id")}

    return data