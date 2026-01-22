#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
echo "== APPLY CRAS/CREAS FRONT STABILIZATION V4 =="
python3 tools/apply_cras_front_stabilization_v4.py
echo "== OK =="
