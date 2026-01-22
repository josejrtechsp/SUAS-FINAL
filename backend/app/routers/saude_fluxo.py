from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session, select

from app.core.db import get_session
from app.core.security import decodificar_token
from app.models.usuario import Usuario
from app.models.caso_pop_rua import CasoPopRua
from app.models.saude_fluxo import SaudeFluxoEvento

router = APIRouter(prefix="/casos", tags=["saude"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


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


# =========================
# “Metrô Saúde” (7 passos)
# =========================
PASSOS: List[Dict[str, Any]] = [
    {"codigo": "TRIAGEM", "ordem": 1, "nome": "Triagem", "descricao": "Necessita saúde? prioridade e motivo operacional."},
    {"codigo": "ENCAMINHAMENTO", "ordem": 2, "nome": "Encaminhamento", "descricao": "Serviço de saúde, unidade e data/hora do encaminhamento."},
    {"codigo": "ACEITE", "ordem": 3, "nome": "Aceite do serviço", "descricao": "Serviço confirma recebimento/aceite."},
    {"codigo": "AGENDAMENTO", "ordem": 4, "nome": "Agendamento", "descricao": "Data/hora/local de recepção."},
    {"codigo": "COMPARECIMENTO", "ordem": 5, "nome": "Comparecimento", "descricao": "Compareceu? sim/não/não se aplica."},
    {"codigo": "RETORNO", "ordem": 6, "nome": "Retorno", "descricao": "Precisa retorno? data/hora se sim."},
    {"codigo": "CONCLUSAO", "ordem": 7, "nome": "Conclusão", "descricao": "Concluído / interrompido / acompanhamento contínuo."},
]

ORDEM = [p["codigo"] for p in PASSOS]

# trava anti-vazamento (mínimo)
TERMOS_PROIBIDOS = [
    "cid", "dsm", "hiv", "aids", "tuberculose", "tb", "hepatite", "hanseniase"
]


def _agora() -> datetime:
    return datetime.utcnow()


def _idx(passo: Optional[str]) -> int:
    if not passo:
        return -1
    try:
        return ORDEM.index(passo)
    except ValueError:
        return -1


def _validar_texto_operacional(txt: Optional[str]) -> None:
    if not txt:
        return
    low = txt.lower()
    for t in TERMOS_PROIBIDOS:
        if t in low:
            raise HTTPException(
                status_code=400,
                detail="Não registre diagnóstico/CID/exame/medicação aqui. Use apenas informação operacional (intersetorial).",
            )


def _ultimo_passo(session: Session, caso_id: int) -> Optional[str]:
    stmt = (
        select(SaudeFluxoEvento)
        .where(SaudeFluxoEvento.caso_id == caso_id)
        .order_by(SaudeFluxoEvento.criado_em.desc(), SaudeFluxoEvento.id.desc())
        .limit(1)
    )
    ev = session.exec(stmt).first()
    return ev.passo if ev else None


def _proximo_passo(ultimo: Optional[str]) -> str:
    if not ultimo:
        return "TRIAGEM"
    i = _idx(ultimo)
    if i < 0:
        return "TRIAGEM"
    if i >= len(ORDEM) - 1:
        return "CONCLUSAO"
    return ORDEM[i + 1]


def _status_ui(i_step: int, ultimo: Optional[str]) -> str:
    """
    Similar ao caso: mostra “em_andamento” no próximo passo a ser feito.
    """
    if not ultimo:
        return "em_andamento" if i_step == 0 else "nao_iniciada"

    i_last = _idx(ultimo)
    if i_last < 0:
        return "em_andamento" if i_step == 0 else "nao_iniciada"

    # passos até o último registrado => concluídos
    if i_step <= i_last:
        return "concluida"

    # próximo passo => em andamento
    if i_step == i_last + 1:
        return "em_andamento"

    return "nao_iniciada"


@router.get("/{caso_id}/saude")
def saude_linha_metro(
    caso_id: int,
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    caso = session.get(CasoPopRua, caso_id)
    if not caso:
        raise HTTPException(status_code=404, detail="Caso não encontrado.")

    ultimo = _ultimo_passo(session, caso_id)
    etapas = []
    for i, p in enumerate(PASSOS):
        etapas.append(
            {
                "codigo": p["codigo"],
                "ordem": p["ordem"],
                "nome": p["nome"],
                "descricao": p["descricao"],
                "status": _status_ui(i, ultimo),
            }
        )

    return {
        "caso_id": caso_id,
        "pessoa_id": getattr(caso, "pessoa_id", None),
        "ultimo_passo": ultimo,
        "proximo_passo": _proximo_passo(ultimo),
        "etapas": etapas,
    }


@router.get("/{caso_id}/saude/eventos")
def saude_listar_eventos(
    caso_id: int,
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    stmt = (
        select(SaudeFluxoEvento)
        .where(SaudeFluxoEvento.caso_id == caso_id)
        .order_by(SaudeFluxoEvento.criado_em.desc(), SaudeFluxoEvento.id.desc())
    )
    itens = session.exec(stmt).all()
    return [x.model_dump() for x in itens]


@router.post("/{caso_id}/saude/eventos", status_code=201)
def saude_criar_evento(
    caso_id: int,
    payload: dict,
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    caso = session.get(CasoPopRua, caso_id)
    if not caso:
        raise HTTPException(status_code=404, detail="Caso não encontrado.")

    passo = (payload.get("passo") or "").strip().upper()
    if passo not in ORDEM:
        raise HTTPException(status_code=400, detail="Passo inválido.")

    # trava ordem: só registra o próximo passo esperado
    ultimo = _ultimo_passo(session, caso_id)
    esperado = _proximo_passo(ultimo)
    if passo != esperado:
        raise HTTPException(
            status_code=400,
            detail=f"Fora de ordem. Último passo: {ultimo or '—'}. Próximo permitido: {esperado}.",
        )

    # trava anti-vazamento
    _validar_texto_operacional(payload.get("observacoes"))

    usuario_nome = payload.get("usuario_responsavel") or getattr(usuario, "nome", None) or "Usuário"

    ev = SaudeFluxoEvento(
        caso_id=caso_id,
        passo=passo,
        criado_em=_agora(),
        usuario_responsavel=str(usuario_nome),

        responsavel_funcao=payload.get("responsavel_funcao"),
        responsavel_servico=payload.get("responsavel_servico"),
        responsavel_contato=payload.get("responsavel_contato"),

        prioridade=payload.get("prioridade"),
        precisa_avaliacao=payload.get("precisa_avaliacao"),
        servico_tipo=payload.get("servico_tipo"),
        unidade_nome=payload.get("unidade_nome"),

        data_hora=_parse_dt(payload.get("data_hora")),
        compareceu=payload.get("compareceu"),
        motivo_nao_compareceu=payload.get("motivo_nao_compareceu"),

        retorno_necessario=payload.get("retorno_necessario"),
        retorno_data_hora=_parse_dt(payload.get("retorno_data_hora")),
        status_final=payload.get("status_final"),

        observacoes=payload.get("observacoes"),
    )

    session.add(ev)
    session.commit()
    session.refresh(ev)
    return ev.model_dump()


def _parse_dt(v: Optional[str]) -> Optional[datetime]:
    if not v:
        return None
    try:
        return datetime.fromisoformat(v.replace("Z", "+00:00")).replace(tzinfo=None)
    except Exception:
        return None