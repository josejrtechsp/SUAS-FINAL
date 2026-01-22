#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime

css_path = Path.home() / "POPNEWS1/frontend/src/cras_ui_v2.css"
if not css_path.exists():
    raise SystemExit(f"Não achei {css_path}")

css = css_path.read_text(encoding="utf-8", errors="ignore")
marker = "CRAS_APPLE_BUTTONS_V2_COMPACT"
if marker in css:
    print("OK: já aplicado (V2_COMPACT).")
    raise SystemExit(0)

bak = css_path.with_suffix(css_path.suffix + ".bak_" + datetime.now().strftime("%Y%m%d_%H%M%S"))
bak.write_text(css, encoding="utf-8")
css_path.write_text(css.rstrip() + "\n\n" + '/* CRAS_APPLE_BUTTONS_V2_COMPACT\n   Refinamento: botões menos "inflados" e sem largura mínima fixa nos cards.\n   Escopo: somente .cras-ui-v2\n*/\n\n.cras-ui-v2 :is(.btn, button.btn, a.btn){\n  height: 32px !important;\n  padding: 0 14px !important;\n  line-height: 30px !important;\n}\n\n/* Cards: NÃO forçar min-width grande (deixa o texto ditar a largura) */\n.cras-ui-v2 .card :is(.btn-primario, .btn-secundario){\n  min-width: unset !important;\n}\n\n/* Secundário vira mais "ghost" */\n.cras-ui-v2 .btn-secundario,\n.cras-ui-v2 .btn.btn-secundario{\n  background: rgba(255,255,255,.72) !important;\n  border: 1px solid rgba(226,232,240,.92) !important;\n}\n\n/* Segmentados (ex.: Recebidos/Enviados): encaixe e tamanho */\n.cras-ui-v2 .card :is(.segmented, .tabs, .tablist){\n  display: inline-flex;\n  gap: 10px;\n  align-items: center;\n}\n\n.cras-ui-v2 .card :is(.segmented button, .tabs button, .tablist button){\n  height: 32px;\n  padding: 0 14px;\n  border-radius: 999px;\n}\n' + "\n", encoding="utf-8")
print("OK: aplicado V2_COMPACT em", css_path)
print("Backup:", bak)
