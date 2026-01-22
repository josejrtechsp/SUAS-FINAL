#!/usr/bin/env bash
set -euo pipefail
python3 tools/patch_cras_enc_splitview_35_65_v9.py
echo "✅ SplitView V9 aplicado. Reinicie o Vite (Ctrl+C; npm run dev) e dê Cmd+Shift+R."
