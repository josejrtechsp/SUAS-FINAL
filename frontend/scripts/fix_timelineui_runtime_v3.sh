#!/usr/bin/env bash
set -euo pipefail
python3 "$(dirname "$0")/fix_timelineui_runtime_v3.py"
echo "✅ Fix aplicado. Agora rode:"
echo "  cd ~/POPNEWS1/frontend && npm run build"
