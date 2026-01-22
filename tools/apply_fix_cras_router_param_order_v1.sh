#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-.}"
cd "$ROOT"
python3 tools/patch_fix_cras_router_param_order_v1.py .
echo "OK: apply_fix_cras_router_param_order_v1"
