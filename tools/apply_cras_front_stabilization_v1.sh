#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

echo "== APPLY CRAS FRONT STABILIZATION V1 =="
python3 tools/apply_cras_front_stabilization_v1.py
echo "== OK =="
