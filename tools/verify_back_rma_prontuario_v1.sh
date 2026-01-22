#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-.}"
cd "$ROOT"

# arquivos
test -f backend/app/models/rma_evento.py || { echo "ERRO: rma_evento.py ausente"; exit 2; }
test -f backend/app/routers/cras_rma.py || { echo "ERRO: cras_rma.py ausente"; exit 2; }
test -f backend/app/routers/cras_prontuario.py || { echo "ERRO: cras_prontuario.py ausente"; exit 2; }
test -f tools/patch_back_rma_prontuario_v1.py || { echo "ERRO: patcher ausente"; exit 2; }

# sintaxe
python3 -m py_compile backend/app/models/rma_evento.py
python3 -m py_compile backend/app/routers/cras_rma.py
python3 -m py_compile backend/app/routers/cras_prontuario.py

# wiring
grep -Fq "app.models.rma_evento" backend/app/core/db.py || { echo "ERRO: db.py não importa app.models.rma_evento"; exit 2; }
grep -Fq "cras_rma_router" backend/app/main.py || { echo "ERRO: main.py não tem cras_rma_router"; exit 2; }
grep -Fq "cras_prontuario_router" backend/app/main.py || { echo "ERRO: main.py não tem cras_prontuario_router"; exit 2; }

echo "OK: verify_back_rma_prontuario_v1"
