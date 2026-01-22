#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-.}"
cd "$ROOT"

test -f frontend/src/CrasApp.jsx || { echo "ERRO: CrasApp.jsx ausente"; exit 2; }
test -f frontend/src/TelaCrasCasos.jsx || { echo "ERRO: TelaCrasCasos.jsx ausente"; exit 2; }

grep -Fq "onNavigate={onNavigate}" frontend/src/CrasApp.jsx || { echo "ERRO: CrasApp não passa onNavigate para TelaCrasCasos"; exit 2; }

grep -Fq "function openPessoa360()" frontend/src/TelaCrasCasos.jsx || { echo "ERRO: handler openPessoa360 ausente"; exit 2; }
grep -Fq "Pessoa 360" frontend/src/TelaCrasCasos.jsx || { echo "ERRO: botão Pessoa 360 não encontrado"; exit 2; }
grep -Fq "Família 360" frontend/src/TelaCrasCasos.jsx || { echo "ERRO: botão Família 360 não encontrado"; exit 2; }

echo "OK: verify_cras_casos_buttons_360_v1"
