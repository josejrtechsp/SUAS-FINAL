from __future__ import annotations

from datetime import date, datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import SQLModel, Session, select

from app.core.auth import exigir_minimo_perfil, get_current_user, pode_acesso_global
from app.core.db import get_session
from app.models.usuario import Usuario
from app.models.osc import (
    Osc,
    OscParceria,
    OscDirigente,
    OscDocumento,
    OscPlanoTrabalho,
    OscMeta,
    OscMetaPrecificacao,
    OscDesembolsoParcela,
)


router = APIRouter(
    prefix="/terceiro-setor",
    tags=["Terceiro Setor"],
    dependencies=[Depends(exigir_minimo_perfil("coord_municipal"))],
)


def _resolver_municipio_id(usuario: Usuario, municipio_id: Optional[int]) -> int:
    """Força município do usuário (exceto admin/consórcio)."""
    if pode_acesso_global(usuario):
        if municipio_id is None:
            raise HTTPException(status_code=400, detail="municipio_id é obrigatório para este perfil.")
        return int(municipio_id)

    mid = getattr(usuario, "municipio_id", None)
    if mid is None:
        raise HTTPException(status_code=403, detail="Usuário sem município associado.")
    if municipio_id is not None and int(municipio_id) != int(mid):
        raise HTTPException(status_code=403, detail="Município não corresponde ao usuário logado.")
    return int(mid)


def _check_municipio(usuario: Usuario, municipio_id: int) -> None:
    if pode_acesso_global(usuario):
        return
    mid = getattr(usuario, "municipio_id", None)
    if mid is None or int(mid) != int(municipio_id):
        raise HTTPException(status_code=403, detail="Acesso negado (município).")




def _coerce_date(v):
    """Converte ISO 'YYYY-MM-DD' (str) para date para evitar erro do SQLite."""
    if v is None:
        return None
    # datetime is also a date, então checar datetime primeiro
    if isinstance(v, datetime):
        return v.date()
    if isinstance(v, date):
        return v
    if isinstance(v, str):
        s = v.strip()
        if not s:
            return None
        try:
            return date.fromisoformat(s[:10])
        except Exception:
            raise HTTPException(status_code=422, detail=f"Data inválida: {v}")
    return v

# =========================
# Schemas (inputs)
# =========================


class DirigenteIn(SQLModel):
    nome: str
    cpf: Optional[str] = None
    cargo: Optional[str] = None
    inicio_mandato: Optional[date] = None
    fim_mandato: Optional[date] = None


class DocumentoIn(SQLModel):
    tipo: str
    titulo: Optional[str] = None
    url: str
    validade: Optional[date] = None


class PlanoIn(SQLModel):
    diagnostico: Optional[str] = None
    descricao_objeto: Optional[str] = None
    publico_alvo: Optional[str] = None
    metodologia: Optional[str] = None


class MetaIn(SQLModel):
    codigo: Optional[str] = None
    titulo: str
    unidade_medida: Optional[str] = None
    quantidade_alvo: Optional[float] = None
    indicador: Optional[str] = None
    linha_base: Optional[str] = None
    criterio_aceite: Optional[str] = None
    meios_verificacao: Optional[str] = None
    prazo: Optional[date] = None
    marcos: Optional[str] = None


class PrecificacaoIn(SQLModel):
    quantidade: Optional[float] = None
    custo_unitario: Optional[float] = None
    memoria_calculo: Optional[str] = None


class ParcelaIn(SQLModel):
    numero: int
    valor: float
    data_prevista: Optional[date] = None
    condicao: Optional[str] = None


class StatusIn(SQLModel):
    status: str


# =========================
# OSC
# =========================


@router.get("/oscs", response_model=List[Osc])
def listar_oscs(
    municipio_id: Optional[int] = None,
    q: Optional[str] = Query(default=None, description="Busca por nome/CNPJ"),
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    mid = _resolver_municipio_id(usuario, municipio_id)
    stmt = select(Osc).where(Osc.municipio_id == mid)
    if q:
        qq = f"%{q.strip().lower()}%"
        stmt = stmt.where((Osc.nome.ilike(qq)) | (Osc.cnpj.ilike(qq)))  # type: ignore
    stmt = stmt.order_by(Osc.ativo.desc(), Osc.nome)
    return session.exec(stmt).all()


@router.post("/oscs", response_model=Osc)
def criar_osc(
    osc: Osc,
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    mid = _resolver_municipio_id(usuario, getattr(osc, "municipio_id", None))
    osc.municipio_id = mid
    osc.criado_em = datetime.utcnow()
    session.add(osc)
    session.commit()
    session.refresh(osc)
    return osc


@router.get("/oscs/{osc_id}", response_model=Osc)
def obter_osc(
    osc_id: int,
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    osc = session.get(Osc, osc_id)
    if not osc:
        raise HTTPException(status_code=404, detail="OSC não encontrada")
    _check_municipio(usuario, int(getattr(osc, "municipio_id", 0)))
    return osc


@router.patch("/oscs/{osc_id}", response_model=Osc)
def atualizar_osc(
    osc_id: int,
    payload: dict,
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    osc = session.get(Osc, osc_id)
    if not osc:
        raise HTTPException(status_code=404, detail="OSC não encontrada")
    _check_municipio(usuario, int(getattr(osc, "municipio_id", 0)))

    for k, v in payload.items():
        if k in {"id", "municipio_id", "criado_em"}:
            continue
        if hasattr(osc, k):
            setattr(osc, k, v)
    session.add(osc)
    session.commit()
    session.refresh(osc)
    return osc


# =========================
# Dirigentes
# =========================


@router.get("/oscs/{osc_id}/dirigentes", response_model=List[OscDirigente])
def listar_dirigentes(
    osc_id: int,
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    osc = session.get(Osc, osc_id)
    if not osc:
        raise HTTPException(status_code=404, detail="OSC não encontrada")
    _check_municipio(usuario, int(osc.municipio_id))

    stmt = select(OscDirigente).where(
        (OscDirigente.municipio_id == int(osc.municipio_id)) & (OscDirigente.osc_id == int(osc_id))
    )
    stmt = stmt.order_by(OscDirigente.fim_mandato.is_(None).desc(), OscDirigente.nome)  # type: ignore
    return session.exec(stmt).all()


@router.post("/oscs/{osc_id}/dirigentes", response_model=OscDirigente)
def criar_dirigente(
    osc_id: int,
    payload: DirigenteIn,
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    osc = session.get(Osc, osc_id)
    if not osc:
        raise HTTPException(status_code=404, detail="OSC não encontrada")
    _check_municipio(usuario, int(osc.municipio_id))

    d = OscDirigente(
        municipio_id=int(osc.municipio_id),
        osc_id=int(osc_id),
        nome=payload.nome.strip(),
        cpf=(payload.cpf or None),
        cargo=(payload.cargo or None),
        inicio_mandato=payload.inicio_mandato,
        fim_mandato=payload.fim_mandato,
        criado_em=datetime.utcnow(),
    )
    session.add(d)
    session.commit()
    session.refresh(d)
    return d


@router.patch("/dirigentes/{dirigente_id}", response_model=OscDirigente)
def atualizar_dirigente(
    dirigente_id: int,
    payload: dict,
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    d = session.get(OscDirigente, dirigente_id)
    if not d:
        raise HTTPException(status_code=404, detail="Dirigente não encontrado")
    _check_municipio(usuario, int(d.municipio_id))

    for k, v in payload.items():
        if k in {"id", "municipio_id", "osc_id", "criado_em"}:
            continue
        if hasattr(d, k):
            setattr(d, k, v)

    session.add(d)
    session.commit()
    session.refresh(d)
    return d


@router.delete("/dirigentes/{dirigente_id}")
def excluir_dirigente(
    dirigente_id: int,
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    d = session.get(OscDirigente, dirigente_id)
    if not d:
        raise HTTPException(status_code=404, detail="Dirigente não encontrado")
    _check_municipio(usuario, int(d.municipio_id))

    session.delete(d)
    session.commit()
    return {"ok": True}


# =========================
# Documentos (metadados — upload entra no Patch B)
# =========================


@router.get("/oscs/{osc_id}/documentos", response_model=List[OscDocumento])
def listar_documentos_osc(
    osc_id: int,
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    osc = session.get(Osc, osc_id)
    if not osc:
        raise HTTPException(status_code=404, detail="OSC não encontrada")
    _check_municipio(usuario, int(osc.municipio_id))

    stmt = select(OscDocumento).where(
        (OscDocumento.municipio_id == int(osc.municipio_id)) & (OscDocumento.osc_id == int(osc_id))
    )
    stmt = stmt.order_by(OscDocumento.validade, OscDocumento.tipo)
    return session.exec(stmt).all()


@router.post("/oscs/{osc_id}/documentos", response_model=OscDocumento)
def criar_documento_osc(
    osc_id: int,
    payload: DocumentoIn,
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    osc = session.get(Osc, osc_id)
    if not osc:
        raise HTTPException(status_code=404, detail="OSC não encontrada")
    _check_municipio(usuario, int(osc.municipio_id))

    doc = OscDocumento(
        municipio_id=int(osc.municipio_id),
        osc_id=int(osc_id),
        tipo=payload.tipo.strip(),
        titulo=(payload.titulo or None),
        url=payload.url.strip(),
        validade=payload.validade,
        criado_em=datetime.utcnow(),
        atualizado_em=datetime.utcnow(),
    )
    session.add(doc)
    session.commit()
    session.refresh(doc)
    return doc


@router.delete("/documentos/{doc_id}")
def excluir_documento_osc(
    doc_id: int,
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    doc = session.get(OscDocumento, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Documento não encontrado")
    _check_municipio(usuario, int(doc.municipio_id))

    session.delete(doc)
    session.commit()
    return {"ok": True}


# =========================
# Parcerias
# =========================


@router.get("/parcerias", response_model=List[OscParceria])
def listar_parcerias(
    municipio_id: Optional[int] = None,
    osc_id: Optional[int] = None,
    status: Optional[str] = None,
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    mid = _resolver_municipio_id(usuario, municipio_id)
    stmt = select(OscParceria).where(OscParceria.municipio_id == mid)
    if osc_id is not None:
        stmt = stmt.where(OscParceria.osc_id == int(osc_id))
    if status:
        stmt = stmt.where(OscParceria.status == status)
    stmt = stmt.order_by(OscParceria.status, OscParceria.data_fim, OscParceria.data_inicio)
    return session.exec(stmt).all()


@router.post("/parcerias", response_model=OscParceria)
def criar_parceria(
    p: OscParceria,
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    mid = _resolver_municipio_id(usuario, getattr(p, "municipio_id", None))
    p.municipio_id = mid

    # valida OSC pertence ao município
    osc = session.get(Osc, int(p.osc_id))
    if not osc or int(getattr(osc, "municipio_id", 0)) != int(mid):
        raise HTTPException(status_code=400, detail="OSC inválida para este município")

    if not getattr(p, "status", None) or str(getattr(p, "status", "")).strip().lower() in ("", "ativa"):
        p.status = "rascunho"

    p.atualizado_em = datetime.utcnow()
    p.criado_em = datetime.utcnow()
    session.add(p)
    session.commit()
    session.refresh(p)
    return p


@router.get("/parcerias/{parceria_id}", response_model=OscParceria)
def obter_parceria(
    parceria_id: int,
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    p = session.get(OscParceria, parceria_id)
    if not p:
        raise HTTPException(status_code=404, detail="Parceria não encontrada")
    _check_municipio(usuario, int(p.municipio_id))
    return p


@router.patch("/parcerias/{parceria_id}", response_model=OscParceria)
def atualizar_parceria(
    parceria_id: int,
    payload: dict,
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    p = session.get(OscParceria, parceria_id)
    if not p:
        raise HTTPException(status_code=404, detail="Parceria não encontrada")
    _check_municipio(usuario, int(p.municipio_id))

    # aliases aceitos para facilitar integração
    if isinstance(payload, dict):
        if "vigencia_inicio" in payload and "data_inicio" not in payload:
            payload["data_inicio"] = payload.pop("vigencia_inicio")
        if "vigencia_fim" in payload and "data_fim" not in payload:
            payload["data_fim"] = payload.pop("vigencia_fim")
        if "numero_termo" in payload and "numero" not in payload:
            payload["numero"] = payload.pop("numero_termo")

    for k, v in payload.items():
        if k in {"id", "municipio_id", "criado_em"}:
            continue
        if k in {"data_inicio", "data_fim"}:
            v = _coerce_date(v)
        if hasattr(p, k):
            setattr(p, k, v)

    p.atualizado_em = datetime.utcnow()
    session.add(p)
    session.commit()
    session.refresh(p)
    return p


@router.post("/parcerias/{parceria_id}/status", response_model=OscParceria)
def atualizar_status(
    parceria_id: int,
    payload: StatusIn,
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    p = session.get(OscParceria, parceria_id)
    if not p:
        raise HTTPException(status_code=404, detail="Parceria não encontrada")
    _check_municipio(usuario, int(p.municipio_id))

    p.status = (payload.status or "").strip().lower()
    p.atualizado_em = datetime.utcnow()
    session.add(p)
    session.commit()
    session.refresh(p)
    return p


# =========================
# Plano de Trabalho
# =========================


@router.get("/parcerias/{parceria_id}/plano", response_model=Optional[OscPlanoTrabalho])
def obter_plano(
    parceria_id: int,
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    p = session.get(OscParceria, parceria_id)
    if not p:
        raise HTTPException(status_code=404, detail="Parceria não encontrada")
    _check_municipio(usuario, int(p.municipio_id))

    stmt = select(OscPlanoTrabalho).where(
        (OscPlanoTrabalho.parceria_id == int(parceria_id)) & (OscPlanoTrabalho.municipio_id == int(p.municipio_id))
    )
    return session.exec(stmt).first()


@router.post("/parcerias/{parceria_id}/plano", response_model=OscPlanoTrabalho)
def upsert_plano(
    parceria_id: int,
    payload: PlanoIn,
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    p = session.get(OscParceria, parceria_id)
    if not p:
        raise HTTPException(status_code=404, detail="Parceria não encontrada")
    _check_municipio(usuario, int(p.municipio_id))

    stmt = select(OscPlanoTrabalho).where(
        (OscPlanoTrabalho.parceria_id == int(parceria_id)) & (OscPlanoTrabalho.municipio_id == int(p.municipio_id))
    )
    pl = session.exec(stmt).first()

    if not pl:
        pl = OscPlanoTrabalho(
            municipio_id=int(p.municipio_id),
            parceria_id=int(parceria_id),
            diagnostico=payload.diagnostico,
            descricao_objeto=payload.descricao_objeto,
            publico_alvo=payload.publico_alvo,
            metodologia=payload.metodologia,
            criado_em=datetime.utcnow(),
            atualizado_em=datetime.utcnow(),
        )
    else:
        for k in ("diagnostico", "descricao_objeto", "publico_alvo", "metodologia"):
            v = getattr(payload, k)
            if v is not None:
                setattr(pl, k, v)
        pl.atualizado_em = datetime.utcnow()

    session.add(pl)
    session.commit()
    session.refresh(pl)
    return pl


# =========================
# Metas
# =========================


@router.get("/parcerias/{parceria_id}/metas", response_model=List[OscMeta])
def listar_metas(
    parceria_id: int,
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    p = session.get(OscParceria, parceria_id)
    if not p:
        raise HTTPException(status_code=404, detail="Parceria não encontrada")
    _check_municipio(usuario, int(p.municipio_id))

    stmt = select(OscMeta).where(
        (OscMeta.parceria_id == int(parceria_id)) & (OscMeta.municipio_id == int(p.municipio_id))
    )
    stmt = stmt.order_by(OscMeta.codigo, OscMeta.titulo)
    return session.exec(stmt).all()


@router.post("/parcerias/{parceria_id}/metas", response_model=OscMeta)
def criar_meta(
    parceria_id: int,
    payload: MetaIn,
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    p = session.get(OscParceria, parceria_id)
    if not p:
        raise HTTPException(status_code=404, detail="Parceria não encontrada")
    _check_municipio(usuario, int(p.municipio_id))

    m = OscMeta(
        municipio_id=int(p.municipio_id),
        parceria_id=int(parceria_id),
        codigo=(payload.codigo or None),
        titulo=payload.titulo.strip(),
        unidade_medida=payload.unidade_medida,
        quantidade_alvo=payload.quantidade_alvo,
        indicador=payload.indicador,
        linha_base=payload.linha_base,
        criterio_aceite=payload.criterio_aceite,
        meios_verificacao=payload.meios_verificacao,
        prazo=payload.prazo,
        marcos=payload.marcos,
        criado_em=datetime.utcnow(),
        atualizado_em=datetime.utcnow(),
    )
    session.add(m)
    session.commit()
    session.refresh(m)
    return m


@router.patch("/metas/{meta_id}", response_model=OscMeta)
def atualizar_meta(
    meta_id: int,
    payload: dict,
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    m = session.get(OscMeta, meta_id)
    if not m:
        raise HTTPException(status_code=404, detail="Meta não encontrada")
    _check_municipio(usuario, int(m.municipio_id))

    # aliases aceitos para facilitar integração
    if isinstance(payload, dict):
        if "prazo_final" in payload and "prazo" not in payload:
            payload["prazo"] = payload.pop("prazo_final")

    for k, v in payload.items():
        if k in {"id", "municipio_id", "parceria_id", "criado_em"}:
            continue
        if k in {"prazo"}:
            v = _coerce_date(v)
        if hasattr(m, k):
            setattr(m, k, v)

    m.atualizado_em = datetime.utcnow()
    session.add(m)
    session.commit()
    session.refresh(m)
    return m


@router.delete("/metas/{meta_id}")
def excluir_meta(
    meta_id: int,
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    m = session.get(OscMeta, meta_id)
    if not m:
        raise HTTPException(status_code=404, detail="Meta não encontrada")
    _check_municipio(usuario, int(m.municipio_id))

    session.delete(m)
    session.commit()
    return {"ok": True}


# =========================
# Precificação por meta
# =========================


@router.get("/metas/{meta_id}/precificacao", response_model=Optional[OscMetaPrecificacao])
def obter_precificacao(
    meta_id: int,
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    m = session.get(OscMeta, meta_id)
    if not m:
        raise HTTPException(status_code=404, detail="Meta não encontrada")
    _check_municipio(usuario, int(m.municipio_id))

    stmt = select(OscMetaPrecificacao).where(
        (OscMetaPrecificacao.meta_id == int(meta_id)) & (OscMetaPrecificacao.municipio_id == int(m.municipio_id))
    )
    return session.exec(stmt).first()


@router.post("/metas/{meta_id}/precificacao", response_model=OscMetaPrecificacao)
def upsert_precificacao(
    meta_id: int,
    payload: PrecificacaoIn,
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    m = session.get(OscMeta, meta_id)
    if not m:
        raise HTTPException(status_code=404, detail="Meta não encontrada")
    _check_municipio(usuario, int(m.municipio_id))

    stmt = select(OscMetaPrecificacao).where(
        (OscMetaPrecificacao.meta_id == int(meta_id)) & (OscMetaPrecificacao.municipio_id == int(m.municipio_id))
    )
    pr = session.exec(stmt).first()

    qtd = payload.quantidade
    cu = payload.custo_unitario
    ct = (qtd * cu) if (qtd is not None and cu is not None) else None

    if not pr:
        pr = OscMetaPrecificacao(
            municipio_id=int(m.municipio_id),
            meta_id=int(meta_id),
            quantidade=qtd,
            custo_unitario=cu,
            custo_total=ct,
            memoria_calculo=payload.memoria_calculo,
            criado_em=datetime.utcnow(),
            atualizado_em=datetime.utcnow(),
        )
    else:
        if payload.quantidade is not None:
            pr.quantidade = payload.quantidade
        if payload.custo_unitario is not None:
            pr.custo_unitario = payload.custo_unitario
        pr.custo_total = (pr.quantidade * pr.custo_unitario) if (pr.quantidade is not None and pr.custo_unitario is not None) else None
        if payload.memoria_calculo is not None:
            pr.memoria_calculo = payload.memoria_calculo
        pr.atualizado_em = datetime.utcnow()

    session.add(pr)
    session.commit()
    session.refresh(pr)
    return pr


# =========================
# Cronograma de desembolso
# =========================


@router.get("/parcerias/{parceria_id}/desembolso", response_model=List[OscDesembolsoParcela])
def listar_desembolso(
    parceria_id: int,
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    p = session.get(OscParceria, parceria_id)
    if not p:
        raise HTTPException(status_code=404, detail="Parceria não encontrada")
    _check_municipio(usuario, int(p.municipio_id))

    stmt = select(OscDesembolsoParcela).where(
        (OscDesembolsoParcela.parceria_id == int(parceria_id)) & (OscDesembolsoParcela.municipio_id == int(p.municipio_id))
    )
    stmt = stmt.order_by(OscDesembolsoParcela.numero)
    return session.exec(stmt).all()


@router.post("/parcerias/{parceria_id}/desembolso", response_model=OscDesembolsoParcela)
def criar_desembolso(
    parceria_id: int,
    payload: ParcelaIn,
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    p = session.get(OscParceria, parceria_id)
    if not p:
        raise HTTPException(status_code=404, detail="Parceria não encontrada")
    _check_municipio(usuario, int(p.municipio_id))

    parcela = OscDesembolsoParcela(
        municipio_id=int(p.municipio_id),
        parceria_id=int(parceria_id),
        numero=int(payload.numero),
        valor=float(payload.valor),
        data_prevista=payload.data_prevista,
        condicao=payload.condicao,
        criado_em=datetime.utcnow(),
        atualizado_em=datetime.utcnow(),
    )
    session.add(parcela)
    session.commit()
    session.refresh(parcela)
    return parcela


@router.patch("/desembolso/{parcela_id}", response_model=OscDesembolsoParcela)
def atualizar_desembolso(
    parcela_id: int,
    payload: dict,
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    parcela = session.get(OscDesembolsoParcela, parcela_id)
    if not parcela:
        raise HTTPException(status_code=404, detail="Parcela não encontrada")
    _check_municipio(usuario, int(parcela.municipio_id))

    for k, v in payload.items():
        if k in {"id", "municipio_id", "parceria_id", "criado_em"}:
            continue
        if hasattr(parcela, k):
            setattr(parcela, k, v)

    parcela.atualizado_em = datetime.utcnow()
    session.add(parcela)
    session.commit()
    session.refresh(parcela)
    return parcela


@router.delete("/desembolso/{parcela_id}")
def excluir_desembolso(
    parcela_id: int,
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    parcela = session.get(OscDesembolsoParcela, parcela_id)
    if not parcela:
        raise HTTPException(status_code=404, detail="Parcela não encontrada")
    _check_municipio(usuario, int(parcela.municipio_id))

    session.delete(parcela)
    session.commit()
    return {"ok": True}
