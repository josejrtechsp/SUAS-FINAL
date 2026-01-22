#!/usr/bin/env bash
set -euo pipefail

if [ $# -lt 2 ]; then
  echo "Uso: $0 <chave_modulo> <Titulo no topo> [Subtitulo]"
  echo "Ex.: $0 equipamentos \"Equipamentos\" \"Gestão de unidades, equipe e agenda\""
  exit 1
fi

KEY="$1"
TITLE="$2"
SUBTITLE="${3:-}"

# PascalCase simples
PASCAL="$(echo "$KEY" | sed -E 's/[^a-zA-Z0-9]+/ /g' | awk '{for(i=1;i<=NF;i++){ $i=toupper(substr($i,1,1)) substr($i,2)}; printf "%s", $0}' | tr -d ' ')"

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

COMP_DIR="frontend/src/components"
TOP_FILE="$COMP_DIR/${PASCAL}TopHeader.jsx"
PAGE_FILE="$COMP_DIR/${PASCAL}PageHeader.jsx"

mkdir -p "$COMP_DIR"

cat > "$TOP_FILE" <<EOF
import React from "react";
import SuasTopHeader from "./SuasTopHeader.jsx";

export default function ${PASCAL}TopHeader(props) {
  return (
    <SuasTopHeader
      {...props}
      titleRight="${TITLE}"
      subtitle={\`${SUBTITLE}\`}
      // Se o módulo tiver Unidade, defina unidadeLabel e onPortal no seu App:
      // unidadeLabel="Unidade:"
      // onPortal={() => ...}
      // tabs={[{ key: "painel", label: "Painel" }]}
    />
  );
}
EOF

cat > "$PAGE_FILE" <<EOF
import React from "react";
import CrasPageHeader from "./CrasPageHeader.jsx";

export default function ${PASCAL}PageHeader(props) {
  return <CrasPageHeader moduleChip="" {...props} />;
}
EOF

# O JS acima não pode usar python; então corrigimos o chip com sed:
# chip = primeiros 8 chars do TITLE (sem espaços)
CHIP="$(echo "$TITLE" | tr -d ' ' | cut -c1-8 | tr '[:lower:]' '[:upper:]')"
perl -pi -e "s/moduleChip=\"\"/moduleChip=\"$CHIP\"/g" "$PAGE_FILE"

echo "✅ Criados:"
echo " - $TOP_FILE"
echo " - $PAGE_FILE"
echo
echo "Próximo passo: no App do módulo, importe ${PASCAL}TopHeader e use no topo."
