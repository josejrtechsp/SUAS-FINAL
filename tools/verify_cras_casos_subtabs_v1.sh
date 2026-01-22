#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-.}"

fail(){ echo "FAIL: $*"; exit 1; }

[ -f "$ROOT/frontend/src/CrasApp.jsx" ] || fail "frontend/src/CrasApp.jsx não encontrado"
[ -f "$ROOT/frontend/src/components/CrasPageHeader.jsx" ] || fail "frontend/src/components/CrasPageHeader.jsx não encontrado"
[ -f "$ROOT/frontend/src/TelaCrasCasos.jsx" ] || fail "frontend/src/TelaCrasCasos.jsx não encontrado"
[ -f "$ROOT/frontend/src/cras_ui_v2.css" ] || fail "frontend/src/cras_ui_v2.css não encontrado"

# checks
grep -q "TAB_SUBTABS_CASOS_V1" "$ROOT/frontend/src/CrasApp.jsx" || fail "CrasApp.jsx sem TAB_SUBTABS_CASOS_V1"
grep -q "subtabs={headerSubtabs}" "$ROOT/frontend/src/CrasApp.jsx" || fail "CrasApp.jsx não passa subtabs para CrasPageHeader"
grep -q "view={activeSubtab" "$ROOT/frontend/src/CrasApp.jsx" || fail "CrasApp.jsx não passa view para TelaCrasCasos"

grep -q "cras-pageheader-v2-subtabs" "$ROOT/frontend/src/components/CrasPageHeader.jsx" || fail "CrasPageHeader.jsx sem render de subtabs"
grep -q "export default function TelaCrasCasos({ apiBase, apiFetch, usuarioLogado, view" "$ROOT/frontend/src/TelaCrasCasos.jsx" || fail "TelaCrasCasos.jsx sem view prop"

grep -q "cras-pageheader-v2-subtabs" "$ROOT/frontend/src/cras_ui_v2.css" || fail "CSS sem estilos de subtabs"

echo "OK: verify_cras_casos_subtabs_v1 (subtelas no header para Casos)"
