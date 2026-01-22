#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-.}"

fail(){ echo "FAIL: $*"; exit 1; }

[ -f "$ROOT/frontend/src/CrasApp.jsx" ] || fail "frontend/src/CrasApp.jsx não encontrado"
[ -f "$ROOT/frontend/src/components/CrasPageHeader.jsx" ] || fail "frontend/src/components/CrasPageHeader.jsx não encontrado"
[ -f "$ROOT/frontend/src/TelaCras.jsx" ] || fail "frontend/src/TelaCras.jsx não encontrado"
[ -f "$ROOT/frontend/src/cras_ui_v2.css" ] || fail "frontend/src/cras_ui_v2.css não encontrado"

# checks

grep -q "TAB_SUBTABS_PAIF_V1" "$ROOT/frontend/src/CrasApp.jsx" || fail "CrasApp.jsx sem TAB_SUBTABS_PAIF_V1"
grep -q "view={activeSubtab" "$ROOT/frontend/src/CrasApp.jsx" || fail "CrasApp.jsx não passa view para TelaCras"
grep -q "help={activeHelp}" "$ROOT/frontend/src/CrasApp.jsx" || fail "CrasApp.jsx não passa help para CrasPageHeader"

grep -q "cras-help-card" "$ROOT/frontend/src/components/CrasPageHeader.jsx" || fail "CrasPageHeader.jsx sem help card"
grep -q "Ver como usar" "$ROOT/frontend/src/components/CrasPageHeader.jsx" || fail "CrasPageHeader.jsx sem botão 'Ver como usar'"

grep -q "export default function TelaCras({ apiBase, apiFetch, usuarioLogado, view" "$ROOT/frontend/src/TelaCras.jsx" || fail "TelaCras.jsx sem view prop"
grep -q "activeView === \"unidade\"" "$ROOT/frontend/src/TelaCras.jsx" || fail "TelaCras.jsx sem visão 'unidade'"

grep -q "HELP_CARD_V1" "$ROOT/frontend/src/cras_ui_v2.css" || fail "CSS sem HELP_CARD_V1"

echo "OK: verify_cras_paif_subtabs_help_v1 (Triagem+PAIF: subtelas + ajuda contextual)"
