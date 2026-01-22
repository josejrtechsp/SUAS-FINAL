#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

read -r -p "Nome do Secretário (ex.: Fulano de Tal): " SIGN_NAME
SIGN_NAME="$(echo "$SIGN_NAME" | sed -e 's/^ *//' -e 's/ *$//')"

if [[ -z "$SIGN_NAME" ]]; then
  echo "ERRO: nome vazio."
  exit 1
fi

SIGN_CARGO="${SIGN_CARGO:-Secretário Municipal de Assistência Social}"
SIGN_ORGAO="${SIGN_ORGAO:-Secretaria Municipal de Assistência Social}"

export SIGN_NAME SIGN_CARGO SIGN_ORGAO

python3 - <<'PY'
import os
from pathlib import Path

name = (os.environ.get("SIGN_NAME") or "").strip()
cargo = (os.environ.get("SIGN_CARGO") or "").strip()
orgao = (os.environ.get("SIGN_ORGAO") or "").strip()

if not name:
    raise SystemExit("ERRO: SIGN_NAME vazio")

p = Path(".env")
lines = p.read_text(encoding="utf-8").splitlines() if p.exists() else []

def upsert(key: str, value: str) -> None:
    for i, l in enumerate(lines):
        if l.startswith(key + "="):
            lines[i] = f"{key}={value}"
            return
    lines.append(f"{key}={value}")

upsert("POPRUA_ASSINANTE_NOME_SMAS", name)
if cargo:
    upsert("POPRUA_ASSINANTE_CARGO_SMAS", cargo)
if orgao:
    upsert("POPRUA_ASSINANTE_ORGAO_SMAS", orgao)

p.write_text("\n".join(lines) + "\n", encoding="utf-8")
print("OK: .env atualizado (POPRUA_ASSINANTE_NOME_SMAS / CARGO / ORGAO)")
PY

echo "OK. Reinicie o backend para aplicar."

