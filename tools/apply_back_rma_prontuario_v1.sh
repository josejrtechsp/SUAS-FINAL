#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-.}"
cd "$ROOT"

python3 tools/patch_back_rma_prontuario_v1.py .

echo "OK: apply_back_rma_prontuario_v1"
