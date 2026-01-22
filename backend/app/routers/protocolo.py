from __future__ import annotations

from datetime import date, datetime, timedelta

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select

from app.core.auth import get_current_user, pode_acesso_global
from app.core.db import get_session
from app.models.caso_pop_rua import CasoPopRua, CasoPopRuaEtapaHistorico
from app.models.pessoa import PessoaRua
from app.models.protocolo import CasoChecklistItem, CasoPlanoAcao, CasoProtocolo
from app.models.usuario import Usuario


router = APIRouter(prefix="/casos", tags=["protocolo"])


# =========================================================
# B1 - Etapas do protocolo (códigos)
# =========================================================
B1_ETAPAS: List[Dict[str, Any]] = [
    {"codigo": "ACOLHIDA", "ordem": 1, "nome": "Acolhida"},
    {"codigo": "DIAGNOSTICO", "ordem": 2, "nome": "Diagnóstico social"},
    {"codigo": "PIA", "ordem": 3, "nome": "Plano / PIA"},
    {"codigo": "EXECUCAO", "ordem": 4, "nome": "Execução"},
    {"codigo": "MONITORAMENTO", "ordem": 5, "nome": "Monitoramento"},
    {"codigo": "ENCERRAMENTO", "ordem": 6, "nome": "Saída qualificada / Encerramento"},
]

B1_ETAPAS_SET = {e["codigo"] for e in B1_ETAPAS}


DEFAULT_CHECKLIST: Dict[str, List[Dict[str, str]]] = {
    "ACOLHIDA": [
        {"chave": "acolhida_escuta", "titulo": "Acolhida e escuta qualificada realizada"},
        {"chave": "acolhida_registro", "titulo": "Registro/identificação mínima concluída"},
    ],
    "DIAGNOSTICO": [
        {"chave": "diag_risco", "titulo": "Vulnerabilidades e riscos mapeados (operacional)"},
        {"chave": "diag_rede", "titulo": "Rede/vínculos identificados"},
    ],
    "PIA": [
        {"chave": "pia_objetivos", "titulo": "Objetivos definidos"},
        {"chave": "pia_responsaveis", "titulo": "Responsáveis e prazos definidos"},
    ],
    "EXECUCAO": [
        {"chave": "exec_enc", "titulo": "Encaminhamentos realizados/registrados"},
        {"chave": "exec_acoes", "titulo": "Ações executadas/registradas"},
    ],
    "MONITORAMENTO": [
        {"chave": "monit_revisao", "titulo": "Revisão do plano realizada"},
        {"chave": "monit_ajustes", "titulo": "Ajustes registrados"},
    ],
    "ENCERRAMENTO": [
        {"chave": "encer_saida", "titulo": "Saída qualificada definida (tipo + data)"},
        {"chave": "encer_just", "titulo": "Encerramento justificado"},
    ],
}


def _perfil(usuario: Usuario) -> str:
    return (getattr(usuario, "perfil", "") or "").strip().lower()


def _verifica_acesso_caso(usuario: Usuario, caso: CasoPopRua) -> None:
    """Regras de acesso por município.

    - admin / gestor_consorcio: acesso global
    - operador / coord_municipal: apenas casos do seu município
    """

    if pode_acesso_global(usuario):
        return

    p = _perfil(usuario)
    if p not in ("operador", "coord_municipal"):
        raise HTTPException(status_code=403, detail="Perfil sem permissão para operar protocolo.")

    mun_user = getattr(usuario, "municipio_id", None)
    if mun_user is None:
        raise HTTPException(status_code=403, detail="Usuário sem município associado.")

    if getattr(caso, "municipio_id", None) is None:
        raise HTTPException(status_code=403, detail="Caso sem município vinculado.")

    if int(caso.municipio_id) != int(mun_user):
        raise HTTPException(status_code=403, detail="Acesso negado: caso fora do seu município.")


def _now() -> datetime:
    return datetime.utcnow()


def _etapa_b1_from_caso(etapa_caso: Optional[str]) -> str:
    """Mapeia a etapa do Caso (linha do metrô) para etapa B1."""
    e = (etapa_caso or "").upper().strip()
    if e in ("ABORDAGEM", "IDENTIFICACAO"):
        return "ACOLHIDA"
    if e in ("DIAGNOSTICO",):
        return "DIAGNOSTICO"
    if e in ("PIA",):
        return "PIA"
    if e in ("EXECUCAO",):
        return "EXECUCAO"
    if e in ("MONITORAMENTO", "ARTICULACAO_REDE", "REVISAO"):
        return "MONITORAMENTO"
    if e in ("ENCERRAMENTO",):
        return "ENCERRAMENTO"
    return "ACOLHIDA"


def _etapa_caso_from_b1(etapa_b1: str) -> str:
    etapa_b1 = (etapa_b1 or "").upper().strip()
    if etapa_b1 == "ACOLHIDA":
        return "ABORDAGEM"
    if etapa_b1 == "DIAGNOSTICO":
        return "DIAGNOSTICO"
    if etapa_b1 == "PIA":
        return "PIA"
    if etapa_b1 == "EXECUCAO":
        return "EXECUCAO"
    if etapa_b1 == "MONITORAMENTO":
        return "MONITORAMENTO"
    if etapa_b1 == "ENCERRAMENTO":
        return "ENCERRAMENTO"
    return "ABORDAGEM"


def _to_dict_check(item: CasoChecklistItem) -> dict:
    def iso(x):
        return x.isoformat() if x else None

    return {
        "id": item.id,
        "caso_id": item.caso_id,
        "etapa": item.etapa,
        "chave": item.chave,
        "titulo": item.titulo,
        "concluido": bool(item.concluido),
        "concluido_em": iso(item.concluido_em),
        "concluido_por_nome": item.concluido_por_nome,
        "obs": item.obs,
    }


def _to_dict_plano(item: CasoPlanoAcao) -> dict:
    def iso_dt(x):
        return x.isoformat() if x else None

    def iso_d(x):
        return x.isoformat() if x else None

    return {
        "id": item.id,
        "caso_id": item.caso_id,
        "objetivo": item.objetivo,
        "acao": item.acao,
        "responsavel": item.responsavel,
        "prazo": iso_d(item.prazo),
        "status": item.status,
        "obs": item.obs,
        "criado_em": iso_dt(item.criado_em),
        "criado_por_nome": item.criado_por_nome,
        "atualizado_em": iso_dt(item.atualizado_em),
        "atualizado_por_nome": item.atualizado_por_nome,
    }


def _ensure_defaults(session: Session, caso: CasoPopRua, usuario: Usuario) -> CasoProtocolo:
    """Cria protocolo e checklist padrão se não existir."""

    protocolo = session.exec(select(CasoProtocolo).where(CasoProtocolo.caso_id == caso.id)).first()
    if protocolo:
        return protocolo

    etapa_b1 = _etapa_b1_from_caso(getattr(caso, "etapa_atual", None))

    protocolo = CasoProtocolo(
        caso_id=caso.id,
        etapa_atual=etapa_b1,
        atualizado_em=_now(),
        atualizado_por_id=getattr(usuario, "id", None),
        atualizado_por_nome=getattr(usuario, "nome", None) or "Usuário",
    )
    session.add(protocolo)
    session.commit()
    session.refresh(protocolo)

    # checklist padrão
    existing_keys = set(
        session.exec(select(CasoChecklistItem.chave).where(CasoChecklistItem.caso_id == caso.id)).all()
    )

    for etapa, itens in DEFAULT_CHECKLIST.items():
        for it in itens:
            if it["chave"] in existing_keys:
                continue
            session.add(
                CasoChecklistItem(
                    caso_id=caso.id,
                    etapa=etapa,
                    chave=it["chave"],
                    titulo=it["titulo"],
                )
            )

    session.commit()
    return protocolo


# =========================================================
# B1 - Resumo rápido + validações LGPD (texto livre)
# =========================================================


_BLOQUEIOS_TERMO = [
    "cid",
    "hiv",
    "ist",
    "sorologia",
    "carga viral",
    "diagnostico",
    "laudo",
    "receita",
]


def _sanitizar_texto_livre(valor: Any, *, max_len: int = 500) -> Optional[str]:
    """Sanitiza e valida campos de texto livre.

    Regra B1: texto operacional curto. Evita virar prontuário/diagnóstico.
    """

    if valor is None:
        return None
    s = str(valor).strip()
    if not s:
        return ""
    if len(s) > max_len:
        raise HTTPException(status_code=400, detail=f"Texto muito longo (máx {max_len} caracteres).")
    low = s.lower()
    for termo in _BLOQUEIOS_TERMO:
        if termo in low:
            raise HTTPException(
                status_code=400,
                detail="Campo de observação deve ser operacional e não conter informação clínica/sensível.",
            )
    return s


def _build_resumo_rapido(
    *,
    caso: CasoPopRua,
    pessoa: Optional[PessoaRua],
    etapa_atual: str,
    checklist: List[CasoChecklistItem],
    plano: List[CasoPlanoAcao],
    dias_vencer: int = 7,
) -> Dict[str, Any]:
    """Gera um resumo pronto para copiar (B1)."""

    hoje = date.today()
    vencer_ate = hoje + timedelta(days=dias_vencer)

    total_chk = len(checklist)
    feitos = sum(1 for it in checklist if it.concluido)
    pendentes = [it for it in checklist if not it.concluido]

    abertas = [a for a in plano if (a.status or "").lower() not in ("concluido", "cancelado")]
    atrasadas = [a for a in abertas if a.prazo and a.prazo < hoje]
    vencendo = [a for a in abertas if a.prazo and hoje <= a.prazo <= vencer_ate]

    nome_pessoa = None
    if pessoa:
        nome_pessoa = pessoa.nome_social or pessoa.nome_civil

    linhas = []
    linhas.append(f"Caso #{caso.id} · Município {getattr(caso, 'municipio_id', '—')}")
    if nome_pessoa:
        linhas.append(f"Pessoa: {nome_pessoa} (ID {pessoa.id})")
    linhas.append(f"Etapa (B1): {etapa_atual}")
    linhas.append(f"Checklist: {feitos}/{total_chk} concluído(s) · {len(pendentes)} pendente(s)")

    if pendentes:
        linhas.append("Pendências (top 5):")
        for it in pendentes[:5]:
            linhas.append(f"- [{it.etapa}] {it.titulo}")

    linhas.append(f"Plano (ações): {len(abertas)} em aberto · {len(atrasadas)} atrasada(s) · {len(vencendo)} vencendo")
    if atrasadas:
        linhas.append("Ações atrasadas (top 5):")
        for a in atrasadas[:5]:
            prazo = a.prazo.isoformat() if a.prazo else "—"
            linhas.append(f"- {a.objetivo}: {a.acao} (Resp.: {a.responsavel}) · Prazo {prazo}")

    return {
        "texto": "\n".join(linhas),
        "checklist_total": total_chk,
        "checklist_concluidos": feitos,
        "checklist_pendentes": len(pendentes),
        "plano_abertas": len(abertas),
        "plano_atrasadas": len(atrasadas),
        "plano_vencendo": len(vencendo),
        "dias_vencer": dias_vencer,
    }


# =========================================================
# Endpoints B1
# =========================================================


@router.get("/{caso_id}/protocolo")
def obter_protocolo(
    caso_id: int,
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    caso = session.get(CasoPopRua, caso_id)
    if not caso:
        raise HTTPException(status_code=404, detail="Caso não encontrado.")

    _verifica_acesso_caso(usuario, caso)
    protocolo = _ensure_defaults(session, caso, usuario)

    checklist = session.exec(
        select(CasoChecklistItem)
        .where(CasoChecklistItem.caso_id == caso_id)
        .order_by(CasoChecklistItem.id.asc())
    ).all()

    plano = session.exec(
        select(CasoPlanoAcao)
        .where(CasoPlanoAcao.caso_id == caso_id)
        .order_by(CasoPlanoAcao.id.desc())
    ).all()

    
    pessoa = None
    if getattr(caso, "pessoa_id", None):
        try:
            pessoa = session.get(PessoaRua, int(caso.pessoa_id))
        except Exception:
            pessoa = None

    resumo = _build_resumo_rapido(
        caso=caso,
        pessoa=pessoa,
        etapa_atual=protocolo.etapa_atual,
        checklist=checklist,
        plano=plano,
        dias_vencer=7,
    )

    return {
        "caso_id": caso_id,
        "etapas": B1_ETAPAS,
        "etapa_atual": protocolo.etapa_atual,
        "atualizado_em": protocolo.atualizado_em.isoformat() if protocolo.atualizado_em else None,
        "atualizado_por_nome": protocolo.atualizado_por_nome,
        "resumo": resumo,
        "checklist": [_to_dict_check(x) for x in checklist],
        "plano": [_to_dict_plano(x) for x in plano],
    }


@router.get("/{caso_id}/protocolo/resumo")
def obter_resumo_rapido(
    caso_id: int,
    dias_vencer: int = Query(7, ge=1, le=60),
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    """Resumo pronto para copiar (B1).

    - Mostra etapa atual, pendências de checklist e ações atrasadas/vencendo.
    """

    caso = session.get(CasoPopRua, caso_id)
    if not caso:
        raise HTTPException(status_code=404, detail="Caso não encontrado.")

    _verifica_acesso_caso(usuario, caso)
    protocolo = _ensure_defaults(session, caso, usuario)

    checklist = session.exec(
        select(CasoChecklistItem).where(CasoChecklistItem.caso_id == caso_id).order_by(CasoChecklistItem.id.asc())
    ).all()
    plano = session.exec(
        select(CasoPlanoAcao).where(CasoPlanoAcao.caso_id == caso_id).order_by(CasoPlanoAcao.id.desc())
    ).all()

    pessoa = None
    if getattr(caso, "pessoa_id", None):
        try:
            pessoa = session.get(PessoaRua, int(caso.pessoa_id))
        except Exception:
            pessoa = None

    resumo = _build_resumo_rapido(
        caso=caso,
        pessoa=pessoa,
        etapa_atual=protocolo.etapa_atual,
        checklist=checklist,
        plano=plano,
        dias_vencer=dias_vencer,
    )

    return resumo


@router.patch("/{caso_id}/protocolo/etapa")
def atualizar_etapa(
    caso_id: int,
    payload: Dict[str, Any],
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    caso = session.get(CasoPopRua, caso_id)
    if not caso:
        raise HTTPException(status_code=404, detail="Caso não encontrado.")
    _verifica_acesso_caso(usuario, caso)

    etapa = (payload.get("etapa_atual") or "").upper().strip()
    if etapa not in B1_ETAPAS_SET:
        raise HTTPException(status_code=400, detail="Etapa inválida.")

    protocolo = _ensure_defaults(session, caso, usuario)
    protocolo.etapa_atual = etapa
    protocolo.atualizado_em = _now()
    protocolo.atualizado_por_id = getattr(usuario, "id", None)
    protocolo.atualizado_por_nome = getattr(usuario, "nome", None) or "Usuário"

    # Atualiza caso (linha do metrô) para manter coerência
    caso.etapa_atual = _etapa_caso_from_b1(etapa)
    caso.data_ultima_atualizacao = _now()
    caso.data_inicio_etapa_atual = _now()

    # Histórico (não trava se falhar)
    try:
        session.add(
            CasoPopRuaEtapaHistorico(
                caso_id=caso.id,
                etapa=caso.etapa_atual,
                usuario_responsavel=getattr(usuario, "nome", None) or "Usuário",
                observacoes=f"Protocolo B1: etapa -> {etapa}",
                tipo_acao="protocolo_b1_etapa",
            )
        )
    except Exception:
        pass

    session.add(protocolo)
    session.add(caso)
    session.commit()
    session.refresh(protocolo)

    return {
        "caso_id": caso_id,
        "etapa_atual": protocolo.etapa_atual,
        "atualizado_em": protocolo.atualizado_em.isoformat() if protocolo.atualizado_em else None,
        "atualizado_por_nome": protocolo.atualizado_por_nome,
    }


@router.post("/{caso_id}/protocolo/checklist/{chave}/toggle")
def toggle_checklist(
    caso_id: int,
    chave: str,
    payload: Dict[str, Any],
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    caso = session.get(CasoPopRua, caso_id)
    if not caso:
        raise HTTPException(status_code=404, detail="Caso não encontrado.")
    _verifica_acesso_caso(usuario, caso)

    _ensure_defaults(session, caso, usuario)

    item = session.exec(
        select(CasoChecklistItem)
        .where(CasoChecklistItem.caso_id == caso_id, CasoChecklistItem.chave == chave)
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item de checklist não encontrado.")

    concluido = bool(payload.get("concluido"))
    obs = _sanitizar_texto_livre(payload.get("obs"), max_len=400)

    item.concluido = concluido
    if obs is not None:
        item.obs = obs

    if concluido:
        item.concluido_em = _now()
        item.concluido_por_id = getattr(usuario, "id", None)
        item.concluido_por_nome = getattr(usuario, "nome", None) or "Usuário"
    else:
        item.concluido_em = None
        item.concluido_por_id = None
        item.concluido_por_nome = None

    session.add(item)
    session.commit()
    session.refresh(item)
    return _to_dict_check(item)


@router.post("/{caso_id}/protocolo/plano")
def criar_acao_plano(
    caso_id: int,
    payload: Dict[str, Any],
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    caso = session.get(CasoPopRua, caso_id)
    if not caso:
        raise HTTPException(status_code=404, detail="Caso não encontrado.")
    _verifica_acesso_caso(usuario, caso)

    _ensure_defaults(session, caso, usuario)

    objetivo = (payload.get("objetivo") or "").strip()
    acao = (payload.get("acao") or "").strip()
    responsavel = (payload.get("responsavel") or "").strip()
    status_val = (payload.get("status") or "pendente").strip()

    if not objetivo or not acao or not responsavel:
        raise HTTPException(status_code=400, detail="objetivo, acao e responsavel são obrigatórios.")

    prazo_raw = payload.get("prazo")
    prazo: Optional[date] = None
    if prazo_raw:
        try:
            prazo = date.fromisoformat(str(prazo_raw))
        except Exception:
            raise HTTPException(status_code=400, detail="prazo inválido (use YYYY-MM-DD).")

    item = CasoPlanoAcao(
        caso_id=caso_id,
        objetivo=objetivo,
        acao=acao,
        responsavel=responsavel,
        prazo=prazo,
        status=status_val,
        obs=_sanitizar_texto_livre(payload.get("obs"), max_len=400),
        criado_em=_now(),
        criado_por_id=getattr(usuario, "id", None),
        criado_por_nome=getattr(usuario, "nome", None) or "Usuário",
        atualizado_em=_now(),
        atualizado_por_id=getattr(usuario, "id", None),
        atualizado_por_nome=getattr(usuario, "nome", None) or "Usuário",
    )
    session.add(item)
    session.commit()
    session.refresh(item)
    return _to_dict_plano(item)


@router.patch("/{caso_id}/protocolo/plano/{acao_id}")
def atualizar_acao_plano(
    caso_id: int,
    acao_id: int,
    payload: Dict[str, Any],
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    caso = session.get(CasoPopRua, caso_id)
    if not caso:
        raise HTTPException(status_code=404, detail="Caso não encontrado.")
    _verifica_acesso_caso(usuario, caso)

    item = session.get(CasoPlanoAcao, acao_id)
    if not item or int(item.caso_id) != int(caso_id):
        raise HTTPException(status_code=404, detail="Ação do plano não encontrada.")

    for campo in ("objetivo", "acao", "responsavel", "status"):
        if campo in payload and payload[campo] is not None:
            setattr(item, campo, str(payload[campo]).strip())

    if "obs" in payload:
        item.obs = _sanitizar_texto_livre(payload.get("obs"), max_len=400)

    if "prazo" in payload:
        prazo_raw = payload.get("prazo")
        if prazo_raw in (None, ""):
            item.prazo = None
        else:
            try:
                item.prazo = date.fromisoformat(str(prazo_raw))
            except Exception:
                raise HTTPException(status_code=400, detail="prazo inválido (use YYYY-MM-DD).")

    item.atualizado_em = _now()
    item.atualizado_por_id = getattr(usuario, "id", None)
    item.atualizado_por_nome = getattr(usuario, "nome", None) or "Usuário"

    session.add(item)
    session.commit()
    session.refresh(item)
    return _to_dict_plano(item)


@router.delete("/{caso_id}/protocolo/plano/{acao_id}")
def remover_acao_plano(
    caso_id: int,
    acao_id: int,
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    caso = session.get(CasoPopRua, caso_id)
    if not caso:
        raise HTTPException(status_code=404, detail="Caso não encontrado.")
    _verifica_acesso_caso(usuario, caso)

    item = session.get(CasoPlanoAcao, acao_id)
    if not item or int(item.caso_id) != int(caso_id):
        raise HTTPException(status_code=404, detail="Ação do plano não encontrada.")

    session.delete(item)
    session.commit()
    return {"ok": True}


@router.get("/protocolo/alertas")
def listar_alertas_prazo(
    dias_vencer: int = Query(7, ge=1, le=60),
    dias_sem_atualizar: int = Query(14, ge=3, le=180),
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    """Alertas de prazo (B2 - opção 1).

    - Ações do plano atrasadas / vencendo.
    - Casos com protocolo sem atualização há X dias.

    Regras de acesso:
    - admin/consórcio: todos
    - operador/coord: somente município
    """

    hoje = date.today()
    vencer_ate = hoje + timedelta(days=dias_vencer)

    # Município do usuário (se não for global)
    mun_user = getattr(usuario, "municipio_id", None)

    # --- Ações do plano (join caso + pessoa) ---
    stmt = (
        select(CasoPlanoAcao, CasoPopRua, PessoaRua)
        .join(CasoPopRua, CasoPlanoAcao.caso_id == CasoPopRua.id)
        .join(PessoaRua, CasoPopRua.pessoa_id == PessoaRua.id)
    )

    if not pode_acesso_global(usuario):
        if mun_user is None:
            raise HTTPException(status_code=403, detail="Usuário sem município associado.")
        stmt = stmt.where(CasoPopRua.municipio_id == int(mun_user))

    # status em aberto
    stmt = stmt.where(CasoPlanoAcao.status.notin_(["concluido", "cancelado"]))

    rows = session.exec(stmt).all()

    atrasadas = []
    vencendo = []
    for acao, caso, pessoa in rows:
        prazo = acao.prazo
        if not prazo:
            continue
        item = {
            "acao_id": acao.id,
            "caso_id": caso.id,
            "municipio_id": caso.municipio_id,
            "pessoa_id": pessoa.id,
            "pessoa_nome": pessoa.nome_social or pessoa.nome_civil or "Pessoa",
            "objetivo": acao.objetivo,
            "acao": acao.acao,
            "responsavel": acao.responsavel,
            "prazo": prazo.isoformat(),
            "status": acao.status,
        }
        if prazo < hoje:
            atrasadas.append(item)
        elif hoje <= prazo <= vencer_ate:
            vencendo.append(item)

    # --- Casos sem atualização do protocolo ---
    limite = datetime.utcnow() - timedelta(days=dias_sem_atualizar)
    stmt_p = select(CasoProtocolo, CasoPopRua).join(CasoPopRua, CasoProtocolo.caso_id == CasoPopRua.id)
    if not pode_acesso_global(usuario):
        stmt_p = stmt_p.where(CasoPopRua.municipio_id == int(mun_user))
    stmt_p = stmt_p.where(CasoProtocolo.atualizado_em < limite)

    estagnados = []
    for prot, caso in session.exec(stmt_p).all():
        estagnados.append(
            {
                "caso_id": caso.id,
                "municipio_id": caso.municipio_id,
                "etapa_atual": prot.etapa_atual,
                "atualizado_em": prot.atualizado_em.isoformat() if prot.atualizado_em else None,
                "atualizado_por_nome": prot.atualizado_por_nome,
            }
        )

    # Ordena (mais críticos primeiro)
    atrasadas.sort(key=lambda x: x.get("prazo") or "")
    vencendo.sort(key=lambda x: x.get("prazo") or "")

    return {
        "dias_vencer": dias_vencer,
        "dias_sem_atualizar": dias_sem_atualizar,
        "atrasadas": atrasadas,
        "vencendo": vencendo,
        "casos_sem_atualizar": estagnados,
    }
