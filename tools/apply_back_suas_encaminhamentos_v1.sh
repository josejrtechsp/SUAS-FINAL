#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-.}"
cd "$ROOT"
python3 tools/patch_back_suas_encaminhamentos_v1.py .
echo "OK: apply_back_suas_encaminhamentos_v1 concluído."
