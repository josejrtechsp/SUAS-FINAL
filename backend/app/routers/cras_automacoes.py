from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select

from app.core.auth import exigir_minimo_perfil, get_current_user, pode_acesso_global
from app.core.db import get_session
from app.models.usuario import Usuario

from app.models.cras_automacoes import CrasAutomacaoExecucao, CrasAutomacaoRegra
from app.models.cras_tarefas import CrasTarefa

from app.models.caso_cras import CasoCras, CasoCrasHistorico
from app.models.cras_pia import CrasPiaPlano, CrasPiaAcao
from app.models.cadunico_precadastro import CadunicoPreCadastro
from app.models.cras_encaminhamento import CrasEncaminhamento, CrasEncaminhamentoEvento


router = APIRouter(
    prefix="/automacoes",
    tags=["CRAS · Automações"],
    dependencies=[Depends(exigir_minimo_perfil("gestor"))],
)


# ---------------------------
# Defaults
# ---------------------------
DEFAULT_RULES: List[Dict[str, Any]] = [
    {
        "chave": "caso_sem_movimentacao",
        "titulo": "Caso sem movimentação",
        "descricao": "Cria tarefa quando um caso está aberto, mas sem movimentação por X dias.",
        "parametros": {"dias_sem_mov": 7, "prazo_dias": 2, "prioridade": "alta"},
    },
    {
        "chave": "pia_acao_vencida",
        "titulo": "PIA com ação vencida",
        "descricao": "Cria tarefa quando uma ação do PIA vence e ainda está pendente.",
        "parametros": {"prazo_dias": 1, "prioridade": "alta"},
    },
    {
        "chave": "encaminhamento_sem_devolutiva",
        "titulo": "Encaminhamento sem devolutiva",
        "descricao": "Cria tarefa quando um encaminhamento excede o prazo de devolutiva.",
        "parametros": {"prazo_dias": 1, "prioridade": "alta"},
    },
    {
        "chave": "cadunico_agendamento_passou",
        "titulo": "CadÚnico: agendamento passou",
        "descricao": "Cria tarefa quando o pré-cadastro está agendado e a data já passou sem finalização.",
        "parametros": {"prazo_dias": 1, "prioridade": "media"},
    },
]


def _now() -> datetime:
    return datetime.utcnow()


def _resolve_municipio(usuario: Usuario, municipio_id: Optional[int]) -> int:
    if pode_acesso_global(usuario):
        if municipio_id:
            return int(municipio_id)
        return int(getattr(usuario, "municipio_id") or 0)
    return int(getattr(usuario, "municipio_id") or 0)


def _ensure_scope(usuario: Usuario, municipio_id: int) -> None:
    if not municipio_id:
        raise HTTPException(status_code=400, detail="municipio_id obrigatório.")
    if not pode_acesso_global(usuario):
        if int(getattr(usuario, "municipio_id") or 0) != int(municipio_id):
            raise HTTPException(status_code=403, detail="Sem acesso a este município.")


def _task_exists(session: Session, ref_tipo: str, ref_id: int, municipio_id: int, unidade_id: Optional[int]) -> bool:
    stmt = select(CrasTarefa).where(CrasTarefa.ref_tipo == ref_tipo, CrasTarefa.ref_id == ref_id)
    stmt = stmt.where(CrasTarefa.municipio_id == municipio_id)
    if unidade_id:
        stmt = stmt.where(CrasTarefa.unidade_id == unidade_id)

    # somente abertas/em andamento contam como duplicidade
    stmt = stmt.where(CrasTarefa.status.in_(["aberta", "em_andamento"]))
    return session.exec(stmt).first() is not None


def _create_task(
    session: Session,
    municipio_id: int,
    unidade_id: Optional[int],
    ref_tipo: str,
    ref_id: int,
    titulo: str,
    descricao: str,
    prioridade: str,
    data_vencimento: Optional[date],
    responsavel_id: Optional[int] = None,
) -> CrasTarefa:
    t = CrasTarefa(
        municipio_id=municipio_id,
        unidade_id=unidade_id,
        ref_tipo=ref_tipo,
        ref_id=ref_id,
        titulo=titulo[:200],
        descricao=(descricao or "")[:2000],
        prioridade=(prioridade or "media")[:20],
        status="aberta",
        data_vencimento=data_vencimento,
        responsavel_id=responsavel_id,
        responsavel_nome=None,
        criado_em=_now(),
        atualizado_em=_now(),
    )
    session.add(t)
    session.commit()
    session.refresh(t)
    return t


def _seed_defaults(session: Session, usuario: Usuario, municipio_id: int, unidade_id: Optional[int] = None) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for base in DEFAULT_RULES:
        chave = base["chave"]
        stmt = select(CrasAutomacaoRegra).where(
            CrasAutomacaoRegra.municipio_id == municipio_id,
            CrasAutomacaoRegra.chave == chave,
        )
        if unidade_id is None:
            stmt = stmt.where(CrasAutomacaoRegra.unidade_id.is_(None))
        else:
            stmt = stmt.where(CrasAutomacaoRegra.unidade_id == unidade_id)

        reg = session.exec(stmt).first()
        if not reg:
            reg = CrasAutomacaoRegra(
                municipio_id=municipio_id,
                unidade_id=unidade_id,
                chave=chave,
                titulo=base["titulo"],
                descricao=base.get("descricao"),
                ativo=True,
                frequencia_minutos=1440,  # 1x/dia
                criado_por_usuario_id=getattr(usuario, "id", None),
                criado_em=_now(),
                atualizado_em=_now(),
            )
            reg.set_parametros(base.get("parametros") or {})
            session.add(reg)
            session.commit()
            session.refresh(reg)

        out.append({
            "id": reg.id,
            "chave": reg.chave,
            "titulo": reg.titulo,
            "ativo": reg.ativo,
            "unidade_id": reg.unidade_id,
            "parametros": reg.parametros(),
        })
    return out


@router.post("/seed")
def seed(
    municipio_id: Optional[int] = None,
    unidade_id: Optional[int] = None,
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
) -> Dict[str, Any]:
    mun = _resolve_municipio(usuario, municipio_id)
    _ensure_scope(usuario, mun)
    regras = _seed_defaults(session, usuario, mun, unidade_id=unidade_id)
    return {"municipio_id": mun, "unidade_id": unidade_id, "regras": regras}


@router.get("/regras")
def listar_regras(
    municipio_id: Optional[int] = None,
    unidade_id: Optional[int] = None,
    include_inativas: bool = False,
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
) -> List[Dict[str, Any]]:
    mun = _resolve_municipio(usuario, municipio_id)
    _ensure_scope(usuario, mun)

    stmt = select(CrasAutomacaoRegra).where(CrasAutomacaoRegra.municipio_id == mun)
    if unidade_id is None:
        # lista tanto regras gerais (unidade_id NULL) quanto específicas? por padrão, só gerais
        stmt = stmt.where(CrasAutomacaoRegra.unidade_id.is_(None))
    else:
        stmt = stmt.where((CrasAutomacaoRegra.unidade_id.is_(None)) | (CrasAutomacaoRegra.unidade_id == unidade_id))

    if not include_inativas:
        stmt = stmt.where(CrasAutomacaoRegra.ativo == True)  # noqa: E712

    regs = session.exec(stmt).all()
    out: List[Dict[str, Any]] = []
    for r in regs:
        out.append({
            "id": r.id,
            "municipio_id": r.municipio_id,
            "unidade_id": r.unidade_id,
            "chave": r.chave,
            "titulo": r.titulo,
            "descricao": r.descricao,
            "ativo": r.ativo,
            "frequencia_minutos": r.frequencia_minutos,
            "ultima_execucao_em": r.ultima_execucao_em.isoformat() if r.ultima_execucao_em else None,
            "parametros": r.parametros(),
        })
    return out


@router.post("/regras/{regra_id}")
def atualizar_regra(
    regra_id: int,
    payload: Dict[str, Any],
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
) -> Dict[str, Any]:
    reg = session.get(CrasAutomacaoRegra, regra_id)
    if not reg:
        raise HTTPException(status_code=404, detail="Regra não encontrada.")
    _ensure_scope(usuario, reg.municipio_id)

    if "ativo" in payload:
        reg.ativo = bool(payload.get("ativo"))
    if "frequencia_minutos" in payload and payload.get("frequencia_minutos") is not None:
        try:
            reg.frequencia_minutos = int(payload.get("frequencia_minutos"))
        except Exception:
            pass
    if "titulo" in payload and payload.get("titulo"):
        reg.titulo = str(payload.get("titulo"))[:160]
    if "descricao" in payload:
        reg.descricao = (str(payload.get("descricao")) if payload.get("descricao") is not None else None)

    if "parametros" in payload and isinstance(payload.get("parametros"), dict):
        reg.set_parametros(payload.get("parametros") or {})

    reg.atualizado_em = _now()
    session.add(reg)
    session.commit()
    session.refresh(reg)

    return {
        "id": reg.id,
        "ativo": reg.ativo,
        "frequencia_minutos": reg.frequencia_minutos,
        "titulo": reg.titulo,
        "descricao": reg.descricao,
        "parametros": reg.parametros(),
    }


def _exec_regra_caso_sem_movimentacao(
    session: Session,
    mun: int,
    unidade_id: Optional[int],
    params: Dict[str, Any],
    dry_run: bool,
) -> Tuple[int, int]:
    dias = int(params.get("dias_sem_mov") or 7)
    prazo_dias = int(params.get("prazo_dias") or 2)
    prioridade = str(params.get("prioridade") or "alta")
    cutoff = _now() - timedelta(days=dias)
    hoje = date.today()
    venc = hoje + timedelta(days=prazo_dias)

    stmt = select(CasoCras).where(CasoCras.municipio_id == mun)
    if unidade_id:
        stmt = stmt.where(CasoCras.unidade_id == unidade_id)
    # caso aberto
    try:
        stmt = stmt.where(CasoCras.data_encerramento.is_(None))
    except Exception:
        pass

    casos = session.exec(stmt).all()
    created = 0
    skipped = 0
    for caso in casos:
        # última movimentação = último histórico
        last_dt = None
        h = session.exec(
            select(CasoCrasHistorico).where(CasoCrasHistorico.caso_id == caso.id).order_by(CasoCrasHistorico.criado_em.desc())
        ).first()
        if h and getattr(h, "criado_em", None):
            last_dt = h.criado_em
        else:
            last_dt = getattr(caso, "atualizado_em", None) or getattr(caso, "data_abertura", None) or _now()

        if last_dt and last_dt < cutoff:
            ref_tipo = "caso_sem_movimentacao"
            ref_id = int(caso.id)
            if _task_exists(session, ref_tipo, ref_id, mun, getattr(caso, "unidade_id", None)):
                skipped += 1
                continue

            titulo = f"Caso #{caso.id}: sem movimentação ({dias}d)"
            etapa = getattr(caso, "etapa_atual", None) or getattr(caso, "etapa", None) or ""
            descricao = f"Caso aberto sem movimentação há {dias} dias. Etapa atual: {etapa}".strip()
            responsavel_id = getattr(caso, "tecnico_responsavel_id", None)

            if not dry_run:
                _create_task(
                    session=session,
                    municipio_id=mun,
                    unidade_id=getattr(caso, "unidade_id", unidade_id),
                    ref_tipo=ref_tipo,
                    ref_id=ref_id,
                    titulo=titulo,
                    descricao=descricao,
                    prioridade=prioridade,
                    data_vencimento=venc,
                    responsavel_id=responsavel_id,
                )
            created += 1
        else:
            skipped += 1

    return created, skipped


def _exec_regra_pia_acao_vencida(
    session: Session,
    mun: int,
    unidade_id: Optional[int],
    params: Dict[str, Any],
    dry_run: bool,
) -> Tuple[int, int]:
    prazo_dias = int(params.get("prazo_dias") or 1)
    prioridade = str(params.get("prioridade") or "alta")
    hoje = date.today()
    venc = hoje + timedelta(days=prazo_dias)

    stmt = (
        select(CrasPiaAcao, CrasPiaPlano)
        .join(CrasPiaPlano, CrasPiaAcao.plano_id == CrasPiaPlano.id)
        .where(CrasPiaPlano.municipio_id == mun)
    )
    if unidade_id:
        stmt = stmt.where(CrasPiaPlano.unidade_id == unidade_id)

    # apenas pendentes e com prazo vencido
    stmt = stmt.where(CrasPiaAcao.status != "concluida")
    stmt = stmt.where(CrasPiaAcao.prazo.is_not(None))
    stmt = stmt.where(CrasPiaAcao.prazo < hoje)

    rows = session.exec(stmt).all()
    created = 0
    skipped = 0
    for acao, plano in rows:
        ref_tipo = "pia_acao_vencida"
        ref_id = int(getattr(acao, "id") or 0)
        if not ref_id:
            continue
        if _task_exists(session, ref_tipo, ref_id, mun, getattr(plano, "unidade_id", unidade_id)):
            skipped += 1
            continue

        caso_id = getattr(plano, "caso_id", None)
        titulo = f"PIA: ação vencida (Caso #{caso_id})" if caso_id else "PIA: ação vencida"
        descricao = f"Ação vencida em {getattr(acao,'prazo',None)}: {getattr(acao,'descricao','')}".strip()
        responsavel_id = getattr(acao, "responsavel_usuario_id", None)

        if not dry_run:
            _create_task(
                session=session,
                municipio_id=mun,
                unidade_id=getattr(plano, "unidade_id", unidade_id),
                ref_tipo=ref_tipo,
                ref_id=ref_id,
                titulo=titulo,
                descricao=descricao,
                prioridade=prioridade,
                data_vencimento=venc,
                responsavel_id=responsavel_id,
            )
        created += 1

    return created, skipped


def _has_devolutiva(session: Session, encaminhamento_id: int) -> bool:
    ev = session.exec(
        select(CrasEncaminhamentoEvento)
        .where(CrasEncaminhamentoEvento.encaminhamento_id == encaminhamento_id)
        .where(CrasEncaminhamentoEvento.tipo.in_(["devolutiva", "concluido", "cancelado"]))
        .order_by(CrasEncaminhamentoEvento.em.desc())
    ).first()
    return ev is not None


def _exec_regra_encaminhamento_sem_devolutiva(
    session: Session,
    mun: int,
    unidade_id: Optional[int],
    params: Dict[str, Any],
    dry_run: bool,
) -> Tuple[int, int]:
    prazo_dias = int(params.get("prazo_dias") or 1)
    prioridade = str(params.get("prioridade") or "alta")
    hoje = date.today()
    venc = hoje + timedelta(days=prazo_dias)

    stmt = select(CrasEncaminhamento).where(CrasEncaminhamento.municipio_id == mun)
    if unidade_id:
        stmt = stmt.where(CrasEncaminhamento.unidade_id == unidade_id)

    # candidatos: não concluídos/cancelados
    stmt = stmt.where(CrasEncaminhamento.status.notin_(["concluido", "cancelado"]))
    encs = session.exec(stmt).all()

    created = 0
    skipped = 0
    for enc in encs:
        # usa prazo específico do encaminhamento (default 7 dias)
        prazo_enc = int(getattr(enc, "prazo_devolutiva_dias", 7) or 7)
        enviado_em = getattr(enc, "enviado_em", None) or getattr(enc, "criado_em", None) or _now()
        if (enviado_em + timedelta(days=prazo_enc)).date() >= hoje:
            skipped += 1
            continue
        if _has_devolutiva(session, int(enc.id)):
            skipped += 1
            continue

        ref_tipo = "encaminhamento_sem_devolutiva"
        ref_id = int(enc.id)
        if _task_exists(session, ref_tipo, ref_id, mun, getattr(enc, "unidade_id", unidade_id)):
            skipped += 1
            continue

        destino = getattr(enc, "destino_nome", "") or ""
        titulo = f"Encaminhamento sem devolutiva: {destino}".strip() or f"Encaminhamento #{enc.id}: sem devolutiva"
        motivo = (getattr(enc, "motivo", "") or "")
        descricao = f"Encaminhamento #{enc.id} para {destino} sem devolutiva. Motivo: {motivo[:300]}".strip()

        if not dry_run:
            _create_task(
                session=session,
                municipio_id=mun,
                unidade_id=getattr(enc, "unidade_id", unidade_id),
                ref_tipo=ref_tipo,
                ref_id=ref_id,
                titulo=titulo,
                descricao=descricao,
                prioridade=prioridade,
                data_vencimento=venc,
                responsavel_id=None,
            )
        created += 1

    return created, skipped


def _exec_regra_cadunico_agendamento_passou(
    session: Session,
    mun: int,
    unidade_id: Optional[int],
    params: Dict[str, Any],
    dry_run: bool,
) -> Tuple[int, int]:
    prazo_dias = int(params.get("prazo_dias") or 1)
    prioridade = str(params.get("prioridade") or "media")
    hoje = date.today()
    venc = hoje + timedelta(days=prazo_dias)

    stmt = select(CadunicoPreCadastro).where(CadunicoPreCadastro.municipio_id == mun)
    if unidade_id:
        stmt = stmt.where(CadunicoPreCadastro.unidade_id == unidade_id)

    stmt = stmt.where(CadunicoPreCadastro.status == "agendado")
    stmt = stmt.where(CadunicoPreCadastro.data_agendada.is_not(None))

    rows = session.exec(stmt).all()
    created = 0
    skipped = 0
    for pc in rows:
        dt = getattr(pc, "data_agendada", None)
        if not dt:
            continue
        try:
            ag_date = dt.date()
        except Exception:
            ag_date = hoje

        if ag_date >= hoje:
            skipped += 1
            continue

        ref_tipo = "cadunico_agendamento_passou"
        ref_id = int(pc.id)
        if _task_exists(session, ref_tipo, ref_id, mun, getattr(pc, "unidade_id", unidade_id)):
            skipped += 1
            continue

        titulo = f"CadÚnico: agendamento passou (pré-cadastro #{pc.id})"
        desc = f"Agendado em {ag_date} e ainda não finalizado. Caso={getattr(pc,'caso_id',None)} Pessoa={getattr(pc,'pessoa_id',None)}".strip()

        responsavel_id = None
        caso_id = getattr(pc, "caso_id", None)
        if caso_id:
            caso = session.get(CasoCras, caso_id)
            if caso:
                responsavel_id = getattr(caso, "tecnico_responsavel_id", None)

        if not dry_run:
            _create_task(
                session=session,
                municipio_id=mun,
                unidade_id=getattr(pc, "unidade_id", unidade_id),
                ref_tipo=ref_tipo,
                ref_id=ref_id,
                titulo=titulo,
                descricao=desc,
                prioridade=prioridade,
                data_vencimento=venc,
                responsavel_id=responsavel_id,
            )
        created += 1

    return created, skipped


def _executar_regra(
    session: Session,
    reg: CrasAutomacaoRegra,
    mun: int,
    unidade_id: Optional[int],
    dry_run: bool,
) -> Dict[str, Any]:
    params = reg.parametros()
    chave = reg.chave
    created = 0
    skipped = 0

    if chave == "caso_sem_movimentacao":
        created, skipped = _exec_regra_caso_sem_movimentacao(session, mun, unidade_id, params, dry_run)
    elif chave == "pia_acao_vencida":
        created, skipped = _exec_regra_pia_acao_vencida(session, mun, unidade_id, params, dry_run)
    elif chave == "encaminhamento_sem_devolutiva":
        created, skipped = _exec_regra_encaminhamento_sem_devolutiva(session, mun, unidade_id, params, dry_run)
    elif chave == "cadunico_agendamento_passou":
        created, skipped = _exec_regra_cadunico_agendamento_passou(session, mun, unidade_id, params, dry_run)
    else:
        # desconhecida
        return {"chave": chave, "created": 0, "skipped": 0, "erro": "Regra não implementada."}

    return {"chave": chave, "created": created, "skipped": skipped}


def _devida(reg: CrasAutomacaoRegra) -> bool:
    if not reg.ativo:
        return False
    if not reg.frequencia_minutos:
        return True
    if not reg.ultima_execucao_em:
        return True
    delta = _now() - reg.ultima_execucao_em
    return delta.total_seconds() >= int(reg.frequencia_minutos) * 60


@router.post("/executar")
def executar(
    municipio_id: Optional[int] = None,
    unidade_id: Optional[int] = None,
    dry_run: bool = False,
    somente_chaves: Optional[List[str]] = Query(default=None),
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
) -> Dict[str, Any]:
    mun = _resolve_municipio(usuario, municipio_id)
    _ensure_scope(usuario, mun)

    # garante regras base para o município (evita vazio no começo)
    _seed_defaults(session, usuario, mun, unidade_id=None)

    stmt = select(CrasAutomacaoRegra).where(CrasAutomacaoRegra.municipio_id == mun)
    if unidade_id is None:
        stmt = stmt.where(CrasAutomacaoRegra.unidade_id.is_(None))
    else:
        stmt = stmt.where((CrasAutomacaoRegra.unidade_id.is_(None)) | (CrasAutomacaoRegra.unidade_id == unidade_id))

    stmt = stmt.where(CrasAutomacaoRegra.ativo == True)  # noqa: E712
    regs = session.exec(stmt).all()

    if somente_chaves:
        wanted = {str(x).strip() for x in somente_chaves if str(x).strip()}
        regs = [r for r in regs if r.chave in wanted]

    resultados: List[Dict[str, Any]] = []
    for reg in regs:
        exec_row = CrasAutomacaoExecucao(
            regra_id=reg.id,
            municipio_id=mun,
            unidade_id=unidade_id,
            iniciado_em=_now(),
            status="ok",
        )
        session.add(exec_row)
        session.commit()
        session.refresh(exec_row)

        try:
            res = _executar_regra(session, reg, mun, unidade_id, dry_run)
            exec_row.set_resumo(res)
            exec_row.finalizado_em = _now()
            exec_row.status = "ok"
            exec_row.erro = None

            # marca última execução
            reg.ultima_execucao_em = _now()
            reg.atualizado_em = _now()
            session.add(reg)
        except Exception as e:
            exec_row.finalizado_em = _now()
            exec_row.status = "erro"
            exec_row.erro = f"{type(e).__name__}: {e}"
            exec_row.set_resumo({"erro": exec_row.erro})

        session.add(exec_row)
        session.commit()
        session.refresh(exec_row)

        resultados.append({
            "regra_id": reg.id,
            "chave": reg.chave,
            "titulo": reg.titulo,
            "execucao_id": exec_row.id,
            "status": exec_row.status,
            "resumo": exec_row.resumo(),
        })

    return {
        "municipio_id": mun,
        "unidade_id": unidade_id,
        "dry_run": dry_run,
        "total_regras": len(resultados),
        "resultados": resultados,
    }


@router.post("/executar-devidas")
def executar_devidas(
    municipio_id: Optional[int] = None,
    unidade_id: Optional[int] = None,
    dry_run: bool = False,
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
) -> Dict[str, Any]:
    """Executa apenas regras 'devidas' (por frequência). Útil para cron/job externo."""
    mun = _resolve_municipio(usuario, municipio_id)
    _ensure_scope(usuario, mun)

    _seed_defaults(session, usuario, mun, unidade_id=None)

    stmt = select(CrasAutomacaoRegra).where(CrasAutomacaoRegra.municipio_id == mun)
    if unidade_id is None:
        stmt = stmt.where(CrasAutomacaoRegra.unidade_id.is_(None))
    else:
        stmt = stmt.where((CrasAutomacaoRegra.unidade_id.is_(None)) | (CrasAutomacaoRegra.unidade_id == unidade_id))

    stmt = stmt.where(CrasAutomacaoRegra.ativo == True)  # noqa: E712
    regs = [r for r in session.exec(stmt).all() if _devida(r)]

    # reaproveita /executar para registrar execuções
    return executar(municipio_id=mun, unidade_id=unidade_id, dry_run=dry_run, somente_chaves=[r.chave for r in regs], session=session, usuario=usuario)
