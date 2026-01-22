from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select

from app.core.db import get_session
from app.core.auth import get_current_user, pode_acesso_global
from app.models.usuario import Usuario
from app.models.cras_unidade import CrasUnidade

from app.models.pessoa_suas import PessoaSUAS
from app.models.familia_suas import FamiliaSUAS
from app.models.caso_cras import CasoCras, CasoCrasHistorico

router = APIRouter(prefix="/cras", tags=["cras-casos"])

METRO_ETAPAS = [
    {"codigo": "TRIAGEM", "nome": "Recepção e Triagem", "sla_dias": 2},
    {"codigo": "DIAGNOSTICO", "nome": "Avaliação e Diagnóstico", "sla_dias": 15},
    {"codigo": "PIA", "nome": "Elaboração do PIA/PAIF", "sla_dias": 15},
    {"codigo": "EXECUCAO", "nome": "Execução das ações", "sla_dias": 30},
    {"codigo": "MONITORAMENTO", "nome": "Monitoramento", "sla_dias": 30},
]

SLA_DEFAULT = {e["codigo"]: int(e["sla_dias"]) for e in METRO_ETAPAS}


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


def _sla_dias(caso: CasoCras) -> int:
    if caso.prazo_etapa_dias is not None:
        return int(caso.prazo_etapa_dias)
    return int(SLA_DEFAULT.get(caso.etapa_atual or "TRIAGEM", 7))


def _calc_flags(caso: CasoCras) -> Dict[str, Any]:
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
    caso: CasoCras,
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
        "tecnico_responsavel_id": caso.tecnico_responsavel_id,
        "data_abertura": caso.data_abertura,
        "data_encerramento": caso.data_encerramento,
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




def _case_dict(session: Session, caso: CasoCras) -> Dict[str, Any]:
    # Hidrata dados do caso para preencher o 'display' em qualquer endpoint
    pessoa = session.get(PessoaSUAS, caso.pessoa_id) if caso.pessoa_id else None
    familia = session.get(FamiliaSUAS, caso.familia_id) if caso.familia_id else None
    refp = session.get(PessoaSUAS, familia.referencia_pessoa_id) if (familia and familia.referencia_pessoa_id) else None
    return _case_to_dict(caso, pessoa=pessoa, familia=familia, ref_pessoa=refp)

@router.get("/linha-metro/etapas")
def listar_etapas_metro() -> List[Dict[str, Any]]:
    return METRO_ETAPAS


@router.get("/casos")
def listar_casos(
    status: Optional[str] = Query(default=None),
    etapa: Optional[str] = Query(default=None),
    unidade_id: Optional[int] = Query(default=None),
    q: Optional[str] = Query(default=None),
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
) -> List[Dict[str, Any]]:
    stmt = select(CasoCras).order_by(CasoCras.id.desc())

    if not pode_acesso_global(usuario):
        um = _mun_id(usuario)
        if um is None:
            raise HTTPException(status_code=403, detail="Usuário sem município.")
        stmt = stmt.where(CasoCras.municipio_id == um)

    if status:
        stmt = stmt.where(CasoCras.status == status)
    if etapa:
        stmt = stmt.where(CasoCras.etapa_atual == etapa)
    if unidade_id:
        stmt = stmt.where(CasoCras.unidade_id == unidade_id)

    casos = session.exec(stmt).all()

    # carrega dados relacionados em batch
    pessoa_ids = [c.pessoa_id for c in casos if c.pessoa_id]
    familia_ids = [c.familia_id for c in casos if c.familia_id]

    pessoas = {}
    if pessoa_ids:
        for p in session.exec(select(PessoaSUAS).where(PessoaSUAS.id.in_(pessoa_ids))).all():
            pessoas[p.id] = p

    familias = {}
    ref_ids = []
    if familia_ids:
        for f in session.exec(select(FamiliaSUAS).where(FamiliaSUAS.id.in_(familia_ids))).all():
            familias[f.id] = f
            if f.referencia_pessoa_id:
                ref_ids.append(f.referencia_pessoa_id)

    ref_pessoas = {}
    if ref_ids:
        for p in session.exec(select(PessoaSUAS).where(PessoaSUAS.id.in_(ref_ids))).all():
            ref_pessoas[p.id] = p

    out = []
    qn = (q or "").strip().lower()
    for c in casos:
        pessoa = pessoas.get(c.pessoa_id) if c.pessoa_id else None
        familia = familias.get(c.familia_id) if c.familia_id else None
        refp = ref_pessoas.get(getattr(familia, "referencia_pessoa_id", None)) if familia else None

        item = _case_to_dict(c, pessoa=pessoa, familia=familia, ref_pessoa=refp)

        if qn:
            hay = " ".join(
                [
                    (item.get("display") or {}).get("nome") or "",
                    (item.get("display") or {}).get("cpf") or "",
                    (item.get("display") or {}).get("nis") or "",
                    (item.get("display") or {}).get("bairro") or "",
                    (item.get("display") or {}).get("territorio") or "",
                ]
            ).lower()
            if qn not in hay:
                continue

        out.append(item)

    return out


@router.post("/casos")
def criar_caso(
    payload: Dict[str, Any],
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
) -> Dict[str, Any]:
    unidade_id = payload.get("unidade_id")
    if not unidade_id:
        raise HTTPException(status_code=400, detail="unidade_id é obrigatório.")

    unidade = session.get(CrasUnidade, int(unidade_id))
    if not unidade:
        raise HTTPException(status_code=404, detail="Unidade CRAS não encontrada.")

    tipo_caso = (payload.get("tipo_caso") or "familia").strip()
    if tipo_caso not in ("familia", "individuo"):
        raise HTTPException(status_code=400, detail="tipo_caso inválido (familia|individuo).")

    # municipio_id
    municipio_id = payload.get("municipio_id") or getattr(unidade, "municipio_id", None)
    if municipio_id is None:
        raise HTTPException(status_code=400, detail="municipio_id não encontrado.")
    _check_municipio(usuario, int(municipio_id))

    pessoa_id = payload.get("pessoa_id")
    familia_id = payload.get("familia_id")

    if tipo_caso == "individuo" and not pessoa_id:
        raise HTTPException(status_code=400, detail="pessoa_id é obrigatório para caso individuo.")
    if tipo_caso == "familia" and not familia_id:
        raise HTTPException(status_code=400, detail="familia_id é obrigatório para caso familia.")

    etapa = "TRIAGEM"
    caso = CasoCras(
        municipio_id=int(municipio_id),
        unidade_id=int(unidade_id),
        tipo_caso=tipo_caso,
        pessoa_id=int(pessoa_id) if pessoa_id else None,
        familia_id=int(familia_id) if familia_id else None,
        status="em_andamento",
        etapa_atual=etapa,
        prioridade=payload.get("prioridade") or "media",
        tecnico_responsavel_id=payload.get("tecnico_responsavel_id"),
        observacoes_iniciais=payload.get("observacoes_iniciais"),
        data_inicio_etapa_atual=_now(),
        prazo_etapa_dias=SLA_DEFAULT.get(etapa, 7),
        atualizado_em=_now(),
    )
    session.add(caso)
    session.commit()
    session.refresh(caso)

    session.add(
        CasoCrasHistorico(
            caso_id=caso.id,
            etapa=caso.etapa_atual,
            tipo_acao="abertura",
            usuario_id=getattr(usuario, "id", None),
            usuario_nome=_usuario_nome(usuario),
            observacoes=payload.get("observacoes_iniciais"),
            criado_em=_now(),
        )
    )
    session.commit()

    return _case_dict(session, caso)


@router.get("/casos/{caso_id}")
def obter_caso(
    caso_id: int,
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
) -> Dict[str, Any]:
    caso = session.get(CasoCras, caso_id)
    if not caso:
        raise HTTPException(status_code=404, detail="Caso não encontrado.")
    _check_municipio(usuario, caso.municipio_id)

    pessoa = session.get(PessoaSUAS, caso.pessoa_id) if caso.pessoa_id else None
    familia = session.get(FamiliaSUAS, caso.familia_id) if caso.familia_id else None
    refp = session.get(PessoaSUAS, familia.referencia_pessoa_id) if (familia and familia.referencia_pessoa_id) else None

    return _case_to_dict(caso, pessoa=pessoa, familia=familia, ref_pessoa=refp)


@router.post("/casos/{caso_id}/avancar-etapa")
def avancar_etapa(
    caso_id: int,
    payload: Dict[str, Any],
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
) -> Dict[str, Any]:
    caso = session.get(CasoCras, caso_id)
    if not caso:
        raise HTTPException(status_code=404, detail="Caso não encontrado.")
    _check_municipio(usuario, caso.municipio_id)

    if caso.status == "encerrado":
        return _case_dict(session, caso)

    etapa_destino = (payload.get("etapa_destino") or "").strip().upper()
    if not etapa_destino:
        raise HTTPException(status_code=400, detail="etapa_destino é obrigatório.")
    if etapa_destino not in SLA_DEFAULT:
        raise HTTPException(status_code=400, detail=f"etapa_destino inválida: {etapa_destino}")

    caso.etapa_atual = etapa_destino
    caso.data_inicio_etapa_atual = _now()
    caso.prazo_etapa_dias = SLA_DEFAULT.get(etapa_destino, 7)

    # zera estagnação ao avançar
    caso.estagnado = False
    caso.motivo_estagnacao = None

    # exige validação na etapa seguinte
    caso.aguardando_validacao = True
    caso.pendente_validacao_desde = _now()

    caso.atualizado_em = _now()

    session.add(caso)
    session.add(
        CasoCrasHistorico(
            caso_id=caso.id,
            etapa=etapa_destino,
            tipo_acao="avanco",
            usuario_id=getattr(usuario, "id", None),
            usuario_nome=_usuario_nome(usuario),
            observacoes=payload.get("observacoes"),
            criado_em=_now(),
        )
    )
    session.commit()
    session.refresh(caso)

    return _case_dict(session, caso)


@router.post("/casos/{caso_id}/validar-recebimento")
def validar_recebimento(
    caso_id: int,
    payload: Dict[str, Any],
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
) -> Dict[str, Any]:
    caso = session.get(CasoCras, caso_id)
    if not caso:
        raise HTTPException(status_code=404, detail="Caso não encontrado.")
    _check_municipio(usuario, caso.municipio_id)

    caso.aguardando_validacao = False
    caso.pendente_validacao_desde = None
    caso.atualizado_em = _now()

    session.add(caso)
    session.add(
        CasoCrasHistorico(
            caso_id=caso.id,
            etapa=caso.etapa_atual,
            tipo_acao="validacao",
            usuario_id=getattr(usuario, "id", None),
            usuario_nome=_usuario_nome(usuario),
            observacoes=payload.get("observacoes"),
            criado_em=_now(),
        )
    )
    session.commit()
    session.refresh(caso)

    return _case_dict(session, caso)


@router.post("/casos/{caso_id}/estagnar")
def estagnar(
    caso_id: int,
    payload: Dict[str, Any],
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
) -> Dict[str, Any]:
    caso = session.get(CasoCras, caso_id)
    if not caso:
        raise HTTPException(status_code=404, detail="Caso não encontrado.")
    _check_municipio(usuario, caso.municipio_id)

    motivo = (payload.get("motivo_estagnacao") or "").strip()
    if not motivo:
        raise HTTPException(status_code=400, detail="motivo_estagnacao é obrigatório.")

    caso.estagnado = True
    caso.motivo_estagnacao = motivo
    caso.atualizado_em = _now()

    session.add(caso)
    session.add(
        CasoCrasHistorico(
            caso_id=caso.id,
            etapa=caso.etapa_atual,
            tipo_acao="estagnacao",
            usuario_id=getattr(usuario, "id", None),
            usuario_nome=_usuario_nome(usuario),
            observacoes=payload.get("observacoes"),
            motivo_estagnacao=motivo,
            criado_em=_now(),
        )
    )
    session.commit()
    session.refresh(caso)

    return _case_dict(session, caso)


@router.post("/casos/{caso_id}/encerrar")
def encerrar(
    caso_id: int,
    payload: Dict[str, Any],
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
) -> Dict[str, Any]:
    caso = session.get(CasoCras, caso_id)
    if not caso:
        raise HTTPException(status_code=404, detail="Caso não encontrado.")
    _check_municipio(usuario, caso.municipio_id)

    caso.status = "encerrado"
    caso.data_encerramento = _now()
    caso.aguardando_validacao = False
    caso.pendente_validacao_desde = None
    caso.atualizado_em = _now()

    session.add(caso)
    session.add(
        CasoCrasHistorico(
            caso_id=caso.id,
            etapa=caso.etapa_atual,
            tipo_acao="encerramento",
            usuario_id=getattr(usuario, "id", None),
            usuario_nome=_usuario_nome(usuario),
            observacoes=payload.get("observacoes"),
            criado_em=_now(),
        )
    )
    session.commit()
    session.refresh(caso)

    return _case_dict(session, caso)


@router.get("/casos/{caso_id}/historico")
def historico(
    caso_id: int,
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
) -> List[Dict[str, Any]]:
    caso = session.get(CasoCras, caso_id)
    if not caso:
        raise HTTPException(status_code=404, detail="Caso não encontrado.")
    _check_municipio(usuario, caso.municipio_id)

    items = session.exec(
        select(CasoCrasHistorico)
        .where(CasoCrasHistorico.caso_id == caso_id)
        .order_by(CasoCrasHistorico.id.asc())
    ).all()

    out = []
    for it in items:
        out.append(
            {
                "id": it.id,
                "caso_id": it.caso_id,
                "etapa": it.etapa,
                "tipo_acao": it.tipo_acao,
                "usuario_id": it.usuario_id,
                "usuario_nome": it.usuario_nome,
                "observacoes": it.observacoes,
                "motivo_estagnacao": it.motivo_estagnacao,
                "criado_em": it.criado_em,
            }
        )
    return out
