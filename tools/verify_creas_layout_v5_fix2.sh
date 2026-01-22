#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

echo "== VERIFY CREAS LAYOUT V5 FIX2 =="
fail=0

FILE="frontend/src/TelaCreasCasos.jsx"
CSS="frontend/src/creas_layout_v5.css"

test -f "$FILE" || { echo "FALHA: $FILE não encontrado"; exit 1; }
test -f "$CSS"  || { echo "FALHA: $CSS não encontrado"; exit 1; }

if grep -n "PATCH_CRAS_FRONT_STABILIZATION_V3" "$FILE" >/dev/null 2>&1; then
  echo "FALHA: ainda existe trecho PATCH_CRAS_FRONT_STABILIZATION_V3 em $FILE"
  fail=1
else
  echo "OK: trecho indevido removido"
fi

if ! grep -n "import \"\./creas_layout_v5\.css\";" "$FILE" >/dev/null 2>&1; then
  echo "FALHA: import de creas_layout_v5.css não encontrado"
  fail=1
else
  echo "OK: CSS local importado"
fi

if ! grep -nE "^\s*let\s+timelineUI\s*=\s*\[\s*\]\s*;\s*$" "$FILE" >/dev/null 2>&1; then
  echo "FALHA: não encontrei 'let timelineUI = [];'"
  fail=1
else
  echo "OK: let timelineUI = []; presente"
fi

if ! grep -n "FIX_CREAS_TIMELINEUI_V5: preencher timelineUI" "$FILE" >/dev/null 2>&1; then
  echo "FALHA: marcador FIX_CREAS_TIMELINEUI_V5 não encontrado"
  fail=1
else
  echo "OK: atribuição timelineUI após memo presente"
fi

if ! grep -n "maxHeight: \"calc\(100vh - 270px\)\"" "$FILE" >/dev/null 2>&1; then
  echo "FALHA: list-card com maxHeight (calc(100vh - 270px)) não encontrado"
  fail=1
else
  echo "OK: lista esquerda com scroll"
fi

if ! grep -n "creas-case-meta" "$FILE" >/dev/null 2>&1; then
  echo "FALHA: bloco creas-case-meta não encontrado"
  fail=1
else
  echo "OK: cabeçalho compacto (meta badges) presente"
fi

echo
if [ "$fail" -ne 0 ]; then
  echo "== VERIFY: FALHOU =="
  exit 1
fi
echo "== VERIFY: OK =="
