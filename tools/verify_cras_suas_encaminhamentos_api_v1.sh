#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-.}"
cd "$ROOT"

F1="frontend/src/components/EncaminhamentosSuas.jsx"
F2="frontend/src/TelaCrasEncaminhamentos.jsx"

test -f "$F1" || { echo "ERRO: faltou $F1"; exit 2; }
test -f "$F2" || { echo "ERRO: faltou $F2"; exit 2; }

grep -Fq "/suas/encaminhamentos" "$F1" || { echo "ERRO: EncaminhamentosSuas não usa API /suas/encaminhamentos"; exit 2; }

grep -Fq "apiBase={apiBase}" "$F2" || { echo "ERRO: TelaCrasEncaminhamentos não passa apiBase"; exit 2; }
grep -Fq "apiFetch={apiFetch}" "$F2" || { echo "ERRO: TelaCrasEncaminhamentos não passa apiFetch"; exit 2; }

echo "OK: verify_cras_suas_encaminhamentos_api_v1"
