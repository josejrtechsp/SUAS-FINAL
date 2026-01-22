#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-.}"

need_file() {
  local f="$1"
  if [ ! -f "$ROOT/$f" ]; then
    echo "ERRO: arquivo não encontrado: $f" >&2
    exit 1
  fi
}

need_grep() {
  local f="$1"; shift
  local pat="$1"; shift
  if ! grep -Fq "$pat" "$ROOT/$f"; then
    echo "ERRO: padrão não encontrado em $f: $pat" >&2
    exit 1
  fi
}

need_file "backend/app/routers/cras.py"
need_file "backend/app/models/cras_triagem.py"
need_file "backend/app/models/cras_paif.py"
need_file "backend/app/models/pessoa_identidade_link.py"
need_file "backend/app/core/db.py"

need_grep "backend/app/routers/cras.py" "converter_triagem_em_paif"
need_grep "backend/app/routers/cras.py" "PessoaIdentidadeLink"
need_grep "backend/app/routers/cras.py" "CasoCras"
need_grep "backend/app/routers/cras.py" "return {\"triagem\": tri, \"paif\": paif, \"caso\": caso}"

need_grep "backend/app/models/cras_triagem.py" "pessoa_suas_id"
need_grep "backend/app/models/cras_triagem.py" "caso_id"
need_grep "backend/app/models/cras_paif.py" "pessoa_suas_id"
need_grep "backend/app/models/cras_paif.py" "caso_id"
need_grep "backend/app/core/db.py" "app.models.pessoa_identidade_link"
need_grep "backend/app/core/db.py" "ALTER TABLE paif_acompanhamento ADD COLUMN pessoa_suas_id"
need_grep "backend/app/core/db.py" "ALTER TABLE cras_triagem ADD COLUMN caso_id"

echo "OK: BACK CRAS Triagem abre Caso (V1) aplicado." 
