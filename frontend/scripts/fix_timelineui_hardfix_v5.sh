#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."  # raiz do projeto (POPNEWS1)

FILE="frontend/src/TelaCreasCasos.jsx"
if [ ! -f "$FILE" ]; then
  echo "ERRO: não achei $FILE"
  exit 1
fi

BK="$FILE.bak_timelineui_hardfix_$(date +%Y%m%d_%H%M%S)"
cp "$FILE" "$BK"
echo "Backup: $BK"

python3 frontend/scripts/fix_timelineui_hardfix_v5.py

echo "✅ Fix aplicado. Agora rode:"
echo "  cd ~/POPNEWS1/frontend && npm run build"
echo "  cd ~/POPNEWS1/frontend && npm run dev"
echo ""
echo "No navegador, faça hard refresh (Ctrl+Shift+R) se necessário."
