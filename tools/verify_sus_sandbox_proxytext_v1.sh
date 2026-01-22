#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
echo "== Verificando SUS Sandbox ProxyText V1 =="

APP="$ROOT/sus_sandbox_frontend/src/App.jsx"
CFG="$ROOT/sus_sandbox_frontend/vite.config.js"

grep -q "__SUS_BACKEND_URL__" "$CFG" || { echo "FALTA define __SUS_BACKEND_URL__ no vite.config.js"; exit 1; }
grep -q "Rodando com proxy: este frontend" "$APP" || { echo "FALTA texto novo na Home (App.jsx)"; exit 1; }

echo "OK: texto da Home e define do Vite atualizados."
