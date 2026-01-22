#!/usr/bin/env python3
"""Atualiza backend/.env SEM editor interativo.

Uso (recomendado):
  OPENAI_API_KEY=sk-... python3 backend/scripts/set_openai_env.py

Ele faz UPSERT de:
  - POPRUA_OPENAI_API_KEY  (usa OPENAI_API_KEY do ambiente)
  - POPRUA_OPENAI_MODEL
  - POPRUA_OPENAI_REASONING_EFFORT

Não imprime a chave.
"""

from __future__ import annotations

import os
import re
from pathlib import Path


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


def upsert(text: str, key: str, value: str) -> str:
    pat = re.compile(rf"^{re.escape(key)}=.*$", re.M)
    line = f"{key}={value}"
    if pat.search(text):
        return pat.sub(line, text)
    text = text.rstrip("\n")
    if text:
        text += "\n"
    return text + line + "\n"


def main() -> None:
    backend_dir = Path(__file__).resolve().parents[1]
    env_path = backend_dir / ".env"

    openai_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not openai_key:
        raise SystemExit("OPENAI_API_KEY não está setada neste terminal. Ex.: OPENAI_API_KEY=sk-... python3 backend/scripts/set_openai_env.py")
    if not looks_like_key(openai_key):
        raise SystemExit("OPENAI_API_KEY não parece uma chave válida (precisa começar com sk- e não ser placeholder).")

    model = os.environ.get("POPRUA_OPENAI_MODEL", "gpt-4")
    effort = os.environ.get("POPRUA_OPENAI_REASONING_EFFORT", "low")

    text = env_path.read_text(encoding="utf-8") if env_path.exists() else ""

    text = upsert(text, "POPRUA_OPENAI_API_KEY", openai_key)
    text = upsert(text, "POPRUA_OPENAI_MODEL", model)
    text = upsert(text, "POPRUA_OPENAI_REASONING_EFFORT", effort)

    env_path.write_text(text, encoding="utf-8")

    print("OK: .env atualizado")
    print(f"- POPRUA_OPENAI_MODEL={model}")
    print(f"- POPRUA_OPENAI_REASONING_EFFORT={effort}")


if __name__ == "__main__":
    main()
