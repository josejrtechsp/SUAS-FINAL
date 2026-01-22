#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-.}"

fail(){ echo "ERRO: $1"; exit 1; }

A="$ROOT/frontend/src/TelaCrasAutomacoes.jsx"
D="$ROOT/frontend/src/TelaCrasDocumentos.jsx"
R="$ROOT/frontend/src/TelaCrasRelatorios.jsx"

test -f "$A" || fail "não achei $A"
test -f "$D" || fail "não achei $D"
test -f "$R" || fail "não achei $R"

python3 - <<'PY'
from pathlib import Path
import re, sys

def chk(msg, ok):
    if not ok:
        print("ERRO:", msg)
        sys.exit(1)

a = Path("frontend/src/TelaCrasAutomacoes.jsx").read_text(encoding="utf-8")
d = Path("frontend/src/TelaCrasDocumentos.jsx").read_text(encoding="utf-8")
r = Path("frontend/src/TelaCrasRelatorios.jsx").read_text(encoding="utf-8")

# Automacoes: viewKey deve existir em escopo do componente, antes de canEdit
m_vk = re.search(r'^\s*const\s+viewKey\s*=\s*String\(view\s*\|\|\s*"ativas"\)\.toLowerCase\(\)\s*;', a, re.M)
m_ce = re.search(r'^\s*const\s+canEdit\s*=\s*useMemo', a, re.M)
chk("TelaCrasAutomacoes: não achei const viewKey", bool(m_vk))
chk("TelaCrasAutomacoes: não achei const canEdit", bool(m_ce))
chk("TelaCrasAutomacoes: viewKey está depois de canEdit (escopo errado)", m_vk.start() < m_ce.start())

# Documentos: precisa de viewKey
chk("TelaCrasDocumentos: não achei const viewKey", 'const viewKey = String(view || "modelos").toLowerCase();' in d)

# Relatorios: assinatura deve incluir view e onSetView e não deve ter overviewKpis undefined antigo
chk("TelaCrasRelatorios: assinatura não inclui view/onSetView", "view = \"painel\"" in r and "onSetView" in r)
chk("TelaCrasRelatorios: não achei const viewKey", 'const viewKey = String(view || "painel").toLowerCase();' in r)
chk("TelaCrasRelatorios: ainda contém map antigo de overviewKpis", "overviewKpis || []).map" not in r)

print("OK: Gestão runtime fix (viewKey + onSetView) aplicado.")
PY
