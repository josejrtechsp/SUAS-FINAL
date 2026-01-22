from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.core.db import get_session
from app.core.auth import get_current_user
from app.models.usuario import Usuario
from app.models.caso_cras import CasoCras, CasoCrasHistorico

router = APIRouter(prefix="/cras", tags=["cras-linha-metro"])

ETAPAS = [
    {"codigo": "TRIAGEM", "titulo": "Recepção e Triagem", "descricao": "Recepção e triagem inicial.", "sla_dias": 2},
    {"codigo": "DIAGNOSTICO", "titulo": "Avaliação e Diagnóstico", "descricao": "Escuta qualificada e diagnóstico social.", "sla_dias": 15},
    {"codigo": "PIA", "titulo": "PIA", "descricao": "Plano Individual de Atendimento (metas, prazos e responsáveis).", "sla_dias": 15},
    {"codigo": "EXECUCAO", "titulo": "Execução das ações", "descricao": "Encaminhamentos e execução das ações planejadas.", "sla_dias": 30},
    {"codigo": "MONITORAMENTO", "titulo": "Monitoramento", "descricao": "Acompanhamento e reavaliação contínua.", "sla_dias": 30},
]

def _check_access(usuario: Usuario, caso: CasoCras):
    if getattr(usuario, "perfil", "") == "admin":
        return
    if getattr(usuario, "municipio_id", None) is None or int(usuario.municipio_id) != int(caso.municipio_id):
        raise HTTPException(status_code=403, detail="Acesso negado.")

def _status_etapa(caso: CasoCras, codigo: str) -> str:
    current_idx = next((i for i, e in enumerate(ETAPAS) if e["codigo"] == caso.etapa_atual), 0)
    idx = next((i for i, e in enumerate(ETAPAS) if e["codigo"] == codigo), 0)
    if idx < current_idx:
        return "concluida"
    if idx == current_idx:
        return "em_andamento"
    return "nao_iniciada"

def _ultima_atualizacao(session: Session, caso_id: int, codigo: str):
    return session.exec(
        select(CasoCrasHistorico)
        .where(CasoCrasHistorico.caso_id == caso_id)
        .where(CasoCrasHistorico.etapa == codigo)
        .order_by(CasoCrasHistorico.id.desc())
    ).first()

@router.get("/casos/{caso_id}/linha-metro")
def linha_metro_do_caso_cras(
    caso_id: int,
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
) -> Dict[str, Any]:
    caso = session.get(CasoCras, caso_id)
    if not caso:
        raise HTTPException(status_code=404, detail="Caso não encontrado.")
    _check_access(usuario, caso)

    etapas: List[Dict[str, Any]] = []
    for ordem, e in enumerate(ETAPAS, start=1):
        st = _status_etapa(caso, e["codigo"])
        last = _ultima_atualizacao(session, caso_id, e["codigo"])

        etapas.append({
            "codigo": e["codigo"],
            "titulo": f"{ordem}. {e['titulo']}",  # ✅ igual PopRua
            "descricao": e["descricao"],
            "status": st,
            "data_hora": (last.criado_em.isoformat() if last and last.criado_em else None),
            "responsavel": (last.usuario_nome if last and last.usuario_nome else None),
            "observacao": (last.observacoes if last and last.observacoes else None),
            "sla_dias": e["sla_dias"],
        })

    return {"caso_id": caso_id, "etapa_atual": caso.etapa_atual, "etapas": etapas}
