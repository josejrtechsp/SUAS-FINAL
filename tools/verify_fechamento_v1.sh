#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-.}"
cd "$ROOT"

test -f backend/app/models/prontuario_pes.py || { echo "ERRO: prontuario_pes.py ausente"; exit 2; }
test -f backend/app/routers/cras_pes.py || { echo "ERRO: cras_pes.py ausente"; exit 2; }
test -f frontend/src/PesProntuarioPanel.jsx || { echo "ERRO: PesProntuarioPanel.jsx ausente"; exit 2; }
grep -Fq "# RMA_PRESTACAO_V1" backend/app/routers/cras_rma.py || { echo "ERRO: cras_rma.py sem prestação"; exit 2; }
echo "OK: verify_fechamento_v1"
