#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
echo "== Verificando SUS Sandbox Plan+Exec V1 =="

need=(
  "sus_sandbox_frontend/src/sus/SUSPlanoTab.jsx"
  "sus_sandbox_frontend/src/sus/SUSExecucaoTab.jsx"
  "sus_sandbox_frontend/src/sus/SUSGestaoPage.jsx"
)

for f in "${need[@]}"; do
  [[ -f "$ROOT/$f" ]] || { echo "FALTA: $f"; exit 1; }
done

grep -q "SUSPlanoTab" "$ROOT/sus_sandbox_frontend/src/sus/SUSGestaoPage.jsx" || { echo "FALTA: uso de SUSPlanoTab"; exit 1; }
grep -q "Gerar tarefa" "$ROOT/sus_sandbox_frontend/src/sus/SUSPlanoTab.jsx" || { echo "FALTA: botão Gerar tarefa"; exit 1; }

echo "OK: Plano (árvore) + Execução (Kanban) instalados."
echo "Dica: reinicie o Vite (Ctrl+C e npm run dev)."
