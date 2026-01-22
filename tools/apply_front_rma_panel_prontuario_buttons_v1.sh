#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-.}"
cd "$ROOT"
python3 tools/patch_front_rma_panel_prontuario_buttons_v1.py .
echo "OK: apply_front_rma_panel_prontuario_buttons_v1"
