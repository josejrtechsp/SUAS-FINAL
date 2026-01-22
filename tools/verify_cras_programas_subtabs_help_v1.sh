#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-.}"

need() {
  local f="$1"
  if [ ! -f "$ROOT/$f" ]; then
    echo "ERRO: arquivo ausente: $f"
    exit 1
  fi
}

grepq() {
  local pat="$1"
  local f="$2"
  if ! grep -q "$pat" "$ROOT/$f"; then
    echo "ERRO: padrão não encontrado em $f: $pat"
    exit 1
  fi
}

need "frontend/src/CrasApp.jsx"
need "frontend/src/TelaCrasProgramas.jsx"

grepq "programas: \[" "frontend/src/CrasApp.jsx"
grepq "programas: \"lista\"" "frontend/src/CrasApp.jsx"
grepq "case \"programas\"" "frontend/src/CrasApp.jsx"
grepq "view=\{activeSubtab \|\| \"lista\"\}" "frontend/src/CrasApp.jsx"
grepq "PROGRAMAS_SUBTABS_HELP_V1" "frontend/src/CrasApp.jsx"

grepq "export default function TelaCrasProgramas" "frontend/src/TelaCrasProgramas.jsx"
grepq "viewKey === \"lista\"" "frontend/src/TelaCrasProgramas.jsx"
grepq "PROGRAMAS_SUBTABS_HELP_V1" "frontend/src/TelaCrasProgramas.jsx"

echo "OK: CRAS · Programas subtabs + guia rápido (V1) aplicado."
