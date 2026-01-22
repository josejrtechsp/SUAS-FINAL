#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
echo "== APPLY CREAS SPLIT LAYOUT V6 =="
python3 tools/apply_creas_split_layout_v6.py
echo "== OK =="
