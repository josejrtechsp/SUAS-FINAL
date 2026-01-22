#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-$HOME/POPNEWS1}"
FILE="$ROOT/frontend/src/TelaCreasCasos.jsx"

if [ ! -f "$FILE" ]; then
  echo "ERRO: nao encontrei $FILE"
  exit 1
fi

TS="$(date +%Y%m%d_%H%M%S)"
cp "$FILE" "$FILE.bak_timelineui_$TS"

python3 "$ROOT/frontend/scripts/patch_fix_timelineui_defined_v2.py" "$FILE"

echo "OK: TelaCreasCasos.jsx corrigido. Backup em: $FILE.bak_timelineui_$TS"
