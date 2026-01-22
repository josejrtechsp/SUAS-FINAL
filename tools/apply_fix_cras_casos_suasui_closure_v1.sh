#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-.}"
cd "$ROOT"
python3 tools/patch_fix_cras_casos_suasui_closure_v1.py .
echo "OK: apply_fix_cras_casos_suasui_closure_v1"
