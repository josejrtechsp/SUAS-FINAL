#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
echo "== VERIFY CRAS NORMALIZE LINHA METRO FIX1 =="

fail=0

check_file () {
  local f="$1"
  if [ ! -f "$f" ]; then
    echo "SKIP: $f (não existe)"
    return 0
  fi

  echo "-- $f"

  if ! grep -n "_normalizeLinhaMetro" "$f" >/dev/null 2>&1; then
    echo "  FALHA: helper _normalizeLinhaMetro não encontrado"
    fail=1
  else
    echo "  OK: helper presente"
  fi

  if grep -n "_normalizeLinhaMetro is not defined" "$f" >/dev/null 2>&1; then
    echo "  AVISO: texto de erro encontrado no arquivo (não esperado)"
  fi

  if grep -n 'linhaMetro={_normalizeLinhaMetro' "$f" >/dev/null 2>&1; then
    echo "  FALHA: ainda existe uso não-guardado linhaMetro={_normalizeLinhaMetro(...)}"
    fail=1
  else
    echo "  OK: uso guardado/seguro"
  fi
}

check_file "frontend/src/TelaCrasCasos.jsx"
check_file "frontend/frontend/src/TelaCrasCasos.jsx"

echo
if [ "$fail" -ne 0 ]; then
  echo "== VERIFY: FALHOU =="
  exit 1
fi
echo "== VERIFY: OK =="
