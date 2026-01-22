#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-.}"
cd "$ROOT"
test -f tools/patch_fix_cras_router_param_order_v1.py || { echo "ERRO: patcher ausente"; exit 2; }
test -f backend/app/routers/cras.py || { echo "ERRO: cras.py ausente"; exit 2; }

# checa sintaxe do arquivo (sem importar deps)
python3 -m py_compile backend/app/routers/cras.py

echo "OK: verify_fix_cras_router_param_order_v1"
