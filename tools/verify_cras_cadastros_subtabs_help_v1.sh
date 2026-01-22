#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-.}"

fail(){ echo "FAIL: $*"; exit 1; }

[ -f "$ROOT/frontend/src/CrasApp.jsx" ] || fail "frontend/src/CrasApp.jsx não encontrado"
[ -f "$ROOT/frontend/src/TelaCrasCadastros.jsx" ] || fail "frontend/src/TelaCrasCadastros.jsx não encontrado"
[ -f "$ROOT/frontend/src/components/CrasPageHeader.jsx" ] || fail "frontend/src/components/CrasPageHeader.jsx não encontrado"

# CrasApp: subtabs + help

grep -q "cadastros: \[" "$ROOT/frontend/src/CrasApp.jsx" || fail "CrasApp.jsx sem subtabs de cadastros"
grep -q "{ key: \"pessoas\"" "$ROOT/frontend/src/CrasApp.jsx" || fail "CrasApp.jsx sem subtab pessoas"
grep -q "{ key: \"familias\"" "$ROOT/frontend/src/CrasApp.jsx" || fail "CrasApp.jsx sem subtab familias"
grep -q "{ key: \"vinculos\"" "$ROOT/frontend/src/CrasApp.jsx" || fail "CrasApp.jsx sem subtab vinculos"
grep -q "{ key: \"atualizacao\"" "$ROOT/frontend/src/CrasApp.jsx" || fail "CrasApp.jsx sem subtab atualizacao"

grep -q "cadastros: \"pessoas\"" "$ROOT/frontend/src/CrasApp.jsx" || fail "CrasApp.jsx sem defaultSubtab cadastros pessoas"

grep -q "case \"cadastros\"" "$ROOT/frontend/src/CrasApp.jsx" || fail "CrasApp.jsx sem case cadastros"
grep -q "view={activeSubtab || \"pessoas\"}" "$ROOT/frontend/src/CrasApp.jsx" || fail "CrasApp.jsx não passa view para TelaCrasCadastros"

grep -q "cadastros: {" "$ROOT/frontend/src/CrasApp.jsx" || fail "CrasApp.jsx sem help cadastros"

# Tela

grep -q "CADASTROS_SUBTABS_HELP_V1" "$ROOT/frontend/src/TelaCrasCadastros.jsx" || fail "TelaCrasCadastros.jsx sem marker"
grep -q "view = \"pessoas\"" "$ROOT/frontend/src/TelaCrasCadastros.jsx" || fail "TelaCrasCadastros.jsx sem view default"

# Header: ajuda

grep -q "Ver como usar" "$ROOT/frontend/src/components/CrasPageHeader.jsx" || fail "CrasPageHeader.jsx sem botão Ver como usar"

echo "OK: verify_cras_cadastros_subtabs_help_v1 (Cadastros: subtelas + guia rápido)"
