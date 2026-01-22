#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
echo "== VERIFY GLOBAL TIMELINE GUARD V1 =="

FILE="frontend/index.html"
test -f "$FILE" || { echo "FALHA: $FILE não encontrado"; exit 1; }

if grep -n "GLOBAL_TIMELINE_GUARD_V1" "$FILE" >/dev/null 2>&1; then
  echo "OK: guard presente em $FILE"
  exit 0
fi

echo "FALHA: não encontrei o marcador GLOBAL_TIMELINE_GUARD_V1 em $FILE"
exit 1
