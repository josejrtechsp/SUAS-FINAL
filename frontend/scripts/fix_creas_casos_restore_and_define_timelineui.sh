#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-$HOME/POPNEWS1}"
FILE="$ROOT/frontend/src/TelaCreasCasos.jsx"

if [ ! -f "$FILE" ]; then
  echo "ERRO: não encontrei $FILE"
  exit 1
fi

# 1) localizar backup mais recente
BAK="$(ls -t "$ROOT/frontend/src/TelaCreasCasos.jsx.bak_timelineui_"* 2>/dev/null | head -n 1 || true)"
if [ -z "$BAK" ]; then
  echo "ERRO: não encontrei backups TelaCreasCasos.jsx.bak_timelineui_*"
  echo "Dica: se você tiver algum backup manual, copie para $FILE e rode novamente."
  exit 1
fi

echo ">> Restaurando backup mais recente:"
echo "   $BAK"
cp "$BAK" "$FILE"

# 2) aplicar fix via python (inserção segura do timelineUI)
python3 "$ROOT/frontend/scripts/fix_creas_casos_timelineui_insert.py" "$FILE"

echo "✅ OK: arquivo restaurado e timelineUI garantido."
echo "Agora rode:"
echo "  cd \"$ROOT/frontend\" && npm run build"
