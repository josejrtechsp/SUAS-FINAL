from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select
from sqlalchemy import or_

from app.core.db import get_session
from app.core.auth import get_current_user, pode_acesso_global
from app.models.usuario import Usuario

from app.models.caso_cras import CasoCras
from app.models.cras_pia import CrasPiaPlano
from app.models.pessoa_suas import PessoaSUAS
from app.models.cadunico_precadastro import CadunicoPreCadastro
from app.models.scfv import ScfvTurma, ScfvParticipante, ScfvPresenca
from app.models.cras_tarefas import CrasTarefa


router = APIRouter(prefix="/cras/relatorios", tags=["cras-relatorios"])


def _mun_id(usuario: Usuario) -> Optional[int]:
    mid = getattr(usuario, "municipio_id", None)
    return int(mid) if mid is not None else None


def _parse_weekdays(dias_str: str) -> List[int]:
    s = (dias_str or "").lower()
    mp = {"seg": 0, "ter": 1, "qua": 2, "qui": 3, "sex": 4, "sab": 5, "dom": 6}
    out = []
    for k, v in mp.items():
        if k in s:
            out.append(v)
    return sorted(set(out))


@router.get("/overview")
def overview(
    unidade_id: int = Query(...),
    ano: Optional[int] = Query(default=None),
    mes: Optional[int] = Query(default=None),
    dias_cadunico: int = Query(30, ge=1, le=365),
    limite_evasao: int = Query(3, ge=1, le=60),
    limite_presenca_min: float = Query(0.75, ge=0.0, le=1.0),
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
) -> Dict[str, Any]:
    # período
    today = date.today()
    ano = int(ano or today.year)
    mes = int(mes or today.month)
    start = date(ano, mes, 1)
    end = (start.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)

    # Casos CRAS da unidade
    stmt = select(CasoCras).where(CasoCras.unidade_id == int(unidade_id))
    if not pode_acesso_global(usuario):
        um = _mun_id(usuario)
        if um is None:
            raise HTTPException(status_code=403, detail="Usuário sem município.")
        stmt = stmt.where(CasoCras.municipio_id == um)

    casos = session.exec(stmt).all()
    caso_ids = [c.id for c in casos if c.id]

    # PIA faltando (casos em andamento sem plano)
    caso_com_plano = set()
    if caso_ids:
        rows = session.exec(select(CrasPiaPlano.caso_id).where(CrasPiaPlano.caso_id.in_(caso_ids))).all()
        caso_com_plano = set([x for x in rows if x is not None])

    faltando = [c for c in casos if c.status == "em_andamento" and (c.id not in caso_com_plano)]

    # mapeia pessoas dos casos faltando
    pessoas_map: Dict[int, PessoaSUAS] = {}
    pessoa_ids = [c.pessoa_id for c in faltando if c.pessoa_id]
    if pessoa_ids:
        for p in session.exec(select(PessoaSUAS).where(PessoaSUAS.id.in_(pessoa_ids))).all():
            pessoas_map[p.id] = p

    pia_faltando_por_tecnico: Dict[str, int] = {}
    pia_faltando_por_territorio: Dict[str, int] = {}
    pia_faltando_rows = []

    for c in faltando[:30]:
        k = str(c.tecnico_responsavel_id or "sem_tecnico")
        pia_faltando_por_tecnico[k] = pia_faltando_por_tecnico.get(k, 0) + 1

        pe = pessoas_map.get(c.pessoa_id)
        terr = (pe.territorio or pe.bairro) if pe else "sem_pessoa"
        pia_faltando_por_territorio[terr] = pia_faltando_por_territorio.get(terr, 0) + 1

        pia_faltando_rows.append({
            "caso_id": c.id,
            "pessoa_id": c.pessoa_id,
            "familia_id": c.familia_id,
            "etapa": c.etapa_atual,
            "status": c.status,
            "nome": (pe.nome_social or pe.nome) if pe else None,
            "cpf": pe.cpf if pe else None,
            "nis": pe.nis if pe else None,
            "territorio": pe.territorio if pe else None,
            "bairro": pe.bairro if pe else None,
        })

    # CadÚnico atrasado
    cut = datetime.utcnow() - timedelta(days=int(dias_cadunico))
    cad_stmt = (
        select(CadunicoPreCadastro)
        .where(CadunicoPreCadastro.unidade_id == int(unidade_id))
        .where(CadunicoPreCadastro.status.in_(["pendente", "agendado"]))
    )
    if not pode_acesso_global(usuario):
        cad_stmt = cad_stmt.where(CadunicoPreCadastro.municipio_id == _mun_id(usuario))

    cad_rows = session.exec(cad_stmt).all()
    cad_atrasados = [x for x in cad_rows if x.criado_em and x.criado_em <= cut]

    cadunico_atrasado_por_status: Dict[str, int] = {}
    cadunico_atrasado_rows = []

    for x in cad_atrasados[:30]:
        cadunico_atrasado_por_status[x.status] = cadunico_atrasado_por_status.get(x.status, 0) + 1
        pe = session.get(PessoaSUAS, int(x.pessoa_id)) if x.pessoa_id else None
        cadunico_atrasado_rows.append({
            "precadastro_id": x.id,
            "caso_id": x.caso_id,
            "pessoa_id": x.pessoa_id,
            "familia_id": x.familia_id,
            "status": x.status,
            "criado_em": x.criado_em.isoformat() if x.criado_em else None,
            "nome": (pe.nome_social or pe.nome) if pe else None,
            "cpf": pe.cpf if pe else None,
            "nis": pe.nis if pe else None,
        })

    # SCFV
    turmas = session.exec(
        select(ScfvTurma)
        .where(ScfvTurma.unidade_id == int(unidade_id))
        .where(ScfvTurma.ativo == True)
    ).all()
    turma_ids = [t.id for t in turmas]

    parts = session.exec(
        select(ScfvParticipante)
        .where(ScfvParticipante.turma_id.in_(turma_ids))
        .where(ScfvParticipante.status == "ativo")
    ).all() if turma_ids else []

    part_ids = [p.id for p in parts]
    pres = session.exec(
        select(ScfvPresenca)
        .where(ScfvPresenca.participante_id.in_(part_ids))
        .where(ScfvPresenca.data >= start)
        .where(ScfvPresenca.data <= end)
    ).all() if part_ids else []

    pres_map = {(x.participante_id, x.data): x for x in pres}
    part_turma = {pt.id: pt.turma_id for pt in parts}
    pres_dates_by_turma: Dict[int, set] = {}
    for x in pres:
        tid = part_turma.get(x.participante_id)
        if tid is None:
            continue
        pres_dates_by_turma.setdefault(tid, set()).add(x.data)

    parts_by_turma: Dict[int, list] = {}
    for pt in parts:
        parts_by_turma.setdefault(pt.turma_id, []).append(pt)

    total_evasao = 0
    total_baixa = 0
    total_sem_reg = 0
    top_turmas = []

    for tma in turmas:
        weekdays = _parse_weekdays(tma.dias or "")
        datas_encontros = []
        if weekdays:
            dd = start
            while dd <= end:
                if dd.weekday() in weekdays:
                    datas_encontros.append(dd)
                dd += timedelta(days=1)
        else:
            datas_encontros = sorted(list(pres_dates_by_turma.get(tma.id, set())))

        sem_reg = [d for d in datas_encontros if d not in pres_dates_by_turma.get(tma.id, set())]
        total_sem_reg += len(sem_reg)

        evasao_turma = 0
        baixa_turma = 0

        for pt in parts_by_turma.get(tma.id, []):
            total = len(datas_encontros)
            if total == 0:
                continue
            presencas = 0
            streak = 0
            streak_max = 0

            for dd in datas_encontros:
                rec = pres_map.get((pt.id, dd))
                if rec is None:
                    streak += 1
                elif rec.presente_bool:
                    presencas += 1
                    streak = 0
                else:
                    streak += 1
                streak_max = max(streak_max, streak)

            taxa = presencas / total if total else None
            if streak_max >= int(limite_evasao):
                evasao_turma += 1
            if taxa is not None and taxa < float(limite_presenca_min):
                baixa_turma += 1

        total_evasao += evasao_turma
        total_baixa += baixa_turma

        if evasao_turma or baixa_turma or len(sem_reg):
            top_turmas.append({
                "turma_id": tma.id,
                "turma_nome": tma.nome,
                "evasao": evasao_turma,
                "baixa_presenca": baixa_turma,
                "sem_registro": len(sem_reg),
                "encontros": len(datas_encontros),
            })

    top_turmas.sort(key=lambda x: (-x["evasao"], -x["baixa_presenca"], -x["sem_registro"], x["turma_nome"]))

    top_pendencias = [
        {"tipo": "PIA faltando", "total": len(faltando)},
        {"tipo": f"CadÚnico atrasado (+{dias_cadunico}d)", "total": len(cad_atrasados)},
        {"tipo": "SCFV evasão", "total": total_evasao},
        {"tipo": "SCFV baixa presença", "total": total_baixa},
        {"tipo": "SCFV sem registro", "total": total_sem_reg},
    ]
    top_pendencias.sort(key=lambda x: -x["total"])

    return {
        "periodo": {"ano": ano, "mes": mes},
        "pia_faltando_total": len(faltando),
        "pia_faltando_por_tecnico": pia_faltando_por_tecnico,
        "pia_faltando_por_territorio": pia_faltando_por_territorio,
        "pia_faltando_rows": pia_faltando_rows,
        "cadunico_atrasado_total": len(cad_atrasados),
        "cadunico_atrasado_por_status": cadunico_atrasado_por_status,
        "cadunico_atrasado_rows": cadunico_atrasado_rows,
        "scfv_evasao_total": total_evasao,
        "scfv_baixa_total": total_baixa,
        "scfv_sem_reg_total": total_sem_reg,
        "scfv_top_turmas": top_turmas[:10],
        "top_pendencias": top_pendencias[:10],
    }


def _month_start(d: date) -> date:
    return date(d.year, d.month, 1)


def _add_months(d: date, months: int) -> date:
    """Soma meses em date (sempre retorna 1º dia do mês)."""
    y = d.year + (d.month - 1 + months) // 12
    m = (d.month - 1 + months) % 12 + 1
    return date(y, m, 1)


@router.get("/serie")
def serie(
    unidade_id: int = Query(...),
    meses: int = Query(12, ge=1, le=60),
    dias_cadunico: int = Query(30, ge=1, le=365),
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
) -> Dict[str, Any]:
    """Série histórica (mensal) para gestão.

    Entrega contagens mensais e backlog no final do mês para:
    - Casos (novos/encerrados/abertos)
    - PIA faltando (abertos sem plano)
    - CadÚnico atrasado (backlog)
    - Tarefas (criadas/abertas/vencidas)
    - SCFV (registros de presença)
    """

    today = date.today()
    end_month = _month_start(today)
    start_month = _add_months(end_month, -(int(meses) - 1))

    # Segurança municipal
    mun_user = _mun_id(usuario)
    if not pode_acesso_global(usuario):
        if mun_user is None:
            raise HTTPException(status_code=403, detail="Usuário sem município.")

    # Pré-fetch leve (MVP): pega registros da unidade e calcula em memória.
    stmt_casos = select(CasoCras).where(CasoCras.unidade_id == int(unidade_id))
    stmt_cad = select(CadunicoPreCadastro).where(CadunicoPreCadastro.unidade_id == int(unidade_id))
    stmt_tarefas = select(CrasTarefa).where(CrasTarefa.unidade_id == int(unidade_id))

    if not pode_acesso_global(usuario):
        stmt_casos = stmt_casos.where(CasoCras.municipio_id == mun_user)
        stmt_cad = stmt_cad.where(CadunicoPreCadastro.municipio_id == mun_user)
        stmt_tarefas = stmt_tarefas.where(CrasTarefa.municipio_id == mun_user)

    casos = session.exec(stmt_casos).all()
    cad = session.exec(stmt_cad).all()
    tarefas = session.exec(stmt_tarefas).all()

    # planos PIA existentes (para decidir backlog)
    caso_ids = [c.id for c in casos if c.id]
    caso_com_plano = set()
    if caso_ids:
        rows = session.exec(select(CrasPiaPlano.caso_id).where(CrasPiaPlano.caso_id.in_(caso_ids))).all()
        caso_com_plano = set([x for x in rows if x is not None])

    # SCFV presenças por unidade (pelo campo data da presença)
    turmas = session.exec(select(ScfvTurma).where(ScfvTurma.unidade_id == int(unidade_id)).where(ScfvTurma.ativo == True)).all()
    turma_ids = [t.id for t in turmas if t and getattr(t, 'id', None) is not None]
    parts = session.exec(select(ScfvParticipante).where(ScfvParticipante.turma_id.in_(turma_ids))).all() if turma_ids else []
    part_ids = [p.id for p in parts if p and getattr(p, 'id', None) is not None]
    presencas = session.exec(select(ScfvPresenca).where(ScfvPresenca.participante_id.in_(part_ids))).all() if part_ids else []

    serie_rows: List[Dict[str, Any]] = []

    m = start_month
    while m <= end_month:
        # mês atual
        ms = m
        me = _add_months(m, 1) - timedelta(days=1)

        # Casos
        novos = 0
        encerrados = 0
        abertos_fim = 0
        pia_faltando_fim = 0

        for c in casos:
            da = getattr(c, 'data_abertura', None)
            de = getattr(c, 'data_encerramento', None)
            if da and ms <= da.date() <= me:
                novos += 1
            if de and ms <= de.date() <= me:
                encerrados += 1

            # backlog no fim do mês
            if da and da.date() <= me and (de is None or de.date() > me):
                abertos_fim += 1
                if getattr(c, 'status', None) == 'em_andamento' and (getattr(c, 'id', None) not in caso_com_plano):
                    pia_faltando_fim += 1

        # CadÚnico backlog
        cad_abertos = 0
        cad_atrasados = 0
        cut = datetime(me.year, me.month, me.day) - timedelta(days=int(dias_cadunico))
        for x in cad:
            st = (getattr(x, 'status', '') or '').strip().lower()
            if st not in ('pendente', 'agendado'):
                continue
            ce = getattr(x, 'criado_em', None)
            if not ce:
                continue
            if ce.date() <= me:
                cad_abertos += 1
                if ce <= cut:
                    cad_atrasados += 1

        # Tarefas
        tarefas_criadas = 0
        tarefas_abertas = 0
        tarefas_vencidas = 0
        for t in tarefas:
            ce = getattr(t, 'criado_em', None)
            if ce and ms <= ce.date() <= me:
                tarefas_criadas += 1
            st = (getattr(t, 'status', '') or '').strip().lower()
            if st != 'concluida':
                # backlog
                if ce and ce.date() <= me:
                    tarefas_abertas += 1
                    dv = getattr(t, 'data_vencimento', None)
                    if dv and dv < me:
                        tarefas_vencidas += 1

        # SCFV presenças registradas (por data do encontro)
        scfv_registros = 0
        for pr in presencas:
            dd = getattr(pr, 'data', None)
            if dd and ms <= dd <= me:
                scfv_registros += 1

        serie_rows.append(
            {
                'ano': ms.year,
                'mes': ms.month,
                'label': f"{ms.month:02d}/{ms.year}",
                'casos_novos': novos,
                'casos_encerrados': encerrados,
                'casos_abertos_fim': abertos_fim,
                'pia_faltando_fim': pia_faltando_fim,
                'cadunico_abertos_fim': cad_abertos,
                'cadunico_atrasados_fim': cad_atrasados,
                'tarefas_criadas': tarefas_criadas,
                'tarefas_abertas_fim': tarefas_abertas,
                'tarefas_vencidas_fim': tarefas_vencidas,
                'scfv_registros_presenca': scfv_registros,
            }
        )

        m = _add_months(m, 1)

    return {
        'unidade_id': int(unidade_id),
        'meses': int(meses),
        'periodo': {'inicio': start_month.isoformat(), 'fim': end_month.isoformat()},
        'dias_cadunico': int(dias_cadunico),
        'rows': serie_rows,
    }


@router.get("/cruzamentos")
def cruzamentos(
    unidade_id: int = Query(...),
    meses: int = Query(12, ge=1, le=60),
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
) -> Dict[str, Any]:
    """Cruzamentos simples (pessoas em múltiplos serviços) — recorte por unidade."""

    today = date.today()
    end = (date(today.year, today.month, 1).replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
    start = _add_months(date(today.year, today.month, 1), -(int(meses) - 1))

    mun_user = _mun_id(usuario)
    if not pode_acesso_global(usuario):
        if mun_user is None:
            raise HTTPException(status_code=403, detail="Usuário sem município.")

    # Casos
    stmt_casos = select(CasoCras).where(CasoCras.unidade_id == int(unidade_id))
    if not pode_acesso_global(usuario):
        stmt_casos = stmt_casos.where(CasoCras.municipio_id == mun_user)
    casos = session.exec(stmt_casos).all()

    set_casos = set()
    for c in casos:
        da = getattr(c, 'data_abertura', None)
        if not da:
            continue
        if da.date() < start or da.date() > end:
            continue
        pid = getattr(c, 'pessoa_id', None)
        if pid:
            set_casos.add(int(pid))

    # CadÚnico
    stmt_cad = select(CadunicoPreCadastro).where(CadunicoPreCadastro.unidade_id == int(unidade_id))
    if not pode_acesso_global(usuario):
        stmt_cad = stmt_cad.where(CadunicoPreCadastro.municipio_id == mun_user)
    cad = session.exec(stmt_cad).all()
    set_cad = set()
    for x in cad:
        ce = getattr(x, 'criado_em', None)
        if not ce:
            continue
        if ce.date() < start or ce.date() > end:
            continue
        pid = getattr(x, 'pessoa_id', None)
        if pid:
            set_cad.add(int(pid))

    # SCFV participantes (pelo cadastro)
    stmt_tur = select(ScfvTurma).where(ScfvTurma.unidade_id == int(unidade_id))
    if not pode_acesso_global(usuario):
        stmt_tur = stmt_tur.where(ScfvTurma.municipio_id == mun_user)
    turmas = session.exec(stmt_tur).all()
    turma_ids = [t.id for t in turmas if t and getattr(t, 'id', None) is not None]
    parts = session.exec(select(ScfvParticipante).where(ScfvParticipante.turma_id.in_(turma_ids))).all() if turma_ids else []
    set_scfv = set()
    for p in parts:
        pid = getattr(p, 'pessoa_id', None)
        if pid:
            set_scfv.add(int(pid))

    # Interseções
    a = set_casos
    b = set_cad
    c = set_scfv

    ab = a & b
    ac = a & c
    bc = b & c
    abc = a & b & c

    return {
        'unidade_id': int(unidade_id),
        'meses': int(meses),
        'periodo': {'inicio': start.isoformat(), 'fim': end.isoformat()},
        'totais': {
            'pessoas_em_casos': len(a),
            'pessoas_em_cadunico': len(b),
            'pessoas_em_scfv': len(c),
        },
        'cruzamentos': {
            'casos_e_cadunico': len(ab),
            'casos_e_scfv': len(ac),
            'cadunico_e_scfv': len(bc),
            'casos_cadunico_scfv': len(abc),
        },
    }
