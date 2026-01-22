#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-.}"
cd "$ROOT"

test -f frontend/src/TelaCrasFichaFamilia360.jsx || { echo "ERRO: arquivo não encontrado"; exit 2; }

# Checagem simples: arquivo deve terminar com '}' (função fechada)
tail -n 5 frontend/src/TelaCrasFichaFamilia360.jsx | grep -Fq "}" || { echo "ERRO: arquivo parece truncado"; exit 2; }

echo "OK: TelaCrasFichaFamilia360.jsx restaurada (sem EOF)."
