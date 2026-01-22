#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

echo "== VERIFY CREAS LAYOUT V5 FIX4 =="
fail=0
FILE="frontend/src/TelaCreasCasos.jsx"
test -f "$FILE" || { echo "FALHA: $FILE não encontrado"; exit 1; }

if grep -n "timelineUICalc" "$FILE" >/dev/null 2>&1; then
  echo "FALHA: ainda existe 'timelineUICalc' no arquivo"
  fail=1
else
  echo "OK: nenhuma referência a timelineUICalc"
fi

if grep -n "\[\s*sel\s*,\s*timelineUI\s*\]" "$FILE" >/dev/null 2>&1; then
  echo "FALHA: ainda existe dependency array circular [sel, timelineUI]"
  fail=1
else
  echo "OK: não existe [sel, timelineUI]"
fi

if ! grep -nE "\bconst\s+timelineUI\s*=\s*useMemo\b" "$FILE" >/dev/null 2>&1; then
  echo "FALHA: não encontrei 'const timelineUI = useMemo' (pode ter outro formato)"
  fail=1
else
  echo "OK: timelineUI via useMemo presente"
fi

echo
if [ "$fail" -ne 0 ]; then
  echo "== VERIFY: FALHOU =="
  exit 1
fi
echo "== VERIFY: OK =="
