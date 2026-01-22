#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

echo "== VERIFY CREAS LAYOUT V5 FIX1 =="
fail=0

FILE="frontend/src/TelaCreasCasos.jsx"
CSS="frontend/src/creas_layout_v5.css"

test -f "$FILE" || { echo "FALHA: $FILE não encontrado"; exit 1; }
test -f "$CSS"  || { echo "FALHA: $CSS não encontrado"; exit 1; }

# 1) o trecho indevido não pode existir mais
if grep -n "PATCH_CRAS_FRONT_STABILIZATION_V3" "$FILE" >/dev/null 2>&1; then
  echo "FALHA: ainda existe trecho PATCH_CRAS_FRONT_STABILIZATION_V3 em $FILE"
  fail=1
else
  echo "OK: trecho indevido removido"
fi

# 2) import do CSS local
if ! grep -n "creas_layout_v5\.css" "$FILE" >/dev/null 2>&1; then
  echo "FALHA: import de creas_layout_v5.css não encontrado"
  fail=1
else
  echo "OK: CSS local importado"
fi

# 3) lista com overflow
if ! grep -n "maxHeight: \"calc\(100vh - 270px\)\"" "$FILE" >/dev/null 2>&1; then
  echo "FALHA: não encontrei maxHeight do list-card (calc(100vh - 270px))"
  fail=1
else
  echo "OK: list-card com maxHeight"
fi

# 4) meta badges
if ! grep -n "creas-case-meta" "$FILE" >/dev/null 2>&1; then
  echo "FALHA: bloco creas-case-meta não encontrado"
  fail=1
else
  echo "OK: cabeçalho compacto presente"
fi

echo
if [ "$fail" -ne 0 ]; then
  echo "== VERIFY: FALHOU =="
  exit 1
fi
echo "== VERIFY: OK =="
