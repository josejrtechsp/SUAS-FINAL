#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

echo "== APPLY CRAS/CREAS FRONT STABILIZATION V2 =="
python3 tools/apply_cras_front_stabilization_v2.py
echo "== OK =="
