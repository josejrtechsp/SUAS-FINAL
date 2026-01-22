#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
echo "== APPLY GLOBAL TIMELINE GUARD V1 =="
python3 tools/apply_global_timeline_guard_v1.py
echo "== OK =="
