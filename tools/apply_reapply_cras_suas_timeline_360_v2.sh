#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-.}"
cd "$ROOT"

# Backend router overwrite (safe)
if [ -f backend/app/routers/suas_encaminhamentos.py ]; then
  echo "OK: backend router já existe, mantendo (patch inclui uma versão atualizada)."
fi

python3 tools/patch_reapply_cras_suas_timeline_360_v2.py .
echo "OK: apply_reapply_cras_suas_timeline_360_v2"
