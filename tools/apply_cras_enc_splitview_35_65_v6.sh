#!/usr/bin/env bash
set -euo pipefail
python3 tools/patch_cras_enc_splitview_35_65_v6.py
echo "✅ SplitView V6 aplicado. Reinicie o Vite (Ctrl+C; npm run dev) e dê Cmd+Shift+R."
