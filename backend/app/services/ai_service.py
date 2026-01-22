from __future__ import annotations

import hashlib
import json
import os
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple

try:
    import requests  # type: ignore
except Exception:  # pragma: no cover
    requests = None  # type: ignore


@dataclass
class AIResult:
    text: str
    raw: Optional[Dict[str, Any]] = None
    provider: str = "none"
    model: Optional[str] = None


class AIError(RuntimeError):
    pass


def _env(*keys: str, default: str = "") -> str:
    for k in keys:
        v = os.getenv(k)
        if v:
            return v
    return default


def _looks_like_openai_key(v: str) -> bool:
    vv = (v or "").strip()
    if not vv:
        return False
    # OpenAI API keys começam com "sk-" (inclui "sk-proj-")
    if not vv.startswith("sk-"):
        return False
    # evita placeholders comuns
    if "..." in vv:
        return False
    # chaves reais tendem a ser longas; protege contra valores muito curtos
    if len(vv) < 25:
        return False
    return True


def _should_retry_without_reasoning_param(msg: str) -> bool:
    """Detecta erro de parâmetro 'reasoning' não suportado.

    Alguns modelos (ex.: gpt-4) não aceitam `reasoning.effort`. Nesses casos, tentamos novamente sem
    enviar o bloco `reasoning` (mantendo o mesmo modelo/endpoint).
    """
    m = (msg or "").lower()
    if not m:
        return False
    if "reasoning.effort" in m and ("not supported" in m or "unsupported" in m):
        return True
    if "unsupported parameter" in m and "reasoning" in m:
        return True
    if "unknown parameter" in m and "reasoning" in m:
        return True
    if "not supported" in m and "reasoning" in m:
        return True
    return False


def _audit_log(event: Dict[str, Any]) -> None:
    """Auditoria mínima (LGPD): salva apenas metadados + hashes (sem conteúdo completo)."""
    try:
        base = _env("POPRUA_AI_AUDIT_DIR", default="storage/ai_audit")
        os.makedirs(base, exist_ok=True)
        day = datetime.now(timezone.utc).strftime("%Y%m%d")
        path = os.path.join(base, f"audit_{day}.jsonl")
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")
    except Exception:
        # não pode travar o sistema por log
        pass


def _extract_output_text(resp: Dict[str, Any]) -> str:
    """Extrai texto do Responses API.

    Nota: não assume output[0].content[0].text. Varre output e agrega output_text.
    """
    if isinstance(resp, dict) and isinstance(resp.get("output_text"), str) and resp["output_text"].strip():
        return resp["output_text"].strip()

    out = resp.get("output")
    texts = []
    if isinstance(out, list):
        for item in out:
            if not isinstance(item, dict):
                continue
            content = item.get("content")
            if isinstance(content, list):
                for c in content:
                    if not isinstance(c, dict):
                        continue
                    if c.get("type") == "output_text" and isinstance(c.get("text"), str):
                        texts.append(c["text"])
    return "\n".join([t for t in texts if t]).strip()


def openai_responses_generate(
    input_text: str,
    instructions: Optional[str] = None,
    model: Optional[str] = None,
    reasoning_effort: Optional[str] = None,
    timeout_s: int = 40,
    return_raw: bool = False,
) -> AIResult:
    """Gera texto usando o OpenAI Responses API.

    Requer `OPENAI_API_KEY` (ou `POPRUA_OPENAI_API_KEY`) no ambiente.
    """
    if requests is None:
        raise AIError("Dependência 'requests' não disponível no ambiente.")

    api_key_poprua = _env("POPRUA_OPENAI_API_KEY")
    api_key_openai = _env("OPENAI_API_KEY")

    # Preferência: usa OPENAI_API_KEY (padrão) e cai para POPRUA_OPENAI_API_KEY.
    # (Isso evita ficar preso em uma chave POPRUA antiga/errada quando o usuário já exportou OPENAI_API_KEY.)
    candidates: list[tuple[str, str]] = []
    if _looks_like_openai_key(api_key_openai):
        candidates.append(("OPENAI_API_KEY", api_key_openai))
    if _looks_like_openai_key(api_key_poprua) and api_key_poprua != api_key_openai:
        candidates.append(("POPRUA_OPENAI_API_KEY", api_key_poprua))

    # Compat: se nada "parece" válido, tenta o que tiver (pode ajudar em ambientes legados)
    if not candidates:
        if api_key_openai:
            candidates.append(("OPENAI_API_KEY", api_key_openai))
        if api_key_poprua and api_key_poprua != api_key_openai:
            candidates.append(("POPRUA_OPENAI_API_KEY", api_key_poprua))

    if not candidates:
        raise AIError("OPENAI_API_KEY não configurado (use OPENAI_API_KEY ou POPRUA_OPENAI_API_KEY).")

    base_url = _env("POPRUA_OPENAI_BASE_URL", default="https://api.openai.com/v1").rstrip("/")
    model_name = model or _env("POPRUA_OPENAI_MODEL", default="gpt-5.2")
    effort = reasoning_effort or _env("POPRUA_OPENAI_REASONING_EFFORT", default="")

    body: Dict[str, Any] = {"model": model_name, "input": input_text}
    if instructions:
        body["instructions"] = instructions
    if effort:
        body["reasoning"] = {"effort": effort}

    url = f"{base_url}/responses"

    used_key_source = None
    last_401_msg = None

    # Alguns modelos não suportam `reasoning.effort`. Se der 400 por causa disso, removemos o bloco
    # `reasoning` e tentamos novamente uma vez (mantendo o mesmo modelo).
    for key_source, api_key in candidates:
        retried_without_reasoning = False

        while True:
            t0 = time.time()
            r = requests.post(
                url,
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json=body,
                timeout=timeout_s,
            )
            dt_ms = int((time.time() - t0) * 1000)

            try:
                data = r.json()
            except Exception:
                data = {"error": {"message": r.text, "status_code": r.status_code}}

            msg = ""
            if isinstance(data, dict):
                msg = (data.get("error") or {}).get("message") or data.get("message") or r.text
            else:
                msg = r.text

            # Retry sem reasoning se o modelo não suporta (ex.: gpt-4)
            if (
                r.status_code == 400
                and (not retried_without_reasoning)
                and isinstance(body, dict)
                and body.get("reasoning") is not None
                and _should_retry_without_reasoning_param(msg)
            ):
                body.pop("reasoning", None)
                retried_without_reasoning = True
                continue

            # Se a 1ª chave falhar por 401 e existir outra candidata, tentamos a próxima.
            if r.status_code == 401 and len(candidates) > 1:
                last_401_msg = msg
                break

            if r.status_code >= 400:
                raise AIError(f"OpenAI error ({r.status_code}): {msg}")

            used_key_source = key_source
            break

        if used_key_source:
            break
    else:
        # Todas as tentativas falharam (provavelmente 401 em todas).
        raise AIError(f"OpenAI error (401): {last_401_msg or 'Incorrect API key provided.'}")

    # opcional: inclui a origem da chave no raw para debug (sem expor segredo)
    if return_raw and isinstance(data, dict) and used_key_source:
        data["_key_source"] = used_key_source

    text = _extract_output_text(data) if isinstance(data, dict) else ""
    return AIResult(
        text=text,
        raw=data if (return_raw and isinstance(data, dict)) else None,
        provider="openai",
        model=model_name,
    )


def generate_text(
    input_text: str,
    instructions: Optional[str] = None,
    model: Optional[str] = None,
    reasoning_effort: Optional[str] = None,
    user_id: Optional[int] = None,
    municipio_id: Optional[int] = None,
    return_raw: bool = False,
) -> AIResult:
    provider = _env("POPRUA_AI_PROVIDER", default="openai").lower().strip()
    if provider in ("", "openai"):
        res = openai_responses_generate(
            input_text=input_text,
            instructions=instructions,
            model=model,
            reasoning_effort=reasoning_effort,
            return_raw=return_raw,
        )
    else:
        raise AIError(f"Provider não suportado: {provider}")

    # auditoria: hashes e metadados
    try:
        inp_hash = hashlib.sha256(input_text.encode("utf-8")).hexdigest()
        out_hash = hashlib.sha256((res.text or "").encode("utf-8")).hexdigest()
        _audit_log(
            {
                "ts": datetime.now(timezone.utc).isoformat(),
                "provider": res.provider,
                "model": res.model,
                "municipio_id": municipio_id,
                "user_id": user_id,
                "input_len": len(input_text),
                "output_len": len(res.text or ""),
                "input_sha256": inp_hash,
                "output_sha256": out_hash,
            }
        )
    except Exception:
        pass

    return res
