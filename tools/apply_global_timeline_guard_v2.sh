#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
echo "== APPLY GLOBAL TIMELINE GUARD V2 =="
python3 tools/apply_global_timeline_guard_v2.py
echo "== OK =="
