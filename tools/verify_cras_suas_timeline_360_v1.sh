#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-.}"
cd "$ROOT"
need(){ test -f "$1" || { echo "ERRO: arquivo ausente: $1"; exit 2; }; }

need tools/patch_cras_suas_timeline_360_v1.py
need tools/apply_cras_suas_timeline_360_v1.sh
need tools/verify_cras_suas_timeline_360_v1.sh
need frontend/src/TelaCrasCasos.jsx
need frontend/src/TelaCrasFichaPessoa360.jsx
need frontend/src/TelaCrasFichaFamilia360.jsx

# Casos deve usar backend
if grep -Fq "suasEncaminhamentosStore" frontend/src/TelaCrasCasos.jsx; then
  echo "ERRO: TelaCrasCasos ainda usa store local (suasEncaminhamentosStore)."
  exit 2
fi
grep -Fq "/suas/encaminhamentos" frontend/src/TelaCrasCasos.jsx || { echo "ERRO: Casos não chama /suas/encaminhamentos"; exit 2; }

# 360 deve ter loader
grep -Fq "loadSuas360" frontend/src/TelaCrasFichaPessoa360.jsx || { echo "ERRO: Pessoa360 sem loadSuas360"; exit 2; }
grep -Fq "loadSuas360" frontend/src/TelaCrasFichaFamilia360.jsx || { echo "ERRO: Familia360 sem loadSuas360"; exit 2; }

echo "OK: verify_cras_suas_timeline_360_v1"
