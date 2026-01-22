from __future__ import annotations

import json
import re
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field as PField

from app.core.auth import exigir_minimo_perfil, get_current_user, pode_acesso_global
from app.core.db import get_session
from app.models.usuario import Usuario
from app.services.ai_service import AIError, generate_text


router = APIRouter(prefix="/ia", tags=["ia"])


# =====================================================
# Utilitários (LGPD/minimização e parsing)
# =====================================================

_RE_EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
_RE_CPF = re.compile(r"\b\d{3}\.?(\d{3})\.?(\d{3})-?\d{2}\b")
_RE_DIGITS11 = re.compile(r"\b\d{11}\b")
_RE_PHONE = re.compile(r"\b\(?\d{2}\)?\s?\d{4,5}-?\d{4}\b")


def _redact(text: Optional[str]) -> str:
    """Redação simples: reduz risco de vazar identificadores.

    Não é anonimização perfeita, mas remove padrões comuns.
    """
    t = (text or "").strip()
    if not t:
        return ""
    t = _RE_EMAIL.sub("<EMAIL>", t)
    t = _RE_CPF.sub("<CPF>", t)
    t = _RE_PHONE.sub("<TEL>", t)
    t = _RE_DIGITS11.sub("<ID>", t)
    return t


def _extract_json_object(text: str) -> Dict[str, Any]:
    """Extrai um objeto JSON da resposta.

    Aceita:
      - ```json ... ```
      - JSON solto no meio do texto
    """
    t = (text or "").strip()
    if not t:
        raise ValueError("Resposta vazia")

    # remove fences
    if t.startswith("```"):
        t = re.sub(r"^```[a-zA-Z0-9_\-]*\n?", "", t)
        t = re.sub(r"\n?```$", "", t).strip()

    # recorta primeiro objeto
    i = t.find("{")
    j = t.rfind("}")
    if i != -1 and j != -1 and j > i:
        t = t[i : j + 1]

    data = json.loads(t)
    if not isinstance(data, dict):
        raise ValueError("JSON não é objeto")
    return data


def _get_modelo(chave_ou_titulo: str):
    """Busca modelo na biblioteca SUAS (documentos_modelos)."""
    from app.services.documentos_modelos import get_modelo  # import local (evita falhas no import do router)

    return get_modelo(chave_ou_titulo)


def _pick_modelo(modelo: Optional[str], tipo: Optional[str]):
    """Resolve modelo (biblioteca) pelo `modelo` ou pelo `tipo`."""
    if modelo:
        m = _get_modelo(modelo)
        if not m:
            raise HTTPException(status_code=400, detail=f"Modelo desconhecido: {modelo}")
        return m

    t = (tipo or "oficio").strip().lower()
    base_key = {
        "oficio": "oficio_padrao",
        "memorando": "memorando_padrao",
        "relatorio": "relatorio_padrao",
        "declaracao": "declaracao_padrao",
    }.get(t, "oficio_padrao")

    m = _get_modelo(base_key)
    if not m:
        raise HTTPException(status_code=500, detail="Biblioteca de modelos indisponível")
    return m


# =====================================================
# Endpoints base (3.3.0)
# =====================================================


class AITextRequest(BaseModel):
    input: str = PField(..., min_length=1)
    instructions: Optional[str] = None
    model: Optional[str] = None
    reasoning_effort: Optional[str] = PField(
        default=None,
        description="low|medium|high|xhigh (depende do modelo).",
    )
    return_raw: bool = False


@router.get("/health", dependencies=[Depends(exigir_minimo_perfil("operador"))])
def ia_health():
    """Health/config mínima (não expõe secrets).

    Retorna informações úteis para debug SEM vazar chave:
      - de qual variável veio (POPRUA_... ou OPENAI_API_KEY)
      - tamanho/prefixo/last4
      - se parece uma chave válida (heurística)
    """
    import os

    def looks_like_key(v: str) -> bool:
        vv = (v or "").strip()
        if not vv:
            return False
        if not vv.startswith("sk-"):
            return False
        if "..." in vv:
            return False
        if len(vv) < 25:
            return False
        return True

    provider = os.getenv("POPRUA_AI_PROVIDER", "openai")
    model = os.getenv("POPRUA_OPENAI_MODEL", "gpt-5.2")
    base_url = os.getenv("POPRUA_OPENAI_BASE_URL", "https://api.openai.com/v1")

    k_poprua = os.getenv("POPRUA_OPENAI_API_KEY") or ""
    k_openai = os.getenv("OPENAI_API_KEY") or ""

    key_source = None
    key = ""
    if looks_like_key(k_openai):
        key_source = "OPENAI_API_KEY"
        key = k_openai
    elif looks_like_key(k_poprua):
        key_source = "POPRUA_OPENAI_API_KEY"
        key = k_poprua
    else:
        # fallback: mantém compatibilidade
        key_source = "POPRUA_OPENAI_API_KEY" if k_poprua else ("OPENAI_API_KEY" if k_openai else None)
        key = k_poprua or k_openai

    return {
        "provider": provider,
        "model": model,
        "base_url": base_url,
        "has_key": bool(key),
        "has_key_valid": looks_like_key(key),
        "key_source": key_source,
        "key_len": len(key),
        "key_prefix": key[:3] if key else "",
        "key_last4": key[-4:] if key else "",
    }


@router.post("/text", dependencies=[Depends(exigir_minimo_perfil("operador"))])
def ia_text(
    payload: AITextRequest,
    usuario: Usuario = Depends(get_current_user),
):
    """Gera texto via IA (Responses API).

    Observação: retorna apenas texto por padrão. `return_raw=true` adiciona metadados da resposta.
    """
    try:
        res = generate_text(
            input_text=payload.input,
            instructions=payload.instructions,
            model=payload.model,
            reasoning_effort=payload.reasoning_effort,
            user_id=getattr(usuario, "id", None),
            municipio_id=getattr(usuario, "municipio_id", None),
            return_raw=payload.return_raw,
        )
    except AIError as e:
        raise HTTPException(status_code=400, detail=str(e))

    out: Dict[str, Any] = {"text": res.text, "provider": res.provider, "model": res.model}
    if payload.return_raw and res.raw is not None:
        out["raw"] = res.raw
    return out


# =====================================================
# 3.3.4 — Rascunhos e Resumos (IA)
# =====================================================


class IARascunhoDocumentoRequest(BaseModel):
    """Gera um rascunho (campos) para um modelo de documento."""

    modelo: Optional[str] = PField(
        default=None,
        description="Chave/título do modelo (ex.: oficio_encaminhamento, oficio_padrao, relatorio_visita_domiciliar).",
    )
    tipo: Optional[str] = PField(
        default=None,
        description="Fallback se modelo não for informado (oficio|memorando|relatorio|declaracao).",
    )
    contexto: Optional[str] = PField(default=None, description="Contexto do pedido/caso (texto livre).")

    destinatario_nome: Optional[str] = None
    destinatario_cargo: Optional[str] = None
    destinatario_orgao: Optional[str] = None

    preferencias: Optional[str] = PField(default=None, description="Preferências de estilo (curto, objetivo, etc.).")

    # overrides IA
    instructions: Optional[str] = None
    model: Optional[str] = None
    reasoning_effort: Optional[str] = None


@router.post("/rascunho/documento", dependencies=[Depends(exigir_minimo_perfil("operador"))])
def ia_rascunho_documento(
    payload: IARascunhoDocumentoRequest,
    usuario: Usuario = Depends(get_current_user),
):
    """Gera rascunho (campos) compatível com /documentos/gerar."""

    modelo = _pick_modelo(payload.modelo, payload.tipo)
    campos_all = list(dict.fromkeys([*(getattr(modelo, "campos_obrigatorios", []) or []), *(getattr(modelo, "campos_opcionais", []) or [])]))

    contexto = _redact(payload.contexto)
    prefs = (payload.preferencias or "").strip()

    instr = payload.instructions or "Escreva formal, padrão prefeitura. Responda SOMENTE com JSON válido."  # noqa

    campos_txt = ", ".join(campos_all) if campos_all else "(nenhum)"

    prompt = (
        f"Você irá preencher CAMPOS para um documento oficial do tipo {getattr(modelo, 'tipo', 'oficio').upper()} (modelo: {getattr(modelo, 'key', 'modelo')}).\n\n"
        "Retorne APENAS um JSON válido no formato:\n"
        "{\n"
        '  "assunto": "...",\n'
        '  "destinatario_nome": "...",\n'
        '  "destinatario_cargo": "...",\n'
        '  "destinatario_orgao": "...",\n'
        '  "campos": {\n'
        '    "<campo>": "<valor>"\n'
        "  }\n"
        "}\n\n"
        "Regras:\n"
        "- Linguagem formal e objetiva.\n"
        "- Não inclua dados pessoais sensíveis; use placeholders (<NOME>, <CPF>, <ENDERECO>) quando necessário.\n"
        f"- Preencha somente estas chaves em 'campos': {campos_txt}.\n\n"
        "Contexto (redigido):\n"
        f"{contexto or '(vazio)'}\n\n"
        + (f"Preferências: {prefs}\n\n" if prefs else "")
        + "Se faltar informação para algum campo obrigatório, use placeholder <CAMPO>."
    )

    # IA é opcional: se não estiver configurada (ou a chave estiver inválida),
    # devolvemos um rascunho determinístico para não travar o fluxo de documentos.
    res = None
    data: Dict[str, Any] = {}
    provider = "fallback"
    model_used = "fallback"
    warnings: list[str] = []

    try:
        res = generate_text(
            input_text=prompt,
            instructions=instr,
            model=payload.model,
            reasoning_effort=payload.reasoning_effort,
            user_id=getattr(usuario, "id", None),
            municipio_id=getattr(usuario, "municipio_id", None),
        )
        data = _extract_json_object(res.text)
        provider = res.provider
        model_used = res.model
    except AIError as e:
        # fallback (sem IA)
        warnings.append(f"IA indisponível: {e}")
        data = {
            "assunto": getattr(modelo, "assunto_padrao", None) or "",
            "destinatario_nome": payload.destinatario_nome or "",
            "destinatario_cargo": payload.destinatario_cargo or "",
            "destinatario_orgao": payload.destinatario_orgao or "",
            "campos": {},
        }
    except Exception as e:
        warnings.append(f"IA indisponível: {e}")
        data = {
            "assunto": getattr(modelo, "assunto_padrao", None) or "",
            "destinatario_nome": payload.destinatario_nome or "",
            "destinatario_cargo": payload.destinatario_cargo or "",
            "destinatario_orgao": payload.destinatario_orgao or "",
            "campos": {},
        }

    campos_in = data.get("campos") if isinstance(data, dict) else None
    if not isinstance(campos_in, dict):
        campos_in = {}

    # filtra campos
    campos_out: Dict[str, Any] = {}
    for k in campos_all:
        if k in campos_in and isinstance(campos_in.get(k), (str, int, float)):
            v = str(campos_in.get(k)).strip()
            if v:
                campos_out[k] = v

    missing = [k for k in (getattr(modelo, "campos_obrigatorios", []) or []) if k not in campos_out]
    for k in missing:
        campos_out[k] = f"<{k}>"

    # fallback inteligente: quando a IA não está disponível, preenche alguns campos comuns
    # com o contexto redigido para não gerar documentos "vazios".
    if contexto:
        if "texto" in campos_all and "texto" not in campos_out:
            campos_out["texto"] = contexto
        if "contexto" in campos_all and "contexto" not in campos_out:
            campos_out["contexto"] = contexto
        if "descricao" in campos_all and "descricao" not in campos_out:
            campos_out["descricao"] = contexto
        if "encaminhamentos" in campos_all and "encaminhamentos" not in campos_out:
            campos_out["encaminhamentos"] = "Solicita-se providências e registro de retorno no sistema, com justificativa e previsão em caso de impossibilidade no prazo."
        if "motivo" in campos_all and "motivo" not in campos_out:
            campos_out["motivo"] = contexto
        if "solicitacao" in campos_all and "solicitacao" not in campos_out:
            campos_out["solicitacao"] = "Solicita-se providências e registro de retorno no sistema."

    assunto = (data.get("assunto") if isinstance(data, dict) else None) or getattr(modelo, "assunto_padrao", "") or ""

    out = {
        "tipo": getattr(modelo, "tipo", "oficio"),
        "modelo": getattr(modelo, "key", None),
        "assunto": (assunto or "").strip(),
        "destinatario_nome": payload.destinatario_nome or data.get("destinatario_nome"),
        "destinatario_cargo": payload.destinatario_cargo or data.get("destinatario_cargo"),
        "destinatario_orgao": payload.destinatario_orgao or data.get("destinatario_orgao"),
        "campos": campos_out,
        "provider": provider,
        "model": model_used,
        "warnings": (
            ([f"Campos obrigatórios preenchidos com placeholder: {', '.join(missing)}"] if missing else [])
            + warnings
        ),
    }
    return out


class IARascunhoEncaminhamentoRequest(BaseModel):
    encaminhamento_id: int
    municipio_id: Optional[int] = PField(default=None, description="Opcional (admin): força município.")
    modelo: str = PField(default="oficio_encaminhamento", description="Modelo a usar (ex.: oficio_encaminhamento).")
    emissor: str = PField(default="cras", description="Emissor/série (cras|smas|creas...).")
    prazo: Optional[str] = None
    contato_retorno: Optional[str] = None
    preferencias: Optional[str] = None

    # overrides IA
    instructions: Optional[str] = None
    model: Optional[str] = None
    reasoning_effort: Optional[str] = None


@router.post("/rascunho/encaminhamento", dependencies=[Depends(exigir_minimo_perfil("operador"))])
def ia_rascunho_encaminhamento(
    payload: IARascunhoEncaminhamentoRequest,
    session=Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    """Gera um rascunho de documento (campos) a partir de um encaminhamento CRAS.

    Retorna `documento_payload` pronto para enviar em /documentos/gerar.
    """

    # imports locais (não quebram a inclusão do router se algo faltar)
    from sqlmodel import select
    from app.models.cras_encaminhamento import CrasEncaminhamento, CrasEncaminhamentoEvento

    enc = session.get(CrasEncaminhamento, payload.encaminhamento_id)
    if not enc:
        raise HTTPException(status_code=404, detail="Encaminhamento não encontrado")

    if pode_acesso_global(usuario):
        mid = int(payload.municipio_id or getattr(enc, "municipio_id", 0) or 0)
        if not mid:
            raise HTTPException(status_code=400, detail="municipio_id é obrigatório para acesso global")
    else:
        mid = int(getattr(usuario, "municipio_id", 0) or 0)
        if not mid or int(getattr(enc, "municipio_id", 0) or 0) != mid:
            raise HTTPException(status_code=403, detail="Sem permissão para esse município")

    modelo = _pick_modelo(payload.modelo, "oficio")

    destino_tipo = (getattr(enc, "destino_tipo", "") or "").strip()
    destino_nome = (getattr(enc, "destino_nome", "") or "").strip()
    status_atual = (getattr(enc, "status", "") or "").strip()

    prazo_default = payload.prazo or f"{getattr(enc, 'prazo_devolutiva_dias', 7)} dias"

    # timeline (últimos eventos)
    eventos = session.exec(
        select(CrasEncaminhamentoEvento)
        .where(CrasEncaminhamentoEvento.encaminhamento_id == payload.encaminhamento_id)
        .order_by(CrasEncaminhamentoEvento.em)
    ).all()
    eventos = list(eventos or [])
    tl_lines = []
    for ev in eventos[-8:]:
        try:
            dt = ev.em.strftime("%d/%m/%Y %H:%M") if getattr(ev, "em", None) else ""
        except Exception:
            dt = ""
        det = _redact(getattr(ev, "detalhe", None))
        tl_lines.append(f"- {dt} {getattr(ev, 'tipo', '')}: {det}".strip())
    timeline_txt = "\n".join([l for l in tl_lines if l and l != "-"])

    motivo_original = _redact(getattr(enc, "motivo", None))
    obs_original = _redact(getattr(enc, "observacao_operacional", None))
    prefs = (payload.preferencias or "").strip()

    instr = payload.instructions or "Escreva formal, padrão prefeitura. Responda SOMENTE com JSON válido."  # noqa

    prompt = (
        f"Você irá redigir um rascunho para o modelo {getattr(modelo, 'key', 'modelo')} ({getattr(modelo, 'titulo', 'documento')}).\n\n"
        "Retorne APENAS um JSON válido com as chaves:\n"
        "{\n"
        '  "assunto": "...",\n'
        '  "motivo": "...",\n'
        '  "solicitacao": "...",\n'
        '  "prazo": "...",\n'
        '  "contato_retorno": "..."\n'
        "}\n\n"
        "Regras:\n"
        "- Linguagem formal e objetiva, padrão prefeitura.\n"
        "- Não inclua nomes/CPF/endereços/dados sensíveis; use placeholders quando necessário.\n"
        f"- Use prazo sugerido: {prazo_default}.\n\n"
        "Contexto do encaminhamento (redigido):\n"
        f"- ID: {payload.encaminhamento_id}\n"
        f"- Destino: {destino_tipo} — {destino_nome}\n"
        f"- Status atual: {status_atual}\n"
        f"- Motivo original: {motivo_original or '(vazio)'}\n"
        + (f"- Observação operacional: {obs_original}\n" if obs_original else "")
        + (f"- Linha do tempo:\n{timeline_txt}\n" if timeline_txt else "")
        + (f"\nPreferências: {prefs}\n" if prefs else "")
    )

    try:
        res = generate_text(
            input_text=prompt,
            instructions=instr,
            model=payload.model,
            reasoning_effort=payload.reasoning_effort,
            user_id=getattr(usuario, "id", None),
            municipio_id=mid,
        )
        data = _extract_json_object(res.text)
    except AIError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Falha ao interpretar JSON da IA: {e}")

    assunto = (data.get("assunto") or getattr(modelo, "assunto_padrao", "") or "").strip()
    motivo = (data.get("motivo") or "").strip() or "<motivo>"
    solicitacao = (data.get("solicitacao") or "").strip() or "<solicitacao>"
    prazo = (payload.prazo or data.get("prazo") or prazo_default or "").strip()
    contato = (payload.contato_retorno or data.get("contato_retorno") or "").strip()

    campos: Dict[str, Any] = {
        "referencia": f"Encaminhamento #{payload.encaminhamento_id} — {destino_nome}" if destino_nome else f"Encaminhamento #{payload.encaminhamento_id}",
        "motivo": motivo,
        "solicitacao": solicitacao,
    }
    if prazo:
        campos["prazo"] = prazo
    if contato:
        campos["contato_retorno"] = contato

    documento_payload = {
        "municipio_id": mid,
        "tipo": getattr(modelo, "tipo", "oficio"),
        "modelo": getattr(modelo, "key", None),
        "assunto": assunto,
        "destinatario_nome": destino_nome or "Destinatário",
        "destinatario_cargo": "Coordenação",
        "destinatario_orgao": (destino_tipo.upper() if destino_tipo else None),
        "campos": campos,
        "emissor": payload.emissor,
        "salvar": False,
    }

    return {
        "encaminhamento_id": payload.encaminhamento_id,
        "documento_payload": documento_payload,
        "provider": res.provider,
        "model": res.model,
    }


class IAResumoEncaminhamentoRequest(BaseModel):
    encaminhamento_id: int
    municipio_id: Optional[int] = None
    tamanho: str = PField(default="curto", description="curto|medio")

    # overrides IA
    instructions: Optional[str] = None
    model: Optional[str] = None
    reasoning_effort: Optional[str] = None


@router.post("/resumo/encaminhamento", dependencies=[Depends(exigir_minimo_perfil("operador"))])
def ia_resumo_encaminhamento(
    payload: IAResumoEncaminhamentoRequest,
    session=Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    """Resumo do encaminhamento (gestão) sem dados pessoais."""

    from sqlmodel import select
    from app.models.cras_encaminhamento import CrasEncaminhamento, CrasEncaminhamentoEvento

    enc = session.get(CrasEncaminhamento, payload.encaminhamento_id)
    if not enc:
        raise HTTPException(status_code=404, detail="Encaminhamento não encontrado")

    if pode_acesso_global(usuario):
        mid = int(payload.municipio_id or getattr(enc, "municipio_id", 0) or 0)
        if not mid:
            raise HTTPException(status_code=400, detail="municipio_id é obrigatório para acesso global")
    else:
        mid = int(getattr(usuario, "municipio_id", 0) or 0)
        if not mid or int(getattr(enc, "municipio_id", 0) or 0) != mid:
            raise HTTPException(status_code=403, detail="Sem permissão para esse município")

    destino_tipo = (getattr(enc, "destino_tipo", "") or "").strip()
    destino_nome = (getattr(enc, "destino_nome", "") or "").strip()
    status_atual = (getattr(enc, "status", "") or "").strip()
    prazo_ref = f"{getattr(enc, 'prazo_devolutiva_dias', 7)} dias"

    eventos = session.exec(
        select(CrasEncaminhamentoEvento)
        .where(CrasEncaminhamentoEvento.encaminhamento_id == payload.encaminhamento_id)
        .order_by(CrasEncaminhamentoEvento.em)
    ).all()
    eventos = list(eventos or [])

    tl_lines = []
    for ev in eventos[-10:]:
        try:
            dt = ev.em.strftime("%d/%m/%Y %H:%M") if getattr(ev, "em", None) else ""
        except Exception:
            dt = ""
        det = _redact(getattr(ev, "detalhe", None))
        tl_lines.append(f"- {dt} {getattr(ev, 'tipo', '')}: {det}".strip())
    timeline_txt = "\n".join([l for l in tl_lines if l and l != "-"])

    tamanho = (payload.tamanho or "curto").strip().lower()
    if tamanho not in ("curto", "medio"):
        tamanho = "curto"

    instr = payload.instructions or "Resuma de forma técnica, padrão gestão pública, sem dados pessoais."  # noqa
    prompt = (
        "Resuma o encaminhamento do SUAS para fins de gestão, sem citar dados pessoais.\n"
        f"Tamanho: {tamanho}.\n\n"
        f"ID: {payload.encaminhamento_id}\n"
        f"Destino: {destino_tipo} — {destino_nome}\n"
        f"Status: {status_atual}\n"
        f"Prazo (referência): {prazo_ref}\n\n"
        + (f"Linha do tempo (redigida):\n{timeline_txt}\n\n" if timeline_txt else "")
        + "Formato de saída:\n- 3 a 6 tópicos curtos (bullet points).\n"
    )

    try:
        res = generate_text(
            input_text=prompt,
            instructions=instr,
            model=payload.model,
            reasoning_effort=payload.reasoning_effort,
            user_id=getattr(usuario, "id", None),
            municipio_id=mid,
        )
    except AIError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {
        "encaminhamento_id": payload.encaminhamento_id,
        "text": (res.text or "").strip(),
        "provider": res.provider,
        "model": res.model,
    }
