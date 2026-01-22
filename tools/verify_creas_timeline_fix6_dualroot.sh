#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
echo "== VERIFY CREAS TIMELINE FIX6 (DUALROOT) =="

fail=0

check_file () {
  local f="$1"
  if [ ! -f "$f" ]; then
    echo "SKIP: $f (não existe)"
    return 0
  fi

  echo "-- $f"

  if ! grep -nE "\bvar\s+timelineUI\s*=\s*\[\s*\]\s*;" "$f" >/dev/null 2>&1; then
    echo "  FALHA: não encontrei 'var timelineUI = [];'"
    fail=1
  else
    echo "  OK: var timelineUI"
  fi

  if ! grep -nE "\bconst\s+timelineUIMemo\s*=\s*useMemo\b" "$f" >/dev/null 2>&1; then
    echo "  FALHA: não encontrei 'const timelineUIMemo = useMemo'"
    fail=1
  else
    echo "  OK: timelineUIMemo"
  fi

  if grep -nE "\bconst\s+timelineUI\s*=\s*useMemo\b" "$f" >/dev/null 2>&1; then
    echo "  FALHA: ainda existe 'const timelineUI = useMemo' (TDZ)"
    fail=1
  else
    echo "  OK: não há const timelineUI = useMemo"
  fi

  if grep -n "\[\s*sel\s*,\s*timelineUI\s*\]" "$f" >/dev/null 2>&1; then
    echo "  FALHA: ainda existe [sel, timelineUI]"
    fail=1
  else
    echo "  OK: não há [sel, timelineUI]"
  fi
}

check_file "frontend/src/TelaCreasCasos.jsx"
check_file "frontend/frontend/src/TelaCreasCasos.jsx"

echo
if [ "$fail" -ne 0 ]; then
  echo "== VERIFY: FALHOU =="
  exit 1
fi
echo "== VERIFY: OK =="
