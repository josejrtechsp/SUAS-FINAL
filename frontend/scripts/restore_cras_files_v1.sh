#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TS="$(date +%Y%m%d_%H%M%S)"
echo ">> Restaurando arquivos CRAS quebrados (backup automático)..."

for f in "frontend/src/TelaCrasEncaminhamentos.jsx" "frontend/src/TelaCrasScfv.jsx"; do
  if [ -f "$ROOT/$f" ]; then
    cp "$ROOT/$f" "$ROOT/$f.bak_restore_$TS"
    echo "Backup: $ROOT/$f.bak_restore_$TS"
  fi
done

# Os arquivos do patch já foram extraídos via unzip -d .
echo "OK: arquivos restaurados."
echo "Agora rode:"
echo "  cd \"$ROOT/frontend\" && npm run build"
