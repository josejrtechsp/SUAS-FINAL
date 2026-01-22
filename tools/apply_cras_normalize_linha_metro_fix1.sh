#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
echo "== APPLY CRAS NORMALIZE LINHA METRO FIX1 =="
python3 tools/apply_cras_normalize_linha_metro_fix1.py
echo "== OK =="
