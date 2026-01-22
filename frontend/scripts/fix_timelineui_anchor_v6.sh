#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
FILE="$ROOT/frontend/src/TelaCreasCasos.jsx"

if [ ! -f "$FILE" ]; then
  echo "ERRO: não achei $FILE"
  exit 1
fi

python3 "$ROOT/frontend/scripts/fix_timelineui_anchor_v6.py" "$FILE"
echo "OK: agora rode:"
echo "  cd \"$ROOT/frontend\" && npm run build"
