#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CRAS Encaminhamentos Split View 35/65 — Patch V3
Corrige a detecção do componente EncaminhamentosSuas:
- Aceita <EncaminhamentosSuas .../> (self-closing) OU
  <EncaminhamentosSuas ...>...</EncaminhamentosSuas>
Aplica split view 35/65 com backup e adiciona CSS no cras_ui_v2.css.
"""

from pathlib import Path
from datetime import datetime
import re

ROOT = Path.home() / "POPNEWS1"
target = ROOT / "frontend/src/TelaCrasEncaminhamentos.jsx"
css_path = ROOT / "frontend/src/cras_ui_v2.css"

if not target.exists():
    raise SystemExit(f"Arquivo não encontrado: {target}")

txt = target.read_text(encoding="utf-8", errors="ignore")

marker = "CRAS_ENC_SPLITVIEW_35_65_V3"
if marker in txt:
    print("OK: SplitView já aplicado (V3).")
    raise SystemExit(0)

CANDIDATES = ["EncaminhamentosSuas", "EncaminhamentosSUAS"]

def find_component_block(source: str, name: str):
    # 1) self-closing
    m1 = re.search(rf"<\s*{name}\b[^>]*?/>", source, flags=re.S)
    if m1:
        return m1.group(0), m1.start(), m1.end()
    # 2) paired (non-greedy)
    m2 = re.search(rf"<\s*{name}\b[^>]*?>.*?</\s*{name}\s*>", source, flags=re.S)
    if m2:
        return m2.group(0), m2.start(), m2.end()
    return None

found = None
for nm in CANDIDATES:
    found = find_component_block(txt, nm)
    if found:
        break

if not found:
    # Ajuda: imprime 20 linhas com "Encaminh" para o usuário diagnosticar
    lines = txt.splitlines()
    hits = [ (i+1, l) for i,l in enumerate(lines) if "Encaminh" in l ]
    print("Não encontrei componente EncaminhamentosSuas/SUAS na tela.")
    print("Trechos com 'Encaminh' (até 20 linhas):")
    for i,l in hits[:20]:
        print(f"{i}: {l[:200]}")
    raise SystemExit(1)

enc_tag, start, end = found

open_left = f'''<div className="cras-enc-split" data-split="{marker}">
            <div className="cras-enc-left">
              <div className="cras-enc-left-stack">'''

txt2 = txt[:start] + open_left + txt[end:]

close_block = f'''              </div>
            </div>
            <div className="cras-enc-right">
              {enc_tag}
            </div>
          </div>'''

# inserir antes do último fechamento do root do JSX
pos_div = txt2.rfind("</div>")
pos_frag = txt2.rfind("</>")

insert_pos = -1
if pos_div != -1 and (pos_frag == -1 or pos_div > pos_frag):
    insert_pos = pos_div
elif pos_frag != -1:
    insert_pos = pos_frag

if insert_pos == -1:
    raise SystemExit("Não consegui localizar o fechamento final do JSX (</div> ou </>). Abortando.")

txt2 = txt2[:insert_pos] + close_block + "\n" + txt2[insert_pos:]

bak = target.with_suffix(target.suffix + ".bak_" + datetime.now().strftime("%Y%m%d_%H%M%S"))
bak.write_text(txt, encoding="utf-8")
target.write_text(txt2, encoding="utf-8")
print("✅ OK: SplitView aplicado em", target)
print("Backup:", bak)

# CSS
if css_path.exists():
    css = css_path.read_text(encoding="utf-8", errors="ignore")
    css_marker = "/* CRAS_ENC_SPLITVIEW_35_65_CSS_V3 */"
    if css_marker not in css:
        css_add = '''
\n\n/* CRAS_ENC_SPLITVIEW_35_65_CSS_V3 */
.cras-ui-v2 .cras-enc-split{
  display: grid;
  grid-template-columns: 0.35fr 0.65fr;
  gap: 16px;
  align-items: start;
}
.cras-ui-v2 .cras-enc-left{ min-width: 0; }
.cras-ui-v2 .cras-enc-right{ min-width: 0; }
.cras-ui-v2 .cras-enc-left-stack{
  display: flex;
  flex-direction: column;
  gap: 14px;
}
@media (max-width: 980px){
  .cras-ui-v2 .cras-enc-split{ grid-template-columns: 1fr; }
}
'''
        css_path.write_text(css + css_add, encoding="utf-8")
        print("✅ CSS SplitView adicionado em", css_path)
else:
    print("⚠️ cras_ui_v2.css não encontrado — pulei CSS.")
