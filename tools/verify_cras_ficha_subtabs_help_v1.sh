#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-.}"

fail() {
  echo "ERRO: $1"
  exit 1
}

FILE="$ROOT/frontend/src/CrasApp.jsx"
[ -f "$FILE" ] || fail "arquivo não encontrado: frontend/src/CrasApp.jsx"

# Checagens robustas (busca literal, sem regex)
grep -Fq 'case "ficha"' "$FILE" || fail 'padrão não encontrado em frontend/src/CrasApp.jsx: case "ficha"'
grep -Fq 'TelaCrasFicha' "$FILE" || fail 'padrão não encontrado em frontend/src/CrasApp.jsx: TelaCrasFicha'
grep -Fq 'Impressão/PDF' "$FILE" || fail 'padrão não encontrado em frontend/src/CrasApp.jsx: Impressão/PDF'
grep -Fq 'impressao' "$FILE" || fail 'padrão não encontrado em frontend/src/CrasApp.jsx: impressao'

for f in TelaCrasFicha.jsx TelaCrasFichaPessoa360.jsx TelaCrasFichaFamilia360.jsx; do
  [ -f "$ROOT/frontend/src/$f" ] || fail "arquivo não encontrado: frontend/src/$f"
done

echo "OK: verify_cras_ficha_subtabs_help_v1 passou."
