#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

echo "== VERIFY CREAS LAYOUT V5 FIX3 =="
fail=0
FILE="frontend/src/TelaCreasCasos.jsx"

test -f "$FILE" || { echo "FALHA: $FILE não encontrado"; exit 1; }

# Checa se existe calc(100vh - 270px) e overflow auto no bloco do creas-casos-list
if ! grep -n "creas-casos-list" "$FILE" >/dev/null 2>&1; then
  echo "FALHA: não encontrei div com className creas-casos-list"
  fail=1
else
  echo "OK: creas-casos-list existe"
fi

if ! grep -n 'calc(100vh - 270px)' "$FILE" >/dev/null 2>&1; then
  echo "FALHA: não encontrei calc(100vh - 270px) no arquivo"
  fail=1
else
  echo "OK: maxHeight calc(100vh - 270px) presente"
fi

if ! grep -n 'overflow: "auto"' "$FILE" >/dev/null 2>&1; then
  echo 'FALHA: não encontrei overflow: "auto" no arquivo'
  fail=1
else
  echo 'OK: overflow "auto" presente'
fi

echo
if [ "$fail" -ne 0 ]; then
  echo "== VERIFY: FALHOU =="
  exit 1
fi
echo "== VERIFY: OK =="
