#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime

ROOT = Path.home() / "POPNEWS1"
css_path = ROOT / "frontend/src/cras_ui_v2.css"

if not css_path.exists():
    raise SystemExit(f"Não achei {css_path}. Você está no projeto certo?")

css = css_path.read_text(encoding="utf-8", errors="ignore")
marker = "/* CRAS_APPLE_BUTTONS_V1 */"
if marker in css:
    print("OK: já aplicado (CRAS_APPLE_BUTTONS_V1).")
    raise SystemExit(0)

bak = css_path.with_suffix(css_path.suffix + ".bak_" + datetime.now().strftime("%Y%m%d_%H%M%S"))
bak.write_text(css, encoding="utf-8")
print("Backup:", bak)

addon = r'''/* CRAS_APPLE_BUTTONS_V1
   Unifica botões do CRAS (estética Apple-like): menos "inflado", mais limpo.
   Escopo: somente .cras-ui-v2
*/
.cras-ui-v2 :is(.btn, button.btn, a.btn){
  height: 34px;
  padding: 0 14px;
  border-radius: 999px;
  font-weight: 800;
  letter-spacing: -0.01em;
  line-height: 32px;
}

.cras-ui-v2 .btn-primario,
.cras-ui-v2 .btn.btn-primario{
  box-shadow: 0 10px 26px rgba(99,102,241,.14);
}

.cras-ui-v2 .btn-secundario,
.cras-ui-v2 .btn.btn-secundario{
  background: rgba(255,255,255,.78);
  border: 1px solid rgba(226,232,240,.92);
  box-shadow: none;
}

.cras-ui-v2 .btn-secundario:hover{
  border-color: rgba(199,210,254,.95);
  transform: translateY(-1px);
}

/* Botões em cards de item (ex.: Encaminhamentos): alinhamento e largura */
.cras-ui-v2 .card :is(.btn-primario, .btn-secundario){
  min-width: 140px;
}

@media (max-width: 980px){
  .cras-ui-v2 .card :is(.btn-primario, .btn-secundario){
    min-width: 124px;
  }
}
'''

css_path.write_text(css.rstrip() + "\n\n" + addon.strip() + "\n", encoding="utf-8")
print("OK: aplicado CRAS_APPLE_BUTTONS_V1 em", css_path)
