#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CRAS Encaminhamentos Split View 35/65 — Patch V2 (fix script)
- Conserta SyntaxError do V1 (escaping).
- Aplica split view com mínimo de risco:
  * Extrai <EncaminhamentosSuas .../> (auto-fechamento)
  * Abre wrapper .cras-enc-split com coluna esquerda (35%) contendo o restante do conteúdo
  * Coloca EncaminhamentosSuas na coluna direita (65%)
  * Fecha wrappers antes do fechamento final do root do JSX (</div> ou </>)
- Faz backup automático do arquivo antes de escrever.
"""

from pathlib import Path
from datetime import datetime
import re
import sys

ROOT = Path.home() / "POPNEWS1"
target = ROOT / "frontend/src/TelaCrasEncaminhamentos.jsx"
css_path = ROOT / "frontend/src/cras_ui_v2.css"

if not target.exists():
    raise SystemExit(f"Arquivo não encontrado: {target}")

txt = target.read_text(encoding="utf-8", errors="ignore")

marker = "CRAS_ENC_SPLITVIEW_35_65_V2"
if marker in txt:
    print("OK: SplitView já aplicado (V2).")
    raise SystemExit(0)

# 1) Encontrar o componente EncaminhamentosSuas (auto-fechamento)
m = re.search(r"<\s*EncaminhamentosSuas\b[^>]*?/>", txt, flags=re.S)
if not m:
    raise SystemExit("Não encontrei <EncaminhamentosSuas .../> em TelaCrasEncaminhamentos.jsx (abortando por segurança).")

enc_tag = m.group(0)

# 2) Substituir a ocorrência pelo OPEN do split/left
open_left = f'''<div className="cras-enc-split" data-split="{marker}">
            <div className="cras-enc-left">
              <div className="cras-enc-left-stack">'''
txt2 = txt[:m.start()] + open_left + txt[m.end():]

# 3) Inserir o CLOSE do left + right (com enc_tag) antes do fechamento do root do return
#    Regra: inserir antes do último </div> ou </> no arquivo (geralmente fecha o root do JSX).
close_block = f'''              </div>
            </div>
            <div className="cras-enc-right">
              {enc_tag}
            </div>
          </div>'''

# Tenta inserir antes do último </div> (mais comum)
pos_div = txt2.rfind("</div>")
pos_frag = txt2.rfind("</>")

insert_pos = -1
if pos_div != -1 and (pos_frag == -1 or pos_div > pos_frag):
    insert_pos = pos_div
elif pos_frag != -1:
    insert_pos = pos_frag

if insert_pos == -1:
    raise SystemExit("Não consegui localizar o fechamento final do JSX (</div> ou </>). Abortando para não quebrar sintaxe.")

txt2 = txt2[:insert_pos] + close_block + "\n" + txt2[insert_pos:]

# 4) Backup + escrever
bak = target.with_suffix(target.suffix + ".bak_" + datetime.now().strftime("%Y%m%d_%H%M%S"))
bak.write_text(txt, encoding="utf-8")
target.write_text(txt2, encoding="utf-8")
print("✅ OK: SplitView aplicado em", target)
print("Backup:", bak)

# 5) CSS: adicionar (se existir cras_ui_v2.css)
if css_path.exists():
    css = css_path.read_text(encoding="utf-8", errors="ignore")
    css_marker = "/* CRAS_ENC_SPLITVIEW_35_65_CSS_V2 */"
    if css_marker not in css:
        css_add = '''
\n\n/* CRAS_ENC_SPLITVIEW_35_65_CSS_V2 */
.cras-ui-v2 .cras-enc-split{
  display: grid;
  grid-template-columns: 0.35fr 0.65fr;
  gap: 16px;
  align-items: start;
}
.cras-ui-v2 .cras-enc-left{
  min-width: 0;
}
.cras-ui-v2 .cras-enc-right{
  min-width: 0;
}
.cras-ui-v2 .cras-enc-left-stack{
  display: flex;
  flex-direction: column;
  gap: 14px;
}
@media (max-width: 980px){
  .cras-ui-v2 .cras-enc-split{
    grid-template-columns: 1fr;
  }
}
'''
        css_path.write_text(css + css_add, encoding="utf-8")
        print("✅ CSS SplitView adicionado em", css_path)
else:
    print("⚠️ Não achei cras_ui_v2.css para adicionar CSS automaticamente (ok se não estiver usando).")
