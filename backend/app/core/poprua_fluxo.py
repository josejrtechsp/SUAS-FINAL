"""Configuração e normalização do fluxo PopRua.

Contexto
--------
O projeto tem dois fluxos relacionados ao PopRua:
1) O fluxo **operacional do caso** (casos.py) – mais completo (9 etapas).
2) O fluxo **visual (linha do metrô)** (linha_metro.py) – mais enxuto (7 etapas)
   e com registros auditáveis (CasoEtapaRegistro).

Problema
--------
Quando `caso.etapa_atual` fica com códigos do fluxo operacional (ex.: IDENTIFICACAO,
EXECUCAO, MONITORAMENTO), a linha do metrô (7 etapas) não conseguia posicionar o
"etapa atual" e acabava marcando tudo como início.

Solução
--------
Este módulo centraliza:
- A lista canônica das etapas visuais (linha do metrô)
- Um mapeamento **CASO -> METRO** (operacional -> visual)
- Um mapeamento **METRO -> CASO** (para sincronização opcional)
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


# =========================================================
# Etapas VISUAIS (Linha do metrô) — PopRua
# =========================================================
METRO_ETAPAS: List[Dict[str, Any]] = [
    {
        "codigo": "ABORDAGEM",
        "nome": "Abordagem",
        "descricao": "Abordagem qualificada e registro mínimo.",
    },
    {
        "codigo": "ACOLHIMENTO",
        "nome": "Acolhimento",
        "descricao": "Acolhimento inicial e provisões imediatas.",
    },
    {
        "codigo": "DIAGNOSTICO",
        "nome": "Diagnóstico",
        "descricao": "Diagnóstico social e identificação de necessidades.",
    },
    {
        "codigo": "PIA",
        "nome": "PIA",
        "descricao": "Plano Individual de Atendimento (metas, prazos e responsáveis).",
    },
    {
        "codigo": "ENCAMINHAMENTO",
        "nome": "Encaminhamento",
        "descricao": "Encaminhamento intersetorial e/ou intermunicipal (quando aplicável).",
    },
    {
        "codigo": "CONTRARREFERENCIA",
        "nome": "Contrarreferência",
        "descricao": "Confirmação de chegada/acolhimento e retorno ao município de origem.",
    },
    {
        "codigo": "ENCERRAMENTO",
        "nome": "Encerramento",
        "descricao": "Saída qualificada / desligamento / encerramento do caso.",
    },
]

METRO_INDEX = {e["codigo"]: idx for idx, e in enumerate(METRO_ETAPAS)}


def _up(s: Optional[str]) -> str:
    return (s or "").strip().upper()


# =========================================================
# Mapas de compatibilidade
# =========================================================
# Operacional (casos.py) -> Visual (linha do metrô)
CASO_TO_METRO = {
    "ABORDAGEM": "ABORDAGEM",
    "IDENTIFICACAO": "ACOLHIMENTO",
    "DIAGNOSTICO": "DIAGNOSTICO",
    "PIA": "PIA",
    "EXECUCAO": "ENCAMINHAMENTO",
    "ARTICULACAO_REDE": "ENCAMINHAMENTO",
    "MONITORAMENTO": "CONTRARREFERENCIA",
    "REVISAO": "CONTRARREFERENCIA",
    "ENCAMINHAMENTO": "ENCAMINHAMENTO",
    "CONTRARREFERENCIA": "CONTRARREFERENCIA",
    "ENCERRAMENTO": "ENCERRAMENTO",
}

# Visual -> Operacional (para sincronização opcional quando registrar no metrô)
METRO_TO_CASO = {
    "ABORDAGEM": "ABORDAGEM",
    "ACOLHIMENTO": "IDENTIFICACAO",
    "DIAGNOSTICO": "DIAGNOSTICO",
    "PIA": "PIA",
    "ENCAMINHAMENTO": "EXECUCAO",
    "CONTRARREFERENCIA": "MONITORAMENTO",
    "ENCERRAMENTO": "ENCERRAMENTO",
}


def etapa_metro(etapa_caso: Optional[str]) -> str:
    """Converte `caso.etapa_atual` para a etapa visual (linha do metrô)."""
    raw = _up(etapa_caso)
    mapped = CASO_TO_METRO.get(raw) or raw
    if mapped in METRO_INDEX:
        return mapped
    # fallback seguro
    return "ABORDAGEM"


def idx_metro(etapa_caso: Optional[str]) -> int:
    """Índice (ordem) da etapa visual equivalente."""
    return int(METRO_INDEX.get(etapa_metro(etapa_caso), 0))


def etapa_valida_metro(codigo: Optional[str]) -> bool:
    return _up(codigo) in METRO_INDEX


def metro_to_caso(etapa_codigo_metro: Optional[str]) -> str:
    """Converte uma etapa visual para o código operacional do caso."""
    return METRO_TO_CASO.get(_up(etapa_codigo_metro), "ABORDAGEM")


def deve_promover_caso_para_metro(etapa_caso_atual: Optional[str], etapa_metro_alvo: str) -> bool:
    """Retorna True se o caso estiver "atrás" e pode ser promovido para o alvo.

    Usa a ordem do metrô (visual) como régua.
    """
    try:
        atual_idx = idx_metro(etapa_caso_atual)
        alvo_idx = int(METRO_INDEX.get(_up(etapa_metro_alvo), 0))
        return atual_idx < alvo_idx
    except Exception:
        return True


def proxima_metro(etapa_codigo_metro: Optional[str]) -> Optional[str]:
    """Próxima etapa visual (linha do metrô)."""
    cur = _up(etapa_codigo_metro)
    if cur not in METRO_INDEX:
        cur = "ABORDAGEM"
    i = int(METRO_INDEX.get(cur, 0))
    if i >= len(METRO_ETAPAS) - 1:
        return None
    return str(METRO_ETAPAS[i + 1]["codigo"])


def pode_avancar_metro(etapa_atual_caso: Optional[str], etapa_alvo_metro: str) -> bool:
    """Retorna True se a etapa alvo (metro) representa avanço em relação ao atual."""
    alvo = _up(etapa_alvo_metro)
    if alvo not in METRO_INDEX:
        return False
    return idx_metro(etapa_atual_caso) < int(METRO_INDEX[alvo])
