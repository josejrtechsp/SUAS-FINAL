from __future__ import annotations

import json
from datetime import datetime, time, timedelta, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, Field as PField
from sqlmodel import Session, select

from app.core.auth import exigir_minimo_perfil, get_current_user, pode_acesso_global
from app.core.db import get_session
from app.models.usuario import Usuario

from app.models.gestao_automacoes import GestaoLoteExecucao, GestaoLoteRegra

try:
    from zoneinfo import ZoneInfo  # py3.9+
except Exception:  # pragma: no cover
    ZoneInfo = None  # type: ignore


router = APIRouter(
    prefix="/gestao/automacoes",
    tags=["gestao"],
    dependencies=[Depends(exigir_minimo_perfil("coord_municipal"))],
)


# =========================
# Helpers
# =========================

def _now_utc() -> datetime:
    return datetime.utcnow().replace(tzinfo=timezone.utc)


def _to_local(dt_utc: Optional[datetime], tz_name: str) -> Optional[datetime]:
    if not dt_utc:
        return None
    if dt_utc.tzinfo is None:
        dt_utc = dt_utc.replace(tzinfo=timezone.utc)
    if ZoneInfo is None:
        # fallback: São Paulo ~ UTC-3
        return dt_utc.astimezone(timezone(timedelta(hours=-3)))
    try:
        return dt_utc.astimezone(ZoneInfo(tz_name))
    except Exception:
        return dt_utc


def _resolver_municipio(usuario: Usuario, municipio_id: Optional[int]) -> Optional[int]:
    if pode_acesso_global(usuario):
        return int(municipio_id) if municipio_id is not None else None
    mid = getattr(usuario, "municipio_id", None)
    if mid is None:
        raise HTTPException(status_code=403, detail="Usuário sem município")
    return int(mid)


def _json_dumps(v: Any) -> str:
    try:
        return json.dumps(v or {}, ensure_ascii=False)
    except Exception:
        return "{}"


def _json_loads(s: str) -> Dict[str, Any]:
    try:
        v = json.loads(s or "{}")
        return v if isinstance(v, dict) else {}
    except Exception:
        return {}


def _due_now(rule: GestaoLoteRegra) -> bool:
    sch = rule.schedule()
    if not sch or not isinstance(sch, dict):
        return False
    if not rule.ativo:
        return False

    tz_name = str(sch.get("tz") or "America/Sao_Paulo")
    freq = str(sch.get("freq") or "").lower().strip()
    hhmm = str(sch.get("time") or "").strip()

    if freq not in ("daily", "weekly"):
        return False
    if not hhmm or ":" not in hhmm:
        return False

    try:
        hh, mm = hhmm.split(":", 1)
        hh_i = int(hh)
        mm_i = int(mm)
    except Exception:
        return False

    now_local = _to_local(_now_utc(), tz_name)
    if not now_local:
        return False

    # weekdays: 0=Mon..6=Sun
    wds = sch.get("weekdays")
    if isinstance(wds, list) and wds:
        try:
            wd = int(now_local.weekday())
            if wd not in {int(x) for x in wds}:
                return False
        except Exception:
            pass

    today_run_local = now_local.replace(hour=hh_i, minute=mm_i, second=0, microsecond=0)
    if now_local < today_run_local:
        return False

    last = rule.last_run_at
    last_local = _to_local(last.replace(tzinfo=timezone.utc) if (last and last.tzinfo is None) else last, tz_name)
    if last_local and last_local >= today_run_local:
        return False

    return True


def _filtrar_itens(items: List[Dict[str, Any]], filtros: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Filtros adicionais além da própria /gestao/fila."""
    tipo = filtros.get("tipo")
    if isinstance(tipo, str) and tipo.strip():
        t = tipo.strip().lower()
        items = [x for x in items if str(x.get("tipo") or "").lower() == t]
    elif isinstance(tipo, list) and tipo:
        ts = {str(x).lower() for x in tipo}
        items = [x for x in items if str(x.get("tipo") or "").lower() in ts]

    dias_min = filtros.get("dias_atraso_min")
    dias_max = filtros.get("dias_atraso_max")
    if isinstance(dias_min, int):
        items = [x for x in items if int(x.get("dias_em_atraso") or 0) >= int(dias_min)]
    if isinstance(dias_max, int):
        items = [x for x in items if int(x.get("dias_em_atraso") or 0) <= int(dias_max)]

    # pendente_de: se o item já vier com pendente_de, usa. Se não, tenta inferir (intermunicipal)
    pendente_de = filtros.get("pendente_de")
    if isinstance(pendente_de, str) and pendente_de.strip():
        pd = pendente_de.strip().lower()

        def _infer(it: Dict[str, Any]) -> str:
            got = str(it.get("pendente_de") or "").strip().lower()
            if got:
                return got
            # inferência mínima para intermunicipal
            if str(it.get("tipo") or "").strip().lower() == "encaminhamento_intermunicipal":
                st = str(it.get("etapa_atual") or it.get("status") or "").strip().lower()
                if st in ("contato", "aceito", "passagem"):
                    return "destino"
                if st in ("solicitado", "agendado", "contrarreferencia"):
                    return "origem"
            return ""

        items = [x for x in items if _infer(x) == pd]

    return items


# =========================
# Schemas
# =========================

class RegraCreate(BaseModel):
    nome: str
    descricao: Optional[str] = None
    acao: str = PField(..., description="cobrar|relatorio|oficio")
    municipio_id: Optional[int] = None
    filtros: Dict[str, Any] = PField(default_factory=dict)
    schedule: Dict[str, Any] = PField(default_factory=dict)
    ativo: bool = True


class RegraUpdate(BaseModel):
    nome: Optional[str] = None
    descricao: Optional[str] = None
    acao: Optional[str] = None
    municipio_id: Optional[int] = None
    filtros: Optional[Dict[str, Any]] = None
    schedule: Optional[Dict[str, Any]] = None
    ativo: Optional[bool] = None


class ExecucaoOut(BaseModel):
    id: int
    regra_id: Optional[int]
    acao: str
    status: str
    iniciado_em: datetime
    finalizado_em: Optional[datetime]
    total: int
    ok: int
    falhas: int
    resumo: Dict[str, Any]




# =========================
# Templates (receitas prontas)
# =========================

# Observação: os filtros aqui são compatíveis com /gestao/fila + _filtrar_itens.
# Você pode aplicar e depois ajustar via PATCH /gestao/automacoes/regras/{id}.

TEMPLATES: List[Dict[str, Any]] = [
    {
        "id": "rede_inter_destino_atraso_3d",
        "nome": "Cobrar REDE (Intermunicipal) atrasados > 3 dias (DESTINO)",
        "descricao": "Gera cobrança diária para encaminhamentos intermunicipais em atraso e pendentes do DESTINO.",
        "acao": "cobrar",
        "filtros": {
            "modulo": "rede",
            "tipo": ["encaminhamento_intermunicipal"],
            "somente_atrasos": True,
            "dias_atraso_min": 3,
            "pendente_de": "destino",
            "assunto": "Cobrança — Intermunicipal em atraso",
            "emissor": "smas",
        },
        "schedule": {"freq": "daily", "time": "09:00", "tz": "America/Sao_Paulo"},
        "ativo": True,
    },
    {
        "id": "cras_atrasos_diario",
        "nome": "Cobrar CRAS (atrasos/estagnação/validação/PIA)",
        "descricao": "Gera cobrança diária para itens do CRAS marcados como atraso (inclui estagnado, validação pendente e PIA faltando).",
        "acao": "cobrar",
        "filtros": {
            "modulo": "cras",
            "tipo": "caso",
            "somente_atrasos": True,
            "dias_atraso_min": 1,
            "assunto": "Cobrança — Pendências CRAS",
            "emissor": "smas",
        },
        "schedule": {"freq": "weekly", "weekdays": [0, 1, 2, 3, 4], "time": "09:00", "tz": "America/Sao_Paulo"},
        "ativo": True,
    },
    {
        "id": "relatorio_semanal_top20_criticos",
        "nome": "Relatório semanal — Top 20 mais críticos (atrasos)",
        "descricao": "Gera relatório técnico semanal com os 20 itens mais críticos (maior atraso) da Fila de Pendências.",
        "acao": "relatorio",
        "filtros": {
            "somente_atrasos": True,
            "dias_atraso_min": 1,
            "max_itens": 20,
            "assunto": "Relatório semanal — 20 mais críticos",
            "emissor": "smas",
        },
        "schedule": {"freq": "weekly", "weekdays": [0], "time": "08:30", "tz": "America/Sao_Paulo"},
        "ativo": True,
    },
]


class TemplateAplicarPayload(BaseModel):
    template_id: str
    municipio_id: Optional[int] = None
    nome: Optional[str] = None
    descricao: Optional[str] = None
    filtros: Optional[Dict[str, Any]] = None
    schedule: Optional[Dict[str, Any]] = None
    ativo: Optional[bool] = True


@router.get("/templates")
def listar_templates():
    return {"items": TEMPLATES}


@router.post("/templates/aplicar")
def aplicar_template(
    payload: TemplateAplicarPayload,
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    tpl = None
    tid = (payload.template_id or "").strip()
    for t in TEMPLATES:
        if str(t.get("id") or "") == tid:
            tpl = t
            break
    if not tpl:
        raise HTTPException(status_code=404, detail="Template não encontrado")

    acao = str(tpl.get("acao") or "").strip().lower()
    if acao not in ("cobrar", "relatorio", "oficio"):
        raise HTTPException(status_code=400, detail="Template inválido: ação")

    mid = _resolver_municipio(usuario, payload.municipio_id)

    nome = (payload.nome or tpl.get("nome") or "").strip() or f"Regra {tid}"
    descricao = (payload.descricao or tpl.get("descricao") or None)

    filtros = dict(tpl.get("filtros") or {})
    if payload.filtros:
        try:
            filtros.update(payload.filtros)
        except Exception:
            pass

    schedule = dict(tpl.get("schedule") or {})
    if payload.schedule:
        try:
            schedule.update(payload.schedule)
        except Exception:
            pass

    ativo = bool(payload.ativo) if payload.ativo is not None else bool(tpl.get("ativo") or True)

    # evita duplicar (mesmo nome no mesmo município)
    try:
        stmt = select(GestaoLoteRegra).where(GestaoLoteRegra.nome == nome)
        if mid is not None:
            stmt = stmt.where(GestaoLoteRegra.municipio_id == int(mid))
        else:
            stmt = stmt.where(GestaoLoteRegra.municipio_id.is_(None))  # type: ignore
        existing = session.exec(stmt).first()
        if existing:
            return {"ja_existia": True, "id": existing.id, "regra": {
                "id": existing.id,
                "municipio_id": existing.municipio_id,
                "nome": existing.nome,
                "descricao": existing.descricao,
                "acao": existing.acao,
                "ativo": existing.ativo,
                "filtros": existing.filtros(),
                "schedule": existing.schedule(),
                "last_run_at": existing.last_run_at,
                "last_run_status": existing.last_run_status,
            }}
    except Exception:
        pass

    r = GestaoLoteRegra(
        municipio_id=mid,
        nome=nome,
        descricao=descricao,
        acao=acao,
        filtros_json=_json_dumps(filtros),
        schedule_json=_json_dumps(schedule),
        ativo=ativo,
        criado_em=datetime.utcnow(),
        atualizado_em=datetime.utcnow(),
    )
    session.add(r)
    session.commit()
    session.refresh(r)

    return {"ja_existia": False, "id": r.id, "regra": {
        "id": r.id,
        "municipio_id": r.municipio_id,
        "nome": r.nome,
        "descricao": r.descricao,
        "acao": r.acao,
        "ativo": r.ativo,
        "filtros": r.filtros(),
        "schedule": r.schedule(),
        "last_run_at": r.last_run_at,
        "last_run_status": r.last_run_status,
    }}


@router.post("/templates/aplicar-padroes")
def aplicar_padroes(
    municipio_id: Optional[int] = Query(default=None, description="Opcional (gestor/admin). Se não, usa o município do usuário."),
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    mid = _resolver_municipio(usuario, municipio_id)
    criadas = []
    existentes = []

    for tpl in TEMPLATES:
        payload = TemplateAplicarPayload(
            template_id=str(tpl.get("id")),
            municipio_id=mid,
            ativo=bool(tpl.get("ativo") or True),
        )
        res = aplicar_template(payload, session=session, usuario=usuario)  # type: ignore
        if res.get("ja_existia"):
            existentes.append(res.get("id"))
        else:
            criadas.append(res.get("id"))

    return {"municipio_id": mid, "criadas": criadas, "existentes": existentes}


# =========================
# CRUD de Regras
# =========================

@router.post("/regras")
def criar_regra(
    payload: RegraCreate,
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    acao = (payload.acao or "").strip().lower()
    if acao not in ("cobrar", "relatorio", "oficio"):
        raise HTTPException(status_code=400, detail="acao inválida")

    mid = _resolver_municipio(usuario, payload.municipio_id)

    r = GestaoLoteRegra(
        municipio_id=mid,
        nome=payload.nome.strip(),
        descricao=(payload.descricao.strip() if payload.descricao else None),
        acao=acao,
        filtros_json=_json_dumps(payload.filtros),
        schedule_json=_json_dumps(payload.schedule),
        ativo=bool(payload.ativo),
        criado_em=datetime.utcnow(),
        atualizado_em=datetime.utcnow(),
    )
    session.add(r)
    session.commit()
    session.refresh(r)
    return {"id": r.id, "regra": r}


@router.get("/regras")
def listar_regras(
    municipio_id: Optional[int] = Query(default=None),
    ativo: Optional[bool] = Query(default=None),
    q: Optional[str] = Query(default=None),
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    mid = _resolver_municipio(usuario, municipio_id)
    stmt = select(GestaoLoteRegra)
    if mid is not None:
        stmt = stmt.where(GestaoLoteRegra.municipio_id == int(mid))
    if ativo is not None:
        stmt = stmt.where(GestaoLoteRegra.ativo == bool(ativo))
    if q:
        qq = f"%{q.strip().lower()}%"
        stmt = stmt.where(GestaoLoteRegra.nome.ilike(qq))  # type: ignore
    rows = list(session.exec(stmt.order_by(GestaoLoteRegra.id.desc())).all())
    return {
        "items": [
            {
                "id": r.id,
                "municipio_id": r.municipio_id,
                "nome": r.nome,
                "descricao": r.descricao,
                "acao": r.acao,
                "ativo": r.ativo,
                "filtros": r.filtros(),
                "schedule": r.schedule(),
                "last_run_at": r.last_run_at,
                "last_run_status": r.last_run_status,
            }
            for r in rows
        ]
    }


@router.patch("/regras/{regra_id}")
def atualizar_regra(
    regra_id: int,
    payload: RegraUpdate,
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    r = session.get(GestaoLoteRegra, int(regra_id))
    if not r:
        raise HTTPException(status_code=404, detail="Regra não encontrada")

    # escopo
    if not pode_acesso_global(usuario):
        if getattr(usuario, "municipio_id", None) is None or int(getattr(usuario, "municipio_id")) != int(r.municipio_id or 0):
            raise HTTPException(status_code=403, detail="Sem permissão")

    if payload.nome is not None:
        r.nome = payload.nome.strip()
    if payload.descricao is not None:
        r.descricao = payload.descricao.strip() if payload.descricao else None
    if payload.acao is not None:
        acao = payload.acao.strip().lower()
        if acao not in ("cobrar", "relatorio", "oficio"):
            raise HTTPException(status_code=400, detail="acao inválida")
        r.acao = acao
    if payload.ativo is not None:
        r.ativo = bool(payload.ativo)

    # municipio_id só para global
    if payload.municipio_id is not None:
        if not pode_acesso_global(usuario):
            raise HTTPException(status_code=403, detail="Somente gestor/admin pode alterar municipio_id")
        r.municipio_id = int(payload.municipio_id)

    if payload.filtros is not None:
        r.filtros_json = _json_dumps(payload.filtros)
    if payload.schedule is not None:
        r.schedule_json = _json_dumps(payload.schedule)

    r.atualizado_em = datetime.utcnow()
    session.add(r)
    session.commit()
    session.refresh(r)

    return {"id": r.id, "regra": r}


@router.get("/regras/{regra_id}/preview")
def preview_regra(
    regra_id: int,
    limit: int = Query(default=50, ge=1, le=200),
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    r = session.get(GestaoLoteRegra, int(regra_id))
    if not r:
        raise HTTPException(status_code=404, detail="Regra não encontrada")

    filtros = r.filtros()

    # Reusa /gestao/fila para seleção base
    try:
        from app.routers.gestao import gestao_fila as _gestao_fila  # type: ignore

        fila = _gestao_fila(
            municipio_id=r.municipio_id,
            unidade_id=filtros.get("unidade_id"),
            territorio=filtros.get("territorio"),
            dias_cadunico=int(filtros.get("dias_cadunico") or 30),
            dias_pia=int(filtros.get("dias_pia") or 15),
            janela_risco_horas=int(filtros.get("janela_risco_horas") or 24),
            modulo=filtros.get("modulo"),
            somente_atrasos=bool(filtros.get("somente_atrasos") or False),
            somente_em_risco=bool(filtros.get("somente_em_risco") or False),
            limit=500,
            offset=0,
            session=session,
            usuario=usuario,
        )
        items = list((fila or {}).get("items") or [])
        items = _filtrar_itens(items, filtros)
        max_it = filtros.get("max_itens")
        if isinstance(max_it, int) and max_it > 0:
            items = items[: int(max_it)]
        return {"total": len(items), "items": items[: int(limit)]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Falha ao gerar preview: {e}")


# =========================
# Execução
# =========================

def _executar_acao_em_lote(
    acao: str,
    items: List[Dict[str, Any]],
    request: Request,
    session: Session,
    usuario: Usuario,
    extra: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Executa cobrar/relatorio/oficio em lote usando as rotas de documentos."""
    extra = extra or {}

    # Import local para não quebrar startup se documentos não existir
    from app.routers.documentos import DocumentoGerar, gerar_documento  # type: ignore

    resultados: List[Dict[str, Any]] = []
    ok = falhas = 0

    # Para cobrança, tentamos usar o atalho de cobrança; se não suportar intermunicipal, cai em ofício padrão
    try:
        from app.routers.documentos import CobrancaDevolutivaAuto, gerar_cobranca_devolutiva  # type: ignore
    except Exception:  # pragma: no cover
        CobrancaDevolutivaAuto = None  # type: ignore
        gerar_cobranca_devolutiva = None  # type: ignore

    for it in items[:500]:
        try:
            ref = int(it.get("referencia_id") or 0)
            if ref <= 0:
                raise ValueError("referencia_id inválido")

            mod = str(it.get("modulo") or "").upper()
            tp = str(it.get("tipo") or "").lower()
            mid = it.get("municipio_id")

            if acao == "cobrar":
                if mod == "REDE" and tp in ("encaminhamento", "encaminhamento_intermunicipal") and gerar_cobranca_devolutiva is not None and CobrancaDevolutivaAuto is not None:
                    try:
                        out = gerar_cobranca_devolutiva(
                            CobrancaDevolutivaAuto(
                                encaminhamento_id=ref,
                                municipio_id=mid,
                                emissor=str(extra.get("emissor") or "smas"),
                                contato_retorno=extra.get("contato_retorno"),
                                salvar=True,
                                retornar_pdf=False,
                                usar_ia=bool(extra.get("usar_ia") or False),
                                ia_instructions=extra.get("ia_instructions"),
                                ia_model=extra.get("ia_model"),
                                ia_reasoning_effort=extra.get("ia_reasoning_effort"),
                            ),
                            request=request,
                            session=session,
                            usuario=usuario,
                        )
                        resultados.append({"ok": True, "item": it, "documento": out})
                        ok += 1
                        continue
                    except Exception:
                        # fallback para ofício padrão
                        pass

                # Fallback: ofício padrão cobrando retorno
                texto = (
                    f"Solicitamos devolutiva/atualização do item na Fila de Pendências:\n"
                    f"- Módulo: {mod}\n- Tipo: {tp}\n- Referência: #{ref}\n\n"
                    f"Se não for possível cumprir o prazo, favor justificar e indicar previsão."
                )
                out = gerar_documento(
                    DocumentoGerar(
                        municipio_id=mid,
                        tipo="oficio",
                        modelo="oficio_padrao",
                        assunto=str(extra.get("assunto") or "Cobrança de devolutiva"),
                        campos={
                            "texto": texto,
                            "assinante_nome": extra.get("assinante_nome"),
                            "assinante_cargo": extra.get("assinante_cargo"),
                        },
                        emissor=str(extra.get("emissor") or "smas"),
                        salvar=True,
                        retornar_pdf=False,
                    ),
                    request=request,
                    session=session,
                    usuario=usuario,
                )
                resultados.append({"ok": True, "item": it, "documento": out})
                ok += 1
                continue

            if acao == "relatorio":
                # modelo por módulo
                modelo = "relatorio_padrao"
                if mod == "CRAS":
                    modelo = "relatorio_tecnico_cras"
                elif mod == "CREAS":
                    modelo = "relatorio_tecnico_creas"
                elif mod == "POPRUA":
                    modelo = "relatorio_tecnico_poprua"

                assunto = str(extra.get("assunto") or "Relatório técnico")
                campos = {
                    "identificacao": f"{mod} · {tp} · ref #{ref}",
                    "descricao": "Relatório gerado automaticamente (Gestão).",
                    "assinante_nome": extra.get("assinante_nome"),
                    "assinante_cargo": extra.get("assinante_cargo"),
                }
                out = gerar_documento(
                    DocumentoGerar(
                        municipio_id=mid,
                        tipo="relatorio",
                        modelo=modelo,
                        assunto=assunto,
                        campos=campos,
                        emissor=str(extra.get("emissor") or "smas"),
                        salvar=True,
                        retornar_pdf=False,
                    ),
                    request=request,
                    session=session,
                    usuario=usuario,
                )
                resultados.append({"ok": True, "item": it, "documento": out})
                ok += 1
                continue

            if acao == "oficio":
                texto = (
                    f"Encaminhamos para ciência e providências referência do item na Fila de Pendências:\n"
                    f"- Módulo: {mod}\n- Tipo: {tp}\n- Referência: #{ref}\n\n"
                    f"Solicitamos registro de andamento no sistema."
                )
                out = gerar_documento(
                    DocumentoGerar(
                        municipio_id=mid,
                        tipo="oficio",
                        modelo="oficio_padrao",
                        assunto=str(extra.get("assunto") or "Ofício"),
                        campos={
                            "texto": texto,
                            "assinante_nome": extra.get("assinante_nome"),
                            "assinante_cargo": extra.get("assinante_cargo"),
                        },
                        emissor=str(extra.get("emissor") or "smas"),
                        salvar=True,
                        retornar_pdf=False,
                    ),
                    request=request,
                    session=session,
                    usuario=usuario,
                )
                resultados.append({"ok": True, "item": it, "documento": out})
                ok += 1
                continue

            raise ValueError("acao inválida")

        except Exception as e:
            falhas += 1
            resultados.append({"ok": False, "item": it, "erro": str(e)})

    return {"total": len(items), "ok": ok, "falhas": falhas, "resultados": resultados}


@router.post("/regras/{regra_id}/executar")
def executar_regra(
    regra_id: int,
    request: Request,
    dry_run: bool = Query(default=False, description="Se true, não gera documentos, apenas lista seleção"),
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    r = session.get(GestaoLoteRegra, int(regra_id))
    if not r:
        raise HTTPException(status_code=404, detail="Regra não encontrada")

    if not pode_acesso_global(usuario):
        if getattr(usuario, "municipio_id", None) is None or int(getattr(usuario, "municipio_id")) != int(r.municipio_id or 0):
            raise HTTPException(status_code=403, detail="Sem permissão")

    filtros = r.filtros()

    # Seleção
    try:
        from app.routers.gestao import gestao_fila as _gestao_fila  # type: ignore

        fila = _gestao_fila(
            municipio_id=r.municipio_id,
            unidade_id=filtros.get("unidade_id"),
            territorio=filtros.get("territorio"),
            dias_cadunico=int(filtros.get("dias_cadunico") or 30),
            dias_pia=int(filtros.get("dias_pia") or 15),
            janela_risco_horas=int(filtros.get("janela_risco_horas") or 24),
            modulo=filtros.get("modulo"),
            somente_atrasos=bool(filtros.get("somente_atrasos") or False),
            somente_em_risco=bool(filtros.get("somente_em_risco") or False),
            limit=500,
            offset=0,
            session=session,
            usuario=usuario,
        )
        items = list((fila or {}).get("items") or [])
        items = _filtrar_itens(items, filtros)
        max_it = filtros.get("max_itens")
        if isinstance(max_it, int) and max_it > 0:
            items = items[: int(max_it)]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Falha ao selecionar itens: {e}")

    if dry_run:
        return {"acao": r.acao, "total": len(items), "items": items[:200]}

    exec_row = GestaoLoteExecucao(
        regra_id=r.id,
        municipio_id=r.municipio_id,
        acao=r.acao,
        status="running",
        total=0,
        ok=0,
        falhas=0,
        criado_por_usuario_id=getattr(usuario, "id", None),
        iniciado_em=datetime.utcnow(),
    )
    session.add(exec_row)
    session.commit()
    session.refresh(exec_row)

    extra = {
        "emissor": filtros.get("emissor") or "smas",
        "assunto": filtros.get("assunto"),
        "contato_retorno": filtros.get("contato_retorno"),
        "assinante_nome": filtros.get("assinante_nome"),
        "assinante_cargo": filtros.get("assinante_cargo"),
        "usar_ia": bool(filtros.get("usar_ia") or False),
        "ia_instructions": filtros.get("ia_instructions"),
        "ia_model": filtros.get("ia_model"),
        "ia_reasoning_effort": filtros.get("ia_reasoning_effort"),
    }

    out = _executar_acao_em_lote(r.acao, items, request, session, usuario, extra=extra)

    exec_row.total = int(out.get("total") or 0)
    exec_row.ok = int(out.get("ok") or 0)
    exec_row.falhas = int(out.get("falhas") or 0)
    exec_row.finalizado_em = datetime.utcnow()

    if exec_row.falhas == 0:
        exec_row.status = "ok"
        r.last_run_status = "ok"
    elif exec_row.ok > 0:
        exec_row.status = "partial"
        r.last_run_status = "partial"
    else:
        exec_row.status = "error"
        r.last_run_status = "error"

    # guarda um resumo leve (não explode SQLite)
    resumo = {
        "acao": r.acao,
        "selecionados": exec_row.total,
        "ok": exec_row.ok,
        "falhas": exec_row.falhas,
        "amostra": out.get("resultados", [])[:20],
    }
    exec_row.set_resumo(resumo)

    r.last_run_at = datetime.utcnow()
    r.atualizado_em = datetime.utcnow()

    session.add(exec_row)
    session.add(r)
    session.commit()

    return {
        "execucao": {
            "id": exec_row.id,
            "regra_id": exec_row.regra_id,
            "acao": exec_row.acao,
            "status": exec_row.status,
            "total": exec_row.total,
            "ok": exec_row.ok,
            "falhas": exec_row.falhas,
            "iniciado_em": exec_row.iniciado_em,
            "finalizado_em": exec_row.finalizado_em,
            "resumo": exec_row.resumo(),
        }
    }


@router.post("/executar-devidas")
def executar_regras_devidas(
    request: Request,
    limite: int = Query(default=20, ge=1, le=100),
    dry_run: bool = Query(default=False),
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    """Executa todas as regras ativas que estão devidas agora.

    Use isso para agendamento externo (cron/job) sem precisar editar código.
    """
    if not pode_acesso_global(usuario):
        # por segurança: somente gestor/admin dispara varredura geral.
        raise HTTPException(status_code=403, detail="Somente gestor/admin pode executar regras devidas")

    regras = list(session.exec(select(GestaoLoteRegra).where(GestaoLoteRegra.ativo == True)).all())  # noqa: E712
    devidas = [r for r in regras if _due_now(r)]

    out: List[Dict[str, Any]] = []
    for r in devidas[: int(limite)]:
        if dry_run:
            out.append({"regra_id": r.id, "nome": r.nome, "acao": r.acao, "due": True})
        else:
            # executa como o usuário atual (gestor/admin)
            try:
                res = executar_regra(r.id, request, dry_run=False, session=session, usuario=usuario)  # type: ignore
                out.append({"regra_id": r.id, "nome": r.nome, "resultado": res.get("execucao")})
            except Exception as e:
                out.append({"regra_id": r.id, "nome": r.nome, "erro": str(e)})

    return {"total_devidas": len(devidas), "executadas": len(out), "items": out}


@router.get("/execucoes")
def listar_execucoes(
    regra_id: Optional[int] = Query(default=None),
    municipio_id: Optional[int] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    mid = _resolver_municipio(usuario, municipio_id)

    stmt = select(GestaoLoteExecucao)
    if regra_id is not None:
        stmt = stmt.where(GestaoLoteExecucao.regra_id == int(regra_id))
    if mid is not None:
        stmt = stmt.where(GestaoLoteExecucao.municipio_id == int(mid))

    rows = list(session.exec(stmt.order_by(GestaoLoteExecucao.id.desc()).offset(int(offset)).limit(int(limit))).all())

    return {
        "items": [
            {
                "id": x.id,
                "regra_id": x.regra_id,
                "acao": x.acao,
                "status": x.status,
                "iniciado_em": x.iniciado_em,
                "finalizado_em": x.finalizado_em,
                "total": x.total,
                "ok": x.ok,
                "falhas": x.falhas,
                "resumo": x.resumo(),
            }
            for x in rows
        ]
    }

# =========================
# SEED (criar regras padrão automaticamente)
# =========================

class SeedPayload(BaseModel):
    municipio_id: Optional[int] = None
    todos_municipios: bool = True
    # se true, tenta também criar regras "globais" (municipio_id=None) quando não houver municípios detectados
    permitir_global_fallback: bool = True


def seed_templates_padroes(
    session: Session,
    municipio_id: Optional[int] = None,
    todos_municipios: bool = True,
    permitir_global_fallback: bool = True,
) -> Dict[str, Any]:
    """Cria regras padrão (TEMPLATES) de forma idempotente + registra log.

    - Se municipio_id for informado: aplica só para ele.
    - Se todos_municipios=True: tenta aplicar para todos os municípios existentes na tabela municipio.
    - Se não conseguir listar municípios, pode cair para municipio_id=None (regra global), se permitir_global_fallback=True.

    Retorna:
      - criadas/existentes (ids de regras)
      - por_municipio (detalhes por município)
      - logs (ids de logs em gestao_lote_execucao com acao='seed')
    """

    started = datetime.utcnow()

    mids: List[Optional[int]] = []

    if municipio_id is not None:
        mids = [int(municipio_id)]
    elif todos_municipios:
        try:
            from app.models.municipio import Municipio  # type: ignore

            rows = session.exec(select(Municipio.id)).all()  # type: ignore
            mids = [int(x) for x in rows] if rows else []
        except Exception:
            mids = []
    else:
        mids = []

    if not mids and permitir_global_fallback:
        mids = [None]

    criadas_all: List[int] = []
    existentes_all: List[int] = []
    logs: List[int] = []

    por_municipio: Dict[str, Any] = {}

    for mid in mids:
        criadas: List[int] = []
        existentes: List[int] = []

        for tpl in TEMPLATES:
            nome = str(tpl.get("nome") or "").strip() or f"Regra {tpl.get('id')}"
            acao = str(tpl.get("acao") or "").strip().lower()
            if acao not in ("cobrar", "relatorio", "oficio"):
                continue

            # evita duplicar (mesmo nome no mesmo município)
            stmt = select(GestaoLoteRegra).where(GestaoLoteRegra.nome == nome)
            if mid is None:
                stmt = stmt.where(GestaoLoteRegra.municipio_id.is_(None))  # type: ignore
            else:
                stmt = stmt.where(GestaoLoteRegra.municipio_id == int(mid))
            existing = session.exec(stmt).first()
            if existing:
                existentes.append(int(existing.id or 0))
                continue

            filtros = dict(tpl.get("filtros") or {})
            schedule = dict(tpl.get("schedule") or {})
            ativo = bool(tpl.get("ativo") or True)

            r = GestaoLoteRegra(
                municipio_id=mid,
                nome=nome,
                descricao=(tpl.get("descricao") or None),
                acao=acao,
                filtros_json=_json_dumps(filtros),
                schedule_json=_json_dumps(schedule),
                ativo=ativo,
                criado_em=datetime.utcnow(),
                atualizado_em=datetime.utcnow(),
            )
            session.add(r)
            session.commit()
            session.refresh(r)
            criadas.append(int(r.id or 0))

        # agrega
        criadas_all.extend(criadas)
        existentes_all.extend(existentes)

        # registra log em gestao_lote_execucao (acao='seed')
        try:
            exec_log = GestaoLoteExecucao(
                regra_id=None,
                municipio_id=mid,
                acao="seed",
                iniciado_em=started,
                finalizado_em=datetime.utcnow(),
                status="ok",
                total=len(TEMPLATES),
                ok=len(criadas),
                falhas=0,
                criado_por_usuario_id=None,
            )
            exec_log.set_resumo(
                {
                    "municipio_id": mid,
                    "templates": [str(t.get("id")) for t in TEMPLATES],
                    "criadas": criadas,
                    "existentes": existentes,
                }
            )
            session.add(exec_log)
            session.commit()
            session.refresh(exec_log)
            if exec_log.id:
                logs.append(int(exec_log.id))
        except Exception:
            # se falhar log, não quebra seed
            pass

        key = str(mid) if mid is not None else "global"
        por_municipio[key] = {
            "municipio_id": mid,
            "criadas": criadas,
            "existentes": existentes,
        }

    return {
        "criadas": criadas_all,
        "existentes": existentes_all,
        "municipios": mids,
        "por_municipio": por_municipio,
        "logs": logs,
    }


@router.post("/seed")
def seed_regras_padroes(
    payload: SeedPayload,
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    """Cria as regras padrão via API (somente gestor/admin)."""
    if not pode_acesso_global(usuario):
        raise HTTPException(status_code=403, detail="Somente gestor/admin pode seedar regras padrão")

    out = seed_templates_padroes(
        session=session,
        municipio_id=payload.municipio_id,
        todos_municipios=bool(payload.todos_municipios),
        permitir_global_fallback=bool(payload.permitir_global_fallback),
    )
    return {"ok": True, **out}


@router.get("/seed/status")
def seed_status(
    municipio_id: Optional[int] = Query(default=None, description="Opcional (gestor/admin). Se não, usa o município do usuário."),
    incluir_todos: bool = Query(default=False, description="Se true e o usuário tiver acesso global, retorna status de todos os municípios."),
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    """Verifica se as regras padrão (templates) foram criadas e mostra o último seed.

    - Para usuários comuns: retorna apenas o próprio município.
    - Para gestor/admin: pode consultar outro município (municipio_id) ou todos (incluir_todos=true).
    """

    def _status_for_mid(mid: Optional[int]) -> Dict[str, Any]:
        # regras existentes por nome
        stmt = select(GestaoLoteRegra)
        if mid is None:
            stmt = stmt.where(GestaoLoteRegra.municipio_id.is_(None))  # type: ignore
        else:
            stmt = stmt.where(GestaoLoteRegra.municipio_id == int(mid))
        regras = list(session.exec(stmt).all())
        by_name = {r.nome: r for r in regras}

        faltando = []
        presentes = []
        for tpl in TEMPLATES:
            nome_tpl = str(tpl.get("nome") or "").strip()
            if not nome_tpl:
                continue
            if nome_tpl in by_name:
                r = by_name[nome_tpl]
                presentes.append({"template_id": tpl.get("id"), "regra_id": r.id, "ativo": r.ativo})
            else:
                faltando.append({"template_id": tpl.get("id"), "nome": nome_tpl})

        # último log de seed
        st = select(GestaoLoteExecucao).where(GestaoLoteExecucao.acao == "seed")
        if mid is None:
            st = st.where(GestaoLoteExecucao.municipio_id.is_(None))  # type: ignore
        else:
            st = st.where(GestaoLoteExecucao.municipio_id == int(mid))
        last = session.exec(st.order_by(GestaoLoteExecucao.id.desc())).first()

        last_out = None
        if last:
            tz = "America/Sao_Paulo"
            last_out = {
                "id": last.id,
                "status": last.status,
                "iniciado_em": last.iniciado_em,
                "finalizado_em": last.finalizado_em,
                "iniciado_em_local": _to_local(last.iniciado_em, tz),
                "finalizado_em_local": _to_local(last.finalizado_em, tz),
                "total": last.total,
                "ok": last.ok,
                "falhas": last.falhas,
                "resumo": last.resumo(),
            }

        return {
            "municipio_id": mid,
            "templates_total": len(TEMPLATES),
            "presentes": presentes,
            "faltando": faltando,
            "ok": len(faltando) == 0,
            "ultimo_seed": last_out,
            "regras_total": len(regras),
        }

    # Escopo
    if incluir_todos and pode_acesso_global(usuario):
        mids: List[Optional[int]] = []
        try:
            from app.models.municipio import Municipio  # type: ignore
            rows = session.exec(select(Municipio.id)).all()  # type: ignore
            mids = [int(x) for x in rows] if rows else []
        except Exception:
            mids = []
        if not mids:
            # fallback: apenas global
            return {"items": [_status_for_mid(None)]}
        return {"items": [_status_for_mid(mid) for mid in mids]}

    mid = _resolver_municipio(usuario, municipio_id)
    return {"item": _status_for_mid(mid)}


@router.get("/seed/logs")
def seed_logs(
    municipio_id: Optional[int] = Query(default=None, description="Opcional (gestor/admin). Se não, usa o município do usuário."),
    limit: int = Query(default=20, ge=1, le=200),
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    """Lista logs de seed (acao='seed') — útil para conferência em produção."""
    mid = _resolver_municipio(usuario, municipio_id)
    stmt = select(GestaoLoteExecucao).where(GestaoLoteExecucao.acao == "seed")
    if mid is None:
        stmt = stmt.where(GestaoLoteExecucao.municipio_id.is_(None))  # type: ignore
    else:
        stmt = stmt.where(GestaoLoteExecucao.municipio_id == int(mid))
    rows = list(session.exec(stmt.order_by(GestaoLoteExecucao.id.desc()).limit(int(limit))).all())
    return {
        "items": [
            {
                "id": x.id,
                "status": x.status,
                "iniciado_em": x.iniciado_em,
                "finalizado_em": x.finalizado_em,
                "total": x.total,
                "ok": x.ok,
                "falhas": x.falhas,
                "resumo": x.resumo(),
            }
            for x in rows
        ]
    }
