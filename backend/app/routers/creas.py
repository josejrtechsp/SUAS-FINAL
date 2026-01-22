from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session, select

from app.core.db import get_session
from app.core.auth import get_current_user, pode_acesso_global
from app.models.usuario import Usuario

from app.models.creas_unidade import CreasUnidade
from app.models.creas_caso import CreasCaso, CreasCasoHistorico

from app.models.pessoa_suas import PessoaSUAS
from app.models.familia_suas import FamiliaSUAS

router = APIRouter(prefix="/creas", tags=["creas"])

# Etapas (alinhado com o front)
CREAS_ETAPAS = [
    {"codigo": "entrada", "nome": "Entrada", "sla_dias": 2},
    {"codigo": "triagem", "nome": "Triagem e classificação", "sla_dias": 2},
    {"codigo": "acolhimento", "nome": "Acolhimento inicial", "sla_dias": 7},
    {"codigo": "diagnostico", "nome": "Diagnóstico/estudo do caso", "sla_dias": 14},
    {"codigo": "plano", "nome": "Plano ativo", "sla_dias": 30},
    {"codigo": "acompanhamento", "nome": "Acompanhamento", "sla_dias": 30},
    {"codigo": "rede", "nome": "Articulação de rede", "sla_dias": 15},
    {"codigo": "reavaliacao", "nome": "Reavaliação", "sla_dias": 30},
    {"codigo": "encerramento", "nome": "Encerramento", "sla_dias": 7},
    {"codigo": "pos", "nome": "Pós-encerramento", "sla_dias": 30},
]
SLA_DEFAULT = {e["codigo"]: int(e["sla_dias"]) for e in CREAS_ETAPAS}


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


def _usuario_nome(usuario: Usuario) -> str:
    return getattr(usuario, "nome", None) or "Usuário"


def _sla_dias(caso: CreasCaso) -> int:
    if caso.prazo_etapa_dias is not None:
        return int(caso.prazo_etapa_dias)
    etapa = (caso.etapa_atual or "entrada").strip().lower()
    return int(SLA_DEFAULT.get(etapa, 7))


def _calc_flags(caso: CreasCaso) -> Dict[str, Any]:
    now = _now()
    dias = 0
    if caso.data_inicio_etapa_atual:
        dias = max(0, (now - caso.data_inicio_etapa_atual).days)

    sla = _sla_dias(caso)
    risco = dias >= max(1, int(sla * 0.8))
    estourado = dias > sla

    valid_pendente = bool(caso.aguardando_validacao)
    valid_estourada = False
    if valid_pendente and caso.pendente_validacao_desde:
        valid_estourada = (now - caso.pendente_validacao_desde).total_seconds() > (48 * 3600)

    cor = "verde"
    if caso.estagnado or estourado or valid_estourada:
        cor = "vermelho"
    elif risco or valid_pendente:
        cor = "laranja"

    return {
        "dias_na_etapa": dias,
        "sla_dias": sla,
        "sla_em_risco": risco,
        "sla_estourado": estourado,
        "validacao_pendente": valid_pendente,
        "validacao_estourada": valid_estourada,
        "cor": cor,
    }


def _case_to_dict(
    caso: CreasCaso,
    pessoa: Optional[PessoaSUAS] = None,
    familia: Optional[FamiliaSUAS] = None,
    ref_pessoa: Optional[PessoaSUAS] = None,
) -> Dict[str, Any]:
    flags = _calc_flags(caso)

    nome = None
    cpf = None
    nis = None
    bairro = None
    territorio = None

    if caso.tipo_caso == "individuo" and pessoa:
        nome = pessoa.nome_social or pessoa.nome
        cpf = pessoa.cpf
        nis = pessoa.nis
        bairro = pessoa.bairro
        territorio = pessoa.territorio

    if caso.tipo_caso == "familia" and familia:
        bairro = familia.bairro
        territorio = familia.territorio
        if ref_pessoa:
            nome = ref_pessoa.nome_social or ref_pessoa.nome
            cpf = ref_pessoa.cpf
            nis = ref_pessoa.nis

    return {
        "id": caso.id,
        "municipio_id": caso.municipio_id,
        "unidade_id": caso.unidade_id,
        "tipo_caso": caso.tipo_caso,
        "pessoa_id": caso.pessoa_id,
        "familia_id": caso.familia_id,
        "status": caso.status,
        "etapa_atual": caso.etapa_atual,
        "prioridade": caso.prioridade,
        "risco": caso.risco,
        "tecnico_responsavel_id": caso.tecnico_responsavel_id,
        "titulo": caso.titulo,
        "tipologia": caso.tipologia,
        "data_abertura": caso.data_abertura,
        "data_encerramento": caso.data_encerramento,
        "motivo_encerramento": caso.motivo_encerramento,
        "estagnado": caso.estagnado,
        "motivo_estagnacao": caso.motivo_estagnacao,
        "aguardando_validacao": caso.aguardando_validacao,
        "pendente_validacao_desde": caso.pendente_validacao_desde,
        "display": {
            "nome": nome,
            "cpf": cpf,
            "nis": nis,
            "bairro": bairro,
            "territorio": territorio,
        },
        **flags,
    }


def _case_dict(session: Session, caso: CreasCaso) -> Dict[str, Any]:
    pessoa = session.get(PessoaSUAS, caso.pessoa_id) if caso.pessoa_id else None
    familia = session.get(FamiliaSUAS, caso.familia_id) if caso.familia_id else None
    refp = session.get(PessoaSUAS, familia.referencia_pessoa_id) if (familia and familia.referencia_pessoa_id) else None
    return _case_to_dict(caso, pessoa=pessoa, familia=familia, ref_pessoa=refp)


@router.get("/linha-metro/etapas")
def listar_etapas_metro() -> List[Dict[str, Any]]:
    return CREAS_ETAPAS


@router.get("/unidades")
def listar_unidades(
    municipio_id: Optional[int] = Query(default=None),
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
) -> List[CreasUnidade]:
    # força município do usuário quando não for acesso global
    if not pode_acesso_global(usuario):
        municipio_id = _mun_id(usuario)

    stmt = select(CreasUnidade).where(CreasUnidade.ativo == True)  # type: ignore
    if municipio_id is not None:
        stmt = stmt.where(CreasUnidade.municipio_id == int(municipio_id))
    stmt = stmt.order_by(CreasUnidade.nome)
    return list(session.exec(stmt).all())


@router.post("/unidades", status_code=status.HTTP_201_CREATED)
def criar_unidade(
    payload: Dict[str, Any],
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
) -> CreasUnidade:
    nome = (payload.get("nome") or "").strip()
    if not nome:
        raise HTTPException(status_code=400, detail="nome é obrigatório")

    municipio_id = payload.get("municipio_id")
    if not pode_acesso_global(usuario):
        municipio_id = _mun_id(usuario)

    if municipio_id is None:
        raise HTTPException(status_code=400, detail="municipio_id é obrigatório")

    _check_municipio(usuario, int(municipio_id))

    u = CreasUnidade(municipio_id=int(municipio_id), nome=nome, ativo=True)
    session.add(u)
    session.commit()
    session.refresh(u)
    return u


@router.get("/casos")
def listar_casos(
    status: Optional[str] = Query(default=None),
    etapa: Optional[str] = Query(default=None),
    unidade_id: Optional[int] = Query(default=None),
    q: Optional[str] = Query(default=None),
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
) -> List[Dict[str, Any]]:
    stmt = select(CreasCaso).order_by(CreasCaso.id.desc())

    if not pode_acesso_global(usuario):
        um = _mun_id(usuario)
        if um is None:
            raise HTTPException(status_code=403, detail="Usuário sem município.")
        stmt = stmt.where(CreasCaso.municipio_id == um)

    if status:
        stmt = stmt.where(CreasCaso.status == status)
    if etapa:
        stmt = stmt.where(CreasCaso.etapa_atual == etapa)
    if unidade_id:
        stmt = stmt.where(CreasCaso.unidade_id == unidade_id)

    casos = session.exec(stmt).all()

    pessoa_ids = [c.pessoa_id for c in casos if c.pessoa_id]
    familia_ids = [c.familia_id for c in casos if c.familia_id]

    pessoas: Dict[int, PessoaSUAS] = {}
    if pessoa_ids:
        for p in session.exec(select(PessoaSUAS).where(PessoaSUAS.id.in_(pessoa_ids))).all():
            pessoas[int(p.id)] = p

    familias: Dict[int, FamiliaSUAS] = {}
    ref_ids: List[int] = []
    if familia_ids:
        for f in session.exec(select(FamiliaSUAS).where(FamiliaSUAS.id.in_(familia_ids))).all():
            familias[int(f.id)] = f
            if f.referencia_pessoa_id:
                ref_ids.append(int(f.referencia_pessoa_id))

    ref_pessoas: Dict[int, PessoaSUAS] = {}
    if ref_ids:
        for p in session.exec(select(PessoaSUAS).where(PessoaSUAS.id.in_(ref_ids))).all():
            ref_pessoas[int(p.id)] = p

    qn = (q or "").strip().lower()
    out: List[Dict[str, Any]] = []
    for c in casos:
        pessoa = pessoas.get(int(c.pessoa_id)) if c.pessoa_id else None
        familia = familias.get(int(c.familia_id)) if c.familia_id else None
        refp = ref_pessoas.get(int(getattr(familia, "referencia_pessoa_id", 0))) if familia and getattr(familia, "referencia_pessoa_id", None) else None

        item = _case_to_dict(c, pessoa=pessoa, familia=familia, ref_pessoa=refp)

        if qn:
            disp = item.get("display") or {}
            hay = " ".join([
                str(disp.get("nome") or ""),
                str(disp.get("cpf") or ""),
                str(disp.get("nis") or ""),
                str(disp.get("bairro") or ""),
                str(disp.get("territorio") or ""),
                str(item.get("titulo") or ""),
                str(item.get("tipologia") or ""),
            ]).lower()
            if qn not in hay:
                continue

        out.append(item)

    return out


@router.post("/casos", status_code=status.HTTP_201_CREATED)
def criar_caso(
    payload: Dict[str, Any],
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
) -> Dict[str, Any]:
    unidade_id = payload.get("unidade_id")
    if not unidade_id:
        raise HTTPException(status_code=400, detail="unidade_id é obrigatório.")

    unidade = session.get(CreasUnidade, int(unidade_id))
    if not unidade:
        raise HTTPException(status_code=404, detail="Unidade CREAS não encontrada.")

    tipo_caso = (payload.get("tipo_caso") or "familia").strip().lower()
    if tipo_caso not in ("familia", "individuo"):
        raise HTTPException(status_code=400, detail="tipo_caso inválido (familia|individuo).")

    municipio_id = payload.get("municipio_id") or getattr(unidade, "municipio_id", None)
    if municipio_id is None:
        raise HTTPException(status_code=400, detail="municipio_id não encontrado.")
    _check_municipio(usuario, int(municipio_id))

    pessoa_id = payload.get("pessoa_id")
    familia_id = payload.get("familia_id")

    if tipo_caso == "individuo" and not pessoa_id:
        raise HTTPException(status_code=400, detail="pessoa_id é obrigatório para tipo_caso=individuo.")
    if tipo_caso == "familia" and not familia_id:
        raise HTTPException(status_code=400, detail="familia_id é obrigatório para tipo_caso=familia.")

    prioridade = (payload.get("prioridade") or "media").strip().lower()
    if prioridade not in ("baixa", "media", "alta"):
        prioridade = "media"

    risco = (payload.get("risco") or "medio").strip().lower()
    if risco not in ("baixo", "medio", "alto"):
        risco = "medio"

    titulo = (payload.get("titulo") or payload.get("nome") or "").strip() or None
    tipologia = (payload.get("tipologia") or "").strip() or None

    caso = CreasCaso(
        municipio_id=int(municipio_id),
        unidade_id=int(unidade_id),
        tipo_caso=tipo_caso,
        pessoa_id=int(pessoa_id) if pessoa_id else None,
        familia_id=int(familia_id) if familia_id else None,
        status="em_andamento",
        etapa_atual=(payload.get("etapa_atual") or "entrada").strip().lower() or "entrada",
        prioridade=prioridade,
        risco=risco,
        tecnico_responsavel_id=payload.get("tecnico_responsavel_id") or getattr(usuario, "id", None),
        titulo=titulo,
        tipologia=tipologia,
        observacoes_iniciais=payload.get("observacoes_iniciais"),
        observacoes_gerais=payload.get("observacoes_gerais"),
        data_abertura=_now(),
        data_inicio_etapa_atual=_now(),
        prazo_etapa_dias=payload.get("prazo_etapa_dias") or SLA_DEFAULT.get((payload.get("etapa_atual") or "entrada").strip().lower(), 7),
        atualizado_em=_now(),
    )

    session.add(caso)
    session.commit()
    session.refresh(caso)

    hist = CreasCasoHistorico(
        caso_id=int(caso.id),
        etapa=caso.etapa_atual,
        tipo_acao="abertura",
        usuario_id=getattr(usuario, "id", None),
        usuario_nome=_usuario_nome(usuario),
        observacoes=payload.get("observacoes_iniciais") or None,
        criado_em=_now(),
    )
    session.add(hist)
    session.commit()

    return _case_dict(session, caso)


@router.get("/casos/{caso_id}")
def obter_caso(
    caso_id: int,
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
) -> Dict[str, Any]:
    caso = session.get(CreasCaso, caso_id)
    if not caso:
        raise HTTPException(status_code=404, detail="Caso CREAS não encontrado.")

    _check_municipio(usuario, int(caso.municipio_id))
    return _case_dict(session, caso)


@router.patch("/casos/{caso_id}")
def atualizar_caso(
    caso_id: int,
    payload: Dict[str, Any],
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
) -> Dict[str, Any]:
    caso = session.get(CreasCaso, caso_id)
    if not caso:
        raise HTTPException(status_code=404, detail="Caso CREAS não encontrado.")
    _check_municipio(usuario, int(caso.municipio_id))

    # Campos permitidos (MVP)
    for field in [
        "prioridade",
        "risco",
        "titulo",
        "tipologia",
        "observacoes_gerais",
        "tecnico_responsavel_id",
        "estagnado",
        "motivo_estagnacao",
    ]:
        if field in payload:
            setattr(caso, field, payload.get(field))

    caso.atualizado_em = _now()
    session.add(caso)
    session.commit()
    session.refresh(caso)

    hist = CreasCasoHistorico(
        caso_id=int(caso.id),
        etapa=caso.etapa_atual,
        tipo_acao="edicao",
        usuario_id=getattr(usuario, "id", None),
        usuario_nome=_usuario_nome(usuario),
        observacoes=(payload.get("observacoes") or payload.get("observacoes_gerais") or None),
        motivo_estagnacao=payload.get("motivo_estagnacao") or None,
        criado_em=_now(),
    )
    session.add(hist)
    session.commit()

    return _case_dict(session, caso)


@router.post("/casos/{caso_id}/avancar")
def avancar_etapa(
    caso_id: int,
    payload: Dict[str, Any],
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
) -> Dict[str, Any]:
    caso = session.get(CreasCaso, caso_id)
    if not caso:
        raise HTTPException(status_code=404, detail="Caso CREAS não encontrado.")
    _check_municipio(usuario, int(caso.municipio_id))

    etapa = (payload.get("etapa") or "").strip().lower()
    if not etapa:
        raise HTTPException(status_code=400, detail="etapa é obrigatória")

    if etapa not in SLA_DEFAULT:
        raise HTTPException(status_code=400, detail="etapa inválida")

    caso.etapa_atual = etapa
    caso.data_inicio_etapa_atual = _now()
    caso.prazo_etapa_dias = int(payload.get("prazo_etapa_dias") or SLA_DEFAULT.get(etapa, 7))

    # reset estagnação ao avançar
    caso.estagnado = False
    caso.motivo_estagnacao = None
    caso.atualizado_em = _now()

    session.add(caso)
    session.commit()
    session.refresh(caso)

    hist = CreasCasoHistorico(
        caso_id=int(caso.id),
        etapa=caso.etapa_atual,
        tipo_acao="avanco",
        usuario_id=getattr(usuario, "id", None),
        usuario_nome=_usuario_nome(usuario),
        observacoes=payload.get("observacoes") or None,
        criado_em=_now(),
    )
    session.add(hist)
    session.commit()

    return _case_dict(session, caso)


@router.post("/casos/{caso_id}/encerrar")
def encerrar_caso(
    caso_id: int,
    payload: Dict[str, Any],
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
) -> Dict[str, Any]:
    caso = session.get(CreasCaso, caso_id)
    if not caso:
        raise HTTPException(status_code=404, detail="Caso CREAS não encontrado.")
    _check_municipio(usuario, int(caso.municipio_id))

    motivo = (payload.get("motivo") or payload.get("motivo_encerramento") or "").strip() or None

    caso.status = "encerrado"
    caso.data_encerramento = _now()
    caso.motivo_encerramento = motivo
    caso.etapa_atual = "encerramento"
    caso.data_inicio_etapa_atual = _now()
    caso.prazo_etapa_dias = int(SLA_DEFAULT.get("encerramento", 7))
    caso.atualizado_em = _now()

    session.add(caso)
    session.commit()
    session.refresh(caso)

    hist = CreasCasoHistorico(
        caso_id=int(caso.id),
        etapa="encerramento",
        tipo_acao="encerramento",
        usuario_id=getattr(usuario, "id", None),
        usuario_nome=_usuario_nome(usuario),
        observacoes=payload.get("resumo") or motivo or None,
        criado_em=_now(),
    )
    session.add(hist)
    session.commit()

    return _case_dict(session, caso)


@router.get("/relatorios/overview")
def overview(
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
) -> Dict[str, Any]:
    stmt = select(CreasCaso)
    if not pode_acesso_global(usuario):
        um = _mun_id(usuario)
        if um is None:
            raise HTTPException(status_code=403, detail="Usuário sem município.")
        stmt = stmt.where(CreasCaso.municipio_id == um)

    total = 0
    ativos = 0
    encerrados = 0
    atrasos = 0
    now = _now()

    for c in session.exec(stmt).all():
        total += 1
        if c.status == "em_andamento":
            ativos += 1
        else:
            encerrados += 1
        # atraso
        due = c.data_inicio_etapa_atual + timedelta(days=_sla_dias(c)) if c.data_inicio_etapa_atual else None
        if c.status == "em_andamento" and due and now > due:
            atrasos += 1

    return {"total": total, "ativos": ativos, "encerrados": encerrados, "atrasos": atrasos}
