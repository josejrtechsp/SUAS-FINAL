from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field as PField
from sqlmodel import Session, select

from app.core.auth import exigir_minimo_perfil, get_current_user
from app.core.db import get_session
from app.models.usuario import Usuario

# Modelos (podem variar por instalação; usamos try/except para não quebrar)
try:
    from app.models.caso_cras import CasoCras, CasoCrasHistorico  # type: ignore
except Exception:  # pragma: no cover
    CasoCras = None  # type: ignore
    CasoCrasHistorico = None  # type: ignore

try:
    from app.models.creas_caso import CreasCaso, CreasCasoHistorico  # type: ignore
except Exception:  # pragma: no cover
    CreasCaso = None  # type: ignore
    CreasCasoHistorico = None  # type: ignore

try:
    from app.models.caso_pop_rua import CasoPopRua, CasoPopRuaEtapaHistorico  # type: ignore
except Exception:  # pragma: no cover
    CasoPopRua = None  # type: ignore
    CasoPopRuaEtapaHistorico = None  # type: ignore

try:
    from app.models.cras_tarefas import CrasTarefa  # type: ignore
except Exception:  # pragma: no cover
    CrasTarefa = None  # type: ignore

try:
    from app.models.cadunico_precadastro import CadunicoPreCadastro  # type: ignore
except Exception:  # pragma: no cover
    CadunicoPreCadastro = None  # type: ignore

try:
    from app.models.osc import OscPrestacaoContas  # type: ignore
except Exception:  # pragma: no cover
    OscPrestacaoContas = None  # type: ignore

router = APIRouter(
    prefix="/gestao",
    tags=["gestao"],
    dependencies=[Depends(exigir_minimo_perfil("coord_municipal"))],
)


def _iso(dt: Any) -> Optional[str]:
    return dt.isoformat() if isinstance(dt, datetime) else None


def _dump(obj: Any) -> Dict[str, Any]:
    if obj is None:
        return {}
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    if hasattr(obj, "dict"):
        return obj.dict()
    out: Dict[str, Any] = {}
    for k in dir(obj):
        if k.startswith("_"):
            continue
        try:
            v = getattr(obj, k)
        except Exception:
            continue
        if callable(v):
            continue
        out[k] = v
    return out


class FilaItemRef(BaseModel):
    modulo: str = PField(..., description="CRAS|CREAS|POPRUA|REDE|OSC")
    tipo: str = PField(..., description="tipo do item (caso|tarefa|cadunico|encaminhamento|encaminhamento_intermunicipal|prestacao_contas)")
    referencia_id: int = PField(..., ge=1)
    municipio_id: Optional[int] = None


@router.get("/fila/item")
def fila_item_detalhe(
    modulo: str = Query(...),
    tipo: str = Query(...),
    referencia_id: int = Query(..., ge=1),
    municipio_id: Optional[int] = Query(default=None, description="Opcional (global): força município"),
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Detalhe do item da fila para alimentar um painel lateral (inspector).
    Retorna:
      - item (no mesmo formato da fila quando possível)
      - dados (registro bruto)
      - eventos (timeline)
    """
    mod = (modulo or "").strip().upper()
    tp = (tipo or "").strip().lower()
    rid = int(referencia_id)

    # tenta pegar o item no MESMO formato da fila atual (reusa gestao_fila)
    item_obj: Optional[Dict[str, Any]] = None
    try:
        from app.routers.gestao import gestao_fila as _gestao_fila  # type: ignore

        fila = _gestao_fila(  # type: ignore
            municipio_id=municipio_id,
            modulo=mod.lower(),
            limit=500,
            offset=0,
            session=session,
            usuario=usuario,
        )
        items = list((fila or {}).get("items") or [])
        for it in items:
            if str(it.get("tipo") or "").lower() == tp and int(it.get("referencia_id") or 0) == rid:
                item_obj = it
                break
    except Exception:
        item_obj = None

    # fallback básico (se não achou na fila)
    if item_obj is None:
        item_obj = {
            "modulo": mod,
            "tipo": tp,
            "referencia_id": rid,
        }

    dados: Dict[str, Any] = {}
    eventos: List[Dict[str, Any]] = []

    # ----------------------------
    # Casos (CRAS/CREAS/POPRUA)
    # ----------------------------
    if tp == "caso":
        if mod == "CRAS" and CasoCras is not None:
            c = session.get(CasoCras, rid)
            if not c:
                raise HTTPException(status_code=404, detail="Caso CRAS não encontrado")
            dados = _dump(c)
            if CasoCrasHistorico is not None:
                rows = session.exec(
                    select(CasoCrasHistorico)
                    .where(CasoCrasHistorico.caso_id == rid)
                    .order_by(CasoCrasHistorico.id.desc())
                ).all()
                eventos = [
                    {
                        "tipo": "caso_evento",
                        "detalhe": getattr(h, "observacoes", None),
                        "por_nome": getattr(h, "usuario_nome", None),
                        "em": _iso(getattr(h, "criado_em", None)),
                        "etapa": getattr(h, "etapa", None),
                        "acao": getattr(h, "tipo_acao", None),
                    }
                    for h in rows[:200]
                ]

        elif mod == "CREAS" and CreasCaso is not None:
            c = session.get(CreasCaso, rid)
            if not c:
                raise HTTPException(status_code=404, detail="Caso CREAS não encontrado")
            dados = _dump(c)
            if CreasCasoHistorico is not None:
                rows = session.exec(
                    select(CreasCasoHistorico)
                    .where(CreasCasoHistorico.caso_id == rid)
                    .order_by(CreasCasoHistorico.id.desc())
                ).all()
                eventos = [
                    {
                        "tipo": "caso_evento",
                        "detalhe": getattr(h, "observacoes", None),
                        "por_nome": getattr(h, "usuario_nome", None),
                        "em": _iso(getattr(h, "criado_em", None)),
                        "etapa": getattr(h, "etapa", None),
                        "acao": getattr(h, "tipo_acao", None),
                    }
                    for h in rows[:200]
                ]

        elif mod == "POPRUA" and CasoPopRua is not None:
            c = session.get(CasoPopRua, rid)
            if not c:
                raise HTTPException(status_code=404, detail="Caso PopRua não encontrado")
            dados = _dump(c)
            if CasoPopRuaEtapaHistorico is not None:
                rows = session.exec(
                    select(CasoPopRuaEtapaHistorico)
                    .where(CasoPopRuaEtapaHistorico.caso_id == rid)
                    .order_by(CasoPopRuaEtapaHistorico.id.desc())
                ).all()
                eventos = [
                    {
                        "tipo": "etapa",
                        "detalhe": getattr(h, "observacoes", None),
                        "por_nome": getattr(h, "usuario_responsavel", None),
                        "em": _iso(getattr(h, "data_acao", None)),
                        "etapa": getattr(h, "etapa", None),
                        "acao": getattr(h, "tipo_acao", None),
                    }
                    for h in rows[:200]
                ]
        else:
            raise HTTPException(status_code=404, detail="Módulo de caso não disponível")

        return {"item": item_obj, "dados": dados, "eventos": eventos}

    # ----------------------------
    # Tarefa (CRAS)
    # ----------------------------
    if tp == "tarefa":
        if CrasTarefa is None:
            raise HTTPException(status_code=404, detail="Módulo de tarefas não disponível")
        t = session.get(CrasTarefa, rid)
        if not t:
            raise HTTPException(status_code=404, detail="Tarefa não encontrada")
        dados = _dump(t)
        eventos = [
            {"tipo": "criado", "em": _iso(getattr(t, "criado_em", None)), "por_nome": getattr(t, "criado_por_nome", None), "detalhe": None},
            {"tipo": "vencimento", "em": _iso(getattr(t, "data_vencimento", None)), "por_nome": None, "detalhe": None},
        ]
        return {"item": item_obj, "dados": dados, "eventos": eventos}

    # ----------------------------
    # CadÚnico (pré-cadastro)
    # ----------------------------
    if tp == "cadunico":
        if CadunicoPreCadastro is None:
            raise HTTPException(status_code=404, detail="Módulo CadÚnico não disponível")
        x = session.get(CadunicoPreCadastro, rid)
        if not x:
            raise HTTPException(status_code=404, detail="Pré-cadastro não encontrado")
        dados = _dump(x)
        eventos = [
            {"tipo": "criado", "em": _iso(getattr(x, "criado_em", None)), "por_nome": getattr(x, "criado_por_nome", None), "detalhe": None},
            {"tipo": "atualizado", "em": _iso(getattr(x, "atualizado_em", None)), "por_nome": getattr(x, "atualizado_por_nome", None), "detalhe": getattr(x, "observacoes", None)},
        ]
        return {"item": item_obj, "dados": dados, "eventos": eventos}

    # ----------------------------
    # Rede (timeline vem do próprio router de gestão)
    # ----------------------------
    if tp in ("encaminhamento", "encaminhamento_intermunicipal"):
        try:
            from app.routers.gestao import gestao_rede_timeline as _tl  # type: ignore

            if tp == "encaminhamento":
                out = _tl(tipo="cras", id=rid, municipio_id=municipio_id, session=session, usuario=usuario)  # type: ignore
            else:
                out = _tl(tipo="intermunicipal", id=rid, municipio_id=municipio_id, session=session, usuario=usuario)  # type: ignore

            return {"item": item_obj, "dados": dict((out or {}).get("dados") or {}), "eventos": list((out or {}).get("eventos") or [])}
        except Exception:
            raise HTTPException(status_code=500, detail="Falha ao montar timeline da Rede")

    # ----------------------------
    # OSC - prestação de contas
    # ----------------------------
    if tp == "prestacao_contas":
        if OscPrestacaoContas is None:
            raise HTTPException(status_code=404, detail="Módulo OSC não disponível")
        pc = session.get(OscPrestacaoContas, rid)
        if not pc:
            raise HTTPException(status_code=404, detail="Prestação de contas não encontrada")
        dados = _dump(pc)
        eventos = [
            {"tipo": "criado", "em": _iso(getattr(pc, "criado_em", None)), "por_nome": getattr(pc, "responsavel_nome", None), "detalhe": None},
            {"tipo": "prazo", "em": _iso(getattr(pc, "prazo_entrega", None)), "por_nome": None, "detalhe": None},
        ]
        return {"item": item_obj, "dados": dados, "eventos": eventos}

    raise HTTPException(status_code=400, detail="tipo inválido")


# ============================================================
# LOTE: Documentos (cobrar / relatório / ofício)
# ============================================================

class LoteDocumentosPayload(BaseModel):
    acao: str = PField(..., description="cobrar|relatorio|oficio")
    items: List[FilaItemRef] = PField(default_factory=list)

    # Documento (geral)
    municipio_id: Optional[int] = None  # útil p/ global
    emissor: str = "smas"
    salvar: bool = True

    # Cobrança
    contato_retorno: Optional[str] = None
    idempotency_key: Optional[str] = None
    forcar_novo: bool = False

    # IA (opcional, quando suportado)
    usar_ia: bool = False
    ia_instructions: Optional[str] = None
    ia_model: Optional[str] = None
    ia_reasoning_effort: Optional[str] = None

    # Ofício/Relatório (opcionais)
    assunto: Optional[str] = None
    destinatario_nome: Optional[str] = None
    destinatario_cargo: Optional[str] = None
    destinatario_orgao: Optional[str] = None
    assinante_nome: Optional[str] = None
    assinante_cargo: Optional[str] = None


def _modelo_relatorio(modulo: str) -> str:
    m = (modulo or "").strip().upper()
    if m == "CRAS":
        return "relatorio_tecnico_cras"
    if m == "CREAS":
        return "relatorio_tecnico_creas"
    if m == "POPRUA":
        return "relatorio_tecnico_poprua"
    return "relatorio_padrao"


@router.post("/fila/lote/documentos")
def fila_lote_documentos(
    payload: LoteDocumentosPayload,
    request: Request,
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Ações em lote para a Fila da Gestão (backend-only).
    - cobrar: usa /documentos/gerar/cobranca-devolutiva (compatível com intermunicipal via PATCH_001A)
    - relatorio: gera relatório técnico (por módulo) com preenchimento mínimo
    - oficio: gera ofício padrão (texto guiado) com referência ao item
    """
    acao = (payload.acao or "").strip().lower()
    if acao not in ("cobrar", "relatorio", "oficio"):
        raise HTTPException(status_code=400, detail="acao inválida (use cobrar|relatorio|oficio)")

    if not payload.items:
        return {"acao": acao, "total": 0, "ok": 0, "falhas": 0, "resultados": []}

    # Imports locais (evita custo no import time)
    from app.routers.documentos import DocumentoGerar, gerar_documento  # type: ignore

    resultados: List[Dict[str, Any]] = []
    ok = falhas = 0

    for idx, it in enumerate(payload.items[:500]):
        ref = int(it.referencia_id)
        mod = (it.modulo or "").strip().upper()
        tp = (it.tipo or "").strip().lower()

        try:
            if acao == "cobrar":
                from app.routers.documentos import CobrancaDevolutivaAuto, gerar_cobranca_devolutiva  # type: ignore

                idem = None
                if payload.idempotency_key:
                    idem = f"{payload.idempotency_key}:{mod}:{tp}:{ref}"

                doc = gerar_cobranca_devolutiva(  # type: ignore
                    CobrancaDevolutivaAuto(
                        encaminhamento_id=ref,
                        municipio_id=(payload.municipio_id or it.municipio_id),
                        emissor=payload.emissor,
                        contato_retorno=payload.contato_retorno,
                        salvar=payload.salvar,
                        retornar_pdf=False,
                        idempotency_key=idem,
                        forcar_novo=payload.forcar_novo,
                        usar_ia=payload.usar_ia,
                        ia_instructions=payload.ia_instructions,
                        ia_model=payload.ia_model,
                        ia_reasoning_effort=payload.ia_reasoning_effort,
                    ),
                    request=request,
                    session=session,
                    usuario=usuario,
                )
                resultados.append({"item": it.model_dump(), "ok": True, "documento": doc})
                ok += 1
                continue

            if acao == "relatorio":
                modelo = _modelo_relatorio(mod)
                assunto = payload.assunto or "Relatório técnico"

                # preenchimento mínimo (garante campos obrigatórios dos técnicos)
                campos: Dict[str, Any] = {
                    "assinante_nome": payload.assinante_nome,
                    "assinante_cargo": payload.assinante_cargo,
                }

                if modelo == "relatorio_tecnico_cras":
                    campos.update(
                        {
                            "identificacao": f"Caso CRAS #{ref}",
                            "demanda": "Relatório gerado pela Gestão (fila) para acompanhamento de fluxo/SLA.",
                            "intervencoes": "Não informado.",
                            "avaliacao": "Não informado.",
                            "encaminhamentos": "Não informado.",
                        }
                    )
                elif modelo == "relatorio_tecnico_creas":
                    campos.update(
                        {
                            "identificacao": f"Caso CREAS #{ref}",
                            "fatos": "Relatório gerado pela Gestão (fila) para acompanhamento.",
                            "risco": "Não informado.",
                            "intervencoes": "Não informado.",
                            "encaminhamentos": "Não informado.",
                        }
                    )
                elif modelo == "relatorio_tecnico_poprua":
                    campos.update(
                        {
                            "identificacao": f"Caso PopRua #{ref}",
                            "abordagem": "Não informado.",
                            "historico": "Não informado.",
                            "necessidades": "Não informado.",
                            "encaminhamentos": "Não informado.",
                        }
                    )
                else:
                    # relatorio_padrao (opcional)
                    campos.update(
                        {
                            "contexto": f"{mod} · {tp} · ref #{ref}",
                            "descricao": "Relatório gerado pela Gestão (fila).",
                            "encaminhamentos": "Não informado.",
                        }
                    )

                doc = gerar_documento(  # type: ignore
                    DocumentoGerar(
                        municipio_id=(payload.municipio_id or it.municipio_id),
                        tipo="relatorio",
                        modelo=modelo,
                        assunto=assunto,
                        campos=campos,
                        emissor=payload.emissor,
                        salvar=payload.salvar,
                        retornar_pdf=False,
                    ),
                    request=request,
                    session=session,
                    usuario=usuario,
                )
                resultados.append({"item": it.model_dump(), "ok": True, "documento": doc})
                ok += 1
                continue

            if acao == "oficio":
                assunto = payload.assunto or "Ofício"
                texto = (
                    f"Encaminhamos, para ciência e providências, referência do item da Fila de Pendências:\n"
                    f"- Módulo: {mod}\n"
                    f"- Tipo: {tp}\n"
                    f"- Referência: #{ref}\n\n"
                    f"Solicitamos retorno/registro de andamento no sistema."
                )

                campos = {
                    "texto": texto,
                    "assinante_nome": payload.assinante_nome,
                    "assinante_cargo": payload.assinante_cargo,
                }

                doc = gerar_documento(  # type: ignore
                    DocumentoGerar(
                        municipio_id=(payload.municipio_id or it.municipio_id),
                        tipo="oficio",
                        modelo="oficio_padrao",
                        assunto=assunto,
                        destinatario_nome=payload.destinatario_nome,
                        destinatario_cargo=payload.destinatario_cargo,
                        destinatario_orgao=payload.destinatario_orgao,
                        campos=campos,
                        emissor=payload.emissor,
                        salvar=payload.salvar,
                        retornar_pdf=False,
                    ),
                    request=request,
                    session=session,
                    usuario=usuario,
                )
                resultados.append({"item": it.model_dump(), "ok": True, "documento": doc})
                ok += 1
                continue

        except Exception as e:
            falhas += 1
            resultados.append({"item": it.model_dump(), "ok": False, "erro": str(e)})

    return {"acao": acao, "total": len(payload.items), "ok": ok, "falhas": falhas, "resultados": resultados}
