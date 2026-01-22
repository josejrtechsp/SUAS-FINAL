#!/usr/bin/env bash
set -euo pipefail
python3 tools/patch_cras_enc_splitview_35_65_v12.py
echo "OK: SplitView V12 applied. Restart Vite (Ctrl+C; npm run dev) and Cmd+Shift+R."
