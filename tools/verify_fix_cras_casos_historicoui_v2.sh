#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-.}"
cd "$ROOT"

test -f frontend/src/TelaCrasCasos.jsx || { echo "ERRO: arquivo ausente"; exit 2; }

# deve ter 1 definição de historicoUI
grep -n "const historicoUI = useMemo" frontend/src/TelaCrasCasos.jsx >/dev/null || { echo "ERRO: historicoUI não definido"; exit 2; }

# não pode ter duas ocorrências do marker
COUNT="$(grep -F "FIX: garantir historicoUI definido" frontend/src/TelaCrasCasos.jsx | wc -l | tr -d ' ')"
if [ "${COUNT}" -gt 1 ]; then
  echo "ERRO: historicoUI duplicado (COUNT=${COUNT})"
  exit 2
fi

echo "OK: verify_fix_cras_casos_historicoui_v2"
