#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
echo "== Verificando SUS Sandbox Ports V1 =="

CFG="$ROOT/sus_sandbox_frontend/vite.config.js"
if [[ ! -f "$CFG" ]]; then
  echo "FALTA: sus_sandbox_frontend/vite.config.js"
  exit 1
fi

grep -q "SUS_BACKEND_URL" "$CFG" || { echo "FALTA: SUS_BACKEND_URL no vite.config.js"; exit 1; }
grep -q "8010" "$CFG" || { echo "AVISO: default 8010 não encontrado (ok se você alterou)"; }

echo "OK: vite.config.js atualizado para portas configuráveis."
echo "Dica: backend em 8010 e frontend em 5174 (ou configure variáveis)."
