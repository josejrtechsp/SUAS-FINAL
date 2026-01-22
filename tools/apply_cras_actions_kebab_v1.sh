#!/usr/bin/env bash
set -euo pipefail
python3 tools/patch_cras_actions_kebab_v1.py
echo "✅ Patch aplicado. Reinicie o Vite (Ctrl+C e npm run dev) e dê Cmd+Shift+R."
