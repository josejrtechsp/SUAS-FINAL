#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-.}"
cd "$ROOT"

need() { test -f "$1" || { echo "ERRO: arquivo ausente: $1"; exit 2; }; }

need backend/app/models/suas_encaminhamento.py
need backend/app/routers/suas_encaminhamentos.py
need tools/patch_back_suas_encaminhamentos_v1.py
need tools/apply_back_suas_encaminhamentos_v1.sh

if ! grep -Fq "suas_encaminhamentos_router" backend/app/main.py; then
  echo "AVISO: main.py ainda não contém suas_encaminhamentos_router (rode o apply)"
fi

if ! grep -Fq "app.models.suas_encaminhamento" backend/app/core/db.py; then
  echo "AVISO: db.py ainda não importa app.models.suas_encaminhamento (rode o apply)"
fi

echo "OK: verify_back_suas_encaminhamentos_v1"
