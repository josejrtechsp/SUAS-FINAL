#!/usr/bin/env bash
set -euo pipefail

ROOT="${HOME}/POPNEWS1"
echo "POPNEWS1: $ROOT"

restore_latest_bak () {
  local target="$1"
  if [[ ! -f "$target" ]]; then
    echo "WARN: alvo não existe: $target"
    return 0
  fi

  local bak
  bak="$(ls -t "${target}.bak_"* 2>/dev/null | head -n 1 || true)"
  if [[ -z "$bak" ]]; then
    echo "WARN: sem backup .bak para: $target"
    return 0
  fi

  local ts
  ts="$(date +%Y%m%d_%H%M%S)"
  cp -f "$target" "${target}.BROKEN_${ts}"
  cp -f "$bak" "$target"
  echo "OK: restaurado $target  <=  $bak"
}

restore_latest_bak "${ROOT}/frontend/src/TelaCrasEncaminhamentos.jsx"
restore_latest_bak "${ROOT}/frontend/src/TelaCrasScfv.jsx"
restore_latest_bak "${ROOT}/frontend/src/CrasApp.jsx"
restore_latest_bak "${ROOT}/frontend/src/components/CrasTabContextHeader.jsx"
restore_latest_bak "${ROOT}/frontend/src/components/CrasPageHeader.jsx"

echo
echo "✅ Rollback concluído."
echo "Agora reinicie o Vite:"
echo "  cd ~/POPNEWS1/frontend && npm run dev"
