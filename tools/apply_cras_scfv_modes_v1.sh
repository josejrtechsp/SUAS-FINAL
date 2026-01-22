#!/usr/bin/env bash
set -euo pipefail
python3 tools/patch_cras_scfv_modes_v1.py
echo "✅ SCFV modos aplicados. Reinicie o Vite (Ctrl+C; npm run dev) e dê Cmd+Shift+R."
