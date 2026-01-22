#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
echo "== VERIFY CREAS TIMELINE FIX5 =="

FILE="frontend/src/TelaCreasCasos.jsx"
test -f "$FILE" || { echo "FALHA: $FILE não encontrado"; exit 1; }

fail=0

# Deve existir var timelineUI
if ! grep -nE "\bvar\s+timelineUI\s*=\s*\[\s*\]\s*;" "$FILE" >/dev/null 2>&1; then
  echo "FALHA: não encontrei 'var timelineUI = [];'"
  fail=1
else
  echo "OK: var timelineUI = []; presente"
fi

# Deve existir timelineUIMemo
if ! grep -nE "\bconst\s+timelineUIMemo\s*=\s*useMemo\b" "$FILE" >/dev/null 2>&1; then
  echo "FALHA: não encontrei 'const timelineUIMemo = useMemo'"
  fail=1
else
  echo "OK: const timelineUIMemo = useMemo presente"
fi

# Não pode existir const timelineUI = useMemo (TDZ)
if grep -nE "\bconst\s+timelineUI\s*=\s*useMemo\b" "$FILE" >/dev/null 2>&1; then
  echo "FALHA: ainda existe 'const timelineUI = useMemo'"
  fail=1
else
  echo "OK: não existe const timelineUI = useMemo"
fi

# Deve existir atribuição defensiva
if ! grep -n "FIX_CREAS_TIMELINEUI_FIX5" "$FILE" >/dev/null 2>&1; then
  echo "FALHA: marcador FIX_CREAS_TIMELINEUI_FIX5 não encontrado"
  fail=1
else
  echo "OK: atribuição defensiva presente"
fi

echo
if [ "$fail" -ne 0 ]; then
  echo "== VERIFY: FALHOU =="
  exit 1
fi
echo "== VERIFY: OK =="
