#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CRAS Encaminhamentos Split View 35/65 — Patch V8
Objetivo: aplicar SplitView 35/65 de forma robusta sem quebrar sintaxe.

Por que versões anteriores falharam:
- Regex simples quebra com '=>' em props e com '<div' em strings.
- Detecção de fechamento por indentação pode pegar o </div> errado.

Estratégia (V8):
1) Encontra o root do JSX: linha que começa com <div ... className="cras-flow-mini"
2) Encontra o fechamento correto do root por contagem de depth, mas contando apenas linhas que começam com <div ou </div> (evita '<div' em strings)
3) Dentro do root, encontra o bloco <EncaminhamentosSuas ...> (multilinha) e seu final (linha com '/>' ou '</EncaminhamentosSuas>')
4) Reescreve o conteúdo do root:
   - left = tudo que estava no root, exceto o bloco EncaminhamentosSuas
   - right = EncaminhamentosSuas
5) Adiciona CSS SplitView em cras_ui_v2.css (com backup) se ainda não existir
6) Backup automático do JSX antes de escrever

"""

from pathlib import Path
from datetime import datetime
import re

ROOT = Path.home() / "POPNEWS1"
target = ROOT / "frontend/src/TelaCrasEncaminhamentos.jsx"
css_path = ROOT / "frontend/src/cras_ui_v2.css"

if not target.exists():
    raise SystemExit(f"Arquivo não encontrado: {target}")

lines = target.read_text(encoding="utf-8", errors="ignore").splitlines(True)
marker = "CRAS_ENC_SPLITVIEW_35_65_V8"
if any(marker in l for l in lines):
    print("OK: SplitView já aplicado (V8).")
    raise SystemExit(0)

# 1) root <div className="cras-flow-mini"...> na linha
root_idx = None
root_open_pat = re.compile(r'^\s*<div\b[^>]*className\s*=\s*["\']cras-flow-mini["\']')
for i,l in enumerate(lines):
    if root_open_pat.search(l):
        root_idx = i
        break
if root_idx is None:
    # debug: procurar menções
    hits = [(i+1,l.strip()) for i,l in enumerate(lines) if "cras-flow-mini" in l]
    print("Não encontrei root <div className="cras-flow-mini">.")
    print("Linhas com 'cras-flow-mini' (até 15):")
    for i,l in hits[:15]:
        print(f"{i}: {l[:220]}")
    raise SystemExit(1)

root_indent = re.match(r'^(\s*)', lines[root_idx]).group(1)
root_depth = 0
root_close_idx = None

# padrões só no começo da linha (evita strings)
open_line = re.compile(r'^\s*<div\b')
close_line = re.compile(r'^\s*</div\s*>')

for i in range(root_idx, len(lines)):
    l = lines[i]
    if open_line.search(l):
        root_depth += 1
    if close_line.search(l):
        root_depth -= 1
    if root_depth == 0 and i > root_idx:
        root_close_idx = i
        break

if root_close_idx is None:
    print("Falha: não consegui fechar o root por depth.")
    # imprime alguns fechamentos para diagnosticar
    closes = [(i+1, lines[i].rstrip()) for i in range(root_idx, min(len(lines), root_idx+260)) if close_line.search(lines[i])]
    print("Primeiros </div> próximos (até 10):")
    for i,l in closes[:10]:
        print(f"{i}: {l}")
    raise SystemExit(1)

# 2) encontrar bloco EncaminhamentosSuas dentro do root
enc_start = None
for i in range(root_idx, root_close_idx+1):
    if "<EncaminhamentosSuas" in lines[i]:
        enc_start = i
        break
if enc_start is None:
    # debug: mostrar linhas com EncaminhamentosSuas
    hits = [(i+1,l.rstrip()) for i,l in enumerate(lines) if "EncaminhamentosSuas" in l]
    print("Não encontrei '<EncaminhamentosSuas' dentro do root cras-flow-mini.")
    print("Linhas com 'EncaminhamentosSuas' (até 20):")
    for i,l in hits[:20]:
        print(f"{i}: {l[:240]}")
    raise SystemExit(1)

enc_end = None
for j in range(enc_start, min(root_close_idx+1, enc_start+400)):
    if "/>" in lines[j]:
        enc_end = j
        break
    if "</EncaminhamentosSuas>" in lines[j]:
        enc_end = j
        break
if enc_end is None:
    raise SystemExit("Não consegui achar o fim do bloco EncaminhamentosSuas (nem '/>' nem '</EncaminhamentosSuas>').")

enc_block = "".join(lines[enc_start:enc_end+1]).rstrip()
enc_indent = re.match(r'^(\s*)', lines[enc_start]).group(1)

# 3) montar novo conteúdo do root
# conteúdo interno do root: (root_idx+1 .. root_close_idx-1)
inner_before = "".join(lines[root_idx+1:enc_start])
inner_after = "".join(lines[enc_end+1:root_close_idx])

open_split = f'''{enc_indent}{{/* {marker} */}}
{enc_indent}<div className="cras-enc-split">
{enc_indent}  <div className="cras-enc-left">
{enc_indent}    <div className="cras-enc-left-stack">
'''
close_left_open_right = f'''{enc_indent}    </div>
{enc_indent}  </div>
{enc_indent}  <div className="cras-enc-right">
{enc_indent}{enc_block}
{enc_indent}  </div>
{enc_indent}</div>
'''

new_inner = open_split + inner_before + inner_after + close_left_open_right

# 4) reconstruir arquivo
new_lines = []
new_lines.extend(lines[:root_idx+1])
new_lines.append(new_inner)
new_lines.extend(lines[root_close_idx:])  # inclui o </div> de fechamento do root e o restante

orig_txt = "".join(lines)
bak = target.with_suffix(target.suffix + ".bak_" + datetime.now().strftime("%Y%m%d_%H%M%S"))
bak.write_text(orig_txt, encoding="utf-8")
target.write_text("".join(new_lines), encoding="utf-8")

print("✅ OK: SplitView V8 aplicado em", target)
print("Backup:", bak)

# 5) CSS
if css_path.exists():
    css = css_path.read_text(encoding="utf-8", errors="ignore")
    css_marker = "/* CRAS_ENC_SPLITVIEW_35_65_CSS_V8 */"
    if css_marker not in css:
        css_bak = css_path.with_suffix(css_path.suffix + ".bak_" + datetime.now().strftime("%Y%m%d_%H%M%S"))
        css_bak.write_text(css, encoding="utf-8")
        css_add = '''
\n\n/* CRAS_ENC_SPLITVIEW_35_65_CSS_V8 */
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
        print("✅ CSS SplitView V8 adicionado em", css_path)
        print("Backup CSS:", css_bak)
else:
    print("⚠️ cras_ui_v2.css não encontrado — pulei CSS.")
