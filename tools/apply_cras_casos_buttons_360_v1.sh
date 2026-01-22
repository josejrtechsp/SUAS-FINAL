#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-.}"
cd "$ROOT"
python3 tools/patch_cras_casos_buttons_360_v1.py .
echo "OK: apply_cras_casos_buttons_360_v1"
