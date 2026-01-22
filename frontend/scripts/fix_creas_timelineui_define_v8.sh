#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PY="$ROOT/frontend/scripts/fix_creas_timelineui_define_v8.py"

python3 "$PY"

echo "Agora rode:"
echo "  cd \"$ROOT/frontend\" && npm run build"
echo "  cd \"$ROOT/frontend\" && npm run dev"
