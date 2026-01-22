#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-.}"
cd "$ROOT"

test -f frontend/src/domain/rmaCollector.js || { echo "ERRO: rmaCollector.js ausente"; exit 2; }

COUNT="$(grep -R "RMA_COLLECT_V1" -n frontend/src/TelaCrasCasos.jsx frontend/src/TelaCras.jsx frontend/src/TelaCrasEncaminhamentos.jsx frontend/src/TelaCrasTarefas.jsx frontend/src/TelaCrasDocumentos.jsx 2>/dev/null | wc -l | tr -d ' ')"
if [ "${COUNT}" -lt 4 ]; then
  echo "ERRO: poucos coletores inseridos (COUNT=${COUNT})."
  exit 2
fi

echo "OK: verify_front_rma_collectors_v1 (COUNT=${COUNT})"
