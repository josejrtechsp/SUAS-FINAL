from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select
from sqlalchemy import or_

from app.core.db import get_session
from app.core.auth import get_current_user, pode_acesso_global
from app.models.usuario import Usuario

from app.models.pessoa_suas import PessoaSUAS
from app.models.familia_suas import FamiliaSUAS, FamiliaMembro
from app.models.caso_cras import CasoCras, CasoCrasHistorico
from app.models.cadunico_precadastro import CadunicoPreCadastro
from app.models.cras_pia import CrasPiaPlano, CrasPiaAcao
from app.models.scfv import ScfvTurma, ScfvParticipante, ScfvPresenca
from app.models.ficha_anexo import FichaAnexo
from app.models.ficha_evento import FichaEvento
from app.models.pessoa import PessoaRua
from app.models.pessoa_identidade_link import PessoaIdentidadeLink
from app.models.cras_paif import PaifAcompanhamento
from app.models.cras_triagem import CrasTriagem
from app.models.cras_encaminhamento import CrasEncaminhamento

router = APIRouter(prefix="/cras/ficha", tags=["cras-ficha"])


def _mun_id(usuario: Usuario) -> Optional[int]:
    mid = getattr(usuario, "municipio_id", None)
    return int(mid) if mid is not None else None


def _check_municipio(usuario: Usuario, municipio_id: int) -> None:
    if pode_acesso_global(usuario):
        return
    um = _mun_id(usuario)
    if um is None or int(municipio_id) != int(um):
        raise HTTPException(status_code=403, detail="Acesso negado (município).")


def _to_iso(dt: Any) -> Optional[str]:
    if dt is None:
        return None
    if isinstance(dt, (datetime, date)):
        return dt.isoformat()
    return str(dt)


def _month_range(ano: int, mes: int):
    from calendar import monthrange
    last = monthrange(ano, mes)[1]
    start = date(ano, mes, 1)
    end = date(ano, mes, last)
    return start, end


def _today_ym():
    d = date.today()
    return d.year, d.month


@router.get("/pessoas/{pessoa_id}")
def ficha_pessoa(
    pessoa_id: int,
    ano: Optional[int] = Query(default=None),
    mes: Optional[int] = Query(default=None),
    limite_faltas_seguidas: int = Query(3, ge=1, le=60),
    presenca_min: float = Query(0.75, ge=0.0, le=1.0),
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
) -> Dict[str, Any]:
    pessoa = session.get(PessoaSUAS, pessoa_id)
    if not pessoa:
        raise HTTPException(status_code=404, detail="Pessoa não encontrada.")
    _check_municipio(usuario, int(pessoa.municipio_id))

    # =========================================
    # Ponte PopRua <-> SUAS (se existir)
    # =========================================
    link = session.exec(
        select(PessoaIdentidadeLink)
        .where(PessoaIdentidadeLink.pessoa_suas_id == pessoa_id)
        .order_by(PessoaIdentidadeLink.id.desc())
    ).first()

    poprua: Optional[Dict[str, Any]] = None
    if link:
        pr = session.get(PessoaRua, link.pessoarua_id)
        try:
            paifs_pop = session.exec(
                select(PaifAcompanhamento)
                .where(or_(PaifAcompanhamento.pessoa_suas_id == pessoa_id, PaifAcompanhamento.pessoa_id == link.pessoarua_id))
                .order_by(PaifAcompanhamento.id.desc())
            ).all()
        except Exception:
            paifs_pop = []
        try:
            triagens_pop = session.exec(
                select(CrasTriagem)
                .where(or_(CrasTriagem.pessoa_suas_id == pessoa_id, CrasTriagem.pessoa_id == link.pessoarua_id))
                .order_by(CrasTriagem.id.desc())
            ).all()
        except Exception:
            triagens_pop = []
        try:
            encs_pop = session.exec(
                select(CrasEncaminhamento)
                .where(or_(CrasEncaminhamento.pessoa_suas_id == pessoa_id, CrasEncaminhamento.pessoa_id == link.pessoarua_id))
                .order_by(CrasEncaminhamento.id.desc())
            ).all()
        except Exception:
            encs_pop = []

        poprua = {
            "link": link.dict(),
            "pessoarua": pr.dict() if pr else None,
            "paif": [x.dict() for x in paifs_pop[:50]],
            "triagens": [x.dict() for x in triagens_pop[:50]],
            "encaminhamentos": [x.dict() for x in encs_pop[:50]],
        }

    # período de referência
    if ano is None or mes is None:
        ano, mes = _today_ym()
    mes_ini, mes_fim = _month_range(int(ano), int(mes))

    # família (se houver vínculo)
    vinc = session.exec(select(FamiliaMembro).where(FamiliaMembro.pessoa_id == pessoa_id)).first()
    familia = session.get(FamiliaSUAS, vinc.familia_id) if vinc else None
    membros = session.exec(select(FamiliaMembro).where(FamiliaMembro.familia_id == familia.id)).all() if familia else []

    # casos CRAS vinculados à pessoa ou à família
    conds = [CasoCras.pessoa_id == pessoa_id]
    if familia:
        conds.append(CasoCras.familia_id == familia.id)

    casos = session.exec(
        select(CasoCras).where(or_(*conds)).order_by(CasoCras.id.desc())
    ).all()
    caso_ids = [c.id for c in casos]

    # histórico auditável
    hist = []
    if caso_ids:
        hist = session.exec(
            select(CasoCrasHistorico)
            .where(CasoCrasHistorico.caso_id.in_(caso_ids))
            .order_by(CasoCrasHistorico.id.desc())
        ).all()

    # CadÚnico
    cad_conds = [CadunicoPreCadastro.pessoa_id == pessoa_id]
    if familia:
        cad_conds.append(CadunicoPreCadastro.familia_id == familia.id)
    if caso_ids:
        cad_conds.append(CadunicoPreCadastro.caso_id.in_(caso_ids))

    cad = session.exec(
        select(CadunicoPreCadastro)
        .where(or_(*cad_conds))
        .order_by(CadunicoPreCadastro.id.desc())
    ).all()
    cad_atual = cad[0] if cad else None

    # PIA/PAIF (por caso)
    plano = None
    acoes: List[CrasPiaAcao] = []
    if caso_ids:
        plano = session.exec(
            select(CrasPiaPlano).where(CrasPiaPlano.caso_id.in_(caso_ids)).order_by(CrasPiaPlano.id.desc())
        ).first()
        if plano:
            acoes = session.exec(select(CrasPiaAcao).where(CrasPiaAcao.plano_id == plano.id).order_by(CrasPiaAcao.id.desc())).all()

    # SCFV: participações ativas
    scfv_parts = session.exec(
        select(ScfvParticipante).where((ScfvParticipante.pessoa_id == pessoa_id) & (ScfvParticipante.status == "ativo"))
    ).all()
    scfv_part_ids = [p.id for p in scfv_parts]

    turmas = {}
    if scfv_parts:
        turma_ids = list({p.turma_id for p in scfv_parts})
        for tma in session.exec(select(ScfvTurma).where(ScfvTurma.id.in_(turma_ids))).all():
            turmas[tma.id] = tma

    pres = []
    if scfv_part_ids:
        pres = session.exec(
            select(ScfvPresenca)
            .where(ScfvPresenca.participante_id.in_(scfv_part_ids))
            .where(ScfvPresenca.data >= mes_ini)
            .where(ScfvPresenca.data <= mes_fim)
        ).all()
    pres_map = {(x.participante_id, x.data): x for x in pres}

    # Condicionalidades + pendências
    cond: List[Dict[str, Any]] = []
    pendencias: List[Dict[str, Any]] = []

    # CadÚnico
    if cad_atual:
        if cad_atual.status in ("pendente", "agendado"):
            dias = (datetime.utcnow().date() - cad_atual.criado_em.date()).days
            if dias >= 30:
                pendencias.append({
                    "tipo": "cadunico_atrasado",
                    "gravidade": "alta",
                    "referencia": f"Pré-cadastro #{cad_atual.id}",
                    "detalhe": f"CadÚnico está {cad_atual.status} há {dias} dias.",
                    "sugerido": "Agendar/atualizar e finalizar ou registrar não compareceu.",
                })
        cond.append({
            "programa": "CadÚnico",
            "ok": cad_atual.status == "finalizado",
            "itens": [
                {"regra": "Pré-cadastro finalizado", "status": cad_atual.status, "ok": cad_atual.status == "finalizado"},
                {"regra": "Agendamento", "valor": _to_iso(cad_atual.data_agendada), "ok": True},
            ]
        })
    else:
        cond.append({"programa": "CadÚnico", "ok": False, "itens": [{"regra": "Existe pré-cadastro vinculado", "ok": False}]})
        pendencias.append({
            "tipo": "cadunico_inexistente",
            "gravidade": "media",
            "referencia": "CadÚnico",
            "detalhe": "Não existe pré-cadastro CadÚnico vinculado.",
            "sugerido": "Criar pré-cadastro a partir do caso e agendar atendimento.",
        })

    # PIA/PAIF
    if plano:
        hoje = date.today()
        atrasadas = sum(1 for a in acoes if a.status != "concluida" and a.prazo and a.prazo < hoje)
        cond.append({
            "programa": "PAIF/PIA",
            "ok": True,
            "itens": [
                {"regra": "Plano existente", "ok": True, "status": plano.status},
                {"regra": "Ações atrasadas", "valor": atrasadas, "ok": atrasadas == 0},
            ]
        })
        if atrasadas:
            pendencias.append({
                "tipo": "pia_acoes_atrasadas",
                "gravidade": "alta" if atrasadas >= 2 else "media",
                "referencia": f"Plano #{plano.id}",
                "detalhe": f"{atrasadas} ação(ões) do PIA/PAIF atrasada(s).",
                "sugerido": "Atualizar prazos, concluir ações ou registrar justificativa.",
            })
    else:
        cond.append({"programa": "PAIF/PIA", "ok": False, "itens": [{"regra": "Plano existente", "ok": False}]})
        if casos:
            pendencias.append({
                "tipo": "pia_inexistente",
                "gravidade": "media",
                "referencia": "PAIF/PIA",
                "detalhe": "Caso CRAS sem PIA/PAIF cadastrado.",
                "sugerido": "Criar plano e cadastrar ações com prazo/responsável.",
            })

    # SCFV
    scfv_status = []
    for pt in scfv_parts:
        turma = turmas.get(pt.turma_id)
        if not turma:
            continue

        datas_encontros = []
        if turma.dias:
            mp = {"seg":0,"ter":1,"qua":2,"qui":3,"sex":4,"sab":5,"dom":6}
            s = (turma.dias or "").lower()
            weekdays = [v for k,v in mp.items() if k in s]
            d = mes_ini
            while d <= mes_fim:
                if d.weekday() in weekdays:
                    datas_encontros.append(d)
                d += timedelta(days=1)
        else:
            datas_encontros = sorted({x.data for x in pres if x.participante_id == pt.id})

        presencas = 0
        faltas = 0
        sem_reg = 0
        streak = 0
        streak_max = 0

        for d in datas_encontros:
            rec = pres_map.get((pt.id, d))
            if rec is None:
                sem_reg += 1
                faltas += 1
                streak += 1
            elif rec.presente_bool:
                presencas += 1
                streak = 0
            else:
                faltas += 1
                streak += 1
            streak_max = max(streak_max, streak)

        total = len(datas_encontros)
        taxa = (presencas / total) if total > 0 else None

        ev_alerta = streak_max >= limite_faltas_seguidas
        pres_alerta = (taxa is not None and taxa < presenca_min)

        scfv_status.append({
            "turma_id": turma.id,
            "turma_nome": turma.nome,
            "mes": f"{ano}-{str(mes).zfill(2)}",
            "total_encontros": total,
            "presencas": presencas,
            "faltas": faltas,
            "sem_registro": sem_reg,
            "taxa_presenca": taxa,
            "faltas_seguidas_max": streak_max,
            "evasao_alerta": ev_alerta,
            "baixa_presenca": pres_alerta,
        })

    cond.append({
        "programa": "SCFV",
        "ok": (len(scfv_status) > 0 and all((not x["evasao_alerta"]) and (not x["baixa_presenca"]) for x in scfv_status)),
        "itens": scfv_status if scfv_status else [{"regra": "Participação em turma", "ok": False}],
    })

    # Timeline
    timeline: List[Dict[str, Any]] = []
    for h in hist:
        timeline.append({
            "tipo": "caso_evento",
            "quando": _to_iso(h.criado_em),
            "titulo": f"{str(h.tipo_acao).upper()} · {h.etapa}",
            "autor": h.usuario_nome,
            "detalhe": h.observacoes,
            "caso_id": h.caso_id,
        })
    for x in cad[:10]:
        timeline.append({
            "tipo": "cadunico",
            "quando": _to_iso(x.atualizado_em),
            "titulo": f"CadÚnico · {x.status}",
            "autor": None,
            "detalhe": x.observacoes,
            "caso_id": x.caso_id,
        })
    for x in pres[:50]:
        timeline.append({
            "tipo": "scfv_presenca",
            "quando": _to_iso(x.atualizado_em),
            "titulo": f"SCFV · {'Presente' if x.presente_bool else 'Ausente'}",
            "autor": None,
            "detalhe": x.observacao,
            "caso_id": None,
        })
    timeline.sort(key=lambda e: e.get("quando") or "", reverse=True)

    # =========================================================
    # Ponte PopRua -> SUAS (para 360 real)
    # =========================================================
    poprua: Optional[Dict[str, Any]] = None
    link = session.exec(
        select(PessoaIdentidadeLink)
        .where(PessoaIdentidadeLink.pessoa_suas_id == pessoa_id)
        .order_by(PessoaIdentidadeLink.id.desc())
    ).first()
    if link:
        pr = session.get(PessoaRua, int(link.pessoarua_id))
        try:
            paifs = session.exec(
                select(PaifAcompanhamento)
                .where(or_(PaifAcompanhamento.pessoa_id == int(link.pessoarua_id), PaifAcompanhamento.pessoa_suas_id == pessoa_id))
                .order_by(PaifAcompanhamento.id.desc())
            ).all()
        except Exception:
            paifs = []
        try:
            triagens = session.exec(
                select(CrasTriagem)
                .where(or_(CrasTriagem.pessoa_id == int(link.pessoarua_id), CrasTriagem.pessoa_suas_id == pessoa_id))
                .order_by(CrasTriagem.id.desc())
            ).all()
        except Exception:
            triagens = []
        try:
            encs = session.exec(
                select(CrasEncaminhamento)
                .where(or_(CrasEncaminhamento.pessoa_id == int(link.pessoarua_id), CrasEncaminhamento.pessoa_suas_id == pessoa_id))
                .order_by(CrasEncaminhamento.id.desc())
            ).all()
        except Exception:
            encs = []

        poprua = {
            "link": link.dict(),
            "pessoarua": pr.dict() if pr else None,
            "paif": [x.dict() for x in paifs[:20]],
            "triagens": [x.dict() for x in triagens[:20]],
            "encaminhamentos_externos": [x.dict() for x in encs[:20]],
        }

    return {
        "pessoa": pessoa.dict(),
        "familia": familia.dict() if familia else None,
        "familia_membros": [m.dict() for m in membros] if membros else [],
        "casos_cras": [c.dict() for c in casos],
        "cadunico": {"atual": cad_atual.dict() if cad_atual else None, "lista": [x.dict() for x in cad[:10]]},
        "pia": {"plano": plano.dict() if plano else None, "acoes": [a.dict() for a in acoes[:50]]},
        "scfv": {"participacoes": scfv_status},
        "condicionalidades": cond,
        "pendencias": pendencias,
        "timeline": timeline[:200],
        "periodo": {"ano": int(ano), "mes": int(mes)},
        "poprua": poprua,
    }


@router.get("/familias/{familia_id}")
def ficha_familia(
    familia_id: int,
    ano: Optional[int] = Query(default=None),
    mes: Optional[int] = Query(default=None),
    limite_faltas_seguidas: int = Query(3, ge=1, le=60),
    presenca_min: float = Query(0.75, ge=0.0, le=1.0),
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
) -> Dict[str, Any]:
    familia = session.get(FamiliaSUAS, familia_id)
    if not familia:
        raise HTTPException(status_code=404, detail="Família não encontrada.")
    _check_municipio(usuario, int(familia.municipio_id))

    if ano is None or mes is None:
        ano, mes = _today_ym()
    mes_ini, mes_fim = _month_range(int(ano), int(mes))

    membros = session.exec(select(FamiliaMembro).where(FamiliaMembro.familia_id == familia_id)).all()
    pessoa_ids = [m.pessoa_id for m in membros]
    pessoas = []
    pessoas_map = {}
    if pessoa_ids:
        pessoas = session.exec(select(PessoaSUAS).where(PessoaSUAS.id.in_(pessoa_ids))).all()
        pessoas_map = {p.id: p for p in pessoas}

    # Casos da família
    casos = session.exec(select(CasoCras).where(CasoCras.familia_id == familia_id).order_by(CasoCras.id.desc())).all()
    caso_ids = [c.id for c in casos]

    # Histórico dos casos
    hist = []
    if caso_ids:
        hist = session.exec(
            select(CasoCrasHistorico)
            .where(CasoCrasHistorico.caso_id.in_(caso_ids))
            .order_by(CasoCrasHistorico.id.desc())
        ).all()

    # CadÚnico (por família / membros / casos)
    cad_conds = [CadunicoPreCadastro.familia_id == familia_id]
    if pessoa_ids:
        cad_conds.append(CadunicoPreCadastro.pessoa_id.in_(pessoa_ids))
    if caso_ids:
        cad_conds.append(CadunicoPreCadastro.caso_id.in_(caso_ids))

    cad = session.exec(select(CadunicoPreCadastro).where(or_(*cad_conds)).order_by(CadunicoPreCadastro.id.desc())).all()
    cad_atual = cad[0] if cad else None

    # PIA/PAIF (por casos)
    planos = []
    acoes = []
    if caso_ids:
        planos = session.exec(select(CrasPiaPlano).where(CrasPiaPlano.caso_id.in_(caso_ids)).order_by(CrasPiaPlano.id.desc())).all()
        plano_ids = [pl.id for pl in planos if pl and pl.id]
        if plano_ids:
            acoes = session.exec(select(CrasPiaAcao).where(CrasPiaAcao.plano_id.in_(plano_ids)).order_by(CrasPiaAcao.id.desc())).all()

    # SCFV (por membros)
    scfv_parts = []
    if pessoa_ids:
        scfv_parts = session.exec(select(ScfvParticipante).where(ScfvParticipante.pessoa_id.in_(pessoa_ids)).where(ScfvParticipante.status == "ativo")).all()
    scfv_part_ids = [p.id for p in scfv_parts]
    turmas = {}
    if scfv_parts:
        turma_ids = list({p.turma_id for p in scfv_parts})
        for tma in session.exec(select(ScfvTurma).where(ScfvTurma.id.in_(turma_ids))).all():
            turmas[tma.id] = tma

    pres = []
    if scfv_part_ids:
        pres = session.exec(
            select(ScfvPresenca)
            .where(ScfvPresenca.participante_id.in_(scfv_part_ids))
            .where(ScfvPresenca.data >= mes_ini)
            .where(ScfvPresenca.data <= mes_fim)
        ).all()
    pres_map = {(x.participante_id, x.data): x for x in pres}

    # Condicionalidades + pendências agregadas
    pendencias: List[Dict[str, Any]] = []
    cond: List[Dict[str, Any]] = []

    # CadÚnico
    if cad_atual:
        ok_cad = cad_atual.status == "finalizado"
        if not ok_cad:
            pendencias.append({
                "tipo": "cadunico_pendente",
                "gravidade": "alta",
                "referencia": f"Família #{familia_id}",
                "detalhe": f"CadÚnico status: {cad_atual.status}",
                "sugerido": "Agendar/atualizar e finalizar ou registrar não compareceu.",
            })
        cond.append({"programa": "CadÚnico", "ok": ok_cad, "itens": [{"regra": "Status", "valor": cad_atual.status, "ok": ok_cad}]})
    else:
        pendencias.append({
            "tipo": "cadunico_inexistente",
            "gravidade": "media",
            "referencia": f"Família #{familia_id}",
            "detalhe": "Sem CadÚnico vinculado (família/membros/casos).",
            "sugerido": "Criar pré-cadastro a partir do CRAS e agendar.",
        })
        cond.append({"programa": "CadÚnico", "ok": False, "itens": [{"regra": "Existe pré-cadastro", "ok": False}]})

    # PIA/PAIF
    if planos:
        hoje = date.today()
        atrasadas = 0
        for a in acoes:
            if a.status != "concluida" and a.prazo and a.prazo < hoje:
                atrasadas += 1
        if atrasadas:
            pendencias.append({
                "tipo": "pia_acoes_atrasadas",
                "gravidade": "alta" if atrasadas >= 2 else "media",
                "referencia": f"Família #{familia_id}",
                "detalhe": f"{atrasadas} ações do PIA/PAIF atrasadas.",
                "sugerido": "Atualizar prazos, concluir ações ou justificar.",
            })
        cond.append({"programa": "PAIF/PIA", "ok": atrasadas == 0, "itens": [{"regra": "Planos", "valor": len(planos), "ok": True}, {"regra":"Ações atrasadas","valor":atrasadas,"ok":atrasadas==0}]})
    else:
        if casos:
            pendencias.append({
                "tipo": "pia_inexistente",
                "gravidade": "media",
                "referencia": f"Família #{familia_id}",
                "detalhe": "Casos CRAS da família sem PIA/PAIF.",
                "sugerido": "Criar plano e ações.",
            })
        cond.append({"programa": "PAIF/PIA", "ok": False, "itens": [{"regra": "Existe plano", "ok": False}]})

    # SCFV agregado (por membro/turma)
    scfv_rows = []
    for pt in scfv_parts:
        turma = turmas.get(pt.turma_id)
        pessoa = pessoas_map.get(pt.pessoa_id)
        nome = (pessoa.nome_social or pessoa.nome) if pessoa else f"Pessoa #{pt.pessoa_id}"
        if not turma:
            continue

        # calendário simples (seg/ter/qua...) dentro do mês
        datas = []
        if turma.dias:
            mp = {"seg":0,"ter":1,"qua":2,"qui":3,"sex":4,"sab":5,"dom":6}
            s = (turma.dias or "").lower()
            weekdays = [v for k,v in mp.items() if k in s]
            d = mes_ini
            while d <= mes_fim:
                if d.weekday() in weekdays:
                    datas.append(d)
                d += timedelta(days=1)
        else:
            datas = sorted({x.data for x in pres if x.participante_id == pt.id})

        presencas = 0
        faltas = 0
        sem_reg = 0
        streak = 0
        streak_max = 0

        for d in datas:
            rec = pres_map.get((pt.id, d))
            if rec is None:
                sem_reg += 1
                faltas += 1
                streak += 1
            elif rec.presente_bool:
                presencas += 1
                streak = 0
            else:
                faltas += 1
                streak += 1
            streak_max = max(streak_max, streak)

        total = len(datas)
        taxa = (presencas / total) if total > 0 else None
        ev = streak_max >= limite_faltas_seguidas
        bp = (taxa is not None and taxa < presenca_min)

        scfv_rows.append({
            "pessoa_id": pt.pessoa_id,
            "pessoa_nome": nome,
            "turma_id": turma.id,
            "turma_nome": turma.nome,
            "total_encontros": total,
            "presencas": presencas,
            "faltas": faltas,
            "sem_registro": sem_reg,
            "taxa_presenca": taxa,
            "faltas_seguidas_max": streak_max,
            "evasao_alerta": ev,
            "baixa_presenca": bp,
        })

        if ev:
            pendencias.append({
                "tipo": "scfv_evasao",
                "gravidade": "alta",
                "referencia": f"Turma #{turma.id} · {nome}",
                "detalhe": f"Faltas seguidas (máx): {streak_max}",
                "sugerido": "Busca ativa + registro de acompanhamento.",
            })
        if bp:
            pendencias.append({
                "tipo": "scfv_baixa_presenca",
                "gravidade": "media",
                "referencia": f"Turma #{turma.id} · {nome}",
                "detalhe": f"Presença: {int((taxa or 0)*100)}%",
                "sugerido": "Reforçar adesão + registrar acompanhamento.",
            })

    cond.append({
        "programa": "SCFV",
        "ok": (len(scfv_rows) > 0 and all((not x["evasao_alerta"]) and (not x["baixa_presenca"]) for x in scfv_rows)),
        "itens": scfv_rows if scfv_rows else [{"regra": "Participação SCFV", "ok": False}],
    })

    # Timeline agregada
    timeline: List[Dict[str, Any]] = []
    for h in hist:
        timeline.append({
            "tipo": "caso_evento",
            "quando": _to_iso(h.criado_em),
            "titulo": f"{str(h.tipo_acao).upper()} · {h.etapa}",
            "autor": h.usuario_nome,
            "detalhe": h.observacoes,
            "caso_id": h.caso_id,
        })
    for x in cad[:10]:
        timeline.append({
            "tipo": "cadunico",
            "quando": _to_iso(x.atualizado_em),
            "titulo": f"CadÚnico · {x.status}",
            "autor": None,
            "detalhe": x.observacoes,
            "caso_id": x.caso_id,
        })
    for x in pres[:80]:
        timeline.append({
            "tipo": "scfv_presenca",
            "quando": _to_iso(x.atualizado_em),
            "titulo": f"SCFV · {'Presente' if x.presente_bool else 'Ausente'}",
            "autor": None,
            "detalhe": x.observacao,
            "caso_id": None,
        })
    # eventos de auditoria da ficha (família)
    try:
        evs = session.exec(select(FichaEvento).where(FichaEvento.alvo_tipo=='familia').where(FichaEvento.alvo_id==familia_id).order_by(FichaEvento.id.desc())).all()
        for ev in evs[:30]:
            timeline.append({
                'tipo': 'ficha_evento',
                'quando': _to_iso(ev.criado_em),
                'titulo': f"FICHA · {ev.tipo}",
                'autor': ev.criado_por_nome,
                'detalhe': ev.detalhe,
                'caso_id': None,
            })
    except Exception:
        pass

    timeline.sort(key=lambda e: e.get("quando") or "", reverse=True)

    # membros com pessoa
    membros_out = []
    for m in membros:
        pp = pessoas_map.get(m.pessoa_id)
        membros_out.append({
            "membro": m.dict(),
            "pessoa": pp.dict() if pp else None,
        })

    # =========================================================
    # Ponte PopRua -> SUAS (agregada por membros)
    # =========================================================
    poprua: Optional[Dict[str, Any]] = None
    poprua: Optional[Dict[str, Any]] = None
    try:
        links = session.exec(
            select(PessoaIdentidadeLink).where(PessoaIdentidadeLink.pessoa_suas_id.in_(pessoa_ids))
        ).all() if pessoa_ids else []
        pr_ids = [int(l.pessoarua_id) for l in links]
        if pr_ids:
            paifs = session.exec(
                select(PaifAcompanhamento)
                .where(or_(PaifAcompanhamento.pessoa_id.in_(pr_ids), PaifAcompanhamento.pessoa_suas_id.in_(pessoa_ids)))
                .order_by(PaifAcompanhamento.id.desc())
            ).all()
            triagens = session.exec(
                select(CrasTriagem)
                .where(or_(CrasTriagem.pessoa_id.in_(pr_ids), CrasTriagem.pessoa_suas_id.in_(pessoa_ids)))
                .order_by(CrasTriagem.id.desc())
            ).all()
            encs = session.exec(
                select(CrasEncaminhamento)
                .where(or_(CrasEncaminhamento.pessoa_id.in_(pr_ids), CrasEncaminhamento.pessoa_suas_id.in_(pessoa_ids)))
                .order_by(CrasEncaminhamento.id.desc())
            ).all()

            poprua = {
                "links": [l.dict() for l in links[:50]],
                "pessoarua_ids": pr_ids,
                "paif": [x.dict() for x in paifs[:20]],
                "triagens": [x.dict() for x in triagens[:20]],
                "encaminhamentos_externos": [x.dict() for x in encs[:20]],
            }
    except Exception:
        poprua = None

    return {
        "familia": familia.dict(),
        "membros": membros_out,
        "casos_cras": [c.dict() for c in casos],
        "cadunico": {"atual": cad_atual.dict() if cad_atual else None, "lista": [x.dict() for x in cad[:10]]},
        "pia": {"planos": [pl.dict() for pl in planos[:10]], "acoes": [a.dict() for a in acoes[:50]]},
        "scfv": {"participacoes": scfv_rows},
        "condicionalidades": cond,
        "pendencias": pendencias,
        "timeline": timeline[:200],
        "poprua": poprua,
        "periodo": {"ano": int(ano), "mes": int(mes)},
    }


@router.get("/anexos")
def listar_anexos(
    alvo_tipo: str = Query(...),  # pessoa|familia
    alvo_id: int = Query(...),
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    if alvo_tipo not in ("pessoa", "familia"):
        raise HTTPException(status_code=400, detail="alvo_tipo inválido (pessoa|familia).")

    # valida município pelo alvo
    if alvo_tipo == "pessoa":
        pe = session.get(PessoaSUAS, int(alvo_id))
        if not pe: raise HTTPException(status_code=404, detail="Pessoa não encontrada.")
        _check_municipio(usuario, int(pe.municipio_id))
        municipio_id = int(pe.municipio_id)
    else:
        fa = session.get(FamiliaSUAS, int(alvo_id))
        if not fa: raise HTTPException(status_code=404, detail="Família não encontrada.")
        _check_municipio(usuario, int(fa.municipio_id))
        municipio_id = int(fa.municipio_id)

    rows = session.exec(
        select(FichaAnexo)
        .where(FichaAnexo.municipio_id == municipio_id)
        .where(FichaAnexo.alvo_tipo == alvo_tipo)
        .where(FichaAnexo.alvo_id == int(alvo_id))
        .order_by(FichaAnexo.id.desc())
    ).all()
    return rows


@router.post("/anexos")
def criar_anexo(
    payload: Dict[str, Any],
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    alvo_tipo = payload.get("alvo_tipo")
    alvo_id = payload.get("alvo_id")
    titulo = (payload.get("titulo") or "").strip()
    url = (payload.get("url") or "").strip()
    tipo = payload.get("tipo")

    if alvo_tipo not in ("pessoa", "familia"):
        raise HTTPException(status_code=400, detail="alvo_tipo inválido (pessoa|familia).")
    if not alvo_id or not titulo or not url:
        raise HTTPException(status_code=400, detail="alvo_id, titulo e url são obrigatórios.")

    if alvo_tipo == "pessoa":
        pe = session.get(PessoaSUAS, int(alvo_id))
        if not pe: raise HTTPException(status_code=404, detail="Pessoa não encontrada.")
        _check_municipio(usuario, int(pe.municipio_id))
        municipio_id = int(pe.municipio_id)
    else:
        fa = session.get(FamiliaSUAS, int(alvo_id))
        if not fa: raise HTTPException(status_code=404, detail="Família não encontrada.")
        _check_municipio(usuario, int(fa.municipio_id))
        municipio_id = int(fa.municipio_id)

    an = FichaAnexo(
        municipio_id=municipio_id,
        alvo_tipo=alvo_tipo,
        alvo_id=int(alvo_id),
        titulo=titulo,
        url=url,
        tipo=tipo,
        criado_por_usuario_id=getattr(usuario, "id", None),
        criado_por_nome=getattr(usuario, "nome", None),
    )
    session.add(an)
    session.commit()
    session.refresh(an)
    return an


@router.get("/eventos")
def listar_eventos(
    alvo_tipo: str = Query(...),
    alvo_id: int = Query(...),
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    if alvo_tipo not in ("pessoa", "familia"):
        raise HTTPException(status_code=400, detail="alvo_tipo inválido (pessoa|familia).")

    if alvo_tipo == "pessoa":
        pe = session.get(PessoaSUAS, int(alvo_id))
        if not pe: raise HTTPException(status_code=404, detail="Pessoa não encontrada.")
        _check_municipio(usuario, int(pe.municipio_id))
        municipio_id = int(pe.municipio_id)
    else:
        fa = session.get(FamiliaSUAS, int(alvo_id))
        if not fa: raise HTTPException(status_code=404, detail="Família não encontrada.")
        _check_municipio(usuario, int(fa.municipio_id))
        municipio_id = int(fa.municipio_id)

    rows = session.exec(
        select(FichaEvento)
        .where(FichaEvento.municipio_id == municipio_id)
        .where(FichaEvento.alvo_tipo == alvo_tipo)
        .where(FichaEvento.alvo_id == int(alvo_id))
        .order_by(FichaEvento.id.desc())
    ).all()
    return rows


@router.post("/eventos")
def criar_evento(
    payload: Dict[str, Any],
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    alvo_tipo = payload.get("alvo_tipo")
    alvo_id = payload.get("alvo_id")
    tipo = (payload.get("tipo") or "").strip()
    detalhe = payload.get("detalhe")

    if alvo_tipo not in ("pessoa", "familia"):
        raise HTTPException(status_code=400, detail="alvo_tipo inválido (pessoa|familia).")
    if not alvo_id or not tipo:
        raise HTTPException(status_code=400, detail="alvo_id e tipo são obrigatórios.")

    if alvo_tipo == "pessoa":
        pe = session.get(PessoaSUAS, int(alvo_id))
        if not pe: raise HTTPException(status_code=404, detail="Pessoa não encontrada.")
        _check_municipio(usuario, int(pe.municipio_id))
        municipio_id = int(pe.municipio_id)
    else:
        fa = session.get(FamiliaSUAS, int(alvo_id))
        if not fa: raise HTTPException(status_code=404, detail="Família não encontrada.")
        _check_municipio(usuario, int(fa.municipio_id))
        municipio_id = int(fa.municipio_id)

    ev = FichaEvento(
        municipio_id=municipio_id,
        alvo_tipo=alvo_tipo,
        alvo_id=int(alvo_id),
        tipo=tipo,
        detalhe=detalhe,
        criado_por_usuario_id=getattr(usuario, "id", None),
        criado_por_nome=getattr(usuario, "nome", None),
    )
    session.add(ev)
    session.commit()
    session.refresh(ev)
    return ev
