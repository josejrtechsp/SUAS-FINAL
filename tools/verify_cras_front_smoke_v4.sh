#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
echo "== VERIFY CRAS/CREAS FRONT SMOKE V4 =="
fail=0

if ! test -f frontend/src/TelaCreasCasos.jsx; then
  echo "FALHA: frontend/src/TelaCreasCasos.jsx não encontrado."
  exit 1
fi

if ! grep -RInE "^\s*let\s+timelineUI\s*=\s*\[\s*\]\s*;\s*$" -n frontend/src/TelaCreasCasos.jsx >/dev/null 2>&1; then
  echo "FALHA: não encontrei 'let timelineUI = [];' em TelaCreasCasos.jsx"
  fail=1
else
  echo "OK: let timelineUI = []; presente"
fi

if grep -RInE "^\s*const\s+timelineUI\s*=" -n frontend/src/TelaCreasCasos.jsx >/dev/null 2>&1; then
  echo "FALHA: ainda existe 'const timelineUI = ...' (pode reintroduzir TDZ)."
  fail=1
else
  echo "OK: não existe const timelineUI = ..."
fi

if ! grep -RInE "timelineUI\s*=\s*Array\.isArray\(timelineUICalc\)\s*\?" -n frontend/src/TelaCreasCasos.jsx >/dev/null 2>&1; then
  echo "FALHA: não encontrei a atribuição defensiva 'timelineUI = Array.isArray(timelineUICalc) ? ...'"
  fail=1
else
  echo "OK: atribuição defensiva de timelineUI presente"
fi

echo
if [ "$fail" -ne 0 ]; then
  echo "== VERIFY: FALHOU =="
  exit 1
fi
echo "== VERIFY: OK =="
