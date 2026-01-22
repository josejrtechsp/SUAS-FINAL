#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")"/.. && pwd)"
cd "$ROOT"
python3 tools/patch_terceiro_setor_front.py
echo ""
echo "Reinicie o front:"
echo "  cd frontend && npm run dev"
