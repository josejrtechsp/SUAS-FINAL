#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
echo "== Verificando SUS Sandbox Back V4 =="

need=(
  "sus_sandbox_backend/app/db.py"
  "sus_sandbox_backend/app/routers/sus.py"
)

for f in "${need[@]}"; do
  [[ -f "$ROOT/$f" ]] || { echo "FALTA: $f"; exit 1; }
done

SUS="$ROOT/sus_sandbox_backend/app/routers/sus.py"

# robust checks (do not depend on exact quote escaping)
grep -q "/auditoria" "$SUS" || { echo "FALTA: endpoint auditoria (/auditoria)"; exit 1; }
grep -q "def list_auditoria" "$SUS" || { echo "FALTA: handler list_auditoria"; exit 1; }
grep -q "FECHADA (edição bloqueada)" "$SUS" || { echo "FALTA: lock por competência"; exit 1; }
grep -q "termo_fechamento" "$SUS" || { echo "FALTA: termo de fechamento"; exit 1; }
grep -q "/download" "$SUS" || { echo "FALTA: download de relatório"; exit 1; }

echo "OK: backend V4 instalado (lock + auditoria + termo + download)."
