#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
echo "== APPLY CREAS LAYOUT V5 FIX3 =="
python3 tools/apply_creas_layout_v5_fix3.py
echo "== OK =="
