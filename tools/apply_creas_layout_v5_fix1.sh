#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
echo "== APPLY CREAS LAYOUT V5 FIX1 =="
python3 tools/apply_creas_layout_v5_fix1.py
echo "== OK =="
