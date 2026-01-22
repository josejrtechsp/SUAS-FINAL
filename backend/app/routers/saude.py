# app/routers/saude.py
from __future__ import annotations

from datetime import datetime
from typing import Optional, List, Dict, Any
import json
import re

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session, select

from app.core.db import get_session
from app.core.security import decodificar_token
from app.models.usuario import Usuario
from app.models.caso_pop_rua import CasoPopRua
from app.models.saude_intersetorial import SaudeIntersetorialRegistro

router = APIRouter(prefix="/saude", tags=["saude"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# ============================
# Auth
# ============================
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


def _is_admin_or_consorcio(usuario: Usuario) -> bool:
    p = (getattr(usuario, "perfil", "") or "").lower()
    return p in ("admin", "gestor_consorcio")


def _agora() -> datetime:
    return datetime.utcnow()


def _validar_acesso_ao_caso(session: Session, usuario: Usuario, caso_id: int) -> CasoPopRua:
    caso = session.get(CasoPopRua, caso_id)
    if not caso:
        raise HTTPException(status_code=404, detail="Caso não encontrado.")

    if _is_admin_or_consorcio(usuario):
        return caso

    muni_user = getattr(usuario, "municipio_id", None)
    if muni_user is None:
        raise HTTPException(status_code=403, detail="Usuário sem município associado.")

    # caso precisa ter municipio_id (no seu model tem)
    if getattr(caso, "municipio_id", None) is not None and int(caso.municipio_id) != int(muni_user):
        raise HTTPException(status_code=403, detail="Sem permissão para acessar este caso.")

    return caso


# ============================
# LGPD: bloqueios (intersetorial não pode virar prontuário clínico)
# ============================
BLOQUEIO_REGEX = re.compile(
    r"\b("
    r"cid|dsm|diagn[oó]st|sorolog|viral|carga\s*viral|exame|laudo|"
    r"hiv|aids|hepatite|tubercul|hanseni|ist|dst|sífilis|gonorreia|"
    r"psiquiat|suic[ií]d|autoagress|"
    r"medica[cç][aã]o|posologia|dose|receita"
    r")\b",
    re.IGNORECASE,
)

# Campos PERMITIDOS (mínimo necessário)
ALLOWED_KEYS_INTERSETORIAL = {
    # triagem / necessidade
    "necessita_avaliacao",          # bool
    "prioridade",                   # "rotina" | "urgente"
    "alerta_operacional",           # bool (sem explicar causa clínica)
    "alergia_grave",                # bool | null (sem detalhar)

    # encaminhamento
    "servico_tipo",                 # "UBS"|"UPA"|"CAPS"|"ConsultorioRua"|"SAMU"|"Hospital"|"Outro"
    "servico_nome",                 # texto curto
    "data_hora",                    # ISO string
    "status_encaminhamento",        # "pendente"|"agendado"|"compareceu"|"nao_compareceu"|"concluido"|"cancelado"

    # funcionalidade (sem causa)
    "restricoes_funcionais",        # lista: ["locomocao","comunicacao","visual","auditiva","autocuidado"]

    # texto operacional curto (sem clínica)
    "observacao_operacional",       # texto curto (logístico)
}

ALLOWED_STATUS = {"pendente", "agendado", "compareceu", "nao_compareceu", "concluido", "cancelado"}
ALLOWED_PRIORIDADE = {"rotina", "urgente"}

ALLOWED_RESTRICOES = {"locomocao", "comunicacao", "visual", "auditiva", "autocuidado"}

ALLOWED_SERVICO_TIPO = {"UBS", "UPA", "CAPS", "ConsultorioRua", "SAMU", "Hospital", "Outro"}


def _scan_text_for_blocked(value: Any) -> None:
    if value is None:
        return
    if isinstance(value, str):
        if BLOQUEIO_REGEX.search(value):
            raise HTTPException(
                status_code=400,
                detail="Conteúdo clínico/sensível detectado. No módulo SAÚDE (INTERSETORIAL) só é permitido o mínimo operacional (LGPD).",
            )
    elif isinstance(value, list):
        for v in value:
            _scan_text_for_blocked(v)
    elif isinstance(value, dict):
        for _, v in value.items():
            _scan_text_for_blocked(v)


def _sanitizar_payload_intersetorial(payload: Dict[str, Any]) -> Dict[str, Any]:
    # remove chaves não permitidas
    clean: Dict[str, Any] = {}
    for k, v in (payload or {}).items():
        if k in ALLOWED_KEYS_INTERSETORIAL:
            clean[k] = v

    # validações básicas
    prioridade = clean.get("prioridade")
    if prioridade and str(prioridade) not in ALLOWED_PRIORIDADE:
        raise HTTPException(status_code=400, detail="prioridade inválida (use: rotina | urgente).")

    st = clean.get("status_encaminhamento")
    if st and str(st) not in ALLOWED_STATUS:
        raise HTTPException(status_code=400, detail="status_encaminhamento inválido.")

    serv = clean.get("servico_tipo")
    if serv and str(serv) not in ALLOWED_SERVICO_TIPO:
        raise HTTPException(status_code=400, detail="servico_tipo inválido.")

    # restrições
    rf = clean.get("restricoes_funcionais")
    if rf is not None:
        if not isinstance(rf, list):
            raise HTTPException(status_code=400, detail="restricoes_funcionais deve ser uma lista.")
        for x in rf:
            if str(x) not in ALLOWED_RESTRICOES:
                raise HTTPException(status_code=400, detail=f"restricao inválida: {x}")

    # texto livre: curto
    obs = clean.get("observacao_operacional")
    if obs is not None:
        obs = str(obs).strip()
        if len(obs) > 280:
            raise HTTPException(status_code=400, detail="observacao_operacional deve ter no máximo 280 caracteres.")
        clean["observacao_operacional"] = obs or None

    # scan anti-clínico
    _scan_text_for_blocked(clean)

    return clean


def _to_dict(r: SaudeIntersetorialRegistro) -> dict:
    return {
        "id": r.id,
        "caso_id": r.caso_id,
        "criado_em": r.criado_em.isoformat() if r.criado_em else None,
        "criado_por_user_id": r.criado_por_user_id,
        "criado_por_nome": r.criado_por_nome,
        "tipo_registro": r.tipo_registro,
        "payload": r.payload_dict(),
    }


# ============================
# Endpoints
# ============================

@router.get("/etapas")
def etapas_saude(usuario: Usuario = Depends(get_current_user)):
    """
    Metadados para o front (dropdowns/validação).
    """
    return {
        "prioridades": sorted(list(ALLOWED_PRIORIDADE)),
        "status_encaminhamento": sorted(list(ALLOWED_STATUS)),
        "servico_tipo": sorted(list(ALLOWED_SERVICO_TIPO)),
        "restricoes_funcionais": sorted(list(ALLOWED_RESTRICOES)),
        "campos_permitidos": sorted(list(ALLOWED_KEYS_INTERSETORIAL)),
    }


@router.get("/casos/{caso_id}/intersetorial")
def listar_intersetorial(
    caso_id: int,
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    _validar_acesso_ao_caso(session, usuario, caso_id)

    stmt = (
        select(SaudeIntersetorialRegistro)
        .where(SaudeIntersetorialRegistro.caso_id == caso_id)
        .order_by(SaudeIntersetorialRegistro.id.desc())
    )
    itens = session.exec(stmt).all()
    return [_to_dict(x) for x in itens]


@router.post("/casos/{caso_id}/intersetorial", status_code=201)
def criar_intersetorial(
    caso_id: int,
    payload: dict,
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    _validar_acesso_ao_caso(session, usuario, caso_id)

    clean = _sanitizar_payload_intersetorial(payload or {})
    if not clean:
        raise HTTPException(status_code=400, detail="Payload vazio. Informe ao menos um campo permitido (intersetorial).")

    reg = SaudeIntersetorialRegistro(
        caso_id=caso_id,
        criado_em=_agora(),
        criado_por_user_id=getattr(usuario, "id", None),
        criado_por_nome=getattr(usuario, "nome", None),
        tipo_registro="intersetorial",
        payload_json=json.dumps(clean, ensure_ascii=False),
    )
    session.add(reg)
    session.commit()
    session.refresh(reg)
    return _to_dict(reg)


@router.post("/casos/{caso_id}/intersetorial/status", status_code=201)
def registrar_status_intersetorial(
    caso_id: int,
    payload: dict,
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    """
    Registra mudança de status como EVENTO (não sobrescreve) para manter rastreabilidade.
    Body:
      - status_encaminhamento (obrigatório)
      - observacao_operacional (opcional)
    """
    _validar_acesso_ao_caso(session, usuario, caso_id)

    st = (payload or {}).get("status_encaminhamento")
    if not st or str(st) not in ALLOWED_STATUS:
        raise HTTPException(status_code=400, detail="status_encaminhamento inválido/obrigatório.")

    obs = (payload or {}).get("observacao_operacional")
    pack = {"status_encaminhamento": str(st)}
    if obs is not None:
        pack["observacao_operacional"] = str(obs).strip()[:280]

    _scan_text_for_blocked(pack)

    reg = SaudeIntersetorialRegistro(
        caso_id=caso_id,
        criado_em=_agora(),
        criado_por_user_id=getattr(usuario, "id", None),
        criado_por_nome=getattr(usuario, "nome", None),
        tipo_registro="status",
        payload_json=json.dumps(pack, ensure_ascii=False),
    )
    session.add(reg)
    session.commit()
    session.refresh(reg)
    return _to_dict(reg)