#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-.}"

need() {
  local f="$1"
  local pat="$2"
  if [ ! -f "$ROOT/$f" ]; then
    echo "ERRO: arquivo não encontrado: $f"
    exit 1
  fi
  if ! grep -Fq "$pat" "$ROOT/$f"; then
    echo "ERRO: padrão não encontrado em $f: $pat"
    exit 1
  fi
}

need "frontend/src/components/CrasPageHeader.jsx" "DERIVED_HELP_V1"
need "frontend/src/components/CrasPageHeader.jsx" "Ver como usar"
need "frontend/src/components/CrasPageHeader.jsx" "tarefas"
need "frontend/src/components/CrasPageHeader.jsx" "encaminhamentos"
need "frontend/src/components/CrasPageHeader.jsx" "casos"

echo "OK: PATCH_CRAS_HELP_REMAINING_V1 aplicado (CrasPageHeader com guia rápido por subtela)."
