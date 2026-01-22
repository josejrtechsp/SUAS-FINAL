#!/usr/bin/env bash
set -euo pipefail

ROOT="${POPNEWS1_ROOT:-$HOME/POPNEWS1}"

if [ ! -d "$ROOT" ]; then
  echo "ERRO: não achei POPNEWS1 em $ROOT. Ajuste POPNEWS1_ROOT e rode de novo."
  exit 1
fi

echo ">> Rodando fix timelineUI V4..."
python3 "$ROOT/frontend/scripts/fix_timelineui_v4.py"
echo "✅ Fix aplicado."
echo "Agora rode:"
echo "  cd $ROOT/frontend && npm run build"
