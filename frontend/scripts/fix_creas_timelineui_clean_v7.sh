#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
TARGET="$ROOT/frontend/src/TelaCreasCasos.jsx"

if [ ! -f "$TARGET" ]; then
  echo "ERRO: não encontrei $TARGET"
  exit 1
fi

python3 "$ROOT/frontend/scripts/fix_creas_timelineui_clean_v7.py" "$TARGET"

echo "OK: TelaCreasCasos.jsx corrigido (timelineUI)."
echo "Agora rode:"
echo "  cd \"$ROOT/frontend\" && npm run build"
