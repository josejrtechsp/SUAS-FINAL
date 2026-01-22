#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
echo "== APPLY CRAS/CREAS FRONT STABILIZATION V3 =="
python3 tools/apply_cras_front_stabilization_v3.py
echo "== OK =="
