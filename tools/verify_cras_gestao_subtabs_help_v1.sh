#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-.}"
F="$ROOT/frontend/src/CrasApp.jsx"
test -f "$F" || { echo "ERRO: não achei $F"; exit 1; }

# Checa presença das subtabs de gestão (literais, sem regex)
grep -Fq 'automacoes' "$F" || { echo "ERRO: não achei chave automacoes em CrasApp.jsx"; exit 1; }
grep -Fq 'documentos' "$F" || { echo "ERRO: não achei chave documentos em CrasApp.jsx"; exit 1; }
grep -Fq 'relatorios' "$F" || { echo "ERRO: não achei chave relatorios em CrasApp.jsx"; exit 1; }

# Checa que os componentes recebem view= (ao menos uma ocorrência)
grep -Fq 'TelaCrasAutomacoes' "$F" || { echo "ERRO: não achei TelaCrasAutomacoes em CrasApp.jsx"; exit 1; }
grep -Fq 'view={activeSubtab' "$F" || { echo "ERRO: não achei view={activeSubtab ...} em CrasApp.jsx"; exit 1; }

# Checa telas
for p in \
  "$ROOT/frontend/src/TelaCrasAutomacoes.jsx" \
  "$ROOT/frontend/src/TelaCrasDocumentos.jsx" \
  "$ROOT/frontend/src/TelaCrasRelatorios.jsx"
do
  test -f "$p" || { echo "ERRO: não achei $p"; exit 1; }
  grep -Fq 'view' "$p" || { echo "ERRO: tela sem prop view: $p"; exit 1; }
done

echo "OK: Gestão (Automações/Documentos/Relatórios) com subtelas + view + guias (patch V1)."
