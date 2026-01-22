#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-.}"
cd "$ROOT"

test -f tools/patch_reapply_cras_suas_timeline_360_v2.py || { echo "ERRO: patcher ausente"; exit 2; }
test -f frontend/src/TelaCrasCasos.jsx || { echo "ERRO: Casos ausente"; exit 2; }
test -f frontend/src/TelaCrasFichaPessoa360.jsx || { echo "ERRO: Pessoa360 ausente"; exit 2; }
test -f frontend/src/TelaCrasFichaFamilia360.jsx || { echo "ERRO: Familia360 ausente"; exit 2; }

# Casos deve chamar backend
grep -Fq "/suas/encaminhamentos" frontend/src/TelaCrasCasos.jsx || { echo "ERRO: Casos não chama /suas/encaminhamentos"; exit 2; }

# 360 deve ter loader
grep -Fq "loadSuas360" frontend/src/TelaCrasFichaPessoa360.jsx || { echo "ERRO: Pessoa360 sem loadSuas360"; exit 2; }
grep -Fq "loadSuas360" frontend/src/TelaCrasFichaFamilia360.jsx || { echo "ERRO: Familia360 sem loadSuas360"; exit 2; }

echo "OK: verify_reapply_cras_suas_timeline_360_v2"
