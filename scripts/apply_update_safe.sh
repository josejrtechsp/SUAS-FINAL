#!/usr/bin/env bash
set -euo pipefail

# Aplica um ZIP de atualização no projeto SEM apagar:
# - backend/storage
# - backend/.env
# - backend/.venv
# - backend/poprua.db
# - frontend/node_modules
# - frontend/.env.local
#
# Uso:
#   cd ~/POPNEWS1
#   bash scripts/apply_update_safe.sh ~/Downloads/SEU_ZIP.zip

ZIP="${1:-}"
if [[ -z "$ZIP" || ! -f "$ZIP" ]]; then
  echo "Uso: bash scripts/apply_update_safe.sh /caminho/arquivo.zip" >&2
  exit 2
fi

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TS="$(date +"%Y%m%d_%H%M%S")"
TMP="$ROOT/_tmp/apply_$TS"

mkdir -p "$TMP"
unzip -q "$ZIP" -d "$TMP"

# backend
if [[ -d "$TMP/backend" ]]; then
  rsync -av \
    --exclude 'poprua.db' \
    --exclude '.venv' \
    --exclude '.env' \
    --exclude 'storage' \
    --exclude '__pycache__' \
    "$TMP/backend/" "$ROOT/backend/"
fi

# frontend
if [[ -d "$TMP/frontend" ]]; then
  rsync -av \
    --exclude 'node_modules' \
    --exclude '.vite' \
    --exclude 'dist' \
    --exclude '.env.local' \
    "$TMP/frontend/" "$ROOT/frontend/"
fi

# scripts + docs (se existirem)
for d in scripts docs tools; do
  if [[ -d "$TMP/$d" ]]; then
    mkdir -p "$ROOT/$d"
    rsync -av "$TMP/$d/" "$ROOT/$d/"
  fi
done

echo "OK: aplicado com segurança. TMP=$TMP"
