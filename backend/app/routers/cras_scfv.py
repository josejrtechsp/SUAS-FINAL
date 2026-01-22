from __future__ import annotations

from datetime import date, datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select

from app.core.db import get_session
from app.core.auth import get_current_user, pode_acesso_global
from app.models.usuario import Usuario

from app.models.scfv import ScfvTurma, ScfvParticipante, ScfvPresenca
from app.models.pessoa_suas import PessoaSUAS

router = APIRouter(prefix="/cras/scfv", tags=["cras-scfv"])


def _now() -> datetime:
    return datetime.utcnow()


def _mun_id(usuario: Usuario) -> Optional[int]:
    mid = getattr(usuario, "municipio_id", None)
    return int(mid) if mid is not None else None


def _check_municipio(usuario: Usuario, municipio_id: int) -> None:
    if pode_acesso_global(usuario):
        return
    um = _mun_id(usuario)
    if um is None or int(municipio_id) != int(um):
        raise HTTPException(status_code=403, detail="Acesso negado (município).")


@router.get("/turmas")
def listar_turmas(
    unidade_id: Optional[int] = Query(default=None),
    ativo: Optional[bool] = Query(default=True),
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
) -> List[ScfvTurma]:
    stmt = select(ScfvTurma).order_by(ScfvTurma.id.desc())

    if not pode_acesso_global(usuario):
        um = _mun_id(usuario)
        if um is None:
            raise HTTPException(status_code=403, detail="Usuário sem município.")
        stmt = stmt.where(ScfvTurma.municipio_id == um)

    if unidade_id:
        stmt = stmt.where(ScfvTurma.unidade_id == int(unidade_id))
    if ativo is not None:
        stmt = stmt.where(ScfvTurma.ativo == bool(ativo))

    return session.exec(stmt).all()


@router.post("/turmas")
def criar_turma(
    payload: Dict[str, Any],
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
) -> ScfvTurma:
    nome = (payload.get("nome") or "").strip()
    if not nome:
        raise HTTPException(status_code=400, detail="nome é obrigatório.")
    unidade_id = payload.get("unidade_id")
    if not unidade_id:
        raise HTTPException(status_code=400, detail="unidade_id é obrigatório.")

    municipio_id = payload.get("municipio_id") or _mun_id(usuario)
    if municipio_id is None:
        raise HTTPException(status_code=400, detail="municipio_id não informado e usuário sem município.")
    _check_municipio(usuario, int(municipio_id))

    turma = ScfvTurma(
        municipio_id=int(municipio_id),
        unidade_id=int(unidade_id),
        nome=nome,
        publico=payload.get("publico"),
        faixa_etaria=payload.get("faixa_etaria"),
        dias=payload.get("dias"),
        horario=payload.get("horario"),
        vagas=payload.get("vagas"),
        local=payload.get("local"),
        ativo=True if payload.get("ativo") is None else bool(payload.get("ativo")),
        criado_em=_now(),
        atualizado_em=_now(),
    )
    session.add(turma)
    session.commit()
    session.refresh(turma)
    return turma


@router.get("/turmas/{turma_id}/participantes")
def listar_participantes(
    turma_id: int,
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
) -> List[Dict[str, Any]]:
    turma = session.get(ScfvTurma, turma_id)
    if not turma:
        raise HTTPException(status_code=404, detail="Turma não encontrada.")
    _check_municipio(usuario, int(turma.municipio_id))

    parts = session.exec(
        select(ScfvParticipante).where(ScfvParticipante.turma_id == turma_id).order_by(ScfvParticipante.id.desc())
    ).all()

    pessoa_ids = [p.pessoa_id for p in parts]
    pessoas = {}
    if pessoa_ids:
        for pe in session.exec(select(PessoaSUAS).where(PessoaSUAS.id.in_(pessoa_ids))).all():
            pessoas[pe.id] = pe

    out = []
    for pt in parts:
        out.append({
            "id": pt.id,
            "turma_id": pt.turma_id,
            "pessoa_id": pt.pessoa_id,
            "caso_id": pt.caso_id,
            "status": pt.status,
            "data_inicio": pt.data_inicio,
            "data_fim": pt.data_fim,
            "pessoa": (pessoas.get(pt.pessoa_id).dict() if pessoas.get(pt.pessoa_id) else None),
        })
    return out


@router.post("/turmas/{turma_id}/inscrever")
def inscrever(
    turma_id: int,
    payload: Dict[str, Any],
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
) -> Dict[str, Any]:
    turma = session.get(ScfvTurma, turma_id)
    if not turma:
        raise HTTPException(status_code=404, detail="Turma não encontrada.")
    _check_municipio(usuario, int(turma.municipio_id))

    pessoa_id = payload.get("pessoa_id")
    if not pessoa_id:
        raise HTTPException(status_code=400, detail="pessoa_id é obrigatório.")

    pessoa = session.get(PessoaSUAS, int(pessoa_id))
    if not pessoa:
        raise HTTPException(status_code=404, detail="Pessoa não encontrada.")
    _check_municipio(usuario, int(pessoa.municipio_id))

    existing = session.exec(
        select(ScfvParticipante).where(
            (ScfvParticipante.turma_id == turma_id)
            & (ScfvParticipante.pessoa_id == int(pessoa_id))
            & (ScfvParticipante.status == "ativo")
        )
    ).first()
    if existing:
        return {"ok": True, "participante_id": existing.id, "detail": "Já inscrito (ativo)."}

    if turma.vagas is not None:
        ativos = session.exec(
            select(ScfvParticipante).where((ScfvParticipante.turma_id == turma_id) & (ScfvParticipante.status == "ativo"))
        ).all()
        if len(ativos) >= int(turma.vagas):
            raise HTTPException(status_code=409, detail="Capacidade máxima atingida.")

    pt = ScfvParticipante(
        turma_id=int(turma_id),
        pessoa_id=int(pessoa_id),
        caso_id=payload.get("caso_id"),
        status="ativo",
        data_inicio=date.today(),
        criado_em=_now(),
        atualizado_em=_now(),
    )
    session.add(pt)
    session.commit()
    session.refresh(pt)
    return {"ok": True, "participante_id": pt.id}


@router.get("/presencas")
def listar_presencas(
    turma_id: int = Query(...),
    data: str = Query(...),
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
) -> List[Dict[str, Any]]:
    turma = session.get(ScfvTurma, int(turma_id))
    if not turma:
        raise HTTPException(status_code=404, detail="Turma não encontrada.")
    _check_municipio(usuario, int(turma.municipio_id))

    dt = date.fromisoformat(str(data))

    parts = session.exec(
        select(ScfvParticipante).where((ScfvParticipante.turma_id == int(turma_id)) & (ScfvParticipante.status == "ativo"))
    ).all()

    pessoa_ids = [p.pessoa_id for p in parts]
    pessoas = {}
    if pessoa_ids:
        for pe in session.exec(select(PessoaSUAS).where(PessoaSUAS.id.in_(pessoa_ids))).all():
            pessoas[pe.id] = pe

    pres = session.exec(
        select(ScfvPresenca)
        .where(ScfvPresenca.data == dt)
        .where(ScfvPresenca.participante_id.in_([p.id for p in parts]))
    ).all()
    pres_map = {x.participante_id: x for x in pres}

    out = []
    for pt in parts:
        px = pres_map.get(pt.id)
        out.append({
            "participante_id": pt.id,
            "pessoa_id": pt.pessoa_id,
            "pessoa": (pessoas.get(pt.pessoa_id).dict() if pessoas.get(pt.pessoa_id) else None),
            "data": dt.isoformat(),
            "presenca_id": px.id if px else None,
            "presente_bool": px.presente_bool if px else None,
            "observacao": px.observacao if px else None,
        })
    return out


@router.post("/presencas")
def upsert_presenca(
    payload: Dict[str, Any],
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
) -> ScfvPresenca:
    participante_id = payload.get("participante_id")
    data_str = payload.get("data")
    if not participante_id or not data_str:
        raise HTTPException(status_code=400, detail="participante_id e data são obrigatórios.")
    dt = date.fromisoformat(str(data_str))

    pt = session.get(ScfvParticipante, int(participante_id))
    if not pt:
        raise HTTPException(status_code=404, detail="Participante não encontrado.")

    turma = session.get(ScfvTurma, pt.turma_id)
    if not turma:
        raise HTTPException(status_code=404, detail="Turma não encontrada.")
    _check_municipio(usuario, int(turma.municipio_id))

    existing = session.exec(
        select(ScfvPresenca).where((ScfvPresenca.participante_id == int(participante_id)) & (ScfvPresenca.data == dt))
    ).first()

    if existing:
        existing.presente_bool = bool(payload.get("presente_bool"))
        existing.observacao = payload.get("observacao")
        existing.atualizado_em = _now()
        session.add(existing)
        session.commit()
        session.refresh(existing)
        return existing

    pres = ScfvPresenca(
        participante_id=int(participante_id),
        data=dt,
        presente_bool=bool(payload.get("presente_bool")),
        observacao=payload.get("observacao"),
        criado_em=_now(),
        atualizado_em=_now(),
    )
    session.add(pres)
    session.commit()
    session.refresh(pres)
    return pres


def _norm(s: str) -> str:
    import unicodedata
    s = (s or "").strip().lower()
    s = unicodedata.normalize("NFKD", s)
    s = "".join([c for c in s if not unicodedata.combining(c)])
    return s


def _parse_weekdays(dias_str: str):
    import re as _re
    s = _norm(dias_str)
    if not s:
        return []
    s = s.replace("feira", " ")
    s = s.replace("/", " ").replace(",", " ").replace(";", " ").replace("|", " ").replace("-", " ")
    s = s.replace("ª", "").replace("º", "")
    s = _re.sub(r"[^a-z0-9\s]", " ", s)
    toks = [x for x in _re.split(r"\s+", s) if x]

    mp = {
        "seg": 0, "segunda": 0, "2": 0, "2a": 0,
        "ter": 1, "terca": 1, "3": 1, "3a": 1,
        "qua": 2, "quarta": 2, "4": 2, "4a": 2,
        "qui": 3, "quinta": 3, "5": 3, "5a": 3,
        "sex": 4, "sexta": 4, "6": 4, "6a": 4,
        "sab": 5, "sabado": 5,
        "dom": 6, "domingo": 6, "1": 6,
    }
    out = []
    for tok in toks:
        tok = tok.strip(".")
        if tok in mp:
            out.append(mp[tok])
    return sorted(set(out))


@router.get("/relatorio/mensal")
def relatorio_mensal(
    turma_id: int = Query(...),
    ano: int = Query(..., ge=2000, le=2100),
    mes: int = Query(..., ge=1, le=12),
    limite_evasao: int = Query(3, ge=1, le=60),
    limite_presenca_min: float = Query(0.75, ge=0.0, le=1.0),
    usar_calendario_turma: bool = Query(True),
    considerar_nao_registrado_como_falta: bool = Query(True),
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
) -> Dict[str, Any]:
    import calendar
    from datetime import timedelta

    turma = session.get(ScfvTurma, int(turma_id))
    if not turma:
        raise HTTPException(status_code=404, detail="Turma não encontrada.")
    _check_municipio(usuario, int(turma.municipio_id))

    last_day = calendar.monthrange(int(ano), int(mes))[1]
    start = date(int(ano), int(mes), 1)
    end = date(int(ano), int(mes), last_day)

    parts = session.exec(
        select(ScfvParticipante).where((ScfvParticipante.turma_id == int(turma_id)) & (ScfvParticipante.status == "ativo"))
    ).all()

    part_ids = [p.id for p in parts]
    if not part_ids:
        return {
            "turma_id": int(turma_id),
            "turma_nome": turma.nome,
            "ano": int(ano),
            "mes": int(mes),
            "limite_evasao": int(limite_evasao),
            "limite_presenca_min": float(limite_presenca_min),
            "fonte_datas": "calendario" if usar_calendario_turma else "registros",
            "total_participantes": 0,
            "total_encontros": 0,
            "total_com_registro": 0,
            "total_sem_registro": 0,
            "datas_encontros": [],
            "datas_com_registro": [],
            "datas_sem_registro": [],
            "rows": [],
        }

    pessoa_ids = [p.pessoa_id for p in parts]
    pessoas = {}
    if pessoa_ids:
        for pe in session.exec(select(PessoaSUAS).where(PessoaSUAS.id.in_(pessoa_ids))).all():
            pessoas[pe.id] = pe

    pres = session.exec(
        select(ScfvPresenca)
        .where(ScfvPresenca.participante_id.in_(part_ids))
        .where(ScfvPresenca.data >= start)
        .where(ScfvPresenca.data <= end)
    ).all()

    datas_registro = sorted({x.data for x in pres})
    pmap = {(x.participante_id, x.data): x for x in pres}

    weekdays = _parse_weekdays(turma.dias or "")

    datas_encontros = []
    fonte = "registros"
    if usar_calendario_turma and weekdays:
        fonte = "calendario"
        d = start
        while d <= end:
            if d.weekday() in weekdays:
                datas_encontros.append(d)
            d += timedelta(days=1)
    else:
        datas_encontros = datas_registro[:]
        fonte = "registros"

    set_reg = set(datas_registro)
    datas_sem_registro = [d for d in datas_encontros if d not in set_reg]
    datas_com_registro = datas_registro[:]

    rows: List[Dict[str, Any]] = []

    for pt in parts:
        pessoa = pessoas.get(pt.pessoa_id)
        nome = (pessoa.nome_social or pessoa.nome) if pessoa else f"Pessoa #{pt.pessoa_id}"
        cpf = pessoa.cpf if pessoa else None
        nis = pessoa.nis if pessoa else None

        start_lim = max(start, pt.data_inicio) if pt.data_inicio else start
        end_lim = min(end, pt.data_fim) if pt.data_fim else end

        encontros_validos = [d for d in datas_encontros if start_lim <= d <= end_lim]

        matrix = {}

        presencas = 0
        faltas_exp = 0
        nao_reg = 0

        streak = 0
        streak_max = 0

        for d in encontros_validos:
            rec = pmap.get((pt.id, d))
            if rec is None:
                nao_reg += 1
                matrix[d.isoformat()] = "NR"
                if considerar_nao_registrado_como_falta:
                    streak += 1
                else:
                    streak = 0
                streak_max = max(streak_max, streak)
                continue

            if rec.presente_bool:
                presencas += 1
                matrix[d.isoformat()] = "P"
                streak = 0
            else:
                faltas_exp += 1
                matrix[d.isoformat()] = "F"
                streak += 1

            streak_max = max(streak_max, streak)

        faltas_total = faltas_exp + (nao_reg if considerar_nao_registrado_como_falta else 0)
        total = len(encontros_validos)
        taxa = (presencas / total) if total > 0 else None

        rows.append({
            "participante_id": pt.id,
            "pessoa_id": pt.pessoa_id,
            "nome": nome,
            "cpf": cpf,
            "nis": nis,
            "total_encontros": total,
            "presencas": presencas,
            "faltas_explicitas": faltas_exp,
            "nao_registrado": nao_reg,
            "faltas_total": faltas_total,
            "taxa_presenca": taxa,
            "faltas_seguidas_atual": streak,
            "faltas_seguidas_max": streak_max,
            "evasao_alerta": (streak_max >= int(limite_evasao)),
            "presenca_alerta": (taxa is not None and taxa < float(limite_presenca_min)),
            "matrix": matrix,
        })

    rows.sort(key=lambda r: (not (r["evasao_alerta"] or r["presenca_alerta"]), -(r["faltas_seguidas_max"] or 0), -(r["faltas_total"] or 0), r["nome"]))

    return {
        "turma_id": int(turma_id),
        "turma_nome": turma.nome,
        "ano": int(ano),
        "mes": int(mes),
        "limite_evasao": int(limite_evasao),
        "limite_presenca_min": float(limite_presenca_min),
        "fonte_datas": fonte,
        "total_participantes": len(parts),
        "total_encontros": len(datas_encontros),
        "total_com_registro": len(set_reg),
        "total_sem_registro": len(datas_sem_registro),
        "datas_encontros": [d.isoformat() for d in datas_encontros],
        "datas_com_registro": [d.isoformat() for d in datas_com_registro],
        "datas_sem_registro": [d.isoformat() for d in datas_sem_registro],
        "rows": rows,
    }



@router.get("/kpis/evasao")
def kpi_evasao(
    unidade_id: int = Query(...),
    ano: int = Query(..., ge=2000, le=2100),
    mes: int = Query(..., ge=1, le=12),
    limite_evasao: int = Query(3, ge=1, le=60),
    limite_presenca_min: float = Query(0.75, ge=0.0, le=1.0),
    usar_calendario_turma: bool = Query(True),
    considerar_nao_registrado_como_falta: bool = Query(True),
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
) -> Dict[str, Any]:
    import calendar
    from datetime import timedelta

    stmt = select(ScfvTurma).where(ScfvTurma.unidade_id == int(unidade_id)).where(ScfvTurma.ativo == True)
    if not pode_acesso_global(usuario):
        um = _mun_id(usuario)
        if um is None:
            raise HTTPException(status_code=403, detail="Usuário sem município.")
        stmt = stmt.where(ScfvTurma.municipio_id == um)

    turmas = session.exec(stmt.order_by(ScfvTurma.id.desc())).all()

    last_day = calendar.monthrange(int(ano), int(mes))[1]
    start = date(int(ano), int(mes), 1)
    end = date(int(ano), int(mes), last_day)

    total_alertas_evasao = 0
    total_alertas_baixa = 0
    dias_sem_registro_total = 0

    top = []

    for turma in turmas:
        parts = session.exec(
            select(ScfvParticipante).where((ScfvParticipante.turma_id == int(turma.id)) & (ScfvParticipante.status == "ativo"))
        ).all()
        part_ids = [p.id for p in parts]
        if not part_ids:
            continue

        pres = session.exec(
            select(ScfvPresenca)
            .where(ScfvPresenca.participante_id.in_(part_ids))
            .where(ScfvPresenca.data >= start)
            .where(ScfvPresenca.data <= end)
        ).all()

        datas_registro = sorted({x.data for x in pres})
        pmap = {(x.participante_id, x.data): x for x in pres}

        weekdays = _parse_weekdays(turma.dias or "")

        datas_encontros = []
        if usar_calendario_turma and weekdays:
            d = start
            while d <= end:
                if d.weekday() in weekdays:
                    datas_encontros.append(d)
                d += timedelta(days=1)
        else:
            datas_encontros = datas_registro[:]

        set_reg = set(datas_registro)
        dias_sem_reg = [d for d in datas_encontros if d not in set_reg]
        dias_sem_registro_total += len(dias_sem_reg)

        alertas_evasao_turma = 0
        alertas_baixa_turma = 0

        for pt in parts:
            # encontros válidos do participante
            start_lim = max(start, pt.data_inicio) if pt.data_inicio else start
            end_lim = min(end, pt.data_fim) if pt.data_fim else end
            encontros_validos = [d for d in datas_encontros if start_lim <= d <= end_lim]

            if not encontros_validos:
                continue

            # streak + taxa presença
            streak = 0
            streak_max = 0
            presencas = 0
            faltas_exp = 0
            nao_reg = 0

            for d in encontros_validos:
                rec = pmap.get((pt.id, d))
                if rec is None:
                    nao_reg += 1
                    if considerar_nao_registrado_como_falta:
                        streak += 1
                    else:
                        streak = 0
                    streak_max = max(streak_max, streak)
                    continue

                if rec.presente_bool:
                    presencas += 1
                    streak = 0
                else:
                    faltas_exp += 1
                    streak += 1

                streak_max = max(streak_max, streak)

            total = len(encontros_validos)
            taxa = presencas / total if total > 0 else None

            if streak_max >= int(limite_evasao):
                alertas_evasao_turma += 1

            if taxa is not None and taxa < float(limite_presenca_min):
                alertas_baixa_turma += 1

        if alertas_evasao_turma or alertas_baixa_turma or len(dias_sem_reg):
            total_alertas_evasao += alertas_evasao_turma
            total_alertas_baixa += alertas_baixa_turma

            top.append({
                "turma_id": turma.id,
                "turma_nome": turma.nome,
                "alertas_evasao": alertas_evasao_turma,
                "alertas_baixa_presenca": alertas_baixa_turma,
                "dias_sem_registro": len(dias_sem_reg),
                "total_encontros": len(datas_encontros),
            })

    # ordena: mais evasão, depois baixa presença, depois dias sem registro
    top.sort(key=lambda x: (
        -(x["alertas_evasao"] or 0),
        -(x["alertas_baixa_presenca"] or 0),
        -(x["dias_sem_registro"] or 0),
        x["turma_nome"]
    ))

    return {
        "unidade_id": int(unidade_id),
        "ano": int(ano),
        "mes": int(mes),
        "limite_evasao": int(limite_evasao),
        "limite_presenca_min": float(limite_presenca_min),
        "total_alertas_evasao": total_alertas_evasao,
        "total_alertas_baixa_presenca": total_alertas_baixa,
        "dias_sem_registro_total": dias_sem_registro_total,
        "total_alertas": (total_alertas_evasao + total_alertas_baixa),  # compatível com o front antigo
        "turmas_com_alerta": len([x for x in top if (x["alertas_evasao"] or x["alertas_baixa_presenca"] or x["dias_sem_registro"])]),
        "top_turmas": top[:10],
    }
