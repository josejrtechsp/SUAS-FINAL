#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CRAS Encaminhamentos Split View 35/65 — Patch V5 (linha + nesting)
Robusto contra '=>' e outros '>' dentro de props:
- Trabalha por linhas, não por regex de tags
- Escopa dentro de export default TelaCrasEncaminhamentos
- Encontra root <div className="cras-flow-mini"> (ou primeiro <div após return)
- Calcula fechamento do root via contagem de <div> / </div>
- Move bloco <EncaminhamentosSuas ...> (multilinha) para coluna direita
- Coloca o restante dentro da coluna esquerda
- Adiciona CSS split no cras_ui_v2.css com backup
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
marker = "CRAS_ENC_SPLITVIEW_35_65_V5"
if any(marker in l for l in lines):
    print("OK: SplitView já aplicado (V5).")
    raise SystemExit(0)

# 1) localizar início da função export default
start_idx = None
for i,l in enumerate(lines):
    if "export default function TelaCrasEncaminhamentos" in l:
        start_idx = i
        break
if start_idx is None:
    raise SystemExit("Não encontrei 'export default function TelaCrasEncaminhamentos'.")

sub = lines[start_idx:]

# 2) localizar root div preferido
root_rel = None
for i,l in enumerate(sub):
    if 'className="cras-flow-mini"' in l or "className='cras-flow-mini'" in l:
        root_rel = i
        break

# fallback: primeiro <div após 'return ('
if root_rel is None:
    ret_rel = None
    for i,l in enumerate(sub):
        if "return (" in l:
            ret_rel = i
            break
    if ret_rel is None:
        raise SystemExit("Não encontrei 'return (' dentro da TelaCrasEncaminhamentos.")
    for i in range(ret_rel, min(len(sub), ret_rel+80)):
        if "<div" in sub[i]:
            root_rel = i
            break
if root_rel is None:
    raise SystemExit("Não consegui localizar o root <div> do JSX.")

root_idx = start_idx + root_rel

# 3) encontrar fechamento do root via contagem de divs
depth = 0
root_close_idx = None
for i in range(root_idx, len(lines)):
    l = lines[i]
    # conta aberturas simples de <div ...> (não conta </div>)
    opens = len(re.findall(r"<\s*div\b", l))
    closes = len(re.findall(r"</\s*div\s*>", l))
    depth += opens
    depth -= closes
    if depth == 0 and i > root_idx:
        root_close_idx = i
        break
if root_close_idx is None:
    raise SystemExit("Não consegui localizar o fechamento do root </div> (nesting).")

# 4) localizar bloco EncaminhamentosSuas (multilinha)
enc_start = None
for i in range(root_idx, root_close_idx+1):
    if "<EncaminhamentosSuas" in lines[i]:
        enc_start = i
        break
if enc_start is None:
    raise SystemExit("Não encontrei '<EncaminhamentosSuas' dentro do JSX do root.")

enc_end = None
for j in range(enc_start, min(root_close_idx+1, enc_start+200)):
    if "/>" in lines[j]:
        enc_end = j
        break
    if "</EncaminhamentosSuas>" in lines[j]:
        enc_end = j
        break
if enc_end is None:
    raise SystemExit("Não consegui determinar o fim do bloco EncaminhamentosSuas (nem '/>' nem '</EncaminhamentosSuas>').")

enc_block = "".join(lines[enc_start:enc_end+1])

# 5) substituir o bloco pelo início do split/left
indent = re.match(r"^(\s*)", lines[enc_start]).group(1)
open_split = (
    f'{indent}{{/* {marker} */}}\n'
    f'{indent}<div className="cras-enc-split">\n'
    f'{indent}  <div className="cras-enc-left">\n'
    f'{indent}    <div className="cras-enc-left-stack">\n'
)

# remover bloco e inserir open_split
new_lines = lines[:enc_start] + [open_split] + lines[enc_end+1:]

# 6) inserir fechamento do left + right + close split antes do fechamento do root
# recalcular índices (tamanho mudou)
# achar novamente o fechamento root (última ocorrência do mesmo índice aproximado: procurar a linha original root closing pattern)
# simples: procurar do fim por primeira </div> que fecha o root; mas já temos root_close_idx original.
# Ajuste: delta = len(new_lines) - len(lines)
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

# 7) backup e escrever
txt = "".join(lines)
bak = target.with_suffix(target.suffix + ".bak_" + datetime.now().strftime("%Y%m%d_%H%M%S"))
bak.write_text(txt, encoding="utf-8")
target.write_text("".join(new_lines), encoding="utf-8")
print("✅ OK: SplitView V5 aplicado em", target)
print("Backup:", bak)

# 8) CSS
if css_path.exists():
    css = css_path.read_text(encoding="utf-8", errors="ignore")
    css_marker = "/* CRAS_ENC_SPLITVIEW_35_65_CSS_V5 */"
    if css_marker not in css:
        css_bak = css_path.with_suffix(css_path.suffix + ".bak_" + datetime.now().strftime("%Y%m%d_%H%M%S"))
        css_bak.write_text(css, encoding="utf-8")
        css_add = '''
\n\n/* CRAS_ENC_SPLITVIEW_35_65_CSS_V5 */
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
        print("✅ CSS SplitView V5 adicionado em", css_path)
        print("Backup CSS:", css_bak)
else:
    print("⚠️ cras_ui_v2.css não encontrado — pulei CSS.")
