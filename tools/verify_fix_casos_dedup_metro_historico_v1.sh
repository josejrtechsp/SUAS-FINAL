#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-.}"
cd "$ROOT"
FILE="frontend/src/TelaCrasCasos.jsx"
test -f "$FILE" || { echo "ERRO: arquivo ausente: $FILE"; exit 2; }

# deve haver exatamente 1 const historicoUI e 1 const linhaMetroUI
H="$(grep -n "const historicoUI = useMemo" "$FILE" | wc -l | tr -d ' ')"
M="$(grep -n "const linhaMetroUI = useMemo" "$FILE" | wc -l | tr -d ' ')"
if [ "$H" != "1" ]; then
  echo "ERRO: historicoUI esperado=1, achado=$H"
  exit 2
fi
if [ "$M" != "1" ]; then
  echo "ERRO: linhaMetroUI esperado=1, achado=$M"
  exit 2
fi

echo "OK: verify_fix_casos_dedup_metro_historico_v1"
