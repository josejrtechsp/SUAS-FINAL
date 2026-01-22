from __future__ import annotations

from datetime import date, datetime, time, timedelta
from typing import Any, Dict, List, Optional, Tuple
import time

from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_  # type: ignore
from sqlmodel import Session, select

from app.core.auth import exigir_minimo_perfil, get_current_user, pode_acesso_global
from app.core.db import get_session
from app.models.usuario import Usuario

# =========================
# Imports opcionais (não travam o app se algum módulo ainda não existir)
# =========================

try:
    from app.models.caso_cras import CasoCras  # type: ignore
except Exception:  # pragma: no cover
    CasoCras = None

try:
    from app.models.cras_tarefas import CrasTarefa  # type: ignore
except Exception:  # pragma: no cover
    CrasTarefa = None

try:
    from app.models.pessoa_suas import PessoaSUAS  # type: ignore
except Exception:  # pragma: no cover
    PessoaSUAS = None

try:
    from app.models.sla_regra import SlaRegra  # type: ignore
except Exception:  # pragma: no cover
    SlaRegra = None


try:
    from app.models.cadunico_precadastro import CadunicoPreCadastro  # type: ignore
except Exception:  # pragma: no cover
    CadunicoPreCadastro = None

try:
    from app.models.cras_pia import CrasPiaPlano  # type: ignore
except Exception:  # pragma: no cover
    CrasPiaPlano = None

try:
    from app.models.cras_unidade import CrasUnidade  # type: ignore
except Exception:  # pragma: no cover
    CrasUnidade = None
try:
    from app.models.caso_pop_rua import CasoPopRua  # type: ignore
except Exception:  # pragma: no cover
    CasoPopRua = None

try:
    from app.models.cras_encaminhamento import CrasEncaminhamento  # type: ignore
except Exception:  # pragma: no cover
    CrasEncaminhamento = None

try:
    from app.models.cras_encaminhamento import CrasEncaminhamentoEvento  # type: ignore
except Exception:  # pragma: no cover
    CrasEncaminhamentoEvento = None

try:
    from app.models.encaminhamentos import EncaminhamentoIntermunicipal  # type: ignore
except Exception:  # pragma: no cover
    EncaminhamentoIntermunicipal = None


try:
    from app.models.encaminhamentos import EncaminhamentoEvento  # type: ignore
except Exception:  # pragma: no cover
    EncaminhamentoEvento = None

try:
    from app.models.municipio import Municipio  # type: ignore
except Exception:  # pragma: no cover
    Municipio = None

# CREAS (atendimento especializado) - opcional
try:
    from app.models.creas_caso import CreasCaso  # type: ignore
except Exception:  # pragma: no cover
    CreasCaso = None

try:
    from app.models.familia_suas import FamiliaSUAS  # type: ignore
except Exception:  # pragma: no cover
    FamiliaSUAS = None

# Terceiro Setor (OSC) - opcional
try:
    from app.models.osc import OscPrestacaoContas  # type: ignore
except Exception:  # pragma: no cover
    OscPrestacaoContas = None


router = APIRouter(
    prefix="/gestao",
    tags=["gestao"],
    dependencies=[Depends(exigir_minimo_perfil("coord_municipal"))],
)

# -----------------------------
# Cache TTL (leve, em memória)
# Ajuda a evitar recomputar fila/dashboard em refresh/repetições do front.
# -----------------------------
_CACHE_TTL: dict[str, tuple[float, object]] = {}

def _cache_get(key: str, ttl_s: int) -> object | None:
    try:
        ts_val = _CACHE_TTL.get(key)
        if not ts_val:
            return None
        ts, val = ts_val
        if (time.time() - ts) <= ttl_s:
            return val
        _CACHE_TTL.pop(key, None)
        return None
    except Exception:
        return None

def _cache_set(key: str, val: object) -> None:
    _CACHE_TTL[key] = (time.time(), val)

def _users_cached(session: Session, ttl_s: int = 60) -> dict[int, str]:
    """Cache simples do mapa id->nome de usuários."""
    key = "users_map"
    cached = _cache_get(key, ttl_s)
    if isinstance(cached, dict):
        return cached  # type: ignore
    m = _prefetch_usuarios(session)
    _cache_set(key, m)
    return m


# =========================
# Helpers
# =========================

def _perfil(u: Usuario) -> str:
    return (getattr(u, "perfil", "") or "").strip().lower()


def _user_municipio_id(u: Usuario) -> Optional[int]:
    mid = getattr(u, "municipio_id", None)
    return int(mid) if mid is not None else None


def _resolver_municipio_id(usuario: Usuario, municipio_id: Optional[int]) -> Optional[int]:
    """
    - Operador/coord municipal: força município do usuário.
    - Gestor consórcio/admin: pode passar municipio_id ou ver geral (None).
    """
    if pode_acesso_global(usuario):
        return int(municipio_id) if municipio_id is not None else None
    return _user_municipio_id(usuario)


def _dt(d: Optional[date]) -> Optional[datetime]:
    if not d:
        return None
    return datetime.combine(d, time.min)


def _dias_atraso(agora: datetime, due_at: Optional[datetime]) -> int:
    if not due_at:
        return 0
    if agora <= due_at:
        return 0
    return int((agora - due_at).total_seconds() // 86400)


def _dias_passados(agora: datetime, when: Any) -> int:
    """Dias decorridos desde um datetime (ou None)."""
    if not isinstance(when, datetime):
        return 0
    if agora <= when:
        return 0
    return int((agora - when).total_seconds() // 86400)



def _mean(values: List[float]) -> Optional[float]:
    if not values:
        return None
    return round(sum(values) / max(len(values), 1), 2)


def _pct(num: int, den: int) -> float:
    if den <= 0:
        return 0.0
    return round(100.0 * float(num) / float(den), 1)


def _clamp(v: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, v))

def _faixa(score: float) -> str:
    if score >= 85:
        return "A"
    if score >= 70:
        return "B"
    if score >= 55:
        return "C"
    return "D"

def _score_cras(d: Dict[str, Any]) -> float:
    total = max(int(d.get("total") or 0), 1)
    atras = int(d.get("atrasados") or 0)
    emr = int(d.get("em_risco") or 0)
    pct_dev = float(d.get("pct_devolutiva_no_prazo") or 0.0)
    avg_dev = d.get("avg_horas_ate_devolutiva")
    avg_dev_val: Optional[float] = float(avg_dev) if isinstance(avg_dev, (int, float)) else None

    score = 100.0
    score -= 50.0 * (atras / total)
    score -= 20.0 * (emr / total)
    score -= 30.0 * (1.0 - pct_dev / 100.0)
    if avg_dev_val is not None:
        score -= 20.0 * min(avg_dev_val / 168.0, 1.0)

    # Penaliza destinos com pendências e nenhuma devolutiva ainda registrada
    if int(d.get("pendentes") or 0) > 0 and int(d.get("devolutivas") or 0) == 0:
        score -= 5.0

    return round(_clamp(score), 1)

def _score_inter(d: Dict[str, Any]) -> float:
    total = max(int(d.get("total") or 0), 1)
    atras = int(d.get("atrasados") or 0)
    emr = int(d.get("em_risco") or 0)
    pct_cont = float(d.get("pct_contato_no_prazo") or 0.0)
    avg_cont = d.get("avg_horas_ate_contato")
    avg_cont_val: Optional[float] = float(avg_cont) if isinstance(avg_cont, (int, float)) else None

    score = 100.0
    score -= 60.0 * (atras / total)
    score -= 20.0 * (emr / total)
    score -= 20.0 * (1.0 - pct_cont / 100.0)
    if avg_cont_val is not None:
        score -= 20.0 * min(avg_cont_val / 168.0, 1.0)

    # Penaliza municípios com pendências e nenhum contato registrado
    if int(d.get("pendentes") or 0) > 0 and int(d.get("contatos") or 0) == 0:
        score -= 5.0

    return round(_clamp(score), 1)

def _score_explicavel_cras(d: Dict[str, Any]) -> Tuple[Dict[str, Any], str]:
    """Explica o score (0–100) do destino CRAS.

    Retorna:
    - breakdown: componentes do score (penalidades) + score final
    - recomendacao: texto curto para orientar a gestão
    """
    total = max(int(d.get("total") or 0), 1)
    atras = int(d.get("atrasados") or 0)
    emr = int(d.get("em_risco") or 0)
    pend = int(d.get("pendentes") or 0)
    devol = int(d.get("devolutivas") or 0)

    pct_dev = float(d.get("pct_devolutiva_no_prazo") or 0.0)
    avg_dev = d.get("avg_horas_ate_devolutiva")
    avg_dev_val: Optional[float] = float(avg_dev) if isinstance(avg_dev, (int, float)) else None

    base = 100.0
    p_atraso = -50.0 * (float(atras) / float(total))
    p_risco = -20.0 * (float(emr) / float(total))
    p_comp = -30.0 * (1.0 - pct_dev / 100.0)
    p_tempo = 0.0
    if avg_dev_val is not None:
        p_tempo = -20.0 * min(avg_dev_val / 168.0, 1.0)
    p_pend = -5.0 if (pend > 0 and devol == 0) else 0.0

    score = round(_clamp(base + p_atraso + p_risco + p_comp + p_tempo + p_pend), 1)

    breakdown: Dict[str, Any] = {
        "base": 100.0,
        "atraso": round(p_atraso, 1),
        "em_risco": round(p_risco, 1),
        "compliance_devolutiva": round(p_comp, 1),
        "tempo_devolutiva": round(p_tempo, 1),
        "pendencia_sem_devolutiva": round(p_pend, 1),
        "score": score,
        "faixa": _faixa(score),
    }

    dicas: List[str] = []
    if atras > 0:
        dicas.append(f"{atras}/{total} encaminhamento(s) em atraso — priorize destravar o destino.")
    if emr > 0:
        dicas.append(f"{emr}/{total} em risco — agir antes de estourar.")
    if pend > 0 and devol == 0:
        dicas.append("Sem devolutiva registrada — cobrar devolutiva/registro de retorno.")
    elif pct_dev < 80.0 and devol > 0:
        dicas.append(f"Devolutiva no prazo baixa ({pct_dev:.1f}%) — ajustar rotina do destino.")
    if avg_dev_val is not None and avg_dev_val > 48.0 and devol > 0:
        dicas.append(f"Tempo médio de devolutiva alto ({avg_dev_val:.1f}h) — acelerar retorno.")
    if not dicas:
        dicas.append("Bom desempenho — manter rotina e monitorar prazos.")

    recomendacao = " ".join(dicas[:2])
    return breakdown, recomendacao


def _score_explicavel_inter(d: Dict[str, Any]) -> Tuple[Dict[str, Any], str]:
    """Explica o score (0–100) por município destino (intermunicipal)."""
    total = max(int(d.get("total") or 0), 1)
    atras = int(d.get("atrasados") or 0)
    emr = int(d.get("em_risco") or 0)
    pend = int(d.get("pendentes") or 0)
    cont = int(d.get("contatos") or 0)

    pct_cont = float(d.get("pct_contato_no_prazo") or 0.0)
    avg_cont = d.get("avg_horas_ate_contato")
    avg_cont_val: Optional[float] = float(avg_cont) if isinstance(avg_cont, (int, float)) else None

    base = 100.0
    p_atraso = -60.0 * (float(atras) / float(total))
    p_risco = -20.0 * (float(emr) / float(total))
    p_comp = -20.0 * (1.0 - pct_cont / 100.0)
    p_tempo = 0.0
    if avg_cont_val is not None:
        p_tempo = -20.0 * min(avg_cont_val / 168.0, 1.0)
    p_pend = -5.0 if (pend > 0 and cont == 0) else 0.0

    score = round(_clamp(base + p_atraso + p_risco + p_comp + p_tempo + p_pend), 1)

    breakdown: Dict[str, Any] = {
        "base": 100.0,
        "atraso": round(p_atraso, 1),
        "em_risco": round(p_risco, 1),
        "compliance_contato": round(p_comp, 1),
        "tempo_contato": round(p_tempo, 1),
        "pendencia_sem_contato": round(p_pend, 1),
        "score": score,
        "faixa": _faixa(score),
    }

    dicas: List[str] = []
    if atras > 0:
        dicas.append(f"{atras}/{total} em atraso — cobrar contato/aceite do município destino.")
    if emr > 0:
        dicas.append(f"{emr}/{total} em risco — agir antes de estourar.")
    if pend > 0 and cont == 0:
        dicas.append("Sem contato registrado — iniciar contato e registrar evidência.")
    elif pct_cont < 80.0 and cont > 0:
        dicas.append(f"Contato no prazo baixo ({pct_cont:.1f}%) — ajustar rotina de contato.")
    if avg_cont_val is not None and avg_cont_val > 48.0 and cont > 0:
        dicas.append(f"Tempo médio até contato alto ({avg_cont_val:.1f}h) — acelerar contato.")
    if not dicas:
        dicas.append("Bom desempenho — manter rotina e monitorar prazos.")

    recomendacao = " ".join(dicas[:2])
    return breakdown, recomendacao


def _sort_key_item(it: Dict[str, Any]) -> Tuple[int, str]:
    # Ordena por maior atraso, depois por due_at (mais antigo primeiro)
    dias = int(it.get("dias_em_atraso") or 0)
    due = it.get("sla_due_at") or ""
    return (-dias, str(due))


def _prefetch_usuarios(session: Session) -> Dict[int, str]:
    """Mapa id->nome para evitar N+1."""
    try:
        rows = session.exec(select(Usuario.id, Usuario.nome)).all()
        return {int(r[0]): str(r[1]) for r in rows if r and r[0] is not None}
    except Exception:
        return {}


def _prefetch_territorio_cras(session: Session, pessoa_ids: List[int]) -> Dict[int, Dict[str, Optional[str]]]:
    """Mapa pessoa_id -> {territorio,bairro}."""
    out: Dict[int, Dict[str, Optional[str]]] = {}
    if not pessoa_ids or PessoaSUAS is None:
        return out
    try:
        pessoas = session.exec(select(PessoaSUAS).where(PessoaSUAS.id.in_(pessoa_ids))).all()  # type: ignore
        for p in pessoas:
            pid = getattr(p, "id", None)
            if pid is None:
                continue
            out[int(pid)] = {
                "territorio": getattr(p, "territorio", None),
                "bairro": getattr(p, "bairro", None),
            }
    except Exception:
        return out
    return out


def _prefetch_cras_unidades(session: Session, municipio_id: Optional[int] = None) -> Dict[int, str]:
    """Mapa unidade_id -> nome (para evitar N+1 e deixar relatorios legiveis)."""
    out: Dict[int, str] = {}
    if CrasUnidade is None:
        return out
    try:
        stmt = select(CrasUnidade)
        if municipio_id is not None:
            stmt = stmt.where(CrasUnidade.municipio_id == int(municipio_id))  # type: ignore
        for u in session.exec(stmt).all():
            uid = getattr(u, "id", None)
            if uid is None:
                continue
            out[int(uid)] = str(getattr(u, "nome", "") or f"Unidade {uid}")
    except Exception:
        return out
    return out


def _norm_territorio(terr: Optional[str], bairro: Optional[str]) -> str:
    t = (terr or "").strip()
    b = (bairro or "").strip()
    return t or b or "Sem territorio"


def _cras_case_due_at(caso: Any) -> Optional[datetime]:
    try:
        inicio = getattr(caso, "data_inicio_etapa_atual", None)
        if not inicio:
            return None
        sla = getattr(caso, "prazo_etapa_dias", None)
        sla_dias = int(sla) if sla is not None else 7
        return inicio + timedelta(days=sla_dias)
    except Exception:
        return None


def _poprua_case_due_at(caso: Any) -> Optional[datetime]:
    try:
        inicio = getattr(caso, "data_inicio_etapa_atual", None)
        if not inicio:
            return None
        sla = getattr(caso, "prazo_etapa_dias", None)
        sla_dias = int(sla) if sla is not None else 7
        return inicio + timedelta(days=sla_dias)
    except Exception:
        return None


def _creas_case_due_at(caso: Any) -> Optional[datetime]:
    try:
        inicio = getattr(caso, 'data_inicio_etapa_atual', None)
        if not inicio:
            return None
        sla = getattr(caso, 'prazo_etapa_dias', None)
        sla_dias = int(sla) if sla is not None else 7
        return inicio + timedelta(days=sla_dias)
    except Exception:
        return None


# =========================
# Rede (SLA por etapa)
# =========================

_CRAS_ENC_NEXT = {
    "enviado": "recebido",
    "recebido": "agendado",
    "agendado": "atendido",
    "atendido": "devolutiva",
    "devolutiva": "concluido",
}

# SLA (dias) por etapa do encaminhamento CRAS (pode ser calibrado depois)
_CRAS_ENC_SLA = {
    "enviado": 2,        # prazo para acusar recebimento
    "recebido": 5,       # prazo para agendar
    "agendado": 7,       # prazo para atender
    "atendido": 2,       # prazo para registrar devolutiva
    "devolutiva": 2,     # prazo para concluir após devolutiva
}

_INTER_NEXT = {
    "solicitado": "contato",
    "contato": "aceito",
    "aceito": "agendado",
    "agendado": "passagem",
    "passagem": "contrarreferencia",
    "contrarreferencia": "concluido",
}

# SLA (dias) por etapa do encaminhamento intermunicipal (pode ser calibrado depois)
_INTER_SLA = {
    "solicitado": 2,
    "contato": 2,
    "aceito": 7,
    "agendado": 7,
    "passagem": 3,
    "contrarreferencia": 3,
}

# =========================
# SLA configurável (Config -> sla_regra)
# =========================

def _prefetch_sla_regras(session: Session, municipio_id: Optional[int]) -> List[Any]:
    """Carrega regras ativas de SLA (municipal + globais) para evitar N+1."""
    if SlaRegra is None:
        return []
    try:
        stmt = select(SlaRegra).where(SlaRegra.ativo == True)  # noqa: E712
        if municipio_id is not None:
            stmt = stmt.where(or_(SlaRegra.municipio_id == int(municipio_id), SlaRegra.municipio_id == None))  # noqa: E711
        return list(session.exec(stmt).all())
    except Exception:
        return []


def _resolver_sla_dias(
    regras: List[Any],
    municipio_id: Optional[int],
    unidade_tipo: Optional[str],
    unidade_id: Optional[int],
    modulo: str,
    etapa: str,
    default_dias: int,
) -> int:
    """Resolve SLA (dias) pela regra mais específica disponível.

    Prioridade (mais específico ganha):
      1) municipio + unidade_tipo + unidade_id
      2) municipio + unidade_tipo
      3) municipio
      4) global (municipio_id=None)
    """
    mod = (modulo or "").strip().lower()
    st = (etapa or "").strip().lower()
    ut = (unidade_tipo or "").strip().lower() or None
    uid = int(unidade_id) if unidade_id is not None else None

    best = None
    best_score = -1

    for r in regras:
        if not getattr(r, "ativo", True):
            continue
        if str(getattr(r, "modulo", "") or "").strip().lower() != mod:
            continue
        if str(getattr(r, "etapa", "") or "").strip().lower() != st:
            continue

        r_mid = getattr(r, "municipio_id", None)
        if r_mid is not None:
            if municipio_id is None:
                continue
            try:
                if int(r_mid) != int(municipio_id):
                    continue
            except Exception:
                continue

        r_ut = (str(getattr(r, "unidade_tipo", "") or "").strip().lower() or None)
        r_uid = getattr(r, "unidade_id", None)
        r_uid = int(r_uid) if r_uid is not None else None

        if r_ut is not None:
            if ut is None or r_ut != ut:
                continue
        if r_uid is not None:
            if uid is None:
                continue
            try:
                if int(r_uid) != int(uid):
                    continue
            except Exception:
                continue

        score = 0
        score += 4 if r_mid is not None else 0
        score += 2 if r_ut is not None else 0
        score += 1 if r_uid is not None else 0

        if score > best_score:
            best = r
            best_score = score
        elif score == best_score and best is not None:
            # desempate: mais recente
            b_upd = getattr(best, "atualizado_em", None)
            r_upd = getattr(r, "atualizado_em", None)
            if isinstance(r_upd, datetime) and isinstance(b_upd, datetime) and r_upd > b_upd:
                best = r

    try:
        return int(getattr(best, "sla_dias")) if best is not None else int(default_dias)
    except Exception:
        return int(default_dias)




def _cras_enc_status(enc: Any) -> str:
    return str(getattr(enc, "status", "") or "").strip().lower() or "enviado"


def _cras_enc_ref_dt(enc: Any) -> Optional[datetime]:
    st = _cras_enc_status(enc)
    # Usa o marco do status atual (ou fallback)
    if st == "enviado":
        return getattr(enc, "enviado_em", None) or getattr(enc, "criado_em", None)
    if st == "recebido":
        return getattr(enc, "recebido_em", None) or getattr(enc, "enviado_em", None) or getattr(enc, "criado_em", None)
    if st == "agendado":
        return getattr(enc, "agendado_em", None) or getattr(enc, "recebido_em", None) or getattr(enc, "enviado_em", None) or getattr(enc, "criado_em", None)
    if st == "atendido":
        return getattr(enc, "atendido_em", None) or getattr(enc, "agendado_em", None) or getattr(enc, "recebido_em", None) or getattr(enc, "enviado_em", None) or getattr(enc, "criado_em", None)
    if st == "devolutiva":
        return getattr(enc, "devolutiva_em", None) or getattr(enc, "atendido_em", None) or getattr(enc, "agendado_em", None) or getattr(enc, "recebido_em", None) or getattr(enc, "enviado_em", None) or getattr(enc, "criado_em", None)
    return getattr(enc, "atualizado_em", None) or getattr(enc, "enviado_em", None) or getattr(enc, "criado_em", None)


def _cras_enc_sla_dias(enc: Any, sla_lookup: Optional[Any] = None) -> int:
    st = _cras_enc_status(enc)
    base = getattr(enc, "prazo_devolutiva_dias", None)
    try:
        base_dias = int(base) if base is not None else 7
    except Exception:
        base_dias = 7

    default_etapa = int(_CRAS_ENC_SLA.get(st, base_dias))
    etapa = default_etapa

    if callable(sla_lookup):
        try:
            mid = getattr(enc, "municipio_id", None)
            uid = getattr(enc, "unidade_id", None)
            etapa = int(sla_lookup(mid, "cras", uid, "cras_encaminhamento", st, default_etapa))
        except Exception:
            etapa = default_etapa

    # evita SLA de etapa maior que o prazo geral do encaminhamento
    return int(min(int(etapa), base_dias)) if base_dias else int(etapa)

def _cras_enc_due_at(enc: Any, sla_lookup: Optional[Any] = None) -> Optional[datetime]:
    ref = _cras_enc_ref_dt(enc)
    if not isinstance(ref, datetime):
        return None
    return ref + timedelta(days=int(_cras_enc_sla_dias(enc, sla_lookup)))

def _enc_due_at(enc: Any, sla_lookup: Optional[Any] = None) -> Optional[datetime]:
    # compat: usado em vários pontos para encaminhamento CRAS
    return _cras_enc_due_at(enc, sla_lookup)

def _inter_status(enc: Any) -> str:
    return str(getattr(enc, "status", "") or "").strip().lower() or "solicitado"


def _inter_ref_dt(enc: Any) -> Optional[datetime]:
    st = _inter_status(enc)
    if st == "solicitado":
        return getattr(enc, "criado_em", None)
    if st == "contato":
        return getattr(enc, "contato_em", None) or getattr(enc, "criado_em", None)
    if st == "aceito":
        return getattr(enc, "aceite_em", None) or getattr(enc, "contato_em", None) or getattr(enc, "criado_em", None)
    if st == "agendado":
        return getattr(enc, "agendado_em", None) or getattr(enc, "aceite_em", None) or getattr(enc, "contato_em", None) or getattr(enc, "criado_em", None)
    if st == "passagem":
        return getattr(enc, "passagem_em", None) or getattr(enc, "agendado_em", None) or getattr(enc, "aceite_em", None) or getattr(enc, "contato_em", None) or getattr(enc, "criado_em", None)
    if st == "contrarreferencia":
        return getattr(enc, "contrarreferencia_em", None) or getattr(enc, "passagem_em", None) or getattr(enc, "agendado_em", None) or getattr(enc, "aceite_em", None) or getattr(enc, "contato_em", None) or getattr(enc, "criado_em", None)
    return getattr(enc, "atualizado_em", None) or getattr(enc, "criado_em", None)


def _inter_sla_dias(enc: Any, sla_lookup: Optional[Any] = None) -> int:
    st = _inter_status(enc)
    default = int(_INTER_SLA.get(st, 15))

    if callable(sla_lookup):
        try:
            # por padrão, mede SLA pelo município DESTINO (responsável por responder)
            mid_dest = getattr(enc, "municipio_destino_id", None)
            mid = int(mid_dest) if mid_dest is not None else getattr(enc, "municipio_origem_id", None)
            mid = int(mid) if mid is not None else None
            return int(sla_lookup(mid, None, None, "rede_intermunicipal", st, default))
        except Exception:
            return default

    return default

def _inter_due_at(enc: Any, sla_lookup: Optional[Any] = None) -> Optional[datetime]:
    ref = _inter_ref_dt(enc)
    if not isinstance(ref, datetime):
        return None
    return ref + timedelta(days=int(_inter_sla_dias(enc, sla_lookup)))


# =========================
# Normalização (WorkItems)
# =========================

def _parse_dt(v: Any) -> Optional[datetime]:
    """Converte um valor em datetime quando possível (aceita str ISO)."""
    if v is None:
        return None
    if isinstance(v, datetime):
        return v
    if isinstance(v, date) and not isinstance(v, datetime):
        try:
            return datetime.combine(v, time.min)
        except Exception:
            return None
    if isinstance(v, str):
        try:
            return datetime.fromisoformat(v)
        except Exception:
            return None
    return None


def _normalize_workitems(items: List[Dict[str, Any]], agora: datetime, risk_window: timedelta = timedelta(hours=24)) -> None:
    """Padroniza campos úteis para o dashboard da Gestão (sem quebrar o front)."""
    for it in items:
        due_dt = _parse_dt(it.get("sla_due_at"))
        dias_atraso = int(it.get("dias_em_atraso") or 0)
        sla_estourado = dias_atraso > 0

        sla_em_risco = False
        if due_dt and not sla_estourado:
            try:
                sla_em_risco = (due_dt - agora) <= risk_window
            except Exception:
                sla_em_risco = False

        ult_dt = _parse_dt(it.get("ultima_movimentacao_em"))
        dias_sem_mov = 0
        if ult_dt and agora > ult_dt:
            dias_sem_mov = int((agora - ult_dt).total_seconds() // 86400)

        # Defaults (não sobrescreve se já vier do item)
        it.setdefault("dias_sem_movimento", dias_sem_mov)
        it.setdefault("dias_na_etapa", dias_sem_mov)
        it.setdefault("sla_em_risco", sla_em_risco)
        it.setdefault("sla_estourado", sla_estourado)
        it.setdefault(
            "sla_status",
            "estourado" if sla_estourado else ("em_risco" if sla_em_risco else ("ok" if due_dt else "nao_definido")),
        )

        flags = it.get("flags")
        if not isinstance(flags, dict):
            flags = {}
        flags.setdefault("sla_em_risco", it.get("sla_em_risco"))
        flags.setdefault("sla_estourado", it.get("sla_estourado"))
        it["flags"] = flags

        # Motivo de trava (fallback)
        if not it.get("motivo_trava"):
            descr = it.get("descricao")
            motivo = str(descr) if descr else None

            sla_em_risco_eff = bool(it.get("sla_em_risco")) or sla_em_risco
            sla_estourado_eff = bool(it.get("sla_estourado")) or sla_estourado

            if motivo is None:
                if flags.get("validacao_pendente"):
                    motivo = "Aguardando validação"
                elif flags.get("estagnado"):
                    motivo = "Estagnado"
                elif str(it.get("modulo") or "").upper() == "OSC":
                    motivo = "Prestação de contas em atraso" if sla_estourado_eff else ("SLA em risco" if sla_em_risco_eff else None)
                elif str(it.get("tipo") or "") == "cadunico":
                    motivo = "CadÚnico atrasado" if sla_estourado_eff else "CadÚnico pendente"
                elif str(it.get("modulo") or "").upper() == "REDE":
                    motivo = "Devolutiva em atraso" if sla_estourado_eff else ("SLA em risco" if sla_em_risco_eff else "Aguardando devolutiva")
                elif sla_em_risco_eff:
                    motivo = "SLA em risco"
                elif sla_estourado_eff:
                    motivo = "SLA estourado"

            it["motivo_trava"] = motivo

# =========================
# Endpoints
# =========================




@router.get("/dashboard/resumo")
def gestao_dashboard_resumo(
    municipio_id: Optional[int] = Query(default=None, description="Filtro opcional por municipio (gestor/admin)."),
    unidade_id: Optional[int] = Query(default=None, description="Filtro opcional por unidade CRAS."),
    territorio: Optional[str] = Query(default=None, description="Filtro opcional por territorio/bairro (CRAS)."),
    de: Optional[date] = Query(default=None, description="Data inicial (opcional)."),
    ate: Optional[date] = Query(default=None, description="Data final (opcional)."),
    dias_cadunico: int = Query(default=30, ge=1, le=365, description="Janela (dias) para considerar CadUnico atrasado."),
    dias_pia: int = Query(default=15, ge=1, le=365, description="Prazo (dias) para considerar PIA pendente/atrasado (MVP)."),
    janela_risco_horas: int = Query(default=24, ge=1, le=168, description="Janela (horas) para considerar SLA em risco (vence em breve)."),
    nocache: bool = Query(default=False, description="Ignora cache TTL (debug/perf)."),
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    """Resumo consolidado (Gestao SUAS) - CRAS + PopRua + Rede (MVP+)."""

    agora = datetime.utcnow()
    risk_window = timedelta(hours=int(janela_risco_horas))
    mid = _resolver_municipio_id(usuario, municipio_id)

    # cache TTL curto (dashboard é agregação; 10-15s reduz carga sem perder utilidade)
    try:
        cache_key = (
            f"dash:{mid}:{unidade_id}:{(territorio or '').strip().lower()}:"
            f"{(de or '')}:{(ate or '')}:{dias_cadunico}:{dias_pia}:{janela_risco_horas}"
        )
        cached = None if nocache else _cache_get(cache_key, 12)
        if isinstance(cached, dict):
            out = dict(cached)
            out["_cached"] = True
            return out
    except Exception:
        pass


    sla_rules = _prefetch_sla_regras(session, mid)

    def sla_lookup(municipio_id: Optional[int], unidade_tipo: Optional[str], unidade_id: Optional[int], modulo: str, etapa: str, default: int) -> int:
        return _resolver_sla_dias(sla_rules, municipio_id, unidade_tipo, unidade_id, modulo, etapa, default)

    dt_de = _dt(de)
    dt_ate = _dt(ate)
    if dt_ate is not None:
        dt_ate = dt_ate + timedelta(days=1)  # inclui o dia

    terr_filtro = (territorio or "").strip().lower() or None

    # Mapas auxiliares
    unidade_nome = _prefetch_cras_unidades(session, mid)

    # -----------------
    # CRAS - casos
    # -----------------
    cras_ativos = 0
    cras_atrasos = 0
    cras_validacao_pendente = 0
    cras_pia_faltando = 0
    cras_pia_atrasado = 0
    cras_em_risco = 0
    cras_pia_em_risco = 0
    cras_tarefas_em_risco = 0
    cras_cadunico_em_risco = 0

    por_unidade: Dict[int, Dict[str, int]] = {}
    por_territorio: Dict[str, Dict[str, int]] = {}

    casos_cras: List[Any] = []
    missing_pia_ids: set[int] = set()

    if CasoCras is not None:
        stmt = select(CasoCras).where(CasoCras.status == "em_andamento")  # type: ignore
        if mid is not None:
            stmt = stmt.where(CasoCras.municipio_id == int(mid))  # type: ignore
        if unidade_id is not None:
            stmt = stmt.where(CasoCras.unidade_id == int(unidade_id))  # type: ignore
        if dt_de is not None:
            stmt = stmt.where(CasoCras.data_abertura >= dt_de)  # type: ignore
        if dt_ate is not None:
            stmt = stmt.where(CasoCras.data_abertura < dt_ate)  # type: ignore

        base = list(session.exec(stmt).all())

        # Prefetch territorio/bairro
        pessoa_ids = [int(getattr(c, "pessoa_id")) for c in base if getattr(c, "pessoa_id", None) is not None]
        terr_map = _prefetch_territorio_cras(session, pessoa_ids)

        # Aplica filtro de territorio (se houver)
        for c in base:
            pid = getattr(c, "pessoa_id", None)
            terr = terr_map.get(int(pid), {}) if pid is not None else {}
            terr_key = _norm_territorio(terr.get("territorio"), terr.get("bairro"))
            if terr_filtro and terr_filtro not in terr_key.lower():
                continue
            # guarda territorio no objeto para reuso
            setattr(c, "__gestao_territorio", terr_key)
            casos_cras.append(c)

        cras_ativos = len(casos_cras)

        # PIA faltando (casos em andamento sem plano)
        if CrasPiaPlano is not None:
            caso_ids = [int(getattr(c, "id")) for c in casos_cras if getattr(c, "id", None) is not None]
            if caso_ids:
                rows = session.exec(select(CrasPiaPlano.caso_id).where(CrasPiaPlano.caso_id.in_(caso_ids))).all()  # type: ignore
                have = {int(x) for x in rows if x is not None}
                missing_pia_ids = {cid for cid in caso_ids if cid not in have}

        for c in casos_cras:
            due = _cras_case_due_at(c)
            dias = _dias_atraso(agora, due)

            em_risco = False
            if due and agora < due and (due - agora) <= risk_window:
                em_risco = True
                cras_em_risco += 1

            estagn = bool(getattr(c, "estagnado", False))

            atraso = (dias > 0) or estagn

            # validacao pendente (48h)
            if bool(getattr(c, "aguardando_validacao", False)):
                desde = getattr(c, "pendente_validacao_desde", None) or getattr(c, "atualizado_em", None)
                if isinstance(desde, datetime) and (agora - desde) > timedelta(hours=48):
                    cras_validacao_pendente += 1
                    atraso = True

            # PIA faltando (count + opcional: considerado atraso se passou o prazo)
            cid = getattr(c, "id", None)
            pia_missing = (cid is not None) and (int(cid) in missing_pia_ids)
            if pia_missing:
                cras_pia_faltando += 1
                try:
                    abertura = getattr(c, "data_abertura", None)
                    due_pia = (abertura + timedelta(days=int(dias_pia))) if isinstance(abertura, datetime) else None
                    if due_pia and agora < due_pia and (due_pia - agora) <= risk_window:
                        cras_pia_em_risco += 1
                    if _dias_atraso(agora, due_pia) > 0:
                        cras_pia_atrasado += 1
                        atraso = True
                except Exception:
                    pass

            if atraso:
                cras_atrasos += 1

            uid = int(getattr(c, "unidade_id", 0) or 0)
            por_unidade.setdefault(uid, {"ativos": 0, "atrasos": 0, "em_risco": 0, "validacao_pendente": 0, "pia_faltando": 0, "pia_atrasado": 0, "cadunico_atrasado": 0, "tarefas_vencidas": 0})
            por_unidade[uid]["ativos"] += 1
            if atraso:
                por_unidade[uid]["atrasos"] += 1
            if em_risco:
                por_unidade[uid]["em_risco"] += 1
            if bool(getattr(c, "aguardando_validacao", False)):
                por_unidade[uid]["validacao_pendente"] += 1
            if pia_missing:
                por_unidade[uid]["pia_faltando"] += 1

            terr_key = getattr(c, "__gestao_territorio", "Sem territorio")
            por_territorio.setdefault(terr_key, {"ativos": 0, "atrasos": 0, "em_risco": 0, "pia_faltando": 0})
            por_territorio[terr_key]["ativos"] += 1
            if atraso:
                por_territorio[terr_key]["atrasos"] += 1
            if em_risco:
                por_territorio[terr_key]["em_risco"] += 1
            if pia_missing:
                por_territorio[terr_key]["pia_faltando"] += 1

    # -----------------
    # CRAS - tarefas vencidas / em risco
    # -----------------
    cras_tarefas_vencidas = 0
    if CrasTarefa is not None:
        stmt = select(CrasTarefa).where(CrasTarefa.status != "concluida")  # type: ignore
        if mid is not None:
            stmt = stmt.where(or_(CrasTarefa.municipio_id == int(mid), CrasTarefa.municipio_id.is_(None)))  # type: ignore
        if unidade_id is not None:
            stmt = stmt.where(or_(CrasTarefa.unidade_id == int(unidade_id), CrasTarefa.unidade_id.is_(None)))  # type: ignore
        tarefas = list(session.exec(stmt).all())

        for t in tarefas:
            venc = getattr(t, "data_vencimento", None)
            if not (venc and isinstance(venc, date)):
                continue

            due_dt = datetime.combine(venc, time.max)

            uid = int(getattr(t, "unidade_id", 0) or 0)
            por_unidade.setdefault(uid, {"ativos": 0, "atrasos": 0, "em_risco": 0, "validacao_pendente": 0, "pia_faltando": 0, "pia_atrasado": 0, "cadunico_atrasado": 0, "tarefas_vencidas": 0})

            if due_dt < agora:
                cras_tarefas_vencidas += 1
                por_unidade[uid]["tarefas_vencidas"] += 1
            else:
                if (due_dt - agora) <= risk_window:
                    cras_tarefas_em_risco += 1
                    por_unidade[uid]["em_risco"] += 1

    # -----------------
    # CRAS - CadUnico pendente / atrasado / em risco
    # -----------------
    cras_cadunico_pendente = 0
    cras_cadunico_atrasado = 0
    if CadunicoPreCadastro is not None:
        stmt = select(CadunicoPreCadastro).where(CadunicoPreCadastro.status.in_(["pendente", "agendado"]))  # type: ignore
        if mid is not None:
            stmt = stmt.where(CadunicoPreCadastro.municipio_id == int(mid))  # type: ignore
        if unidade_id is not None:
            stmt = stmt.where(CadunicoPreCadastro.unidade_id == int(unidade_id))  # type: ignore
        rows = list(session.exec(stmt).all())
        cras_cadunico_pendente = len(rows)

        # prefetch territorio (para filtro opcional)
        pids = [int(getattr(x, "pessoa_id")) for x in rows if getattr(x, "pessoa_id", None) is not None]
        terr_map2 = _prefetch_territorio_cras(session, pids)

        for x in rows:
            criado = getattr(x, "criado_em", None)
            if not isinstance(criado, datetime):
                continue

            pid = getattr(x, "pessoa_id", None)
            terr2 = terr_map2.get(int(pid), {}) if pid is not None else {}
            terr_key = _norm_territorio(terr2.get("territorio"), terr2.get("bairro"))
            if terr_filtro and terr_filtro not in terr_key.lower():
                continue

            due_dt = criado + timedelta(days=int(dias_cadunico))

            uid = int(getattr(x, "unidade_id", 0) or 0)
            por_unidade.setdefault(uid, {"ativos": 0, "atrasos": 0, "em_risco": 0, "validacao_pendente": 0, "pia_faltando": 0, "pia_atrasado": 0, "cadunico_atrasado": 0, "tarefas_vencidas": 0})

            if due_dt < agora:
                cras_cadunico_atrasado += 1
                por_unidade[uid]["cadunico_atrasado"] += 1
            else:
                if (due_dt - agora) <= risk_window:
                    cras_cadunico_em_risco += 1
                    por_unidade[uid]["em_risco"] += 1

    # -----------------
    # PopRua - casos
    # -----------------
    poprua_ativos = 0
    poprua_atrasos = 0
    poprua_em_risco = 0
    if CasoPopRua is not None:
        stmt = select(CasoPopRua).where(CasoPopRua.ativo == True)  # type: ignore
        stmt = stmt.where(CasoPopRua.status != "encerrado")  # type: ignore
        if mid is not None:
            stmt = stmt.where(CasoPopRua.municipio_id == int(mid))  # type: ignore
        if dt_de is not None:
            stmt = stmt.where(CasoPopRua.data_abertura >= dt_de)  # type: ignore
        if dt_ate is not None:
            stmt = stmt.where(CasoPopRua.data_abertura < dt_ate)  # type: ignore
        casos = list(session.exec(stmt).all())
        poprua_ativos = len(casos)
        for c in casos:
            due = _poprua_case_due_at(c)
            dias = _dias_atraso(agora, due)
            if due and agora < due and (due - agora) <= risk_window:
                poprua_em_risco += 1
            estagn = bool(getattr(c, "estagnado", False)) or bool(getattr(c, "flag_estagnado", False))
            if dias > 0 or estagn:
                poprua_atrasos += 1

    # -----------------
    # CREAS - casos (MVP)
    # -----------------
    creas_ativos = 0
    creas_atrasos = 0
    creas_em_risco = 0
    creas_validacao_pendente = 0
    if CreasCaso is not None:
        stmt = select(CreasCaso).where(CreasCaso.status == 'em_andamento')  # type: ignore
        if mid is not None:
            stmt = stmt.where(CreasCaso.municipio_id == int(mid))  # type: ignore
        if dt_de is not None:
            stmt = stmt.where(CreasCaso.data_abertura >= dt_de)  # type: ignore
        if dt_ate is not None:
            stmt = stmt.where(CreasCaso.data_abertura < dt_ate)  # type: ignore

        casos = list(session.exec(stmt).all())
        creas_ativos = len(casos)
        for c in casos:
            due = _creas_case_due_at(c)
            dias = _dias_atraso(agora, due)

            if due and agora < due and (due - agora) <= risk_window:
                creas_em_risco += 1

            estagn = bool(getattr(c, 'estagnado', False))

            atraso = (dias > 0) or estagn

            if bool(getattr(c, 'aguardando_validacao', False)):
                desde = getattr(c, 'pendente_validacao_desde', None) or getattr(c, 'atualizado_em', None) or getattr(c, 'data_inicio_etapa_atual', None)
                if isinstance(desde, datetime) and (agora - desde) > timedelta(hours=48):
                    creas_validacao_pendente += 1
                    atraso = True

            if atraso:
                creas_atrasos += 1

    # -----------------
    # Rede - encaminhamentos CRAS
    # -----------------
    rede_aguardando = 0
    rede_atrasados = 0
    rede_em_risco = 0

    # Compliance (Gestão): tempos e % no prazo
    rede_recebidos = 0
    rede_recebidos_no_prazo = 0
    rede_devolutivas = 0
    rede_devolutivas_no_prazo = 0
    rede_conclusoes = 0
    rede_conclusoes_no_prazo = 0
    _recv_h: List[float] = []
    _dev_h: List[float] = []
    _conc_d: List[float] = []

    if CrasEncaminhamento is not None:
        stmt = select(CrasEncaminhamento)
        if mid is not None:
            stmt = stmt.where(CrasEncaminhamento.municipio_id == int(mid))  # type: ignore
        if unidade_id is not None:
            stmt = stmt.where(CrasEncaminhamento.unidade_id == int(unidade_id))  # type: ignore
        encs = list(session.exec(stmt).all())
        finais = {"concluido", "cancelado"}
        for e in encs:
            st = _cras_enc_status(e)
            if st not in finais:
                rede_aguardando += 1
                due = _enc_due_at(e, sla_lookup)
                if due and agora < due and (due - agora) <= risk_window:
                    rede_em_risco += 1
                if _dias_atraso(agora, due) > 0:
                    rede_atrasados += 1

            # --- tempos / compliance (independente de estar finalizado) ---
            enviado_em = getattr(e, "enviado_em", None)
            recebido_em = getattr(e, "recebido_em", None)
            if isinstance(enviado_em, datetime) and isinstance(recebido_em, datetime):
                rede_recebidos += 1
                _recv_h.append(max(0.0, (recebido_em - enviado_em).total_seconds() / 3600.0))
                if recebido_em <= (enviado_em + timedelta(days=int(sla_lookup(getattr(e, "municipio_id", None), "cras", getattr(e, "unidade_id", None), "cras_encaminhamento", "enviado", int(_CRAS_ENC_SLA.get("enviado", 2)))))):
                    rede_recebidos_no_prazo += 1

            atendido_em = getattr(e, "atendido_em", None)
            devolutiva_em = getattr(e, "devolutiva_em", None)
            if isinstance(devolutiva_em, datetime):
                rede_devolutivas += 1
                base = atendido_em if isinstance(atendido_em, datetime) else enviado_em
                if isinstance(base, datetime):
                    _dev_h.append(max(0.0, (devolutiva_em - base).total_seconds() / 3600.0))
                if isinstance(atendido_em, datetime):
                    if devolutiva_em <= (atendido_em + timedelta(days=int(sla_lookup(getattr(e, "municipio_id", None), "cras", getattr(e, "unidade_id", None), "cras_encaminhamento", "atendido", int(_CRAS_ENC_SLA.get("atendido", 2)))))):
                        rede_devolutivas_no_prazo += 1

            concluido_em = getattr(e, "concluido_em", None)
            if isinstance(concluido_em, datetime):
                rede_conclusoes += 1
                if isinstance(enviado_em, datetime):
                    _conc_d.append(max(0.0, (concluido_em - enviado_em).total_seconds() / 86400.0))
                if isinstance(devolutiva_em, datetime):
                    if concluido_em <= (devolutiva_em + timedelta(days=int(sla_lookup(getattr(e, "municipio_id", None), "cras", getattr(e, "unidade_id", None), "cras_encaminhamento", "devolutiva", int(_CRAS_ENC_SLA.get("devolutiva", 2)))))):
                        rede_conclusoes_no_prazo += 1

    rede_avg_horas_ate_recebido = _mean(_recv_h)
    rede_avg_horas_ate_devolutiva = _mean(_dev_h)
    rede_avg_dias_ate_conclusao = _mean(_conc_d)
    rede_pct_recebido_no_prazo = _pct(rede_recebidos_no_prazo, rede_recebidos)
    rede_pct_devolutiva_no_prazo = _pct(rede_devolutivas_no_prazo, rede_devolutivas)
    rede_pct_conclusao_no_prazo = _pct(rede_conclusoes_no_prazo, rede_conclusoes)

    # -----------------
    # Rede - encaminhamentos intermunicipais (MVP)
    # -----------------
    inter_aguardando = 0
    inter_atrasados = 0
    inter_em_risco = 0

    # Compliance (Gestão): tempo e % no prazo do primeiro contato
    inter_contatos = 0
    inter_contatos_no_prazo = 0
    _cont_h: List[float] = []

    if EncaminhamentoIntermunicipal is not None:
        stmt = select(EncaminhamentoIntermunicipal)
        if mid is not None:
            stmt = stmt.where(
                or_(
                    EncaminhamentoIntermunicipal.municipio_origem_id == int(mid),  # type: ignore
                    EncaminhamentoIntermunicipal.municipio_destino_id == int(mid),  # type: ignore
                )
            )
        encs = list(session.exec(stmt).all())
        finais = {"concluido", "cancelado"}
        for e in encs:
            st = _inter_status(e)
            if st not in finais:
                inter_aguardando += 1
                due = _inter_due_at(e, sla_lookup)
                if due and agora < due and (due - agora) <= risk_window:
                    inter_em_risco += 1
                if _dias_atraso(agora, due) > 0:
                    inter_atrasados += 1

            criado_em = getattr(e, "criado_em", None)
            contato_em = getattr(e, "contato_em", None)
            if isinstance(criado_em, datetime) and isinstance(contato_em, datetime):
                inter_contatos += 1
                _cont_h.append(max(0.0, (contato_em - criado_em).total_seconds() / 3600.0))
                if contato_em <= (criado_em + timedelta(days=int(sla_lookup((getattr(e, "municipio_destino_id", None) or getattr(e, "municipio_origem_id", None)), None, None, "rede_intermunicipal", "solicitado", int(_INTER_SLA.get("solicitado", 2)))))):
                    inter_contatos_no_prazo += 1

    inter_avg_horas_ate_contato = _mean(_cont_h)
    inter_pct_contato_no_prazo = _pct(inter_contatos_no_prazo, inter_contatos)

    # -----------------
    # Terceiro Setor (OSC) - prestações pendentes e críticas
    # -----------------
    osc_pendencias = 0
    osc_criticas = 0
    osc_em_risco = 0
    if OscPrestacaoContas is not None:
        stmt = select(OscPrestacaoContas).where(OscPrestacaoContas.status.notin_(["aprovado", "reprovado"]))  # type: ignore
        if mid is not None:
            stmt = stmt.where(OscPrestacaoContas.municipio_id == int(mid))  # type: ignore
        rows = list(session.exec(stmt).all())
        osc_pendencias = len(rows)
        hoje = date.today()
        for pc in rows:
            prazo = getattr(pc, "prazo_entrega", None)
            if isinstance(prazo, date):
                due_dt = datetime.combine(prazo, time.max)
                if due_dt < agora:
                    osc_criticas += 1
                else:
                    if (due_dt - agora) <= risk_window:
                        osc_em_risco += 1

    # Totais
    casos_ativos_total = cras_ativos + poprua_ativos + creas_ativos
    cras_em_risco_total = cras_em_risco + cras_pia_em_risco + cras_tarefas_em_risco + cras_cadunico_em_risco
    pendencias_em_risco_total = cras_em_risco_total + poprua_em_risco + creas_em_risco + rede_em_risco + inter_em_risco + osc_em_risco
    pendencias_atrasadas_total = (
        cras_atrasos
        + creas_atrasos
        + poprua_atrasos
        + rede_atrasados
        + inter_atrasados
        + cras_tarefas_vencidas
        + cras_cadunico_atrasado
        + cras_pia_atrasado
        + osc_criticas
    )

    # Formata breakdowns
    por_unidade_list: List[Dict[str, Any]] = []
    for uid, b in por_unidade.items():
        por_unidade_list.append(
            {
                "unidade_id": uid if uid != 0 else None,
                "unidade_nome": unidade_nome.get(uid, "Sem unidade") if uid != 0 else "Sem unidade",
                **b,
            }
        )
    por_unidade_list.sort(key=lambda x: (-int(x.get("atrasos") or 0), -int(x.get("ativos") or 0), str(x.get("unidade_nome") or "")))

    por_territorio_list: List[Dict[str, Any]] = []
    for terr, b in por_territorio.items():
        por_territorio_list.append({"territorio": terr, **b})
    por_territorio_list.sort(key=lambda x: (-int(x.get("atrasos") or 0), -int(x.get("ativos") or 0), str(x.get("territorio") or "")))

    # Rankings de rede (Top 5 melhores/piores) — visão "secretário"
    # Não altera o front; adiciona dados extras no resumo.
    rede_rankings: Dict[str, Any] = {
        "cras": {"pior": [], "melhor": []},
        "intermunicipal": {"pior": [], "melhor": []},
    }
    try:
        met = gestao_rede_metricas(
            municipio_id=mid,
            janela_risco_horas=int(janela_risco_horas),
            limit_destinos=200,
            limit_municipios=200,
            session=session,
            usuario=usuario,
        )
        dests = (met.get("cras") or {}).get("por_destino") or []
        munis = (met.get("intermunicipal") or {}).get("por_municipio_destino") or []

        def _pick_dest(d: Dict[str, Any]) -> Dict[str, Any]:
            return {
                "destino_tipo": d.get("destino_tipo"),
                "destino_nome": d.get("destino_nome"),
                "total": int(d.get("total") or 0),
                "pendentes": int(d.get("pendentes") or 0),
                "atrasados": int(d.get("atrasados") or 0),
                "em_risco": int(d.get("em_risco") or 0),
                "pct_devolutiva_no_prazo": float(d.get("pct_devolutiva_no_prazo") or 0.0),
                "avg_horas_ate_devolutiva": d.get("avg_horas_ate_devolutiva"),
                "score": float(d.get("score") or 0.0),
                "faixa": d.get("faixa"),
                "recomendacao": d.get("recomendacao"),
                "score_breakdown": d.get("score_breakdown"),
            }

        def _pick_muni(d: Dict[str, Any]) -> Dict[str, Any]:
            out = {
                "municipio_destino_id": d.get("municipio_destino_id"),
                "municipio_destino_nome": d.get("municipio_destino_nome"),
                "total": int(d.get("total") or 0),
                "pendentes": int(d.get("pendentes") or 0),
                "atrasados": int(d.get("atrasados") or 0),
                "em_risco": int(d.get("em_risco") or 0),
                "pct_contato_no_prazo": float(d.get("pct_contato_no_prazo") or 0.0),
                "avg_horas_ate_contato": d.get("avg_horas_ate_contato"),
                    "score": float(d.get("score") or 0.0),
                    "faixa": d.get("faixa"),
                    "score_breakdown": d.get("score_breakdown"),
                    "recomendacao": d.get("recomendacao"),
                }

        # "Piores": menor score (e depois mais atrasos)
        dests_worst = sorted(dests, key=lambda x: (float(x.get("score") or 0.0), -int(x.get("atrasados") or 0), -int(x.get("em_risco") or 0)))
        munis_worst = sorted(munis, key=lambda x: (float(x.get("score") or 0.0), -int(x.get("atrasados") or 0), -int(x.get("em_risco") or 0)))
        rede_rankings["cras"]["pior"] = [_pick_dest(x) for x in dests_worst[:5]]
        rede_rankings["intermunicipal"]["pior"] = [_pick_muni(x) for x in munis_worst[:5]]

        # "Melhores": maior compliance, menor atraso, menor tempo (None vai pro fim)
        def _dest_best_key(x: Dict[str, Any]):
            pct = float(x.get("pct_devolutiva_no_prazo") or 0.0)
            atras = int(x.get("atrasados") or 0)
            emr = int(x.get("em_risco") or 0)
            avg = x.get("avg_horas_ate_devolutiva")
            avg_val = float(avg) if isinstance(avg, (int, float)) else 1e9
            return (-pct, atras, emr, avg_val, -int(x.get("concluidos") or 0))

        def _mun_best_key(x: Dict[str, Any]):
            pct = float(x.get("pct_contato_no_prazo") or 0.0)
            atras = int(x.get("atrasados") or 0)
            emr = int(x.get("em_risco") or 0)
            avg = x.get("avg_horas_ate_contato")
            avg_val = float(avg) if isinstance(avg, (int, float)) else 1e9
            return (-pct, atras, emr, avg_val, -int(x.get("concluidos") or 0))

        dests_best = sorted(dests, key=lambda x: (-float(x.get("score") or 0.0), -float(x.get("pct_devolutiva_no_prazo") or 0.0), int(x.get("atrasados") or 0), int(x.get("em_risco") or 0)))
        munis_best = sorted(munis, key=lambda x: (-float(x.get("score") or 0.0), -float(x.get("pct_contato_no_prazo") or 0.0), int(x.get("atrasados") or 0), int(x.get("em_risco") or 0)))

        rede_rankings["cras"]["melhor"] = [_pick_dest(x) for x in dests_best[:5]]
        rede_rankings["intermunicipal"]["melhor"] = [_pick_muni(x) for x in munis_best[:5]]
    except Exception:
        pass

    out = {
        "perfil": _perfil(usuario),
        "filtros": {
            "municipio_id": mid,
            "unidade_id": unidade_id,
            "territorio": territorio,
            "de": str(de) if de else None,
            "ate": str(ate) if ate else None,
        },
        "kpis": {
            "casos_ativos_total": casos_ativos_total,
            "pendencias_atrasadas_total": pendencias_atrasadas_total,
            "pendencias_em_risco_total": pendencias_em_risco_total,
            "encaminhamentos_aguardando_total": rede_aguardando + inter_aguardando,
        },
        "por_modulo": {
            "cras": {
                "ativos": cras_ativos,
                "atrasos": cras_atrasos,
                "em_risco": cras_em_risco_total,
                "validacao_pendente": cras_validacao_pendente,
                "tarefas_vencidas": cras_tarefas_vencidas,
                "pia_faltando": cras_pia_faltando,
                "pia_atrasado": cras_pia_atrasado,
                "cadunico_pendente": cras_cadunico_pendente,
                "cadunico_atrasado": cras_cadunico_atrasado,
            },
            "poprua": {"ativos": poprua_ativos, "atrasos": poprua_atrasos, "em_risco": poprua_em_risco},
            "rede": {
                "aguardando": rede_aguardando,
                "atrasados": rede_atrasados,
                "inter_aguardando": inter_aguardando,
                "inter_atrasados": inter_atrasados,
                "em_risco": rede_em_risco + inter_em_risco,

                # Compliance (Gestão)
                "pct_recebido_no_prazo": rede_pct_recebido_no_prazo,
                "pct_devolutiva_no_prazo": rede_pct_devolutiva_no_prazo,
                "pct_conclusao_no_prazo": rede_pct_conclusao_no_prazo,
                "avg_horas_ate_recebido": rede_avg_horas_ate_recebido,
                "avg_horas_ate_devolutiva": rede_avg_horas_ate_devolutiva,
                "avg_dias_ate_conclusao": rede_avg_dias_ate_conclusao,

                "pct_contato_no_prazo": inter_pct_contato_no_prazo,
                "avg_horas_ate_contato": inter_avg_horas_ate_contato,
                "rankings": rede_rankings,
            },
            "creas": {"ativos": creas_ativos, "atrasos": creas_atrasos, "em_risco": creas_em_risco, "validacao_pendente": creas_validacao_pendente},
            "osc": {"pendencias": osc_pendencias, "criticas": osc_criticas, "em_risco": osc_em_risco},
        },
        "por_unidade": por_unidade_list,
        "por_territorio": por_territorio_list,
    }
    try:
        if not nocache:
            _cache_set(cache_key, out)
    except Exception:
        pass
    return out



@router.get("/fila")

def gestao_fila(
    municipio_id: Optional[int] = Query(default=None, description="Filtro opcional por municipio (gestor/admin)."),
    unidade_id: Optional[int] = Query(default=None, description="Filtro opcional por unidade CRAS."),
    territorio: Optional[str] = Query(default=None, description="Filtro opcional por territorio/bairro (CRAS)."),
    dias_cadunico: int = Query(default=30, ge=1, le=365, description="Janela (dias) para considerar CadUnico atrasado."),
    dias_pia: int = Query(default=15, ge=1, le=365, description="Prazo (dias) para considerar PIA pendente/atrasado (MVP)."),
    janela_risco_horas: int = Query(default=24, ge=1, le=168, description="Janela (horas) para considerar SLA em risco (vence em breve)."),
    nocache: bool = Query(default=False, description="Ignora cache TTL (debug/perf)."),
    modulo: Optional[str] = Query(default=None, description="Filtro opcional (cras|creas|poprua|rede|osc)."),
    somente_atrasos: bool = Query(default=False, description="Se true, retorna somente itens em atraso."),
    somente_em_risco: bool = Query(default=False, description="Se true, retorna somente itens com SLA em risco (vence em breve)."),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    """Fila do secretario: itens acionaveis consolidados (MVP+)."""

    agora = datetime.utcnow()
    risk_window = timedelta(hours=int(janela_risco_horas))
    mid = _resolver_municipio_id(usuario, municipio_id)

    sla_rules = _prefetch_sla_regras(session, mid)

    def sla_lookup(municipio_id: Optional[int], unidade_tipo: Optional[str], unidade_id: Optional[int], modulo: str, etapa: str, default: int) -> int:
        return _resolver_sla_dias(sla_rules, municipio_id, unidade_tipo, unidade_id, modulo, etapa, default)

    modulo_norm = (modulo or "").strip().lower() or None
    terr_filtro = (territorio or "").strip().lower() or None

    # cache TTL curto (evita recomputar em refresh/filtragem repetida)
    try:
        cache_key = (
            f"fila:{mid}:{unidade_id}:{terr_filtro}:{dias_cadunico}:{dias_pia}:"
            f"{janela_risco_horas}:{modulo_norm}:{int(somente_atrasos)}:{int(somente_em_risco)}:"
            f"{limit}:{offset}"
        )
        cached = None if nocache else _cache_get(cache_key, 8)
        if isinstance(cached, dict):
            out = dict(cached)
            out["_cached"] = True
            return out
    except Exception:
        pass


    user_map = _users_cached(session)

    items: List[Dict[str, Any]] = []

    # Performance: evita varrer o banco inteiro quando a tela pede poucos itens
    cap_fetch_base = int(min(8000, max(400, limit * 60)))
    cap_fetch_small = int(min(3000, max(200, limit * 30)))

    # -----------------
    # CRAS - casos
    # -----------------
    missing_pia_ids: set[int] = set()
    if (modulo_norm in (None, "cras")) and CasoCras is not None:
        stmt = select(CasoCras).where(CasoCras.status == "em_andamento")  # type: ignore
        if mid is not None:
            stmt = stmt.where(CasoCras.municipio_id == int(mid))  # type: ignore
        if unidade_id is not None:
            stmt = stmt.where(CasoCras.unidade_id == int(unidade_id))  # type: ignore
        # otimização: lê só os casos mais antigos/urgentes (reduz custo em escala)
        try:
            stmt = stmt.order_by(CasoCras.data_inicio_etapa_atual.asc())  # type: ignore
        except Exception:
            pass
        stmt = stmt.limit(cap_fetch_base)
        casos = list(session.exec(stmt).all())

        pessoa_ids = [int(getattr(c, "pessoa_id")) for c in casos if getattr(c, "pessoa_id", None) is not None]
        terr_map = _prefetch_territorio_cras(session, pessoa_ids)

        # PIA faltando (para flag no item)
        if CrasPiaPlano is not None:
            caso_ids = [int(getattr(c, "id")) for c in casos if getattr(c, "id", None) is not None]
            if caso_ids:
                rows = session.exec(select(CrasPiaPlano.caso_id).where(CrasPiaPlano.caso_id.in_(caso_ids))).all()  # type: ignore
                have = {int(x) for x in rows if x is not None}
                missing_pia_ids = {cid for cid in caso_ids if cid not in have}

        for c in casos:
            pid = getattr(c, "pessoa_id", None)
            terr = terr_map.get(int(pid), {}) if pid is not None else {}
            terr_key = _norm_territorio(terr.get("territorio"), terr.get("bairro"))
            if terr_filtro and terr_filtro not in terr_key.lower():
                continue

            due = _cras_case_due_at(c)
            dias = _dias_atraso(agora, due)

            estagn = bool(getattr(c, "estagnado", False))
            motivo_estagn = getattr(c, "motivo_estagnacao", None)

            # validacao pendente (48h)
            valid_pendente = False
            if bool(getattr(c, "aguardando_validacao", False)):
                desde = getattr(c, "pendente_validacao_desde", None) or getattr(c, "atualizado_em", None)
                if isinstance(desde, datetime) and (agora - desde) > timedelta(hours=48):
                    valid_pendente = True

            # PIA faltando
            cid = getattr(c, "id", None)
            pia_missing = (cid is not None) and (int(cid) in missing_pia_ids)
            pia_dias = 0
            try:
                abertura = getattr(c, "data_abertura", None)
                due_pia = (abertura + timedelta(days=int(dias_pia))) if isinstance(abertura, datetime) else None
                pia_dias = _dias_atraso(agora, due_pia)
            except Exception:
                pia_dias = 0

            em_atraso = (dias > 0) or estagn or valid_pendente or (pia_missing and pia_dias > 0)

            if somente_atrasos and not em_atraso:
                continue

            rid = getattr(c, "tecnico_responsavel_id", None)
            rnome = user_map.get(int(rid)) if rid is not None else None

            flags = {
                "estagnado": bool(estagn),
                "validacao_pendente": bool(valid_pendente),
                "pia_faltando": bool(pia_missing),
            }

            items.append(
                {
                    "modulo": "CRAS",
                    "tipo": "caso",
                    "referencia_id": getattr(c, "id", None),
                    "titulo": f"Caso CRAS #{getattr(c, 'id', '')} - {getattr(c, 'etapa_atual', '')}",
                    "descricao": (
                        "Aguardando validacao" if valid_pendente else (f"Estagnado: {motivo_estagn}" if estagn and motivo_estagn else ("Estagnado" if estagn else None))
                    ),
                    "municipio_id": getattr(c, "municipio_id", None),
                    "unidade_id": getattr(c, "unidade_id", None),
                    "territorio": terr_key,
                    "responsavel_id": rid,
                    "responsavel_nome": rnome,
                    "etapa_atual": getattr(c, "etapa_atual", None),
                    "status": getattr(c, "status", None),
                    "ultima_movimentacao_em": (
                        getattr(c, "atualizado_em", None) or getattr(c, "data_inicio_etapa_atual", None) or getattr(c, "data_abertura", None)
                    ),
                    "sla_due_at": due.isoformat() if isinstance(due, datetime) else None,
                    "dias_em_atraso": int(dias),
                    "dias_na_etapa": _dias_passados(agora, getattr(c, "data_inicio_etapa_atual", None) or getattr(c, "data_abertura", None)),
                    "sla_dias": int(getattr(c, "prazo_etapa_dias", None) or 7),
                    "prioridade": getattr(c, "prioridade", None),
                    "flags": flags,
                    "pia_dias_em_atraso": int(pia_dias) if pia_missing else 0,
                }
            )

    # -----------------
    # CRAS - tarefas
    # -----------------
    if (modulo_norm in (None, "cras")) and CrasTarefa is not None:
        stmt = select(CrasTarefa).where(CrasTarefa.status != "concluida")  # type: ignore
        if mid is not None:
            stmt = stmt.where(or_(CrasTarefa.municipio_id == int(mid), CrasTarefa.municipio_id.is_(None)))  # type: ignore
        if unidade_id is not None:
            stmt = stmt.where(or_(CrasTarefa.unidade_id == int(unidade_id), CrasTarefa.unidade_id.is_(None)))  # type: ignore
        # otimização: pega só as tarefas mais próximas do vencimento
        try:
            stmt = stmt.order_by(CrasTarefa.data_vencimento.asc())  # type: ignore
        except Exception:
            pass
        stmt = stmt.limit(cap_fetch_small)
        tarefas = list(session.exec(stmt).all())
        hoje = date.today()
        for t in tarefas:
            venc = getattr(t, "data_vencimento", None)
            if not venc:
                continue
            due = datetime.combine(venc, time.min)
            dias = _dias_atraso(agora, due)
            if somente_atrasos and dias <= 0:
                continue
            # se nao for somente_atrasos, mostramos todas as tarefas em aberto com vencimento (mesmo futuras)
            if (not somente_atrasos) and isinstance(venc, date) and venc >= hoje:
                # ainda assim pode ser util; mantemos
                pass
            items.append(
                {
                    "modulo": "CRAS",
                    "tipo": "tarefa",
                    "referencia_id": getattr(t, "id", None),
                    "titulo": getattr(t, "titulo", None),
                    "descricao": getattr(t, "descricao", None),
                    "municipio_id": getattr(t, "municipio_id", None),
                    "unidade_id": getattr(t, "unidade_id", None),
                    "territorio": None,
                    "responsavel_id": getattr(t, "responsavel_id", None),
                    "responsavel_nome": getattr(t, "responsavel_nome", None),
                    "etapa_atual": None,
                    "status": getattr(t, "status", None),
                    "ultima_movimentacao_em": getattr(t, "atualizado_em", None) or getattr(t, "criado_em", None),
                    "sla_due_at": due.isoformat(),
                    "dias_em_atraso": int(dias),
                    "prioridade": getattr(t, "prioridade", None),
                }
            )

    # -----------------
    # CRAS - CadUnico atrasado
    # -----------------
    if (modulo_norm in (None, "cras")) and CadunicoPreCadastro is not None:
        stmt = select(CadunicoPreCadastro).where(CadunicoPreCadastro.status.in_(["pendente", "agendado"]))  # type: ignore
        if mid is not None:
            stmt = stmt.where(CadunicoPreCadastro.municipio_id == int(mid))  # type: ignore
        if unidade_id is not None:
            stmt = stmt.where(CadunicoPreCadastro.unidade_id == int(unidade_id))  # type: ignore
        # otimização: pega os pré-cadastros mais antigos
        try:
            stmt = stmt.order_by(CadunicoPreCadastro.criado_em.asc())  # type: ignore
        except Exception:
            pass
        stmt = stmt.limit(cap_fetch_small)
        rows = list(session.exec(stmt).all())
        cut = agora - timedelta(days=int(dias_cadunico))

        # territorio para filtro
        pids = [int(getattr(x, "pessoa_id")) for x in rows if getattr(x, "pessoa_id", None) is not None]
        terr_map2 = _prefetch_territorio_cras(session, pids)

        for x in rows:
            criado = getattr(x, "criado_em", None)
            if not isinstance(criado, datetime):
                continue

            pid = getattr(x, "pessoa_id", None)
            terr2 = terr_map2.get(int(pid), {}) if pid is not None else {}
            terr_key = _norm_territorio(terr2.get("territorio"), terr2.get("bairro"))
            if terr_filtro and terr_filtro not in terr_key.lower():
                continue

            # consideramos atraso se passou do cut
            if somente_atrasos and (criado > cut):
                continue

            # SLA: cut (criado + dias_cadunico)
            due = criado + timedelta(days=int(dias_cadunico))
            ag = getattr(x, "data_agendada", None)
            if isinstance(ag, datetime) and ag < due:
                due = ag
            dias = _dias_atraso(agora, due)

            items.append(
                {
                    "modulo": "CRAS",
                    "tipo": "cadunico",
                    "referencia_id": getattr(x, "id", None),
                    "titulo": f"CadUnico - {getattr(x, 'status', '')} - pre-cadastro #{getattr(x, 'id', '')}",
                    "descricao": None,
                    "municipio_id": getattr(x, "municipio_id", None),
                    "unidade_id": getattr(x, "unidade_id", None),
                    "territorio": terr_key,
                    "responsavel_id": None,
                    "responsavel_nome": None,
                    "etapa_atual": None,
                    "status": getattr(x, "status", None),
                    "ultima_movimentacao_em": getattr(x, "atualizado_em", None) or getattr(x, "criado_em", None),
                    "sla_due_at": due.isoformat() if isinstance(due, datetime) else None,
                    "dias_em_atraso": int(dias),
                    "prioridade": "alta" if dias > 0 else "media",
                    "caso_id": getattr(x, "caso_id", None),
                    "pessoa_id": getattr(x, "pessoa_id", None),
                    "familia_id": getattr(x, "familia_id", None),
                }
            )

    # -----------------
    # CREAS - casos
    # -----------------
    if (modulo_norm in (None, "creas")) and CreasCaso is not None:
        stmt = select(CreasCaso).where(CreasCaso.status == "em_andamento")  # type: ignore
        if mid is not None:
            stmt = stmt.where(CreasCaso.municipio_id == int(mid))  # type: ignore
        # otimização: lê só os casos mais antigos/urgentes (reduz custo em escala)
        try:
            stmt = stmt.order_by(CreasCaso.data_inicio_etapa_atual.asc())  # type: ignore
        except Exception:
            pass
        stmt = stmt.limit(cap_fetch_base)
        casos = list(session.exec(stmt).all())

        pessoa_ids = [int(getattr(c, "pessoa_id")) for c in casos if getattr(c, "pessoa_id", None) is not None]
        terr_map = _prefetch_territorio_cras(session, pessoa_ids)

        fam_map: Dict[int, Dict[str, Optional[str]]] = {}
        if FamiliaSUAS is not None:
            fam_ids = [int(getattr(c, "familia_id")) for c in casos if getattr(c, "familia_id", None) is not None]
            if fam_ids:
                try:
                    fams = session.exec(select(FamiliaSUAS).where(FamiliaSUAS.id.in_(fam_ids))).all()  # type: ignore
                    for f in fams:
                        fid = getattr(f, "id", None)
                        if fid is None:
                            continue
                        fam_map[int(fid)] = {"territorio": getattr(f, "territorio", None), "bairro": getattr(f, "bairro", None)}
                except Exception:
                    fam_map = {}

        for c in casos:
            terr_key = "Sem territorio"
            pid = getattr(c, "pessoa_id", None)
            if pid is not None:
                t = terr_map.get(int(pid), {})
                terr_key = _norm_territorio(t.get("territorio"), t.get("bairro"))
            else:
                fid = getattr(c, "familia_id", None)
                if fid is not None:
                    t = fam_map.get(int(fid), {})
                    terr_key = _norm_territorio(t.get("territorio"), t.get("bairro"))

            if terr_filtro and terr_filtro not in terr_key.lower():
                continue

            due = _creas_case_due_at(c)
            dias = _dias_atraso(agora, due)
            estagn = bool(getattr(c, "estagnado", False))
            motivo_estagn = getattr(c, "motivo_estagnacao", None)

            valid_pendente = False
            if bool(getattr(c, "aguardando_validacao", False)):
                desde = getattr(c, "pendente_validacao_desde", None) or getattr(c, "atualizado_em", None) or getattr(c, "data_inicio_etapa_atual", None)
                if isinstance(desde, datetime) and (agora - desde) > timedelta(hours=48):
                    valid_pendente = True

            em_atraso = (dias > 0) or estagn or valid_pendente
            if somente_atrasos and not em_atraso:
                continue

            rid = getattr(c, "tecnico_responsavel_id", None)
            rnome = user_map.get(int(rid)) if rid is not None else None

            flags = {
                "estagnado": bool(estagn),
                "validacao_pendente": bool(valid_pendente),
            }

            items.append(
                {
                    "modulo": "CREAS",
                    "tipo": "caso",
                    "referencia_id": getattr(c, "id", None),
                    "titulo": f"Caso CREAS #{getattr(c, 'id', '')} - {getattr(c, 'etapa_atual', '')}",
                    "descricao": (
                        "Aguardando validacao" if valid_pendente else (f"Estagnado: {motivo_estagn}" if estagn and motivo_estagn else ("Estagnado" if estagn else None))
                    ),
                    "municipio_id": getattr(c, "municipio_id", None),
                    "unidade_id": getattr(c, "unidade_id", None),
                    "territorio": terr_key,
                    "responsavel_id": rid,
                    "responsavel_nome": rnome,
                    "etapa_atual": getattr(c, "etapa_atual", None),
                    "status": getattr(c, "status", None),
                    "ultima_movimentacao_em": (
                        getattr(c, "atualizado_em", None) or getattr(c, "data_inicio_etapa_atual", None) or getattr(c, "data_abertura", None)
                    ),
                    "sla_due_at": due.isoformat() if isinstance(due, datetime) else None,
                    "dias_em_atraso": int(dias),
                    "dias_na_etapa": _dias_passados(agora, getattr(c, "data_inicio_etapa_atual", None) or getattr(c, "data_abertura", None)),
                    "sla_dias": int(getattr(c, "prazo_etapa_dias", None) or 7),
                    "prioridade": getattr(c, "prioridade", None),
                    "flags": flags,
                }
            )

    # -----------------
    # PopRua - casos
    # -----------------
    if (modulo_norm in (None, "poprua")) and CasoPopRua is not None:
        stmt = select(CasoPopRua).where(CasoPopRua.ativo == True)  # type: ignore
        stmt = stmt.where(CasoPopRua.status != "encerrado")  # type: ignore
        if mid is not None:
            stmt = stmt.where(CasoPopRua.municipio_id == int(mid))  # type: ignore
        # otimização: lê só os casos mais antigos/urgentes (reduz custo em escala)
        try:
            stmt = stmt.order_by(CasoPopRua.data_inicio_etapa_atual.asc())  # type: ignore
        except Exception:
            pass
        stmt = stmt.limit(cap_fetch_base)
        casos = list(session.exec(stmt).all())
        for c in casos:
            due = _poprua_case_due_at(c)
            dias = _dias_atraso(agora, due)
            estagn = bool(getattr(c, "estagnado", False)) or bool(getattr(c, "flag_estagnado", False))
            if somente_atrasos and dias <= 0 and not estagn:
                continue
            motivo = getattr(c, "motivo_estagnacao", None) or getattr(c, "tipo_estagnacao", None)

            # melhor estimativa de "dias na etapa" (prioriza data_inicio_etapa_atual)
            inicio_etapa = (
                getattr(c, "data_inicio_etapa_atual", None)
                or getattr(c, "data_abertura", None)
                or getattr(c, "data_ultima_atualizacao", None)
                or getattr(c, "data_ultima_acao", None)
            )

            items.append(
                {
                    "modulo": "POPRUA",
                    "tipo": "caso",
                    "referencia_id": getattr(c, "id", None),
                    "titulo": f"Caso PopRua #{getattr(c, 'id', '')} - {getattr(c, 'etapa_atual', '')}",
                    "descricao": (f"Estagnado: {motivo}" if estagn and motivo else ("Estagnado" if estagn else None)),
                    "municipio_id": getattr(c, "municipio_id", None),
                    "unidade_id": None,
                    "territorio": None,
                    "responsavel_id": None,
                    "responsavel_nome": None,
                    "etapa_atual": getattr(c, "etapa_atual", None),
                    "status": getattr(c, "status", None),
                    "ultima_movimentacao_em": getattr(c, "data_ultima_atualizacao", None) or getattr(c, "data_ultima_acao", None),
                    "sla_due_at": due.isoformat() if isinstance(due, datetime) else None,
                    "dias_em_atraso": int(dias),
                    "dias_na_etapa": _dias_passados(agora, inicio_etapa),
                    "sla_dias": int(getattr(c, "prazo_etapa_dias", None) or 7),
                    "prioridade": getattr(c, "prioridade", None),
                    "flags": {"estagnado": bool(estagn)},
                }
            )

        # -----------------
    # Rede - encaminhamentos CRAS (devolutiva obrigatória + SLA por etapa)
    # -----------------
    if (modulo_norm in (None, "rede")) and CrasEncaminhamento is not None:
        stmt = select(CrasEncaminhamento)
        if mid is not None:
            stmt = stmt.where(CrasEncaminhamento.municipio_id == int(mid))  # type: ignore
        if unidade_id is not None:
            stmt = stmt.where(CrasEncaminhamento.unidade_id == int(unidade_id))  # type: ignore
        # otimização: limita a leitura para reduzir custo em escala
        try:
            stmt = stmt.order_by(CrasEncaminhamento.criado_em.asc())  # type: ignore
        except Exception:
            pass
        stmt = stmt.limit(cap_fetch_base)
        encs = list(session.exec(stmt).all())
        finais = {"concluido", "cancelado"}
        for e in encs:
            st = _cras_enc_status(e)
            if st in finais:
                continue

            due = _enc_due_at(e, sla_lookup)
            dias = _dias_atraso(agora, due)
            if somente_atrasos and dias <= 0:
                continue

            ref_dt = _cras_enc_ref_dt(e)
            sla_dias = _cras_enc_sla_dias(e, sla_lookup)

            next_step = _CRAS_ENC_NEXT.get(st)
            motivo_trava = None
            if dias > 0:
                motivo_trava = f"Etapa {next_step or 'seguinte'} em atraso"
            else:
                motivo_trava = f"Aguardando {next_step}" if next_step else "Aguardando conclusão"

            items.append(
                {
                    "modulo": "REDE",
                    "tipo": "encaminhamento",
                    "referencia_id": getattr(e, "id", None),
                    "titulo": f"Encaminhamento #{getattr(e, 'id', '')} - {str(getattr(e, 'destino_tipo', '')).upper()} - {getattr(e, 'destino_nome', '')}",
                    "descricao": None,
                    "municipio_id": getattr(e, "municipio_id", None),
                    "unidade_id": getattr(e, "unidade_id", None),
                    "territorio": None,
                    "responsavel_id": None,
                    "responsavel_nome": getattr(e, "criado_por_nome", None),
                    "etapa_atual": st,
                    "status": getattr(e, "status", None),
                    "ultima_movimentacao_em": getattr(e, "atualizado_em", None) or ref_dt or getattr(e, "enviado_em", None) or getattr(e, "criado_em", None),
                    "sla_due_at": due.isoformat() if isinstance(due, datetime) else None,
                    "dias_em_atraso": int(dias),
                    "dias_na_etapa": _dias_passados(agora, ref_dt),
                    "sla_dias": int(sla_dias),
                    "prioridade": None,
                    "motivo_trava": motivo_trava,
                    "destino_tipo": getattr(e, "destino_tipo", None),
                    "destino_nome": getattr(e, "destino_nome", None),
                }
            )

        # -----------------
    # Rede - intermunicipal (SLA por etapa)
    # -----------------
    if (modulo_norm in (None, "rede")) and EncaminhamentoIntermunicipal is not None:
        stmt = select(EncaminhamentoIntermunicipal)
        if mid is not None:
            stmt = stmt.where(
                or_(
                    EncaminhamentoIntermunicipal.municipio_origem_id == int(mid),  # type: ignore
                    EncaminhamentoIntermunicipal.municipio_destino_id == int(mid),  # type: ignore
                )
            )
        # otimização: limita a leitura para reduzir custo em escala
        try:
            stmt = stmt.order_by(EncaminhamentoIntermunicipal.criado_em.asc())  # type: ignore
        except Exception:
            pass
        stmt = stmt.limit(cap_fetch_base)
        encs = list(session.exec(stmt).all())
        finais = {"concluido", "cancelado"}
        for e in encs:
            st = _inter_status(e)
            if st in finais:
                continue

            due = _inter_due_at(e, sla_lookup)
            dias = _dias_atraso(agora, due)
            if somente_atrasos and dias <= 0:
                continue

            ref_dt = _inter_ref_dt(e)
            sla_dias = _inter_sla_dias(e, sla_lookup)

            next_step = _INTER_NEXT.get(st)
            motivo_trava = None
            if dias > 0:
                motivo_trava = f"Etapa {next_step or 'seguinte'} em atraso"
            else:
                motivo_trava = f"Aguardando {next_step}" if next_step else "Aguardando conclusão"

            items.append(
                {
                    "modulo": "REDE",
                    "tipo": "encaminhamento_intermunicipal",
                    "referencia_id": getattr(e, "id", None),
                    "titulo": f"Intermunicipal #{getattr(e, 'id', '')} - {getattr(e, 'status', '')}",
                    "descricao": None,
                    "municipio_id": getattr(e, "municipio_origem_id", None),
                    "unidade_id": None,
                    "territorio": None,
                    "responsavel_id": None,
                    "responsavel_nome": getattr(e, "autorizado_por_nome", None),
                    "etapa_atual": st,
                    "status": getattr(e, "status", None),
                    "ultima_movimentacao_em": getattr(e, "atualizado_em", None) or ref_dt or getattr(e, "criado_em", None),
                    "sla_due_at": due.isoformat() if isinstance(due, datetime) else None,
                    "dias_em_atraso": int(dias),
                    "dias_na_etapa": _dias_passados(agora, ref_dt),
                    "sla_dias": int(sla_dias),
                    "prioridade": None,
                    "motivo_trava": motivo_trava,
                    "municipio_origem_id": getattr(e, "municipio_origem_id", None),
                    "municipio_destino_id": getattr(e, "municipio_destino_id", None),
                }
            )

    # -----------------
    # Terceiro Setor (OSC) - prestações pendentes
    # -----------------
    if (modulo_norm in (None, "osc")) and OscPrestacaoContas is not None:
        stmt = select(OscPrestacaoContas).where(OscPrestacaoContas.status.notin_(["aprovado", "reprovado"]))  # type: ignore
        if mid is not None:
            stmt = stmt.where(OscPrestacaoContas.municipio_id == int(mid))  # type: ignore
        # otimização: pega as prestações com prazo mais próximo/antigo
        try:
            stmt = stmt.order_by(OscPrestacaoContas.prazo_entrega.asc())  # type: ignore
        except Exception:
            pass
        stmt = stmt.limit(cap_fetch_small)
        prests = list(session.exec(stmt).all())
        for pc in prests:
            prazo = getattr(pc, "prazo_entrega", None)
            due = datetime.combine(prazo, time.min) if isinstance(prazo, date) else None
            dias = _dias_atraso(agora, due)
            if somente_atrasos and dias <= 0:
                continue

            rid = getattr(pc, "responsavel_id", None)
            rnome = user_map.get(int(rid)) if rid is not None else getattr(pc, "responsavel_nome", None)
            comp = getattr(pc, "competencia", None)
            titulo = f"Prestação de contas #{getattr(pc, 'id', '')}" + (f" · {comp}" if comp else "")

            items.append(
                {
                    "modulo": "OSC",
                    "tipo": "prestacao_contas",
                    "referencia_id": getattr(pc, "id", None),
                    "titulo": titulo,
                    "descricao": getattr(pc, "observacao", None),
                    "municipio_id": getattr(pc, "municipio_id", None),
                    "unidade_id": None,
                    "territorio": None,
                    "responsavel_id": rid,
                    "responsavel_nome": rnome,
                    "etapa_atual": None,
                    "status": getattr(pc, "status", None),
                    "ultima_movimentacao_em": getattr(pc, "atualizado_em", None) or getattr(pc, "criado_em", None),
                    "sla_due_at": due.isoformat() if isinstance(due, datetime) else None,
                    "dias_em_atraso": int(dias),
                    "prioridade": "alta" if dias > 0 else "media",
                }
            )

    # Padroniza campos extras (SLA em risco, motivo, etc.)
    _normalize_workitems(items, agora, risk_window=risk_window)

    # Filtro opcional: somente itens em risco (ou urgentes)
    if somente_em_risco:
        if somente_atrasos:
            items = [it for it in items if bool(it.get("sla_em_risco")) or bool(it.get("sla_estourado"))]
        else:
            items = [it for it in items if bool(it.get("sla_em_risco"))]

    # Ordena + pagina
    items.sort(key=_sort_key_item)
    total = len(items)
    paged = items[offset : offset + limit]

    return {
        "perfil": _perfil(usuario),
        "filtros": {
            "municipio_id": mid,
            "unidade_id": unidade_id,
            "territorio": territorio,
            "dias_cadunico": dias_cadunico,
            "dias_pia": dias_pia,
            "modulo": modulo_norm,
            "somente_atrasos": somente_atrasos,
            "somente_em_risco": somente_em_risco,
            "janela_risco_horas": janela_risco_horas,
        },
        "total": total,
        "limit": limit,
        "offset": offset,
        "items": paged,
    }

    try:
        if not nocache:
            _cache_set(cache_key, out)
    except Exception:
        pass
    return out


@router.get("/dashboard/sla")
def gestao_dashboard_sla(
    municipio_id: Optional[int] = Query(default=None, description="Filtro opcional por município (gestor/admin)."),
    group_by: str = Query(default="modulo", description="modulo|unidade|territorio|etapa|responsavel|destino"),
    janela_risco_horas: int = Query(default=24, ge=1, le=168, description="Janela (horas) para considerar SLA em risco (vence em breve) — usado em group_by=destino."),
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    """Ranking de gargalos (SLA).

    - Padrão: calcula a partir da fila em atraso.
    - group_by=destino: inclui métricas de compliance (devolutiva no prazo e tempo médio) por destino.
    """

    group = (group_by or "modulo").strip().lower()

    # Caso especial: ranking por destino com métricas
    if group == "destino":
        metricas = gestao_rede_metricas(
            municipio_id=municipio_id,
            janela_risco_horas=int(janela_risco_horas),
            limit_destinos=200,
            limit_municipios=200,
            session=session,
            usuario=usuario,
        )

        items: List[Dict[str, Any]] = []

        # CRAS destinos (CREAS/OSC/etc.)
        for d in (metricas.get("cras") or {}).get("por_destino") or []:
            dt = str(d.get("destino_tipo") or "outro").strip().lower()
            dn = str(d.get("destino_nome") or "Sem destino").strip()
            items.append(
                {
                    "chave": f"{dt.upper()} · {dn}",
                    "tipo": "cras_destino",
                    "destino_tipo": dt,
                    "destino_nome": dn,
                    "total": int(d.get("total") or 0),
                    "pendentes": int(d.get("pendentes") or 0),
                    "concluidos": int(d.get("concluidos") or 0),
                    "cancelados": int(d.get("cancelados") or 0),
                    "atrasados": int(d.get("atrasados") or 0),
                    "em_risco": int(d.get("em_risco") or 0),
                    "pct_recebido_no_prazo": float(d.get("pct_recebido_no_prazo") or 0.0),
                    "pct_devolutiva_no_prazo": float(d.get("pct_devolutiva_no_prazo") or 0.0),
                    "pct_conclusao_no_prazo": float(d.get("pct_conclusao_no_prazo") or 0.0),
                    "avg_horas_ate_recebido": d.get("avg_horas_ate_recebido"),
                    "avg_horas_ate_devolutiva": d.get("avg_horas_ate_devolutiva"),
                    "avg_dias_ate_conclusao": d.get("avg_dias_ate_conclusao"),
                    "score": float(d.get("score") or 0.0),
                    "faixa": d.get("faixa"),
                }
            )

        # Intermunicipal por município destino
        for d in (metricas.get("intermunicipal") or {}).get("por_municipio_destino") or []:
            did = d.get("municipio_destino_id")
            dnome = str(d.get("municipio_destino_nome") or f"Município {did}")
            items.append(
                {
                    "chave": f"Município destino · {dnome}",
                    "tipo": "intermunicipal_destino",
                    "municipio_destino_id": did,
                    "municipio_destino_nome": dnome,
                    "total": int(d.get("total") or 0),
                    "pendentes": int(d.get("pendentes") or 0),
                    "concluidos": int(d.get("concluidos") or 0),
                    "cancelados": int(d.get("cancelados") or 0),
                    "atrasados": int(d.get("atrasados") or 0),
                    "em_risco": int(d.get("em_risco") or 0),
                    "pct_contato_no_prazo": float(d.get("pct_contato_no_prazo") or 0.0),
                    "avg_horas_ate_contato": d.get("avg_horas_ate_contato"),
                    "score": float(d.get("score") or 0.0),
                    "faixa": d.get("faixa"),
                    "score_breakdown": d.get("score_breakdown"),
                    "recomendacao": d.get("recomendacao"),
                }
            )

        def pct_key(x: Dict[str, Any]) -> float:
            if x.get("tipo") == "intermunicipal_destino":
                return float(x.get("pct_contato_no_prazo") or 0.0)
            return float(x.get("pct_devolutiva_no_prazo") or 0.0)

        def avg_key(x: Dict[str, Any]) -> float:
            if x.get("tipo") == "intermunicipal_destino":
                v = x.get("avg_horas_ate_contato")
            else:
                v = x.get("avg_horas_ate_devolutiva")
            try:
                return float(v or 0.0)
            except Exception:
                return 0.0

        # Ordena: mais atrasos, mais em risco, menor compliance, maior tempo médio
        items.sort(
            key=lambda x: (
                float(x.get("score") or 0.0),
                -int(x.get("atrasados") or 0),
                -int(x.get("em_risco") or 0),
                pct_key(x),
                -avg_key(x),
            )
        )

        return {
            "perfil": _perfil(usuario),
            "group_by": group,
            "janela_risco_horas": int(janela_risco_horas),
            "items": items,
        }

    # Padrão: reusa fila em atraso (sem paginação)
    # Importante: ao chamar esta função internamente (fora do FastAPI),
    # precisamos passar explicitamente os valores padrão (e não deixar
    # os defaults `Query(...)` vazarem), senão ocorre erro 500.
    fila = gestao_fila(
        municipio_id=municipio_id,
        unidade_id=None,
        territorio=None,
        dias_cadunico=30,
        dias_pia=15,
        janela_risco_horas=int(janela_risco_horas),
        modulo=None,
        somente_atrasos=True,
        somente_em_risco=False,
        limit=500,
        offset=0,
        session=session,
        usuario=usuario,
    )
    items = list(fila.get("items") or [])

    muni_nome: Dict[int, str] = {}
    if group == "destino" and Municipio is not None:
        try:
            for mid2, nome2 in session.exec(select(Municipio.id, Municipio.nome)).all():  # type: ignore
                if mid2 is None:
                    continue
                muni_nome[int(mid2)] = str(nome2)
        except Exception:
            muni_nome = {}

    def key_for(it: Dict[str, Any]) -> str:
        if group == "unidade":
            return str(it.get("unidade_id") or "Sem unidade")
        if group == "territorio":
            return str(it.get("territorio") or "Sem território")
        if group == "etapa":
            return str(it.get("etapa_atual") or "Sem etapa")
        if group == "responsavel":
            return str(it.get("responsavel_nome") or it.get("responsavel_id") or "Sem responsável")
        if group == "destino":
            mod = str(it.get("modulo") or "").upper()
            if mod == "REDE":
                if str(it.get("tipo") or "") == "encaminhamento":
                    dt = str(it.get("destino_tipo") or "").strip()
                    dn = str(it.get("destino_nome") or "").strip()
                    if dt or dn:
                        return f"{dt.upper()} · {dn or 'Sem destino'}"
                if str(it.get("tipo") or "") == "encaminhamento_intermunicipal":
                    dest_id = it.get("municipio_destino_id")
                    if dest_id is not None:
                        try:
                            did = int(dest_id)
                            return f"Município destino · {muni_nome.get(did, f'Município {did}') }"
                        except Exception:
                            return f"Município destino · {dest_id}"
                    return "Município destino · Sem destino"
            return str(it.get("modulo") or "MÓDULO")

        # default: modulo
        return str(it.get("modulo") or "MÓDULO")

    buckets: Dict[str, Dict[str, Any]] = {}
    for it in items:
        k = key_for(it)
        b = buckets.setdefault(
            k,
            {
                "chave": k,
                "count": 0,
                "max_dias_atraso": 0,
                "total_dias_atraso": 0,
            },
        )
        dias = int(it.get("dias_em_atraso") or 0)
        b["count"] += 1
        b["total_dias_atraso"] += dias
        b["max_dias_atraso"] = max(int(b["max_dias_atraso"]), dias)

    out: List[Dict[str, Any]] = []
    for k, b in buckets.items():
        cnt = int(b["count"]) or 1
        out.append(
            {
                "chave": k,
                "count": int(b["count"]),
                "media_dias_atraso": round(float(b["total_dias_atraso"]) / cnt, 2),
                "max_dias_atraso": int(b["max_dias_atraso"]),
            }
        )

    out.sort(key=lambda x: (-int(x.get("count") or 0), -int(x.get("max_dias_atraso") or 0)))

    return {
        "perfil": _perfil(usuario),
        "group_by": group,
        "items": out,
    }


@router.get("/rede/encaminhamentos")
def gestao_rede_encaminhamentos(
    municipio_id: Optional[int] = Query(default=None, description="Filtro opcional por município (gestor/admin)."),
    janela_risco_horas: int = Query(default=24, ge=1, le=168, description="Janela (horas) para considerar SLA em risco (vence em breve)."),
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    """Visão de rede: encaminhamentos (CRAS) + intermunicipais (SLA por etapa)."""

    agora = datetime.utcnow()
    risk_window = timedelta(hours=int(janela_risco_horas))
    mid = _resolver_municipio_id(usuario, municipio_id)

    sla_rules = _prefetch_sla_regras(session, mid)

    def sla_lookup(municipio_id: Optional[int], unidade_tipo: Optional[str], unidade_id: Optional[int], modulo: str, etapa: str, default: int) -> int:
        return _resolver_sla_dias(sla_rules, municipio_id, unidade_tipo, unidade_id, modulo, etapa, default)

    out: Dict[str, Any] = {"municipio_id": mid, "cras": {}, "intermunicipal": {}}

    # Prefetch nomes de municípios (se existir)
    muni_nome: Dict[int, str] = {}
    if Municipio is not None:
        try:
            for mid2, nome2 in session.exec(select(Municipio.id, Municipio.nome)).all():  # type: ignore
                if mid2 is None:
                    continue
                muni_nome[int(mid2)] = str(nome2)
        except Exception:
            muni_nome = {}

    # CRAS
    if CrasEncaminhamento is not None:
        stmt = select(CrasEncaminhamento)
        if mid is not None:
            stmt = stmt.where(CrasEncaminhamento.municipio_id == int(mid))  # type: ignore
        encs = list(session.exec(stmt).all())

        por_status: Dict[str, int] = {}
        por_destino_tipo: Dict[str, int] = {}
        por_destino_nome: Dict[str, int] = {}

        finais = {"concluido", "cancelado"}
        aguardando = 0
        atrasados = 0
        em_risco = 0

        # Gargalos por destino
        gargalos: Dict[Tuple[str, str], Dict[str, Any]] = {}

        for e in encs:
            st = _cras_enc_status(e)
            por_status[st] = por_status.get(st, 0) + 1

            dest_tipo = str(getattr(e, "destino_tipo", "") or "outro").strip().lower()
            dest_nome = str(getattr(e, "destino_nome", "") or "Sem destino").strip()

            por_destino_tipo[dest_tipo] = por_destino_tipo.get(dest_tipo, 0) + 1
            por_destino_nome[dest_nome] = por_destino_nome.get(dest_nome, 0) + 1

            if st in finais:
                continue

            aguardando += 1
            due = _enc_due_at(e, sla_lookup)
            dias = _dias_atraso(agora, due)

            if dias > 0:
                atrasados += 1
            elif due and agora < due and (due - agora) <= risk_window:
                em_risco += 1

            key = (dest_tipo, dest_nome)
            g = gargalos.setdefault(
                key,
                {
                    "destino_tipo": dest_tipo,
                    "destino_nome": dest_nome,
                    "aguardando": 0,
                    "atrasados": 0,
                    "em_risco": 0,
                    "max_dias_em_atraso": 0,
                },
            )
            g["aguardando"] += 1
            if dias > 0:
                g["atrasados"] += 1
                g["max_dias_em_atraso"] = max(int(g["max_dias_em_atraso"] or 0), int(dias))
            elif due and agora < due and (due - agora) <= risk_window:
                g["em_risco"] += 1

        top_gargalos = list(gargalos.values())
        top_gargalos.sort(key=lambda x: (-int(x.get("atrasados") or 0), -int(x.get("em_risco") or 0), -int(x.get("max_dias_em_atraso") or 0)))
        top_gargalos = top_gargalos[:10]

        # Enriquecer gargalos com compliance (quando disponível)
        try:
            met = gestao_rede_metricas(
                municipio_id=municipio_id,
                janela_risco_horas=int(janela_risco_horas),
                limit_destinos=200,
                limit_municipios=200,
                session=session,
                usuario=usuario,
            )
            mp = {}
            for d in (met.get('cras') or {}).get('por_destino') or []:
                k = (str(d.get('destino_tipo') or '').strip().lower(), str(d.get('destino_nome') or '').strip())
                mp[k] = d
            for g in top_gargalos:
                k = (str(g.get('destino_tipo') or '').strip().lower(), str(g.get('destino_nome') or '').strip())
                d = mp.get(k)
                if not d:
                    continue
                g['pct_devolutiva_no_prazo'] = float(d.get('pct_devolutiva_no_prazo') or 0.0)
                g['avg_horas_ate_devolutiva'] = d.get('avg_horas_ate_devolutiva')
                g['score'] = float(d.get('score') or 0.0)
        except Exception:
            pass

        out["cras"] = {
            "total": len(encs),
            "aguardando": aguardando,
            "atrasados": atrasados,
            "em_risco": em_risco,
            "por_status": por_status,
            "por_destino_tipo": por_destino_tipo,
            "por_destino_nome": por_destino_nome,
            "top_gargalos": top_gargalos,
        }

    # Intermunicipal
    if EncaminhamentoIntermunicipal is not None:
        stmt = select(EncaminhamentoIntermunicipal)
        if mid is not None:
            stmt = stmt.where(
                or_(
                    EncaminhamentoIntermunicipal.municipio_origem_id == int(mid),  # type: ignore
                    EncaminhamentoIntermunicipal.municipio_destino_id == int(mid),  # type: ignore
                )
            )
        encs = list(session.exec(stmt).all())

        por_status: Dict[str, int] = {}
        por_destino_muni: Dict[str, int] = {}
        finais = {"concluido", "cancelado"}
        aguardando = 0
        atrasados = 0
        em_risco = 0

        gargalos2: Dict[int, Dict[str, Any]] = {}

        for e in encs:
            st = _inter_status(e)
            por_status[st] = por_status.get(st, 0) + 1

            dest_id = getattr(e, "municipio_destino_id", None)
            dest_key = str(dest_id) if dest_id is not None else "Sem destino"
            por_destino_muni[dest_key] = por_destino_muni.get(dest_key, 0) + 1

            if st in finais:
                continue

            aguardando += 1
            due = _inter_due_at(e, sla_lookup)
            dias = _dias_atraso(agora, due)

            if dias > 0:
                atrasados += 1
            elif due and agora < due and (due - agora) <= risk_window:
                em_risco += 1

            if dest_id is not None:
                g = gargalos2.setdefault(
                    int(dest_id),
                    {
                        "municipio_destino_id": int(dest_id),
                        "municipio_destino_nome": muni_nome.get(int(dest_id), f"Município {dest_id}"),
                        "aguardando": 0,
                        "atrasados": 0,
                        "em_risco": 0,
                        "max_dias_em_atraso": 0,
                    },
                )
                g["aguardando"] += 1
                if dias > 0:
                    g["atrasados"] += 1
                    g["max_dias_em_atraso"] = max(int(g["max_dias_em_atraso"] or 0), int(dias))
                elif due and agora < due and (due - agora) <= risk_window:
                    g["em_risco"] += 1

        top_gargalos2 = list(gargalos2.values())
        top_gargalos2.sort(key=lambda x: (-int(x.get("atrasados") or 0), -int(x.get("em_risco") or 0), -int(x.get("max_dias_em_atraso") or 0)))
        top_gargalos2 = top_gargalos2[:10]

        # Enriquecer gargalos intermunicipais com compliance (quando disponível)
        try:
            met = gestao_rede_metricas(
                municipio_id=municipio_id,
                janela_risco_horas=int(janela_risco_horas),
                limit_destinos=200,
                limit_municipios=200,
                session=session,
                usuario=usuario,
            )
            mp = {}
            for d in (met.get('intermunicipal') or {}).get('por_municipio_destino') or []:
                try:
                    mp[int(d.get('municipio_destino_id'))] = d
                except Exception:
                    continue
            for g in top_gargalos2:
                try:
                    did = int(g.get('municipio_destino_id'))
                except Exception:
                    continue
                d = mp.get(did)
                if not d:
                    continue
                g['pct_contato_no_prazo'] = float(d.get('pct_contato_no_prazo') or 0.0)
                g['avg_horas_ate_contato'] = d.get('avg_horas_ate_contato')
                g['score'] = float(d.get('score') or 0.0)
        except Exception:
            pass

        out["intermunicipal"] = {
            "total": len(encs),
            "aguardando": aguardando,
            "atrasados": atrasados,
            "em_risco": em_risco,
            "por_status": por_status,
            "por_destino_municipio": por_destino_muni,
            "top_gargalos": top_gargalos2,
        }

    return out


@router.get("/rede/metricas")
def gestao_rede_metricas(
    municipio_id: Optional[int] = Query(default=None, description="Filtro opcional por município (gestor/admin)."),
    janela_risco_horas: int = Query(default=24, ge=1, le=168, description="Janela (horas) para considerar SLA em risco (vence em breve)."),
    limit_destinos: int = Query(default=20, ge=1, le=200, description="Limite de destinos retornados (CRAS)."),
    limit_municipios: int = Query(default=20, ge=1, le=200, description="Limite de municípios retornados (intermunicipal)."),
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    """Métricas de rede para a Gestão.

    Foco: tempo médio de devolutiva e compliance por destino.
    Não altera o front; serve para o dashboard do secretário.

    Retorna:
      - CRAS: métricas por destino (tipo+nome)
      - Intermunicipal: métricas por município destino
    """

    agora = datetime.utcnow()
    risk_window = timedelta(hours=int(janela_risco_horas))
    mid = _resolver_municipio_id(usuario, municipio_id)

    sla_rules = _prefetch_sla_regras(session, mid)

    def sla_lookup(municipio_id: Optional[int], unidade_tipo: Optional[str], unidade_id: Optional[int], modulo: str, etapa: str, default: int) -> int:
        return _resolver_sla_dias(sla_rules, municipio_id, unidade_tipo, unidade_id, modulo, etapa, default)

    def _mean(values: List[float]) -> Optional[float]:
        if not values:
            return None
        return round(sum(values) / max(len(values), 1), 2)

    def _pct(num: int, den: int) -> float:
        if den <= 0:
            return 0.0
        return round(100.0 * float(num) / float(den), 1)

    # Prefetch nomes de municípios (se existir)
    muni_nome: Dict[int, str] = {}
    if Municipio is not None:
        try:
            for mid2, nome2 in session.exec(select(Municipio.id, Municipio.nome)).all():  # type: ignore
                if mid2 is None:
                    continue
                muni_nome[int(mid2)] = str(nome2)
        except Exception:
            muni_nome = {}

    out: Dict[str, Any] = {
        "municipio_id": mid,
        "janela_risco_horas": int(janela_risco_horas),
        "cras": {"por_destino": []},
        "intermunicipal": {"por_municipio_destino": []},
    }

    # =========================
    # CRAS encaminhamentos
    # =========================
    if CrasEncaminhamento is not None:
        stmt = select(CrasEncaminhamento)
        if mid is not None:
            stmt = stmt.where(CrasEncaminhamento.municipio_id == int(mid))  # type: ignore
        encs = list(session.exec(stmt).all())

        finais = {"concluido", "cancelado"}

        buckets: Dict[Tuple[str, str], Dict[str, Any]] = {}
        for e in encs:
            st = _cras_enc_status(e)
            dest_tipo = str(getattr(e, "destino_tipo", "") or "outro").strip().lower()
            dest_nome = str(getattr(e, "destino_nome", "") or "Sem destino").strip()
            key = (dest_tipo, dest_nome)
            b = buckets.setdefault(
                key,
                {
                    "destino_tipo": dest_tipo,
                    "destino_nome": dest_nome,
                    "total": 0,
                    "pendentes": 0,
                    "concluidos": 0,
                    "cancelados": 0,
                    "atrasados": 0,
                    "em_risco": 0,
                    "recebidos": 0,
                    "recebidos_no_prazo": 0,
                    "devolutivas": 0,
                    "devolutivas_no_prazo": 0,
                    "conclusoes": 0,
                    "conclusoes_no_prazo": 0,
                    "avg_horas_ate_recebido": None,
                    "avg_horas_ate_devolutiva": None,
                    "avg_dias_ate_conclusao": None,
                },
            )

            b["total"] += 1

            # Situação atual (para atrasos/em_risco)
            if st in finais:
                if st == "concluido":
                    b["concluidos"] += 1
                if st == "cancelado":
                    b["cancelados"] += 1
            else:
                b["pendentes"] += 1
                due = _cras_enc_due_at(e, sla_lookup)
                dias = _dias_atraso(agora, due)
                if dias > 0:
                    b["atrasados"] += 1
                elif due and agora < due and (due - agora) <= risk_window:
                    b["em_risco"] += 1

            # Tempo até recebido (SLA de etapa "enviado")
            enviado_em = getattr(e, "enviado_em", None)
            recebido_em = getattr(e, "recebido_em", None)
            if isinstance(enviado_em, datetime) and isinstance(recebido_em, datetime):
                b["recebidos"] += 1
                horas = max(0.0, (recebido_em - enviado_em).total_seconds() / 3600.0)
                b.setdefault("_recv_h", []).append(horas)
                # no prazo: recebido <= enviado + SLA(enviado)
                if recebido_em <= (enviado_em + timedelta(days=int(sla_lookup(getattr(e, "municipio_id", None), "cras", getattr(e, "unidade_id", None), "cras_encaminhamento", "enviado", int(_CRAS_ENC_SLA.get("enviado", 2)))))):
                    b["recebidos_no_prazo"] += 1

            # Tempo até devolutiva (SLA de etapa "atendido")
            atendido_em = getattr(e, "atendido_em", None)
            devolutiva_em = getattr(e, "devolutiva_em", None)
            if isinstance(devolutiva_em, datetime):
                b["devolutivas"] += 1
                # preferimos medir do "atendido" ao "devolutiva"; fallback no enviado
                base = atendido_em if isinstance(atendido_em, datetime) else enviado_em
                if isinstance(base, datetime):
                    horas = max(0.0, (devolutiva_em - base).total_seconds() / 3600.0)
                    b.setdefault("_dev_h", []).append(horas)
                # no prazo: devolutiva <= atendido + SLA(atendido)
                if isinstance(atendido_em, datetime):
                    if devolutiva_em <= (atendido_em + timedelta(days=int(sla_lookup(getattr(e, "municipio_id", None), "cras", getattr(e, "unidade_id", None), "cras_encaminhamento", "atendido", int(_CRAS_ENC_SLA.get("atendido", 2)))))):
                        b["devolutivas_no_prazo"] += 1

            # Conclusão (SLA de etapa "devolutiva")
            concluido_em = getattr(e, "concluido_em", None)
            if isinstance(concluido_em, datetime):
                b["conclusoes"] += 1
                if isinstance(enviado_em, datetime):
                    dias_tot = max(0.0, (concluido_em - enviado_em).total_seconds() / 86400.0)
                    b.setdefault("_conc_d", []).append(dias_tot)
                # no prazo: concluido <= devolutiva + SLA(devolutiva)
                if isinstance(devolutiva_em, datetime):
                    if concluido_em <= (devolutiva_em + timedelta(days=int(sla_lookup(getattr(e, "municipio_id", None), "cras", getattr(e, "unidade_id", None), "cras_encaminhamento", "devolutiva", int(_CRAS_ENC_SLA.get("devolutiva", 2)))))):
                        b["conclusoes_no_prazo"] += 1

        rows: List[Dict[str, Any]] = []
        for b in buckets.values():
            recv_h = b.pop("_recv_h", []) if "_recv_h" in b else []
            dev_h = b.pop("_dev_h", []) if "_dev_h" in b else []
            conc_d = b.pop("_conc_d", []) if "_conc_d" in b else []
            b["avg_horas_ate_recebido"] = _mean([float(x) for x in recv_h])
            b["avg_horas_ate_devolutiva"] = _mean([float(x) for x in dev_h])
            b["avg_dias_ate_conclusao"] = _mean([float(x) for x in conc_d])
            b["pct_recebido_no_prazo"] = _pct(int(b.get("recebidos_no_prazo") or 0), int(b.get("recebidos") or 0))
            b["pct_devolutiva_no_prazo"] = _pct(int(b.get("devolutivas_no_prazo") or 0), int(b.get("devolutivas") or 0))
            b["pct_conclusao_no_prazo"] = _pct(int(b.get("conclusoes_no_prazo") or 0), int(b.get("conclusoes") or 0))
            b["score"] = _score_cras(b)
            b["faixa"] = _faixa(float(b["score"]))
            b["score_breakdown"], b["recomendacao"] = _score_explicavel_cras(b)
            rows.append(b)

        # Ordena: mais atrasos, depois menor compliance de devolutiva
        rows.sort(
            key=lambda x: (
                float(x.get("score") or 0.0),
                -int(x.get("atrasados") or 0),
                -int(x.get("em_risco") or 0),
                float(x.get("pct_devolutiva_no_prazo") or 0.0),
                -int(x.get("pendentes") or 0),
            )
        )
        out["cras"]["por_destino"] = rows[: int(limit_destinos)]

    # =========================
    # Intermunicipal
    # =========================
    if EncaminhamentoIntermunicipal is not None:
        stmt = select(EncaminhamentoIntermunicipal)
        if mid is not None:
            stmt = stmt.where(
                or_(
                    EncaminhamentoIntermunicipal.municipio_origem_id == int(mid),  # type: ignore
                    EncaminhamentoIntermunicipal.municipio_destino_id == int(mid),  # type: ignore
                )
            )
        encs = list(session.exec(stmt).all())

        finais = {"concluido", "cancelado"}

        buckets2: Dict[int, Dict[str, Any]] = {}
        for e in encs:
            dest_id = getattr(e, "municipio_destino_id", None)
            if dest_id is None:
                continue
            did = int(dest_id)
            st = _inter_status(e)
            b = buckets2.setdefault(
                did,
                {
                    "municipio_destino_id": did,
                    "municipio_destino_nome": muni_nome.get(did, f"Município {did}"),
                    "total": 0,
                    "pendentes": 0,
                    "concluidos": 0,
                    "cancelados": 0,
                    "atrasados": 0,
                    "em_risco": 0,
                    "contatos": 0,
                    "contatos_no_prazo": 0,
                    "avg_horas_ate_contato": None,
                },
            )

            b["total"] += 1

            if st in finais:
                if st == "concluido":
                    b["concluidos"] += 1
                if st == "cancelado":
                    b["cancelados"] += 1
            else:
                b["pendentes"] += 1
                due = _inter_due_at(e, sla_lookup)
                dias = _dias_atraso(agora, due)
                if dias > 0:
                    b["atrasados"] += 1
                elif due and agora < due and (due - agora) <= risk_window:
                    b["em_risco"] += 1

            criado_em = getattr(e, "criado_em", None)
            contato_em = getattr(e, "contato_em", None)
            if isinstance(criado_em, datetime) and isinstance(contato_em, datetime):
                b["contatos"] += 1
                horas = max(0.0, (contato_em - criado_em).total_seconds() / 3600.0)
                b.setdefault("_cont_h", []).append(horas)
                if contato_em <= (criado_em + timedelta(days=int(sla_lookup((getattr(e, "municipio_destino_id", None) or getattr(e, "municipio_origem_id", None)), None, None, "rede_intermunicipal", "solicitado", int(_INTER_SLA.get("solicitado", 2)))))):
                    b["contatos_no_prazo"] += 1

        rows2: List[Dict[str, Any]] = []
        for b in buckets2.values():
            cont_h = b.pop("_cont_h", []) if "_cont_h" in b else []
            b["avg_horas_ate_contato"] = _mean([float(x) for x in cont_h])
            b["pct_contato_no_prazo"] = _pct(int(b.get("contatos_no_prazo") or 0), int(b.get("contatos") or 0))
            b["score"] = _score_inter(b)
            b["faixa"] = _faixa(float(b["score"]))
            b["score_breakdown"], b["recomendacao"] = _score_explicavel_inter(b)
            rows2.append(b)

        rows2.sort(key=lambda x: (float(x.get("score") or 0.0), -int(x.get("atrasados") or 0), -int(x.get("em_risco") or 0), float(x.get("pct_contato_no_prazo") or 0.0)))
        out["intermunicipal"]["por_municipio_destino"] = rows2[: int(limit_municipios)]

    return out


@router.get("/rede/timeline")
def gestao_rede_timeline(
    tipo: str = Query(..., description="cras|intermunicipal"),
    id: int = Query(..., ge=1, description="ID do encaminhamento"),
    municipio_id: Optional[int] = Query(default=None, description="Filtro opcional por município (gestor/admin)"),
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    """Linha do tempo (auditoria) da REDE.

    - tipo=cras: encaminhamentos do CRAS (destino CREAS/OSC/etc.)
    - tipo=intermunicipal: encaminhamentos intermunicipais

    Retorna eventos registrados (quando existirem) e também completa com marcos (timestamps)
    para não ficar vazio caso algum evento não tenha sido persistido.
    """

    t = (tipo or "").strip().lower()
    mid = _resolver_municipio_id(usuario, municipio_id)

    def _dt_iso(v: Any) -> Optional[str]:
        if isinstance(v, datetime):
            return v.isoformat()
        return None

    def _model_dump(obj: Any) -> Dict[str, Any]:
        if obj is None:
            return {}
        if hasattr(obj, "model_dump"):
            return obj.model_dump()
        if hasattr(obj, "dict"):
            return obj.dict()
        return {}

    def _merge_events(primary: List[Dict[str, Any]], synthetic: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        seen = set()
        out: List[Dict[str, Any]] = []
        for ev in primary:
            key = (str(ev.get("tipo") or ""), str(ev.get("em") or ""))
            if key in seen:
                continue
            seen.add(key)
            out.append(ev)
        for ev in synthetic:
            key = (str(ev.get("tipo") or ""), str(ev.get("em") or ""))
            if key in seen:
                continue
            seen.add(key)
            out.append(ev)
        out.sort(key=lambda x: str(x.get("em") or ""), reverse=True)
        return out

    if t in ("cras", "encaminhamento"):
        if CrasEncaminhamento is None:
            return {"detail": "Módulo CRAS não disponível."}
        enc = session.get(CrasEncaminhamento, int(id))
        if not enc:
            return {"detail": "Encaminhamento CRAS não encontrado."}
        enc_mid = getattr(enc, "municipio_id", None)
        if mid is not None and enc_mid is not None and int(enc_mid) != int(mid):
            return {"detail": "Encaminhamento não encontrado."}

        primary: List[Dict[str, Any]] = []
        if 'CrasEncaminhamentoEvento' in globals() and CrasEncaminhamentoEvento is not None:
            try:
                stmt = (
                    select(CrasEncaminhamentoEvento)
                    .where(CrasEncaminhamentoEvento.encaminhamento_id == int(id))
                    .order_by(CrasEncaminhamentoEvento.em.desc())
                )
                for ev in session.exec(stmt).all():
                    primary.append({
                        "tipo": getattr(ev, "tipo", None),
                        "detalhe": getattr(ev, "detalhe", None),
                        "por_nome": getattr(ev, "por_nome", None),
                        "em": _dt_iso(getattr(ev, "em", None)),
                        "fonte": "evento",
                    })
            except Exception:
                primary = []

        # Synthetic events from timestamps (fallback)
        synth: List[Dict[str, Any]] = []
        por_nome = getattr(enc, "atualizado_por_nome", None) or getattr(enc, "criado_por_nome", None)
        mapping = [
            ("enviado", "enviado_em"),
            ("recebido", "recebido_em"),
            ("agendado", "agendado_em"),
            ("atendido", "atendido_em"),
            ("devolutiva", "devolutiva_em"),
            ("concluido", "concluido_em"),
            ("cancelado", "cancelado_em"),
        ]
        for tp, field in mapping:
            dtv = getattr(enc, field, None)
            iso = _dt_iso(dtv)
            if iso:
                synth.append({"tipo": tp, "detalhe": None, "por_nome": por_nome, "em": iso, "fonte": "marco"})

        eventos = _merge_events(primary, synth)

        return {
            "tipo": "cras",
            "id": int(id),
            "municipio_id": int(enc_mid) if enc_mid is not None else None,
            "dados": _model_dump(enc),
            "eventos": eventos,
        }

    if t in ("intermunicipal", "inter"):
        if EncaminhamentoIntermunicipal is None:
            return {"detail": "Módulo intermunicipal não disponível."}
        enc = session.get(EncaminhamentoIntermunicipal, int(id))
        if not enc:
            return {"detail": "Encaminhamento intermunicipal não encontrado."}

        orig = getattr(enc, "municipio_origem_id", None)
        dest = getattr(enc, "municipio_destino_id", None)
        if mid is not None:
            ok = (orig is not None and int(orig) == int(mid)) or (dest is not None and int(dest) == int(mid))
            if not ok:
                return {"detail": "Encaminhamento não encontrado."}

        primary: List[Dict[str, Any]] = []
        if 'EncaminhamentoEvento' in globals() and EncaminhamentoEvento is not None:
            try:
                stmt = (
                    select(EncaminhamentoEvento)
                    .where(EncaminhamentoEvento.encaminhamento_id == int(id))
                    .order_by(EncaminhamentoEvento.em.desc())
                )
                for ev in session.exec(stmt).all():
                    primary.append({
                        "tipo": getattr(ev, "tipo", None),
                        "detalhe": getattr(ev, "detalhe", None),
                        "por_nome": getattr(ev, "por_nome", None),
                        "em": _dt_iso(getattr(ev, "em", None)),
                        "fonte": "evento",
                    })
            except Exception:
                primary = []

        synth: List[Dict[str, Any]] = []
        por_nome = getattr(enc, "autorizado_por_nome", None)
        mapping = [
            ("solicitado", "criado_em"),
            ("contato", "contato_em"),
            ("aceito", "aceite_em"),
            ("agendado", "agendado_em"),
            ("passagem", "passagem_em"),
            ("contrarreferencia", "contrarreferencia_em"),
            ("concluido", "concluido_em"),
            ("cancelado", "cancelado_em"),
        ]
        for tp, field in mapping:
            dtv = getattr(enc, field, None)
            iso = _dt_iso(dtv)
            if iso:
                synth.append({"tipo": tp, "detalhe": None, "por_nome": por_nome, "em": iso, "fonte": "marco"})

        eventos = _merge_events(primary, synth)

        return {
            "tipo": "intermunicipal",
            "id": int(id),
            "municipio_origem_id": int(orig) if orig is not None else None,
            "municipio_destino_id": int(dest) if dest is not None else None,
            "dados": _model_dump(enc),
            "eventos": eventos,
        }

    return {"detail": "tipo inválido. Use cras ou intermunicipal."}


@router.get("/rede/timeline-destino")
def gestao_rede_timeline_destino(
    tipo: str = Query(..., description="cras|intermunicipal"),
    municipio_id: Optional[int] = Query(default=None, description="Filtro opcional por município (gestor/admin)."),
    destino_tipo: Optional[str] = Query(default=None, description="(cras) Tipo do destino: creas|osc|..."),
    destino_nome: Optional[str] = Query(default=None, description="(cras) Nome do destino."),
    municipio_destino_id: Optional[int] = Query(default=None, description="(intermunicipal) Município destino ID."),
    limit_eventos: int = Query(default=200, ge=1, le=2000, description="Limite de eventos retornados (mais recentes)."),
    limit_encaminhamentos: int = Query(default=50, ge=1, le=500, description="Limite de encaminhamentos no resumo."),
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    """Linha do tempo consolidada por destino (visão secretário).

    - tipo=cras: consolida eventos de encaminhamentos CRAS para um destino (tipo+nome)
    - tipo=intermunicipal: consolida eventos de encaminhamentos intermunicipais por município destino

    Retorna eventos registrados (quando existirem) e completa com marcos (timestamps) para garantir trilha.
    """
    t = (tipo or "").strip().lower()
    mid = _resolver_municipio_id(usuario, municipio_id)

    def _dt_iso(v: Any) -> Optional[str]:
        if isinstance(v, datetime):
            return v.isoformat()
        return None

    def _merge(primary: List[Dict[str, Any]], synthetic: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        seen = set()
        out: List[Dict[str, Any]] = []
        for ev in primary + synthetic:
            key = (int(ev.get("ref_id") or 0), str(ev.get("tipo") or ""), str(ev.get("em") or ""))
            if key in seen:
                continue
            seen.add(key)
            out.append(ev)
        out.sort(key=lambda x: str(x.get("em") or ""), reverse=True)
        return out

    if t == "cras":
        if CrasEncaminhamento is None:
            return {"detail": "Módulo CRAS não disponível."}
        dt = (destino_tipo or "").strip().lower()
        dn = (destino_nome or "").strip()
        if not dt or not dn:
            return {"detail": "Para tipo=cras, informe destino_tipo e destino_nome."}

        stmt = (
            select(CrasEncaminhamento)
            .where(CrasEncaminhamento.destino_tipo == dt)
            .where(CrasEncaminhamento.destino_nome == dn)
            .order_by(CrasEncaminhamento.id.desc())
        )
        if mid is not None:
            stmt = stmt.where(CrasEncaminhamento.municipio_id == int(mid))

        encs = session.exec(stmt).all()
        enc_ids = [int(e.id) for e in encs if getattr(e, "id", None) is not None]

        # Busca eventos persistidos (se existirem)
        primary_events: Dict[int, List[Dict[str, Any]]] = {eid: [] for eid in enc_ids}
        if CrasEncaminhamentoEvento is not None and enc_ids:
            try:
                stmt_ev = (
                    select(CrasEncaminhamentoEvento)
                    .where(CrasEncaminhamentoEvento.encaminhamento_id.in_(enc_ids))  # type: ignore
                    .order_by(CrasEncaminhamentoEvento.em.desc())
                )
                for ev in session.exec(stmt_ev).all():
                    eid = int(getattr(ev, "encaminhamento_id", 0) or 0)
                    primary_events.setdefault(eid, []).append(
                        {
                            "ref_id": eid,
                            "ref_tipo": "encaminhamento",
                            "tipo": getattr(ev, "tipo", None),
                            "detalhe": getattr(ev, "detalhe", None),
                            "por_nome": getattr(ev, "por_nome", None),
                            "em": _dt_iso(getattr(ev, "em", None)),
                            "fonte": "evento",
                        }
                    )
            except Exception:
                primary_events = {eid: [] for eid in enc_ids}

        def _titulo_enc(e: Any) -> str:
            return f"Encaminhamento #{int(getattr(e,'id',0) or 0)} - {dt.upper()} - {dn}"

        # Monta eventos sintéticos por marcos
        mapping = [
            ("enviado", "enviado_em"),
            ("recebido", "recebido_em"),
            ("agendado", "agendado_em"),
            ("atendido", "atendido_em"),
            ("devolutiva", "devolutiva_em"),
            ("concluido", "concluido_em"),
            ("cancelado", "cancelado_em"),
        ]

        flat: List[Dict[str, Any]] = []
        enc_resumo: List[Dict[str, Any]] = []
        for e in encs[: int(limit_encaminhamentos)]:
            eid = int(getattr(e, "id", 0) or 0)
            enc_mid = getattr(e, "municipio_id", None)
            enc_resumo.append(
                {
                    "id": eid,
                    "municipio_id": int(enc_mid) if enc_mid is not None else None,
                    "status": getattr(e, "status", None),
                    "destino_tipo": getattr(e, "destino_tipo", None),
                    "destino_nome": getattr(e, "destino_nome", None),
                    "enviado_em": _dt_iso(getattr(e, "enviado_em", None)),
                    "recebido_em": _dt_iso(getattr(e, "recebido_em", None)),
                    "devolutiva_em": _dt_iso(getattr(e, "devolutiva_em", None)),
                    "concluido_em": _dt_iso(getattr(e, "concluido_em", None)),
                }
            )

            por_nome = getattr(e, "atualizado_por_nome", None) or getattr(e, "criado_por_nome", None)

            synth: List[Dict[str, Any]] = []
            for tp, field in mapping:
                iso = _dt_iso(getattr(e, field, None))
                if iso:
                    synth.append(
                        {
                            "ref_id": eid,
                            "ref_tipo": "encaminhamento",
                            "tipo": tp,
                            "detalhe": None,
                            "por_nome": por_nome,
                            "em": iso,
                            "fonte": "marco",
                        }
                    )

            merged = _merge(primary_events.get(eid, []), synth)
            for ev in merged:
                ev2 = dict(ev)
                ev2["titulo"] = _titulo_enc(e)
                flat.append(ev2)

        flat.sort(key=lambda x: str(x.get("em") or ""), reverse=True)

        return {
            "tipo": "cras",
            "municipio_id": int(mid) if mid is not None else None,
            "destino_tipo": dt,
            "destino_nome": dn,
            "total_encaminhamentos": len(encs),
            "encaminhamentos": enc_resumo,
            "eventos": flat[: int(limit_eventos)],
        }

    if t in ("intermunicipal", "inter"):
        if EncaminhamentoIntermunicipal is None:
            return {"detail": "Módulo intermunicipal não disponível."}
        if municipio_destino_id is None:
            return {"detail": "Para tipo=intermunicipal, informe municipio_destino_id."}
        did = int(municipio_destino_id)

        stmt = (
            select(EncaminhamentoIntermunicipal)
            .where(EncaminhamentoIntermunicipal.municipio_destino_id == did)  # type: ignore
            .order_by(EncaminhamentoIntermunicipal.id.desc())  # type: ignore
        )
        if mid is not None:
            stmt = stmt.where(or_(EncaminhamentoIntermunicipal.municipio_origem_id == int(mid), EncaminhamentoIntermunicipal.municipio_destino_id == int(mid)))  # type: ignore

        encs = session.exec(stmt).all()
        enc_ids = [int(e.id) for e in encs if getattr(e, "id", None) is not None]

        primary_events: Dict[int, List[Dict[str, Any]]] = {eid: [] for eid in enc_ids}
        if EncaminhamentoEvento is not None and enc_ids:
            try:
                stmt_ev = (
                    select(EncaminhamentoEvento)
                    .where(EncaminhamentoEvento.encaminhamento_id.in_(enc_ids))  # type: ignore
                    .order_by(EncaminhamentoEvento.em.desc())
                )
                for ev in session.exec(stmt_ev).all():
                    eid = int(getattr(ev, "encaminhamento_id", 0) or 0)
                    primary_events.setdefault(eid, []).append(
                        {
                            "ref_id": eid,
                            "ref_tipo": "encaminhamento_intermunicipal",
                            "tipo": getattr(ev, "tipo", None),
                            "detalhe": getattr(ev, "detalhe", None),
                            "por_nome": getattr(ev, "por_nome", None),
                            "em": _dt_iso(getattr(ev, "em", None)),
                            "fonte": "evento",
                        }
                    )
            except Exception:
                primary_events = {eid: [] for eid in enc_ids}

        mapping = [
            ("solicitado", "criado_em"),
            ("contato", "contato_em"),
            ("aceito", "aceite_em"),
            ("agendado", "agendado_em"),
            ("passagem", "passagem_em"),
            ("contrarreferencia", "contrarreferencia_em"),
            ("concluido", "concluido_em"),
            ("cancelado", "cancelado_em"),
        ]

        muni_nome = None
        if Municipio is not None:
            try:
                mobj = session.get(Municipio, did)
                muni_nome = getattr(mobj, "nome", None) if mobj else None
            except Exception:
                muni_nome = None

        flat: List[Dict[str, Any]] = []
        enc_resumo: List[Dict[str, Any]] = []
        for e in encs[: int(limit_encaminhamentos)]:
            eid = int(getattr(e, "id", 0) or 0)
            orig = getattr(e, "municipio_origem_id", None)
            dest = getattr(e, "municipio_destino_id", None)
            enc_resumo.append(
                {
                    "id": eid,
                    "municipio_origem_id": int(orig) if orig is not None else None,
                    "municipio_destino_id": int(dest) if dest is not None else None,
                    "status": getattr(e, "status", None),
                    "criado_em": _dt_iso(getattr(e, "criado_em", None)),
                    "contato_em": _dt_iso(getattr(e, "contato_em", None)),
                    "aceite_em": _dt_iso(getattr(e, "aceite_em", None)),
                    "concluido_em": _dt_iso(getattr(e, "concluido_em", None)),
                }
            )

            por_nome = getattr(e, "autorizado_por_nome", None)
            synth: List[Dict[str, Any]] = []
            for tp, field in mapping:
                iso = _dt_iso(getattr(e, field, None))
                if iso:
                    synth.append(
                        {
                            "ref_id": eid,
                            "ref_tipo": "encaminhamento_intermunicipal",
                            "tipo": tp,
                            "detalhe": None,
                            "por_nome": por_nome,
                            "em": iso,
                            "fonte": "marco",
                        }
                    )

            merged = _merge(primary_events.get(eid, []), synth)
            for ev in merged:
                ev2 = dict(ev)
                ev2["titulo"] = f"Intermunicipal #{eid} - destino {muni_nome or did}"
                flat.append(ev2)

        flat.sort(key=lambda x: str(x.get("em") or ""), reverse=True)

        return {
            "tipo": "intermunicipal",
            "municipio_id": int(mid) if mid is not None else None,
            "municipio_destino_id": did,
            "municipio_destino_nome": muni_nome or f"Município {did}",
            "total_encaminhamentos": len(encs),
            "encaminhamentos": enc_resumo,
            "eventos": flat[: int(limit_eventos)],
        }

    return {"detail": "tipo inválido. Use cras ou intermunicipal."}
