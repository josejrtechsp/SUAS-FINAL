#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-.}"
cd "$ROOT"
FILE="frontend/src/TelaCrasRelatorios.jsx"
test -f "$FILE" || { echo "ERRO: TelaCrasRelatorios.jsx ausente"; exit 2; }

grep -Fq "RMA_PRONTUARIO_EXPORT_V3" "$FILE" || { echo "ERRO: marker V3 não encontrado"; exit 2; }
grep -Fq "__downloadRmaCsv" "$FILE" || { echo "ERRO: helper __downloadRmaCsv ausente"; exit 2; }

if grep -Eq "onClick=\{\s*downloadRmaCsv\s*\}" "$FILE"; then
  echo "ERRO: ainda existe onClick={downloadRmaCsv}"
  exit 2
fi

echo "OK: verify_front_rma_prontuario_export_v3"
