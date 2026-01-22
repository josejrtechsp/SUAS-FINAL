#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-.}"
cd "$ROOT"
python3 tools/patch_fix_casos_dedup_metro_historico_v1.py .
echo "OK: apply_fix_casos_dedup_metro_historico_v1"
