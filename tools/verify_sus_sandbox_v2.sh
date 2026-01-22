#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
echo "== Verificando SUS Sandbox V2 =="

need_files=(
  "sus_sandbox_backend/app/main.py"
  "sus_sandbox_backend/app/routers/sus.py"
  "sus_sandbox_backend/app/storage.py"
  "sus_sandbox_frontend/src/sus/susApi.js"
  "sus_sandbox_frontend/src/sus/SUSGestaoPage.jsx"
  "sus_sandbox_frontend/src/sus/SUSConformidadePage.jsx"
)

for f in "${need_files[@]}"; do
  [[ -f "$ROOT/$f" ]] || { echo "FALTA: $f"; exit 1; }
done

echo "OK: arquivos-chave presentes."
echo "Dica: rode backend e teste:"
echo "  curl -sS http://127.0.0.1:8009/sus/health"
