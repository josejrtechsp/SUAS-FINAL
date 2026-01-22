#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

echo "== VERIFY CRAS/CREAS FRONT SMOKE V3 =="
fail=0

if ! test -f frontend/src/TelaCreasCasos.jsx; then
  echo "FALHA: frontend/src/TelaCreasCasos.jsx não encontrado."
  exit 1
fi

if grep -RIn "\[\s*sel\s*,\s*timelineUI\s*\]" -n frontend/src/TelaCreasCasos.jsx >/dev/null 2>&1; then
  echo "FALHA: TelaCreasCasos.jsx ainda contém [sel, timelineUI]."
  fail=1
else
  echo "OK: [sel, timelineUI] não aparece em TelaCreasCasos.jsx"
fi

if ! grep -RInE "\b(const|let|var)\s+timelineUI\b" -n frontend/src/TelaCreasCasos.jsx >/dev/null 2>&1; then
  echo "FALHA: nenhuma declaração de timelineUI encontrada em TelaCreasCasos.jsx"
  fail=1
else
  echo "OK: timelineUI declarado em TelaCreasCasos.jsx"
fi

echo
if [ "$fail" -ne 0 ]; then
  echo "== VERIFY: FALHOU =="
  exit 1
fi
echo "== VERIFY: OK =="
