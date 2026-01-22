#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

TOP="frontend/src/components/SuasTopHeader.jsx"
PAGE="frontend/src/components/CrasPageHeader.jsx"
CSS="frontend/src/App.css"
WR_CRAS="frontend/src/components/CrasTopHeader.jsx"
WR_CREAS="frontend/src/components/CreasTopHeader.jsx"

err(){ echo "❌ $1"; exit 1; }

[ -f "$TOP" ] || err "Faltando $TOP"
[ -f "$PAGE" ] || err "Faltando $PAGE"
[ -f "$CSS" ] || err "Faltando $CSS"
[ -f "$WR_CRAS" ] || err "Faltando $WR_CRAS"
[ -f "$WR_CREAS" ] || err "Faltando $WR_CREAS"

# SuasTopHeader precisa usar as classes do PopRua
grep -q 'className="app-header"' "$TOP" || err "SuasTopHeader não usa class app-header"
grep -q 'className="app-tabs"' "$TOP"   || err "SuasTopHeader não usa class app-tabs"
grep -q 'btn-logout' "$TOP"             || err "SuasTopHeader não renderiza botão Sair no padrão PopRua"

# Ninguém mais pode ter app-header além do SuasTopHeader
BAD=$(grep -R 'className="app-header"' -n frontend/src/components/*.jsx | grep -v 'SuasTopHeader.jsx' || true)
if [ -n "$BAD" ]; then
  echo "$BAD"
  err "Existe outro componente com app-header. O topo deve ser único (SuasTopHeader)."
fi

# PageHeader full width (pra não encolher no flex-wrap)
grep -q 'flex: "0 0 100%"' "$PAGE" || err "CrasPageHeader não está full width (flex 0 0 100%)"
grep -q 'width: "100%"' "$PAGE"    || err "CrasPageHeader não está full width (width 100%)"

# Wrappers devem importar SuasTopHeader (ou indireto via CrasTopHeader wrapper)
grep -q 'from "./SuasTopHeader.jsx"' "$WR_CRAS" || err "CrasTopHeader não está apontando para SuasTopHeader"
grep -q 'from "./SuasTopHeader.jsx"' "$WR_CREAS" || err "CreasTopHeader não está apontando para SuasTopHeader"

# CSS precisa ter os blocos do header
grep -q '^\.app-header' "$CSS" || err "App.css não contém .app-header"
grep -q '^\.app-tabs' "$CSS"   || err "App.css não contém .app-tabs"

echo "✅ Padrão visual OK (topo PopRua travado + page-header fullwidth)."
