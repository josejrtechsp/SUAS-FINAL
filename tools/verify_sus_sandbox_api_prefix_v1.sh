#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
echo "== Verificando SUS Sandbox API Prefix V1 =="

CFG="$ROOT/sus_sandbox_frontend/vite.config.js"
API="$ROOT/sus_sandbox_frontend/src/sus/susApi.js"

grep -q '"/api"' "$CFG" || { echo "FALTA: proxy /api no vite.config.js"; exit 1; }
grep -q "rewrite" "$CFG" || { echo "FALTA: rewrite no proxy /api"; exit 1; }
grep -q 'const API = "/api/sus";' "$API" || { echo "FALTA: base API /api/sus no susApi.js"; exit 1; }

echo "OK: proxy /api + base /api/sus configurados."
