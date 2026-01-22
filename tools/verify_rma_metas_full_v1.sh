#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-.}"
cd "$ROOT"
test -f backend/app/models/rma_meta.py || { echo "ERRO: rma_meta.py ausente"; exit 2; }
test -f frontend/src/RmaMetasPanel.jsx || { echo "ERRO: RmaMetasPanel.jsx ausente"; exit 2; }
grep -Fq "RMA_METAS_PANEL_V1" frontend/src/RmaMetasPanel.jsx || { echo "ERRO: marker metas panel ausente"; exit 2; }
grep -Fq "# RMA_METAS_V1" backend/app/routers/cras_rma.py || { echo "ERRO: endpoints metas não inseridos"; exit 2; }
echo "OK: verify_rma_metas_full_v1"
