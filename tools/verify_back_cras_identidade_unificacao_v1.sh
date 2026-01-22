#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-.}"

need_file() {
  local f="$1"
  if [[ ! -f "$ROOT/$f" ]]; then
    echo "ERRO: arquivo não encontrado: $f" >&2
    exit 1
  fi
}

need_grep_f() {
  local f="$1"; shift
  local pat="$1"; shift
  if ! grep -qF "$pat" "$ROOT/$f"; then
    echo "ERRO: padrão não encontrado em $f: $pat" >&2
    exit 1
  fi
}

# Arquivos novos
need_file "backend/app/models/pessoa_identidade_link.py"
need_file "backend/app/routers/cras_identidade.py"

# Integrações
need_grep_f "backend/app/main.py" "from app.routers.cras_identidade import router as cras_identidade_router"
need_grep_f "backend/app/main.py" "app.include_router(cras_identidade_router)"

need_grep_f "backend/app/core/db.py" "app.models.pessoa_identidade_link"

# Colunas auxiliares nos models
need_grep_f "backend/app/models/cras_paif.py" "pessoa_suas_id"
need_grep_f "backend/app/models/cras_triagem.py" "pessoa_suas_id"
need_grep_f "backend/app/models/cras_encaminhamento.py" "pessoa_suas_id"

# Bug fix: municipio_id no listar_paif
need_grep_f "backend/app/routers/cras.py" "municipio_id: Optional[int] = Query(default=None)"

# CadÚnico filtros
need_grep_f "backend/app/routers/cras_cadunico.py" "caso_id: Optional[int] = Query(default=None)"

# Ficha 360 inclui poprua
need_grep_f "backend/app/routers/cras_ficha.py" "poprua":

echo "OK: PATCH_BACK_CRAS_IDENTIDADE_UNIFICACAO_V1 aplicado." 
