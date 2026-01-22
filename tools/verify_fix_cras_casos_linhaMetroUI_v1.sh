#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-.}"
cd "$ROOT"

FILE="frontend/src/TelaCrasCasos.jsx"
test -f "$FILE" || { echo "ERRO: arquivo ausente: $FILE"; exit 2; }

grep -Fq "const linhaMetroUI = useMemo" "$FILE" || { echo "ERRO: linhaMetroUI ainda não definido"; exit 2; }

echo "OK: verify_fix_cras_casos_linhaMetroUI_v1"
