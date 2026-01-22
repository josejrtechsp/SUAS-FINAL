#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

echo "== VERIFY CRAS FRONT SMOKE V1 =="

fail=0

if grep -RIn "useMemo(.*\[\s*sel\s*,\s*timelineUI\s*\]" -n frontend/src/TelaCreasCasos.jsx >/dev/null 2>&1; then
  echo "FALHA: TelaCreasCasos.jsx ainda tem dependency array com [sel, timelineUI] (circular)."
  fail=1
else
  echo "OK: dependency array circular (timelineUI) removida em TelaCreasCasos.jsx"
fi

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
