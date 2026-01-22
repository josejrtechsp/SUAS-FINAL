#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CRAS Encaminhamentos Split View 35/65 — Patch V7
Correção: localizar fechamento do <div className="cras-flow-mini"> por INDENTAÇÃO (não por nesting count).

Por que: o método de contagem de <div> falha quando há '<div' em strings/JSX/trechos não-HTML.

Estratégia:
1) Acha a linha que contém className="cras-flow-mini" (primeira ocorrência).
2) Captura indentação dessa linha (whitespace à esquerda).
3) Acha o primeiro </div> com a MESMA indentação depois disso (fecha esse bloco).
4) Dentro desse intervalo, encontra o bloco <EncaminhamentosSuas ...> (multilinha).
5) Substitui esse bloco pelo open split/left.
6) Insere o close split (com EncaminhamentosSuas original na direita) logo antes do </div> de fechamento.
7) Backup automático e CSS split em cras_ui_v2.css.

Seguro: se não achar padrões, aborta sem escrever.
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
marker = "CRAS_ENC_SPLITVIEW_35_65_V7"
if any(marker in l for l in lines):
    print("OK: SplitView já aplicado (V7).")
    raise SystemExit(0)

# 1) localizar root cras-flow-mini
root_idx = None
for i,l in enumerate(lines):
    if "cras-flow-mini" in l and "<div" in l:
        root_idx = i
        break
if root_idx is None:
    # fallback: linha com cras-flow-mini mesmo que <div esteja em linha anterior
    for i,l in enumerate(lines):
        if "cras-flow-mini" in l:
            root_idx = i
            break
if root_idx is None:
    raise SystemExit("Não encontrei 'cras-flow-mini' em TelaCrasEncaminhamentos.jsx.")

# indent do root (whitespace até o primeiro '<')
m_indent = re.match(r"^(\s*)<", lines[root_idx])
root_indent = m_indent.group(1) if m_indent else re.match(r"^(\s*)", lines[root_idx]).group(1)

# 2) achar fechamento por indentação: primeiro </div> com a mesma indentação após root
close_pat = re.compile(rf"^{re.escape(root_indent)}</div>\s*$")
root_close_idx = None
for j in range(root_idx+1, len(lines)):
    if close_pat.match(lines[j]):
        root_close_idx = j
        break

if root_close_idx is None:
    # debug: mostra 10 linhas com </div> próximas
    near = []
    for j in range(root_idx, min(len(lines), root_idx+260)):
        if "</div>" in lines[j]:
            near.append((j+1, lines[j].rstrip()[:200]))
    print("Não consegui localizar o fechamento do root </div> por indentação.")
    print("Indent root repr:", repr(root_indent))
    print("Fechamentos </div> próximos (até 10):")
    for ln, tx in near[:10]:
        print(f"{ln}: {tx}")
    raise SystemExit(1)

# 3) localizar bloco EncaminhamentosSuas dentro do intervalo
enc_start = None
for i in range(root_idx, root_close_idx+1):
    if "<EncaminhamentosSuas" in lines[i]:
        enc_start = i
        break
if enc_start is None:
    raise SystemExit("Não encontrei '<EncaminhamentosSuas' dentro do bloco cras-flow-mini.")

enc_end = None
for k in range(enc_start, min(root_close_idx+1, enc_start+320)):
    if "/>" in lines[k]:
        enc_end = k
        break
    if "</EncaminhamentosSuas>" in lines[k]:
        enc_end = k
        break
if enc_end is None:
    raise SystemExit("Não consegui determinar o fim do bloco EncaminhamentosSuas (nem '/>' nem '</EncaminhamentosSuas>').")

enc_block = "".join(lines[enc_start:enc_end+1]).rstrip()

# 4) substituir bloco por open split/left
enc_indent = re.match(r"^(\s*)", lines[enc_start]).group(1)
open_split = (
    f"{enc_indent}{{/* {marker} */}}\n"
    f"{enc_indent}<div className=\"cras-enc-split\">\n"
    f"{enc_indent}  <div className=\"cras-enc-left\">\n"
    f"{enc_indent}    <div className=\"cras-enc-left-stack\">\n"
)

new_lines = lines[:enc_start] + [open_split] + lines[enc_end+1:]

# 5) re-localizar root_close_idx no new_lines (pois índices mudaram) pelo mesmo padrão
#    Primeiro: achar novamente o root_idx (mesma linha original ainda existe)
root_idx2 = None
for i,l in enumerate(new_lines):
    if "cras-flow-mini" in l:
        root_idx2 = i
        break
if root_idx2 is None:
    raise SystemExit("Após alteração, não consegui relocalizar cras-flow-mini (abortando).")

# indent do root de novo
m_indent2 = re.match(r"^(\s*)<", new_lines[root_idx2])
root_indent2 = m_indent2.group(1) if m_indent2 else re.match(r"^(\s*)", new_lines[root_idx2]).group(1)
close_pat2 = re.compile(rf"^{re.escape(root_indent2)}</div>\s*$")

root_close_idx2 = None
for j in range(root_idx2+1, len(new_lines)):
    if close_pat2.match(new_lines[j]):
        root_close_idx2 = j
        break
if root_close_idx2 is None:
    raise SystemExit("Após alteração, não consegui relocalizar o fechamento do root </div> (abortando).")

# 6) inserir close split antes do fechamento do root
close_split = (
    f"{enc_indent}    </div>\n"
    f"{enc_indent}  </div>\n"
    f"{enc_indent}  <div className=\"cras-enc-right\">\n"
    f"{enc_indent}{enc_block}\n"
    f"{enc_indent}  </div>\n"
    f"{enc_indent}</div>\n"
)

new_lines = new_lines[:root_close_idx2] + [close_split] + new_lines[root_close_idx2:]

# 7) backup e escrever
orig_txt = "".join(lines)
bak = target.with_suffix(target.suffix + ".bak_" + datetime.now().strftime("%Y%m%d_%H%M%S"))
bak.write_text(orig_txt, encoding="utf-8")
target.write_text("".join(new_lines), encoding="utf-8")
print("✅ OK: SplitView V7 aplicado em", target)
print("Backup:", bak)

# 8) CSS
if css_path.exists():
    css = css_path.read_text(encoding="utf-8", errors="ignore")
    css_marker = "/* CRAS_ENC_SPLITVIEW_35_65_CSS_V7 */"
    if css_marker not in css:
        css_bak = css_path.with_suffix(css_path.suffix + ".bak_" + datetime.now().strftime("%Y%m%d_%H%M%S"))
        css_bak.write_text(css, encoding="utf-8")
        css_add = '''
\n\n/* CRAS_ENC_SPLITVIEW_35_65_CSS_V7 */
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
        print("✅ CSS SplitView V7 adicionado em", css_path)
        print("Backup CSS:", css_bak)
else:
    print("⚠️ cras_ui_v2.css não encontrado — pulei CSS.")
