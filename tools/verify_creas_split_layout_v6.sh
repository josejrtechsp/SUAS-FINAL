#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
echo "== VERIFY CREAS SPLIT LAYOUT V6 =="

fail=0
check () {
  local f="$1"
  if [ ! -f "$f" ]; then
    echo "SKIP: $f (não existe)"
    return 0
  fi
  echo "-- $f"
  if ! grep -n "CREAS_SPLIT_LAYOUT_V6" "$f" >/dev/null 2>&1; then
    echo "  FALHA: marcador CREAS_SPLIT_LAYOUT_V6 não encontrado"
    fail=1
  else
    echo "  OK: marcador presente"
  fi
  if ! grep -n 'className="creas-split"' "$f" >/dev/null 2>&1; then
    echo "  FALHA: wrapper creas-split não encontrado"
    fail=1
  else
    echo "  OK: wrapper creas-split"
  fi
  if ! grep -n 'className="col-esquerda" style={{ flex: "0 0 420px", maxWidth: 420 }}' "$f" >/dev/null 2>&1; then
    echo "  AVISO: style da col-esquerda não está no formato exato (pode estar ok com variação)"
  else
    echo "  OK: col-esquerda width"
  fi
  if ! grep -n 'className="col-direita" style={{ flex: "1 1 auto", minWidth: 0 }}' "$f" >/dev/null 2>&1; then
    echo "  AVISO: style da col-direita não está no formato exato (pode estar ok com variação)"
  else
    echo "  OK: col-direita flex"
  fi
}

check "frontend/src/TelaCreasCasos.jsx"
check "frontend/frontend/src/TelaCreasCasos.jsx"

echo
if [ "$fail" -ne 0 ]; then
  echo "== VERIFY: FALHOU =="
  exit 1
fi
echo "== VERIFY: OK =="
