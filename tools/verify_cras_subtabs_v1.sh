#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-.}"

need(){
  local f="$1"; local pat="$2";
  if ! grep -q "$pat" "$ROOT/$f"; then
    echo "ERRO: padrão não encontrado: $pat em $f" >&2
    exit 1
  fi
}

need "frontend/src/CrasApp.jsx" "cras_subtabs_v1"
need "frontend/src/CrasApp.jsx" "subtabs:" 
need "frontend/src/components/CrasPageHeader.jsx" "cras-pageheader-v2-subtabs"
need "frontend/src/TelaCrasEncaminhamentos.jsx" "const view = String(subView" 
need "frontend/src/TelaCrasEncaminhamentos.jsx" "view === \"suas\"" 
need "frontend/src/TelaCrasTarefas.jsx" "CRAS_TAREFAS_SUBVIEWS_V1" 
need "frontend/src/TelaCrasTarefas.jsx" "view === \"lote\"" 

echo "OK: PATCH_CRAS_SUBTABS_V1 aplicado (checks básicos passaram)."
