#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CRAS Encaminhamentos Split View 35/65 — Patch V6
Correção: detectar corretamente o root <div className="cras-flow-mini"> (ou fallback).
Motivação: V5 falhou em localizar o root no seu arquivo.

Estratégia:
1) Localiza o root pela classe "cras-flow-mini" (regex).
2) Calcula o fechamento do root via contagem de <div> / </div>.
3) Localiza o bloco <EncaminhamentosSuas ...> (multilinha) dentro do root.
4) Substitui EncaminhamentosSuas por abertura do split/left.
5) Insere fechamento do split (inclui o EncaminhamentosSuas original na coluna direita) antes do fechamento do root.
6) Backup automático + CSS no cras_ui_v2.css.

Observação: não depende de regex que quebra com '=>' dentro de props.
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

lines = target.read_text(encoding="utf-8", errors="ignore").splitlines(True)
marker = "CRAS_ENC_SPLITVIEW_35_65_V6"
if any(marker in l for l in lines):
    print("OK: SplitView já aplicado (V6).")
    raise SystemExit(0)

# 1) localizar root <div className="cras-flow-mini">
root_idx = None
root_pat = re.compile(r'<\s*div\b[^>]*className\s*=\s*["\']cras-flow-mini["\']')
for i,l in enumerate(lines):
    if root_pat.search(l):
        root_idx = i
        break

# fallback: procurar primeira <div> depois de 'return'
if root_idx is None:
    ret_idx = None
    ret_pat = re.compile(r'\breturn\s*\(')
    for i,l in enumerate(lines):
        if ret_pat.search(l):
            ret_idx = i
            break
    if ret_idx is not None:
        div_pat = re.compile(r'<\s*div\b')
        for j in range(ret_idx, min(len(lines), ret_idx + 120)):
            if div_pat.search(lines[j]):
                root_idx = j
                break

if root_idx is None:
    # debug
    print("Não consegui localizar o root <div> do JSX.")
    print("Dica: procure por 'cras-flow-mini' no arquivo e confirme se existe.")
    hits = [ (i+1,l.strip()) for i,l in enumerate(lines) if "cras-flow-mini" in l ]
    for i,l in hits[:20]:
        print(f"{i}: {l[:200]}")
    raise SystemExit(1)

# 2) encontrar fechamento do root via contagem de divs
depth = 0
root_close_idx = None
for i in range(root_idx, len(lines)):
    l = lines[i]
    opens = len(re.findall(r"<\s*div\b", l))
    closes = len(re.findall(r"</\s*div\s*>", l))
    depth += opens
    depth -= closes
    if depth == 0 and i > root_idx:
        root_close_idx = i
        break

if root_close_idx is None:
    raise SystemExit("Não consegui localizar o fechamento do root </div> (nesting).")

# 3) localizar bloco EncaminhamentosSuas (multilinha) dentro do root
enc_start = None
for i in range(root_idx, root_close_idx+1):
    if "<EncaminhamentosSuas" in lines[i]:
        enc_start = i
        break
if enc_start is None:
    # debug
    print("Não encontrei '<EncaminhamentosSuas' dentro do root.")
    for i in range(root_idx, min(root_close_idx+1, root_idx+220)):
        if "Encaminh" in lines[i]:
            print(f"{i+1}: {lines[i].rstrip()[:240]}")
    raise SystemExit(1)

enc_end = None
for j in range(enc_start, min(root_close_idx+1, enc_start+260)):
    if "/>" in lines[j]:
        enc_end = j
        break
    if "</EncaminhamentosSuas>" in lines[j]:
        enc_end = j
        break
if enc_end is None:
    raise SystemExit("Não consegui determinar o fim do bloco EncaminhamentosSuas (nem '/>' nem '</EncaminhamentosSuas>').")

enc_block = "".join(lines[enc_start:enc_end+1])

# 4) substituir bloco pelo open split/left
indent = re.match(r"^(\s*)", lines[enc_start]).group(1)
open_split = (
    f'{indent}{{/* {marker} */}}\n'
    f'{indent}<div className="cras-enc-split">\n'
    f'{indent}  <div className="cras-enc-left">\n'
    f'{indent}    <div className="cras-enc-left-stack">\n'
)

new_lines = lines[:enc_start] + [open_split] + lines[enc_end+1:]

# 5) inserir close split antes do fechamento do root
delta = len(new_lines) - len(lines)
root_close_idx2 = root_close_idx + delta

close_split = (
    f'{indent}    </div>\n'
    f'{indent}  </div>\n'
    f'{indent}  <div className="cras-enc-right">\n'
    f'{indent}{enc_block.rstrip()}\n'
    f'{indent}  </div>\n'
    f'{indent}</div>\n'
)

new_lines = new_lines[:root_close_idx2] + [close_split] + new_lines[root_close_idx2:]

# 6) backup e escrever
orig_txt = "".join(lines)
bak = target.with_suffix(target.suffix + ".bak_" + datetime.now().strftime("%Y%m%d_%H%M%S"))
bak.write_text(orig_txt, encoding="utf-8")
target.write_text("".join(new_lines), encoding="utf-8")
print("✅ OK: SplitView V6 aplicado em", target)
print("Backup:", bak)

# 7) CSS
if css_path.exists():
    css = css_path.read_text(encoding="utf-8", errors="ignore")
    css_marker = "/* CRAS_ENC_SPLITVIEW_35_65_CSS_V6 */"
    if css_marker not in css:
        css_bak = css_path.with_suffix(css_path.suffix + ".bak_" + datetime.now().strftime("%Y%m%d_%H%M%S"))
        css_bak.write_text(css, encoding="utf-8")
        css_add = '''
\n\n/* CRAS_ENC_SPLITVIEW_35_65_CSS_V6 */
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
        print("✅ CSS SplitView V6 adicionado em", css_path)
        print("Backup CSS:", css_bak)
else:
    print("⚠️ cras_ui_v2.css não encontrado — pulei CSS.")
