#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
echo "== Verificando SUS Sandbox Back V3 =="

need=(
  "sus_sandbox_backend/app/db.py"
  "sus_sandbox_backend/app/utils.py"
  "sus_sandbox_backend/app/routers/sus.py"
)

for f in "${need[@]}"; do
  [[ -f "$ROOT/$f" ]] || { echo "FALTA: $f"; exit 1; }
done

grep -q "/relatorios/gerar" "$ROOT/sus_sandbox_backend/app/routers/sus.py" || { echo "FALTA endpoint /relatorios/gerar"; exit 1; }
grep -q "_auto_conformidade_items" "$ROOT/sus_sandbox_backend/app/routers/sus.py" || { echo "FALTA conformidade auto"; exit 1; }

echo "OK: backend V3 (competência/prazo/conformidade auto/relatórios) instalado."
