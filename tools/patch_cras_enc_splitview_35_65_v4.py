#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CRAS Encaminhamentos Split View 35/65 — Patch V4 (robusto)
Motivo: o componente <EncaminhamentosSuas ...> possui props com '=>', que contém '>' e quebra regex simples.
Este patch:
- Encontra o bloco JSX do componente EncaminhamentosSuas (self-closing ou tag pareada), usando regex 'tempered' que não quebra com '=>'
- Insere wrapper split após a tag de abertura do ROOT do return (primeiro elemento JSX após 'return (')
- Substitui o EncaminhamentosSuas por: fecha left, renderiza right com EncaminhamentosSuas, fecha split
- Adiciona CSS no cras_ui_v2.css
- Faz backup automático
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

marker = "CRAS_ENC_SPLITVIEW_35_65_V4"
if marker in txt:
    print("OK: SplitView já aplicado (V4).")
    raise SystemExit(0)

# 1) localizar return(
mret = re.search(r"return\s*\(", txt)
if not mret:
    raise SystemExit("Não encontrei 'return (' no arquivo (abortando).")

after_ret = txt[mret.end():]

# 2) achar o primeiro elemento JSX após return(
mroot = re.search(r"<\s*[A-Za-z]", after_ret)
if not mroot:
    raise SystemExit("Não encontrei o primeiro elemento JSX após return( (abortando).")

root_start = mret.end() + mroot.start()

# achar o fim da tag de abertura do root (primeiro '>' após root_start)
root_open_end = txt.find(">", root_start)
if root_open_end == -1:
    raise SystemExit("Não consegui localizar o fechamento da tag de abertura do root (>) (abortando).")

# 3) localizar EncaminhamentosSuas: self-closing OU pareado (robusto contra =>)
# self-closing: <EncaminhamentosSuas ... />
re_self = re.compile(r"<\s*EncaminhamentosSuas\b(?:(?!\/>).)*\/>", re.S)
# pareado: <EncaminhamentosSuas ...> ... </EncaminhamentosSuas>
re_pair = re.compile(r"<\s*EncaminhamentosSuas\b(?:(?!<\s*/\s*EncaminhamentosSuas\s*>).)*<\s*/\s*EncaminhamentosSuas\s*>", re.S)

m = re_self.search(txt)
if not m:
    m = re_pair.search(txt)

if not m:
    # ajuda: imprime as linhas próximas do componente importado
    lines = txt.splitlines()
    hits = [(i+1,l) for i,l in enumerate(lines) if "EncaminhamentosSuas" in l or "Encaminhamentos SUAS" in l]
    print("Não encontrei bloco JSX do EncaminhamentosSuas.")
    print("Linhas com 'EncaminhamentosSuas' (até 30):")
    for i,l in hits[:30]:
        print(f"{i}: {l[:220]}")
    raise SystemExit(1)

enc_block = m.group(0)

# 4) inserir abertura do split logo após abrir o root
open_split = f'''
    {{/* {marker} */}}
    <div className="cras-enc-split" data-split="{marker}">
      <div className="cras-enc-left">
        <div className="cras-enc-left-stack">
'''
txt2 = txt[:root_open_end+1] + open_split + txt[root_open_end+1:]

# 5) substituir o EncaminhamentosSuas pelo fechamento do left + right + close split
replacement = f'''
        </div>
      </div>
      <div className="cras-enc-right">
        {enc_block}
      </div>
    </div>
'''
# precisa substituir no txt2; mas a inserção mudou offsets. Rebuscar o bloco novamente.
m2 = re_self.search(txt2) or re_pair.search(txt2)
if not m2:
    raise SystemExit("Após inserir o wrapper, não consegui relocalizar o bloco EncaminhamentosSuas (abortando).")

txt2 = txt2[:m2.start()] + replacement + txt2[m2.end():]

# 6) backup + salvar
bak = target.with_suffix(target.suffix + ".bak_" + datetime.now().strftime("%Y%m%d_%H%M%S"))
bak.write_text(txt, encoding="utf-8")
target.write_text(txt2, encoding="utf-8")
print("✅ OK: SplitView V4 aplicado em", target)
print("Backup:", bak)

# 7) CSS
if css_path.exists():
    css = css_path.read_text(encoding="utf-8", errors="ignore")
    css_marker = "/* CRAS_ENC_SPLITVIEW_35_65_CSS_V4 */"
    if css_marker not in css:
        css_add = '''
\n\n/* CRAS_ENC_SPLITVIEW_35_65_CSS_V4 */
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
        print("✅ CSS SplitView V4 adicionado em", css_path)
else:
    print("⚠️ cras_ui_v2.css não encontrado — pulei CSS.")
