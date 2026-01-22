#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-.}"
cd "$ROOT"
test -f frontend/src/RmaQuickPanel.jsx || { echo "ERRO: RmaQuickPanel.jsx ausente"; exit 2; }
test -f frontend/src/ProntuarioQuickExport.jsx || { echo "ERRO: ProntuarioQuickExport.jsx ausente"; exit 2; }
grep -Fq 'import RmaQuickPanel' frontend/src/TelaCrasRelatorios.jsx || { echo "ERRO: Relatórios não importou RmaQuickPanel"; exit 2; }
echo "OK: verify_front_rma_panel_prontuario_buttons_v1"
