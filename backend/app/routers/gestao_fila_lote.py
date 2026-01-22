from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field as PField
from sqlmodel import Session, select

from app.core.auth import exigir_minimo_perfil, get_current_user, pode_acesso_global
from app.core.db import get_session
from app.models.usuario import Usuario

# Optional imports (não travam o app se algum módulo estiver ausente)
try:
    from app.models.encaminhamentos import EncaminhamentoIntermunicipal  # type: ignore
except Exception:  # pragma: no cover
    EncaminhamentoIntermunicipal = None  # type: ignore

try:
    from app.models.cras_encaminhamento import CrasEncaminhamento  # type: ignore
except Exception:  # pragma: no cover
    CrasEncaminhamento = None  # type: ignore

try:
    from app.models.municipio import Municipio  # type: ignore
except Exception:  # pragma: no cover
    Municipio = None  # type: ignore

router = APIRouter(
    prefix="/gestao/fila/lote",
    tags=["gestao"],
    dependencies=[Depends(exigir_minimo_perfil("coord_municipal"))],
)


def _parse_iso(s: Optional[str]) -> Optional[datetime]:
    if not s:
        return None
    try:
        return datetime.fromisoformat(str(s).replace("Z", ""))
    except Exception:
        return None


def _fmt_data_br(dt: Optional[datetime]) -> Optional[str]:
    if not dt:
        return None
    try:
        return dt.strftime("%d/%m/%Y")
    except Exception:
        return None


class FilaFiltro(BaseModel):
    municipio_id: Optional[int] = None
    unidade_id: Optional[int] = None
    territorio: Optional[str] = None

    modulo: Optional[str] = PField(default=None, description="cras|creas|poprua|rede|osc")
    tipo: Optional[str] = PField(default=None, description="ex.: caso|tarefa|cadunico|encaminhamento|encaminhamento_intermunicipal|prestacao_contas")

    somente_atrasos: bool = False
    somente_em_risco: bool = False

    dias_atraso_min: Optional[int] = None
    dias_atraso_max: Optional[int] = None

    limit: int = 200


class LoteDocumentosPayload(BaseModel):
    acao: str = PField(..., description="cobrar|relatorio|oficio")
    filtro: FilaFiltro = PField(default_factory=FilaFiltro)

    emissor: str = "smas"
    salvar: bool = True
    dry_run: bool = False

    # Documento
    assunto: Optional[str] = None
    contato_retorno: Optional[str] = None

    destinatario_nome: Optional[str] = None
    destinatario_cargo: Optional[str] = None
    destinatario_orgao: Optional[str] = None

    assinante_nome: Optional[str] = None
    assinante_cargo: Optional[str] = None
    assinante_orgao: Optional[str] = None

    # IA (opcional)
    usar_ia: bool = False
    ia_instructions: Optional[str] = None
    ia_model: Optional[str] = None
    ia_reasoning_effort: Optional[str] = None


def _selecionar_itens_da_fila(
    filtro: FilaFiltro,
    session: Session,
    usuario: Usuario,
) -> Tuple[List[Dict[str, Any]], int]:
    """Reusa /gestao/fila (mesmo motor) e aplica filtros adicionais."""

    from app.routers.gestao import gestao_fila as _gestao_fila  # import local

    out = _gestao_fila(
        municipio_id=filtro.municipio_id,
        unidade_id=filtro.unidade_id,
        territorio=filtro.territorio,
        modulo=filtro.modulo,
        somente_atrasos=filtro.somente_atrasos,
        somente_em_risco=filtro.somente_em_risco,
        limit=500,
        offset=0,
        session=session,
        usuario=usuario,
    )

    items = list((out or {}).get("items") or [])
    total_sem_filtro_extra = len(items)

    # filtro por tipo (mais usado)
    if filtro.tipo:
        t = str(filtro.tipo).strip().lower()
        items = [it for it in items if str(it.get("tipo") or "").strip().lower() == t]

    # filtro por faixa de atraso
    if filtro.dias_atraso_min is not None:
        minv = int(filtro.dias_atraso_min)
        items = [it for it in items if int(it.get("dias_em_atraso") or 0) >= minv]

    if filtro.dias_atraso_max is not None:
        maxv = int(filtro.dias_atraso_max)
        items = [it for it in items if int(it.get("dias_em_atraso") or 0) <= maxv]

    lim = int(filtro.limit or 200)
    if lim < 1:
        lim = 1
    if lim > 500:
        lim = 500

    items = items[:lim]
    return items, total_sem_filtro_extra


@router.get("/preview")
def preview(
    municipio_id: Optional[int] = None,
    unidade_id: Optional[int] = None,
    territorio: Optional[str] = None,
    modulo: Optional[str] = None,
    tipo: Optional[str] = None,
    somente_atrasos: bool = False,
    somente_em_risco: bool = False,
    dias_atraso_min: Optional[int] = None,
    dias_atraso_max: Optional[int] = None,
    limit: int = 200,
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    filtro = FilaFiltro(
        municipio_id=municipio_id,
        unidade_id=unidade_id,
        territorio=territorio,
        modulo=modulo,
        tipo=tipo,
        somente_atrasos=somente_atrasos,
        somente_em_risco=somente_em_risco,
        dias_atraso_min=dias_atraso_min,
        dias_atraso_max=dias_atraso_max,
        limit=limit,
    )

    items, total = _selecionar_itens_da_fila(filtro, session=session, usuario=usuario)
    return {"total_fila": total, "selecionados": len(items), "items": items}


@router.post("/documentos")
def executar_lote_documentos(
    payload: LoteDocumentosPayload,
    request: Request,
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    acao = (payload.acao or "").strip().lower()
    if acao not in ("cobrar", "relatorio", "oficio"):
        raise HTTPException(status_code=400, detail="acao inválida (use cobrar|relatorio|oficio)")

    itens, total_fila = _selecionar_itens_da_fila(payload.filtro, session=session, usuario=usuario)

    if payload.dry_run:
        return {"acao": acao, "dry_run": True, "total_fila": total_fila, "selecionados": len(itens), "items": itens}

    # Imports locais para reduzir risco de erro na carga
    from app.routers.documentos import DocumentoGerar, gerar_documento  # type: ignore

    resultados: List[Dict[str, Any]] = []
    ok = 0
    falhas = 0

    # mapa rápido de municípios (para ofícios intermunicipais)
    muni_map: Dict[int, str] = {}
    if Municipio is not None:
        try:
            rows = session.exec(select(Municipio)).all()  # type: ignore
            for m in rows:
                mid = getattr(m, "id", None)
                if mid is not None:
                    muni_map[int(mid)] = f"{getattr(m, 'nome', '')} - {getattr(m, 'uf', '')}".strip(" -")
        except Exception:
            muni_map = {}

    def _doc_municipio_id(item: Dict[str, Any]) -> Optional[int]:
        mid = item.get("municipio_id")
        return int(mid) if mid is not None else None

    for it in itens:
        try:
            modulo = str(it.get("modulo") or "").strip().upper()
            tipo = str(it.get("tipo") or "").strip().lower()
            ref_id = int(it.get("referencia_id") or 0)
            if ref_id <= 0:
                raise ValueError("referencia_id inválida")

            mid = _doc_municipio_id(it)

            # segurança extra: municipal não pode gerar documentos para outros municípios
            if (mid is not None) and (not pode_acesso_global(usuario)):
                umid = getattr(usuario, "municipio_id", None)
                if umid is not None and int(umid) != int(mid):
                    raise HTTPException(status_code=403, detail="Sem permissão para esse município")

            if acao == "cobrar":
                # 1) Encaminhamento CRAS (Rede)
                if tipo == "encaminhamento":
                    from app.routers.documentos import CobrancaDevolutivaAuto, gerar_cobranca_devolutiva  # type: ignore

                    doc = gerar_cobranca_devolutiva(
                        CobrancaDevolutivaAuto(
                            encaminhamento_id=ref_id,
                            municipio_id=mid,
                            emissor=payload.emissor,
                            contato_retorno=payload.contato_retorno,
                            salvar=payload.salvar,
                            retornar_pdf=False,
                            usar_ia=payload.usar_ia,
                            ia_instructions=payload.ia_instructions,
                            ia_model=payload.ia_model,
                            ia_reasoning_effort=payload.ia_reasoning_effort,
                        ),
                        request=request,
                        session=session,
                        usuario=usuario,
                    )
                    resultados.append({"item": it, "ok": True, "documento": doc})
                    ok += 1
                    continue

                # 2) Intermunicipal (Rede) -> gera um ofício padrão usando o modelo de cobrança
                if tipo == "encaminhamento_intermunicipal":
                    if EncaminhamentoIntermunicipal is None:
                        raise HTTPException(status_code=404, detail="Módulo intermunicipal não disponível")

                    enc = session.get(EncaminhamentoIntermunicipal, ref_id)
                    if not enc:
                        raise HTTPException(status_code=404, detail="Encaminhamento intermunicipal não encontrado")

                    destino_id = getattr(enc, "municipio_destino_id", None)
                    destino_nome = muni_map.get(int(destino_id), None) if destino_id is not None else None

                    due = _parse_iso(it.get("sla_due_at"))
                    prazo_txt = None
                    if due:
                        prazo_txt = f"até {_fmt_data_br(due)}"
                    else:
                        sla_dias = int(it.get("sla_dias") or 0) or 5
                        prazo_txt = f"{sla_dias} dias"

                    referencia = f"Intermunicipal #{ref_id}"

                    campos = {
                        "referencia": referencia,
                        "prazo": prazo_txt,
                        "data_envio": _fmt_data_br(_parse_iso(getattr(enc, "criado_em", None))) if getattr(enc, "criado_em", None) else None,
                        "solicitacao": getattr(enc, "motivo", None) or None,
                        "contato_retorno": payload.contato_retorno,
                        "assinante_nome": payload.assinante_nome,
                        "assinante_cargo": payload.assinante_cargo,
                        "assinante_orgao": payload.assinante_orgao,
                    }

                    doc = gerar_documento(
                        DocumentoGerar(
                            municipio_id=mid,
                            tipo="oficio",
                            modelo="oficio_cobranca_devolutiva",
                            assunto=payload.assunto or "Cobrança de devolutiva (Intermunicipal)",
                            destinatario_nome=payload.destinatario_nome,
                            destinatario_cargo=payload.destinatario_cargo,
                            destinatario_orgao=payload.destinatario_orgao or destino_nome,
                            campos={k: v for k, v in campos.items() if v is not None},
                            emissor=payload.emissor,
                            salvar=payload.salvar,
                            retornar_pdf=False,
                        ),
                        request=request,
                        session=session,
                        usuario=usuario,
                    )

                    resultados.append({"item": it, "ok": True, "documento": doc})
                    ok += 1
                    continue

                raise HTTPException(status_code=400, detail=f"Tipo não suportado para cobrança: {tipo}")

            if acao == "relatorio":
                assunto = payload.assunto or "Relatório"
                contexto = f"Fila de Pendências · {modulo} · {tipo} · ref #{ref_id}"
                descricao = it.get("titulo") or "Item da fila"

                campos = {
                    "contexto": contexto,
                    "descricao": str(descricao),
                    "encaminhamentos": f"Motivo/trava: {it.get('motivo_trava') or '—'}\nStatus: {it.get('status') or '—'}",
                    "assinante_nome": payload.assinante_nome,
                    "assinante_cargo": payload.assinante_cargo,
                }

                doc = gerar_documento(
                    DocumentoGerar(
                        municipio_id=mid,
                        tipo="relatorio",
                        modelo="relatorio_padrao",
                        assunto=assunto,
                        campos={k: v for k, v in campos.items() if v is not None},
                        emissor=payload.emissor,
                        salvar=payload.salvar,
                        retornar_pdf=False,
                    ),
                    request=request,
                    session=session,
                    usuario=usuario,
                )

                resultados.append({"item": it, "ok": True, "documento": doc})
                ok += 1
                continue

            if acao == "oficio":
                assunto = payload.assunto or "Ofício"
                texto = (
                    "Encaminhamos, para ciência e providências, referência do item da Fila de Pendências:\n"
                    f"- Módulo: {modulo}\n"
                    f"- Tipo: {tipo}\n"
                    f"- Referência: #{ref_id}\n\n"
                    "Solicitamos registro de andamento no sistema."
                )

                campos = {
                    "texto": texto,
                    "assinante_nome": payload.assinante_nome,
                    "assinante_cargo": payload.assinante_cargo,
                }

                doc = gerar_documento(
                    DocumentoGerar(
                        municipio_id=mid,
                        tipo="oficio",
                        modelo="oficio_padrao",
                        assunto=assunto,
                        destinatario_nome=payload.destinatario_nome,
                        destinatario_cargo=payload.destinatario_cargo,
                        destinatario_orgao=payload.destinatario_orgao,
                        campos={k: v for k, v in campos.items() if v is not None},
                        emissor=payload.emissor,
                        salvar=payload.salvar,
                        retornar_pdf=False,
                    ),
                    request=request,
                    session=session,
                    usuario=usuario,
                )

                resultados.append({"item": it, "ok": True, "documento": doc})
                ok += 1
                continue

        except Exception as e:
            falhas += 1
            resultados.append({"item": it, "ok": False, "erro": str(e)})

    return {
        "acao": acao,
        "total_fila": total_fila,
        "selecionados": len(itens),
        "ok": ok,
        "falhas": falhas,
        "resultados": resultados,
    }
