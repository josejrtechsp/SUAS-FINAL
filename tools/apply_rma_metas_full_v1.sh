#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-.}"
cd "$ROOT"
python3 tools/patch_back_rma_metas_v1.py .
python3 tools/patch_front_rma_metas_panel_v1.py .
echo "OK: apply_rma_metas_full_v1"
