#!/usr/bin/env bash
set -euo pipefail
python3 tools/patch_cras_padrao_header_subtabs_v1.py
echo "✅ OK. Reinicie o Vite (Ctrl+C; npm run dev) e dê Cmd+Shift+R."
