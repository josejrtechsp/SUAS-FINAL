#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
echo "== Verificando SUS_SANDBOX_V1 =="

need=(
  "sus_sandbox_frontend/package.json"
  "sus_sandbox_frontend/src/App.jsx"
  "sus_sandbox_frontend/src/sus/SUSHubPage.jsx"
  "sus_sandbox_backend/requirements.txt"
  "sus_sandbox_backend/app/main.py"
  "sus_sandbox_backend/app/routers/sus.py"
)

for f in "${need[@]}"; do
  [[ -f "$ROOT/$f" ]] || { echo "FALTA: $f"; exit 1; }
done

echo "OK: estrutura do sandbox presente."
echo "Próximo: rode backend (8009) e frontend (5174)."
