#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
echo "== Verificando SUS Sandbox ErrorBoundary V1 =="

EB="$ROOT/sus_sandbox_frontend/src/components/ErrorBoundary.jsx"
APP="$ROOT/sus_sandbox_frontend/src/App.jsx"

[[ -f "$EB" ]] || { echo "FALTA: $EB"; exit 1; }
grep -q "ErrorBoundary" "$APP" || { echo "FALTA: import ErrorBoundary no App.jsx"; exit 1; }
grep -q "wrap\(<SUSGestaoPage" "$APP" || { echo "FALTA: rotas embrulhadas com wrap()"; exit 1; }

echo "OK: ErrorBoundary instalado e rotas embrulhadas."
echo "Dica: reinicie o Vite (Ctrl+C e npm run dev)."
