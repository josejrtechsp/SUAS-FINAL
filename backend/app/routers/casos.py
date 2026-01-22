# app/routers/casos.py
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlmodel import Session, select

from sqlalchemy import func

from app.core.db import get_session
from app.core.auth import get_current_user, pode_acesso_global, nivel_perfil
from app.core.poprua_fluxo import etapa_metro
from app.models.usuario import Usuario
from app.models.caso_pop_rua import CasoPopRua, CasoPopRuaEtapaHistorico

router = APIRouter(prefix="/casos", tags=["casos"])


# =========================================================
# RBAC / acesso
# =========================================================
NIVEL_VER = max(nivel_perfil("recepcao"), nivel_perfil("leitura"), 1)
NIVEL_OPERAR = max(nivel_perfil("tecnico"), nivel_perfil("operador"), 10)


def _perfil(usuario: Usuario) -> str:
    return (getattr(usuario, "perfil", "") or "").strip().lower()


def _agora() -> datetime:
    return datetime.utcnow()


def _usuario_nome(usuario: Usuario, payload: dict) -> str:
    return payload.get("usuario_responsavel") or getattr(usuario, "nome", None) or "Usuário"


def _exigir_nivel(usuario: Usuario, minimo: int, *, acao: str) -> None:
    if int(nivel_perfil(getattr(usuario, "perfil", None))) < int(minimo):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Acesso negado: perfil sem permissão para {acao}.",
        )


def _verifica_acesso_caso(usuario: Usuario, caso: CasoPopRua) -> None:
    """Regra de acesso por município.

    - acesso global (gestor_consorcio/admin): pode tudo
    - demais: só pode acessar casos do seu município
    """

    if pode_acesso_global(usuario):
        return

    mun_user = getattr(usuario, "municipio_id", None)
    if mun_user is None:
        raise HTTPException(status_code=403, detail="Usuário sem município associado.")

    if getattr(caso, "municipio_id", None) is None:
        raise HTTPException(status_code=403, detail="Caso sem município vinculado. Acesso negado.")

    if int(caso.municipio_id) != int(mun_user):
        raise HTTPException(status_code=403, detail="Acesso negado: caso fora do seu município.")


# =========================================================
# Definição das etapas (linha do metrô)
# =========================================================
ETAPAS: List[Dict[str, Any]] = [
    {
        "codigo": "ABORDAGEM",
        "ordem": 1,
        "nome": "Abordagem inicial",
        "descricao": "Primeiro contato com a equipe, escuta inicial e identificação da situação.",
    },
    {
        "codigo": "IDENTIFICACAO",
        "ordem": 2,
        "nome": "Identificação e registro",
        "descricao": "Coleta de dados básicos, documentos, origem, vínculos e necessidades.",
    },
    {
        "codigo": "DIAGNOSTICO",
        "ordem": 3,
        "nome": "Avaliação e diagnóstico",
        "descricao": "Análise técnica, riscos/vulnerabilidades e priorização do atendimento.",
    },
    {
        "codigo": "PIA",
        "ordem": 4,
        "nome": "Elaboração do PIA / Plano",
        "descricao": "Definição do plano de atendimento, metas, prazos e responsáveis.",
    },
    {
        "codigo": "EXECUCAO",
        "ordem": 5,
        "nome": "Execução das ações",
        "descricao": "Encaminhamentos, benefícios, cuidados em saúde, acolhimento etc.",
    },
    {
        "codigo": "MONITORAMENTO",
        "ordem": 6,
        "nome": "Monitoramento",
        "descricao": "Acompanhamento das ações e reavaliação contínua.",
    },
    {
        "codigo": "ARTICULACAO_REDE",
        "ordem": 7,
        "nome": "Articulação em rede",
        "descricao": "Diálogo com outras políticas/municípios (saúde, habitação, trabalho etc.).",
    },
    {
        "codigo": "REVISAO",
        "ordem": 8,
        "nome": "Revisão e replanejamento",
        "descricao": "Revisão do plano quando necessário e inclusão de novas ações.",
    },
    {
        "codigo": "ENCERRAMENTO",
        "ordem": 9,
        "nome": "Encerramento do caso",
        "descricao": "Fechamento com registro do motivo e condições de saída.",
    },
]


def _idx_etapa(codigo: Optional[str]) -> int:
    if not codigo:
        return 0
    for i, e in enumerate(ETAPAS):
        if e["codigo"] == codigo:
            return i
    return 0


def _status_etapa(caso: CasoPopRua, etapa_codigo: str) -> str:
    etapa_atual = getattr(caso, "etapa_atual", None)
    status_caso = getattr(caso, "status", None)

    if status_caso == "encerrado" or etapa_atual == "ENCERRAMENTO":
        return "concluida"

    i_atual = _idx_etapa(etapa_atual)
    i_etapa = _idx_etapa(etapa_codigo)

    if i_etapa < i_atual:
        return "concluida"
    if i_etapa == i_atual:
        return "em_andamento"
    return "nao_iniciada"


def _caso_to_dict(c: CasoPopRua) -> dict:
    def iso(x):
        return x.isoformat() if x else None

    return {
        "id": c.id,
        "pessoa_id": c.pessoa_id,
        "municipio_id": c.municipio_id,
        "status": c.status,
        "etapa_atual": c.etapa_atual,
        "etapa_atual_metro": etapa_metro(getattr(c, "etapa_atual", None)),
        "observacoes_iniciais": c.observacoes_iniciais,
        "observacoes_gerais": c.observacoes_gerais,
        "ativo": c.ativo,
        "data_abertura": iso(c.data_abertura),
        "data_ultima_atualizacao": iso(c.data_ultima_atualizacao),
        "data_encerramento": iso(c.data_encerramento),
        "motivo_encerramento": c.motivo_encerramento,
        "data_inicio_etapa_atual": iso(c.data_inicio_etapa_atual),
        "prazo_etapa_dias": c.prazo_etapa_dias,
        "estagnado": c.estagnado,
        "motivo_estagnacao": c.motivo_estagnacao,
        "data_prevista_proxima_acao": iso(getattr(c, "data_prevista_proxima_acao", None)),
        "data_ultima_acao": iso(getattr(c, "data_ultima_acao", None)),
        "flag_estagnado": getattr(c, "flag_estagnado", False),
        "dias_estagnado": getattr(c, "dias_estagnado", 0),
        "tipo_estagnacao": getattr(c, "tipo_estagnacao", None),
    }




def _caso_preview_to_dict(row: Any) -> dict:
    """Versão leve para LISTAS.

    Evita enviar textos longos e campos que só fazem sentido no detalhe.
    """

    def iso(x):
        return x.isoformat() if x else None

    (
        _id,
        pessoa_id,
        municipio_id,
        status,
        etapa_atual,
        ativo,
        data_abertura,
        data_ultima_atualizacao,
        data_inicio_etapa_atual,
        prazo_etapa_dias,
        estagnado,
        motivo_estagnacao,
        data_prevista_proxima_acao,
        data_ultima_acao,
        flag_estagnado,
        dias_estagnado,
        tipo_estagnacao,
    ) = row

    return {
        "id": _id,
        "pessoa_id": pessoa_id,
        "municipio_id": municipio_id,
        "status": status,
        "etapa_atual": etapa_atual,
        "etapa_atual_metro": etapa_metro(etapa_atual),
        "ativo": ativo,
        "data_abertura": iso(data_abertura),
        "data_ultima_atualizacao": iso(data_ultima_atualizacao),
        "data_inicio_etapa_atual": iso(data_inicio_etapa_atual),
        "prazo_etapa_dias": prazo_etapa_dias,
        "estagnado": estagnado,
        "motivo_estagnacao": motivo_estagnacao,
        "data_prevista_proxima_acao": iso(data_prevista_proxima_acao),
        "data_ultima_acao": iso(data_ultima_acao),
        "flag_estagnado": flag_estagnado,
        "dias_estagnado": dias_estagnado,
        "tipo_estagnacao": tipo_estagnacao,
    }


def _parse_dt(v: Any) -> Optional[datetime]:
    if v is None or v == "":
        return None
    if isinstance(v, datetime):
        return v
    try:
        return datetime.fromisoformat(str(v).replace("Z", "+00:00")).replace(tzinfo=None)
    except Exception:
        return None


# =========================================================
# Endpoints
# =========================================================
@router.get("/")
def listar_casos(
    response: Response,
    incluir_inativos: bool = Query(False, description="Se true, inclui casos arquivados (ativo=false)."),
    pessoa_id: Optional[int] = Query(None, description="Filtra por pessoa_id (útil para 'Casos da pessoa')."),
    municipio_id: Optional[int] = Query(None, description="(Acesso global) Filtra por município específico."),
    limit: int = Query(200, ge=1, le=500, description="Paginação. Default=200 (máx 500)."),
    offset: int = Query(0, ge=0, description="Paginação (offset)."),
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    """Lista de casos PopRua (LEVE e paginada).

    - Evita retornar milhares de registros (que travam front/iPad)
    - Retorna apenas campos essenciais (preview)
    - Total vem no header X-Total-Count
    """

    _exigir_nivel(usuario, NIVEL_VER, acao="listar casos")

    # Filters
    conds = []

    if not incluir_inativos:
        conds.append(CasoPopRua.ativo == True)  # noqa: E712

    # município: usuários comuns ficam restritos ao próprio município
    if pode_acesso_global(usuario):
        if municipio_id is not None:
            conds.append(CasoPopRua.municipio_id == int(municipio_id))
    else:
        mun_user = getattr(usuario, "municipio_id", None)
        if mun_user is not None:
            conds.append(CasoPopRua.municipio_id == int(mun_user))

    if pessoa_id is not None:
        conds.append(CasoPopRua.pessoa_id == int(pessoa_id))

    # total
    total_stmt = select(func.count()).select_from(CasoPopRua)
    for c in conds:
        total_stmt = total_stmt.where(c)
    total = session.exec(total_stmt).one() or 0

    if response is not None:
        response.headers["X-Total-Count"] = str(total)
        # permite ler no browser (CORS)
        prev = response.headers.get("Access-Control-Expose-Headers")
        expose = "X-Total-Count" if not prev else f"{prev}, X-Total-Count"
        response.headers["Access-Control-Expose-Headers"] = expose

    # list (preview)
    stmt = (
        select(
            CasoPopRua.id,
            CasoPopRua.pessoa_id,
            CasoPopRua.municipio_id,
            CasoPopRua.status,
            CasoPopRua.etapa_atual,
            CasoPopRua.ativo,
            CasoPopRua.data_abertura,
            CasoPopRua.data_ultima_atualizacao,
            CasoPopRua.data_inicio_etapa_atual,
            CasoPopRua.prazo_etapa_dias,
            CasoPopRua.estagnado,
            CasoPopRua.motivo_estagnacao,
            CasoPopRua.data_prevista_proxima_acao,
            CasoPopRua.data_ultima_acao,
            CasoPopRua.flag_estagnado,
            CasoPopRua.dias_estagnado,
            CasoPopRua.tipo_estagnacao,
        )
        .order_by(CasoPopRua.id.desc())
        .offset(int(offset))
        .limit(int(limit))
    )
    for c in conds:
        stmt = stmt.where(c)

    rows = session.exec(stmt).all()
    return [_caso_preview_to_dict(r) for r in rows]



@router.post("/", status_code=201)
def criar_caso(
    payload: dict,
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    _exigir_nivel(usuario, NIVEL_OPERAR, acao="criar caso")

    pessoa_id = payload.get("pessoa_id")
    municipio_id = payload.get("municipio_id")
    obs_ini = payload.get("observacoes_iniciais")

    if not pessoa_id:
        raise HTTPException(status_code=400, detail="pessoa_id é obrigatório.")

    if not pode_acesso_global(usuario):
        municipio_id = getattr(usuario, "municipio_id", None)

    if not municipio_id:
        raise HTTPException(status_code=400, detail="municipio_id é obrigatório.")

    now = _agora()

    caso = CasoPopRua(
        pessoa_id=int(pessoa_id),
        municipio_id=int(municipio_id),
        observacoes_iniciais=obs_ini or None,
        observacoes_gerais=payload.get("observacoes_gerais") or None,
        status="em_andamento",
        etapa_atual="ABORDAGEM",
        ativo=True,
        data_abertura=now,
        data_ultima_atualizacao=now,
        data_inicio_etapa_atual=now,
        estagnado=False,
    )

    session.add(caso)
    session.commit()
    session.refresh(caso)

    hist = CasoPopRuaEtapaHistorico(
        caso_id=caso.id,
        etapa=caso.etapa_atual,
        data_acao=now,
        usuario_responsavel=_usuario_nome(usuario, payload),
        observacoes=payload.get("observacoes") or payload.get("observacoes_iniciais"),
        tipo_acao="abertura_caso",
        motivo_estagnacao=None,
    )
    session.add(hist)
    session.commit()

    return _caso_to_dict(caso)


@router.get("/{caso_id}")
def obter_caso(
    caso_id: int,
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    _exigir_nivel(usuario, NIVEL_VER, acao="visualizar caso")

    caso = session.get(CasoPopRua, caso_id)
    if not caso:
        raise HTTPException(status_code=404, detail="Caso não encontrado.")

    _verifica_acesso_caso(usuario, caso)
    return _caso_to_dict(caso)


@router.patch("/{caso_id}")
def atualizar_caso(
    caso_id: int,
    payload: dict,
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    """Atualização mínima (backend-only) para fechar lacunas de operação.

    Não substitui o fluxo principal (avançar etapa / arquivar), mas permite:
    - ajustar SLA (prazo_etapa_dias)
    - registrar próxima ação (data_prevista_proxima_acao)
    - registrar última ação (data_ultima_acao)
    - marcar estagnação com justificativa
    - atualizar observações do caso
    """

    _exigir_nivel(usuario, NIVEL_OPERAR, acao="atualizar caso")

    caso = session.get(CasoPopRua, caso_id)
    if not caso:
        raise HTTPException(status_code=404, detail="Caso não encontrado.")

    _verifica_acesso_caso(usuario, caso)

    allowed = {
        "observacoes_iniciais",
        "observacoes_gerais",
        "prazo_etapa_dias",
        "data_prevista_proxima_acao",
        "data_ultima_acao",
        "estagnado",
        "motivo_estagnacao",
        "motivo_encerramento",
    }

    changes: List[str] = []
    now = _agora()

    # SLA
    if "prazo_etapa_dias" in payload and "prazo_etapa_dias" in allowed:
        try:
            v = payload.get("prazo_etapa_dias")
            caso.prazo_etapa_dias = int(v) if v not in (None, "") else None
            changes.append("prazo_etapa_dias")
        except Exception:
            raise HTTPException(status_code=400, detail="prazo_etapa_dias inválido")

    # Próxima ação / última ação
    if "data_prevista_proxima_acao" in payload and "data_prevista_proxima_acao" in allowed:
        caso.data_prevista_proxima_acao = _parse_dt(payload.get("data_prevista_proxima_acao"))
        changes.append("data_prevista_proxima_acao")

    if "data_ultima_acao" in payload and "data_ultima_acao" in allowed:
        caso.data_ultima_acao = _parse_dt(payload.get("data_ultima_acao"))
        changes.append("data_ultima_acao")

    # Observações
    if "observacoes_iniciais" in payload and "observacoes_iniciais" in allowed:
        caso.observacoes_iniciais = (payload.get("observacoes_iniciais") or "").strip() or None
        changes.append("observacoes_iniciais")

    if "observacoes_gerais" in payload and "observacoes_gerais" in allowed:
        caso.observacoes_gerais = (payload.get("observacoes_gerais") or "").strip() or None
        changes.append("observacoes_gerais")

    # Estagnação
    if "estagnado" in payload and "estagnado" in allowed:
        est = payload.get("estagnado")
        est_bool = bool(est) if not isinstance(est, str) else est.strip().lower() in ("1", "true", "sim", "s")

        if est_bool:
            motivo = (payload.get("motivo_estagnacao") or "").strip()
            if not motivo:
                raise HTTPException(status_code=400, detail="motivo_estagnacao é obrigatório quando estagnado=true")
            caso.estagnado = True
            caso.motivo_estagnacao = motivo
            changes.append("estagnado")
            changes.append("motivo_estagnacao")
        else:
            caso.estagnado = False
            # opcionalmente limpa o motivo
            if "motivo_estagnacao" in payload:
                caso.motivo_estagnacao = (payload.get("motivo_estagnacao") or "").strip() or None
                changes.append("motivo_estagnacao")
            changes.append("estagnado")

    if "motivo_encerramento" in payload and "motivo_encerramento" in allowed:
        caso.motivo_encerramento = (payload.get("motivo_encerramento") or "").strip() or None
        changes.append("motivo_encerramento")

    # ignora qualquer campo fora da lista permitida
    if not changes:
        return _caso_to_dict(caso)

    caso.data_ultima_atualizacao = now
    session.add(caso)

    # Auditoria mínima: 1 histórico por PATCH
    resumo = ", ".join(sorted(set(changes)))
    obs_hist = (payload.get("observacoes") or "").strip() or None
    obs_final = obs_hist or f"Atualização: {resumo}"

    tipo_acao = "atualizacao_caso"
    if "prazo_etapa_dias" in changes:
        tipo_acao = "ajuste_sla"
    if "estagnado" in changes:
        tipo_acao = "estagnacao"

    hist = CasoPopRuaEtapaHistorico(
        caso_id=caso.id,
        etapa=caso.etapa_atual or "ABORDAGEM",
        data_acao=now,
        usuario_responsavel=getattr(usuario, "nome", None) or "Usuário",
        observacoes=obs_final[:600] if obs_final else None,
        tipo_acao=tipo_acao,
        motivo_estagnacao=caso.motivo_estagnacao,
    )
    session.add(hist)

    session.commit()
    session.refresh(caso)

    return _caso_to_dict(caso)


@router.post("/{caso_id}/avancar-etapa")
def avancar_etapa(
    caso_id: int,
    payload: dict,
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    _exigir_nivel(usuario, NIVEL_OPERAR, acao="avançar etapa")

    caso = session.get(CasoPopRua, caso_id)
    if not caso:
        raise HTTPException(status_code=404, detail="Caso não encontrado.")

    _verifica_acesso_caso(usuario, caso)

    atual = caso.etapa_atual or "ABORDAGEM"
    if caso.status == "encerrado" or atual == "ENCERRAMENTO":
        return _caso_to_dict(caso)

    idx = _idx_etapa(atual)
    prox_idx = min(idx + 1, len(ETAPAS) - 1)
    prox = ETAPAS[prox_idx]["codigo"]

    now = _agora()

    caso.etapa_atual = prox
    caso.data_ultima_atualizacao = now
    caso.data_inicio_etapa_atual = now

    if prox == "ENCERRAMENTO":
        caso.status = "encerrado"
        caso.data_encerramento = now

    session.add(caso)

    hist = CasoPopRuaEtapaHistorico(
        caso_id=caso.id,
        etapa=prox,
        data_acao=now,
        usuario_responsavel=_usuario_nome(usuario, payload),
        observacoes=payload.get("observacoes"),
        tipo_acao="avanco_etapa",
        motivo_estagnacao=payload.get("motivo_estagnacao"),
    )
    session.add(hist)

    session.commit()
    session.refresh(caso)

    return _caso_to_dict(caso)


@router.post("/{caso_id}/arquivar")
def arquivar_caso(
    caso_id: int,
    payload: dict,
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    _exigir_nivel(usuario, NIVEL_OPERAR, acao="arquivar caso")

    caso = session.get(CasoPopRua, caso_id)
    if not caso:
        raise HTTPException(status_code=404, detail="Caso não encontrado.")

    _verifica_acesso_caso(usuario, caso)

    motivo = (payload.get("motivo") or "").strip() or "Arquivado pelo usuário."
    now = _agora()

    if caso.ativo is False:
        return _caso_to_dict(caso)

    caso.ativo = False
    caso.data_ultima_atualizacao = now
    session.add(caso)

    hist = CasoPopRuaEtapaHistorico(
        caso_id=caso.id,
        etapa=caso.etapa_atual or "ABORDAGEM",
        data_acao=now,
        usuario_responsavel=_usuario_nome(usuario, payload),
        observacoes=motivo,
        tipo_acao="arquivamento",
        motivo_estagnacao=None,
    )
    session.add(hist)

    session.commit()
    session.refresh(caso)
    return _caso_to_dict(caso)


@router.post("/{caso_id}/desarquivar")
def desarquivar_caso(
    caso_id: int,
    payload: dict,
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    _exigir_nivel(usuario, NIVEL_OPERAR, acao="desarquivar caso")

    caso = session.get(CasoPopRua, caso_id)
    if not caso:
        raise HTTPException(status_code=404, detail="Caso não encontrado.")

    _verifica_acesso_caso(usuario, caso)

    motivo = (payload.get("motivo") or "").strip() or "Desarquivado pelo usuário."
    now = _agora()

    if caso.ativo is True:
        return _caso_to_dict(caso)

    caso.ativo = True
    caso.data_ultima_atualizacao = now
    session.add(caso)

    hist = CasoPopRuaEtapaHistorico(
        caso_id=caso.id,
        etapa=caso.etapa_atual or "ABORDAGEM",
        data_acao=now,
        usuario_responsavel=_usuario_nome(usuario, payload),
        observacoes=motivo,
        tipo_acao="desarquivamento",
        motivo_estagnacao=None,
    )
    session.add(hist)

    session.commit()
    session.refresh(caso)
    return _caso_to_dict(caso)


@router.get("/{caso_id}/historico-etapas")
def historico_etapas(
    caso_id: int,
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    _exigir_nivel(usuario, NIVEL_VER, acao="ver histórico")

    caso = session.get(CasoPopRua, caso_id)
    if not caso:
        raise HTTPException(status_code=404, detail="Caso não encontrado.")

    _verifica_acesso_caso(usuario, caso)

    stmt = (
        select(CasoPopRuaEtapaHistorico)
        .where(CasoPopRuaEtapaHistorico.caso_id == caso_id)
        .order_by(CasoPopRuaEtapaHistorico.data_acao.desc())
    )
    itens = session.exec(stmt).all()

    return [
        {
            "id": x.id,
            "caso_id": x.caso_id,
            "etapa": x.etapa,
            "data_acao": x.data_acao.isoformat() if x.data_acao else None,
            "usuario_responsavel": x.usuario_responsavel,
            "observacoes": x.observacoes,
            "tipo_acao": x.tipo_acao,
            "motivo_estagnacao": x.motivo_estagnacao,
        }
        for x in itens
    ]
