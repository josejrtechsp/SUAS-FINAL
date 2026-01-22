#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-.}"
cd "$ROOT"

need_file() {
  local f="$1"
  if [ ! -f "$f" ]; then
    echo "ERRO: arquivo ausente: $f"
    exit 1
  fi
}

need_file "frontend/src/CrasApp.jsx"
need_file "frontend/src/TelaCrasEncaminhamentos.jsx"
need_file "frontend/src/TelaCrasTarefas.jsx"

# Usa grep literal (-F) para evitar erro de regex com chaves/pipe.
must_grep() {
  local f="$1"
  local pat="$2"
  if ! grep -Fq -- "$pat" "$f"; then
    echo "ERRO: padrão não encontrado em $f: $pat"
    exit 1
  fi
}

# CrasApp: subtabs e wiring
must_grep "frontend/src/CrasApp.jsx" 'encaminhamentos: ['
must_grep "frontend/src/CrasApp.jsx" '{ key: "suas", label: "Encaminhamento SUAS" }'
must_grep "frontend/src/CrasApp.jsx" 'tarefas: ['
must_grep "frontend/src/CrasApp.jsx" '{ key: "por_tecnico", label: "Por técnico" }'

must_grep "frontend/src/CrasApp.jsx" 'case "encaminhamentos":'
must_grep "frontend/src/CrasApp.jsx" 'subView={activeSubtab || "suas"}'
must_grep "frontend/src/CrasApp.jsx" 'onSubViewChange={setActiveSubtab}'

must_grep "frontend/src/CrasApp.jsx" 'case "tarefas":'
must_grep "frontend/src/CrasApp.jsx" 'subView={activeSubtab || "por_tecnico"}'
must_grep "frontend/src/CrasApp.jsx" 'onSubViewChange={setActiveSubtab}'

# Gestão: cases existem
must_grep "frontend/src/CrasApp.jsx" 'case "automacoes":'
must_grep "frontend/src/CrasApp.jsx" 'case "documentos":'
must_grep "frontend/src/CrasApp.jsx" 'case "relatorios":'

# Telas: subviews
must_grep "frontend/src/TelaCrasEncaminhamentos.jsx" 'const view = String(subView || "suas");'
must_grep "frontend/src/TelaCrasEncaminhamentos.jsx" 'view === "todos"'

must_grep "frontend/src/TelaCrasTarefas.jsx" 'const view = String(subView || "por_tecnico");'
must_grep "frontend/src/TelaCrasTarefas.jsx" 'CRAS_TAREFAS_SUBVIEWS_V1'

echo "OK: CRAS Encaminhamentos/Tarefas clicáveis no header + Gestão ativa."
