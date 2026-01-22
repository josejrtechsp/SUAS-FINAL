#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
echo "== Verificando SUS Sandbox Fix SUS API V1 =="

API="$ROOT/sus_sandbox_frontend/src/sus/susApi.js"
GEST="$ROOT/sus_sandbox_frontend/src/sus/SUSGestaoPage.jsx"

grep -q 'const API = "/api/sus";' "$API" || { echo "FALTA base /api/sus"; exit 1; }
grep -q "listProgramas" "$API" || { echo "FALTA listProgramas"; exit 1; }
grep -q "normalizeFileUrl" "$API" || { echo "FALTA normalizeFileUrl"; exit 1; }
grep -q "normalizeFileUrl" "$GEST" || { echo "FALTA uso de normalizeFileUrl no SUSGestaoPage"; exit 1; }

echo "OK: susApi completo + Gestão corrigida."
echo "Dica: reinicie o Vite (Ctrl+C e npm run dev)."
