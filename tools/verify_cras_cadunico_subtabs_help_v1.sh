#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-.}"

fail(){ echo "FAIL: $*"; exit 1; }

[ -f "$ROOT/frontend/src/CrasApp.jsx" ] || fail "frontend/src/CrasApp.jsx não encontrado"
[ -f "$ROOT/frontend/src/TelaCrasCadUnico.jsx" ] || fail "frontend/src/TelaCrasCadUnico.jsx não encontrado"
[ -f "$ROOT/frontend/src/components/CrasPageHeader.jsx" ] || fail "frontend/src/components/CrasPageHeader.jsx não encontrado"

# CrasApp: subtabs + help

grep -q "cadunico: \[" "$ROOT/frontend/src/CrasApp.jsx" || fail "CrasApp.jsx sem subtabs de cadunico"
grep -q "{ key: \"precadastro\"" "$ROOT/frontend/src/CrasApp.jsx" || fail "CrasApp.jsx sem subtab precadastro"
grep -q "{ key: \"agendamentos\"" "$ROOT/frontend/src/CrasApp.jsx" || fail "CrasApp.jsx sem subtab agendamentos"
grep -q "{ key: \"pendencias\"" "$ROOT/frontend/src/CrasApp.jsx" || fail "CrasApp.jsx sem subtab pendencias"
grep -q "{ key: \"historico\"" "$ROOT/frontend/src/CrasApp.jsx" || fail "CrasApp.jsx sem subtab historico"

grep -q "cadunico: \"precadastro\"" "$ROOT/frontend/src/CrasApp.jsx" || fail "CrasApp.jsx sem defaultSubtab cadunico precadastro"

grep -q "case \"cadunico\"" "$ROOT/frontend/src/CrasApp.jsx" || fail "CrasApp.jsx sem case cadunico"
grep -q "view={activeSubtab || \"precadastro\"}" "$ROOT/frontend/src/CrasApp.jsx" || fail "CrasApp.jsx não passa view para TelaCrasCadUnico"

grep -q "cadunico: {" "$ROOT/frontend/src/CrasApp.jsx" || fail "CrasApp.jsx sem help cadunico"

# Tela

grep -q "CRAS_CADUNICO_SUBTABS_HELP_V1" "$ROOT/frontend/src/TelaCrasCadUnico.jsx" || fail "TelaCrasCadUnico.jsx sem marker"
grep -q "view = \"precadastro\"" "$ROOT/frontend/src/TelaCrasCadUnico.jsx" || fail "TelaCrasCadUnico.jsx sem view default"
grep -q "activeView" "$ROOT/frontend/src/TelaCrasCadUnico.jsx" || fail "TelaCrasCadUnico.jsx sem activeView"

# Header: ajuda

grep -q "Ver como usar" "$ROOT/frontend/src/components/CrasPageHeader.jsx" || fail "CrasPageHeader.jsx sem botão Ver como usar"

echo "OK: verify_cras_cadunico_subtabs_help_v1 (CadÚnico: subtelas + guia rápido)"
