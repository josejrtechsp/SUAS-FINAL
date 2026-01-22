#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
FILE="$ROOT/frontend/src/TelaCreasCasos.jsx"

if [ ! -f "$FILE" ]; then
  echo "ERRO: não encontrei $FILE"
  exit 1
fi

TS="$(date +%Y%m%d_%H%M%S)"
cp "$FILE" "$FILE.bak_fix_timelineui_$TS"

python3 "$ROOT/frontend/scripts/patch_fix_timelineui_defined.py" "$FILE"

echo "OK: timelineUI definido com segurança."
echo "Backup: $FILE.bak_fix_timelineui_$TS"
