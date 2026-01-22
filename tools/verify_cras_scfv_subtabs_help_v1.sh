#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-.}"

need_file () {
  local f="$1"
  if [[ ! -f "$ROOT/$f" ]]; then
    echo "ERRO: arquivo não encontrado: $f"
    exit 1
  fi
}

must_contain () {
  local f="$1"
  local pat="$2"
  if ! grep -Fq -- "$pat" "$ROOT/$f"; then
    echo "ERRO: padrão não encontrado em $f: $pat"
    exit 1
  fi
}

need_file "frontend/src/CrasApp.jsx"
need_file "frontend/src/TelaCrasScfv.jsx"

# Verificações robustas (sem regex), para não quebrar por detalhes de formatação
must_contain "frontend/src/CrasApp.jsx" "scfv:"
must_contain "frontend/src/CrasApp.jsx" 'label: "Chamada"'
must_contain "frontend/src/CrasApp.jsx" 'label: "Turmas"'
must_contain "frontend/src/CrasApp.jsx" 'label: "Alertas"'
must_contain "frontend/src/CrasApp.jsx" 'label: "Exportar"'
must_contain "frontend/src/CrasApp.jsx" 'scfv: "chamada"'

# Marcador de versão no arquivo da tela
must_contain "frontend/src/TelaCrasScfv.jsx" "SCFV_SUBTABS_HELP_V1"

echo "OK: verify_cras_scfv_subtabs_help_v1.sh atualizado (grep -F, sem regex)."
