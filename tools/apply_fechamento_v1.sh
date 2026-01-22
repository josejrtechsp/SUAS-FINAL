#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-.}"
cd "$ROOT"
python3 tools/patch_back_fechamento_v1.py .
python3 tools/patch_front_fechamento_v1.py .
echo "OK: apply_fechamento_v1"
