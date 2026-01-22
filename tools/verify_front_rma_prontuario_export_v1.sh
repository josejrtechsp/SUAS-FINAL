\
#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-.}"
cd "$ROOT"
FILE="frontend/src/TelaCrasRelatorios.jsx"
test -f "$FILE" || { echo "ERRO: TelaCrasRelatorios.jsx ausente"; exit 2; }
grep -Fq "RMA_PRONTUARIO_EXPORT_V1" "$FILE" || { echo "ERRO: marker não encontrado"; exit 2; }
grep -Fq "downloadRmaCsv" "$FILE" || { echo "ERRO: downloadRmaCsv ausente"; exit 2; }
echo "OK: verify_front_rma_prontuario_export_v1"
