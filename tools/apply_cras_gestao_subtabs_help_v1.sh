#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-.}"

python3 "tools/patch_cras_gestao_subtabs_help_v1.py" "$ROOT"

echo "OK: patch_cras_gestao_subtabs_help_v1 aplicado."
