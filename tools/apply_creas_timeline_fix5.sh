#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
echo "== APPLY CREAS TIMELINE FIX5 =="
python3 tools/apply_creas_timeline_fix5.py
echo "== OK =="
