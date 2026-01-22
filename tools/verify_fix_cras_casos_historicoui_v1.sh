#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-.}"
cd "$ROOT"
test -f frontend/src/TelaCrasCasos.jsx || { echo "ERRO: arquivo ausente"; exit 2; }
# verifica que historicoUI está definido
grep -Fq "const historicoUI = useMemo" frontend/src/TelaCrasCasos.jsx || { echo "ERRO: historicoUI ainda não definido"; exit 2; }
echo "OK: verify_fix_cras_casos_historicoui_v1"
