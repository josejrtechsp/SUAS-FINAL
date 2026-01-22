#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

CANON="scripts/layout_canon"

copy_one () {
  local src="$1"
  local dst="$2"
  [ -f "$src" ] || { echo "❌ Canonical missing: $src"; exit 1; }
  mkdir -p "$(dirname "$dst")"
  if [ -f "$dst" ]; then
    cp "$dst" "${dst}.bak_$(date +%Y%m%d_%H%M%S)"
  fi
  cp "$src" "$dst"
}

copy_one "$CANON/SuasTopHeader.jsx" "frontend/src/components/SuasTopHeader.jsx"
copy_one "$CANON/CrasPageHeader.jsx" "frontend/src/components/CrasPageHeader.jsx"
copy_one "$CANON/App.css" "frontend/src/App.css"

echo "✅ Layout restaurado a partir do canonical (scripts/layout_canon)."
