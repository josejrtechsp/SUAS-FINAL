#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
echo "== APPLY CREAS TIMELINE FIX6 (DUALROOT) =="
python3 tools/apply_creas_timeline_fix6_dualroot.py
echo "== OK =="
