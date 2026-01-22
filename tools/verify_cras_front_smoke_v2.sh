#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

echo "== VERIFY CRAS/CREAS FRONT SMOKE V2 =="
fail=0

# CREAS: não pode existir [sel, timelineUI] em lugar nenhum
if grep -RIn "\[\s*sel\s*,\s*timelineUI\s*\]" -n frontend/src/TelaCreasCasos.jsx >/dev/null 2>&1; then
  echo "FALHA: TelaCreasCasos.jsx ainda contém [sel, timelineUI]."
  fail=1
else
  echo "OK: [sel, timelineUI] removido de TelaCreasCasos.jsx"
fi

# CRAS: garantir normalização do linhaMetroUI (mesmo check do V1)
if grep -RIn "linhaMetro=\{\s*linhaMetroUI\s*\}" -n frontend/src/TelaCrasCasos.jsx >/dev/null 2>&1; then
  echo "FALHA: TelaCrasCasos.jsx ainda passa linhaMetroUI sem normalização."
  fail=1
else
  echo "OK: linhaMetroUI normalizado em TelaCrasCasos.jsx"
fi

if ! grep -RIn "_normalizeLinhaMetro" -n frontend/src/TelaCrasCasos.jsx >/dev/null 2>&1; then
  echo "FALHA: helper _normalizeLinhaMetro não encontrado em TelaCrasCasos.jsx"
  fail=1
else
  echo "OK: helper _normalizeLinhaMetro presente em TelaCrasCasos.jsx"
fi

echo
if [ "$fail" -ne 0 ]; then
  echo "== VERIFY: FALHOU =="
  exit 1
fi
echo "== VERIFY: OK =="
