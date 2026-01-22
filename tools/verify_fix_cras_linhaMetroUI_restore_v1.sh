#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-.}"
cd "$ROOT"
FILE="frontend/src/TelaCrasCasos.jsx"
test -f "$FILE" || { echo "ERRO: arquivo ausente"; exit 2; }
grep -Fq "FIX: linhaMetroUI deve ser OBJETO" "$FILE" || { echo "ERRO: marker não encontrado"; exit 2; }
echo "OK: verify_fix_cras_linhaMetroUI_restore_v1"
