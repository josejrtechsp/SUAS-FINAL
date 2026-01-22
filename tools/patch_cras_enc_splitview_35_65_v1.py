#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime

ROOT = Path.home() / "POPNEWS1"
css_path = ROOT / "frontend/src/cras_ui_v2.css"
tela_path = ROOT / "frontend/src/TelaCrasEncaminhamentos.jsx"

if not css_path.exists():
    raise SystemExit(f"Não achei {css_path}")
if not tela_path.exists():
    raise SystemExit(f"Não achei {tela_path}")

# --- CSS append (safe, marker-based)
css = css_path.read_text(encoding="utf-8", errors="ignore")
css_marker = "CRAS_ENC_SPLITVIEW_35_65_V1"
if css_marker not in css:
    css_bak = css_path.with_suffix(css_path.suffix + ".bak_" + datetime.now().strftime("%Y%m%d_%H%M%S"))
    css_bak.write_text(css, encoding="utf-8")

    css_add = r'''
/* CRAS_ENC_SPLITVIEW_35_65_V1
   Encaminhamentos: layout Split View (35/65) estilo "Mail" (Apple-like).
   Sem alterar lógica, só distribuição.
   Escopo: .cras-ui-v2
*/
.cras-ui-v2 .cras-enc-split{
  display: grid;
  grid-template-columns: 35% minmax(0, 65%);
  gap: 16px;
  align-items: start;
}

.cras-ui-v2 .cras-enc-right{
  grid-column: 2;
  grid-row: 1;
  min-width: 0;
}

.cras-ui-v2 .cras-enc-left{
  grid-column: 1;
  grid-row: 1;
  min-width: 0;
}

/* No split view, a coluna esquerda vira "stack" */
.cras-ui-v2 .cras-enc-left .cras-enc-left-stack{
  display: flex;
  flex-direction: column;
  gap: 12px;
}

/* Em telas menores, vira 1 coluna */
@media (max-width: 980px){
  .cras-ui-v2 .cras-enc-split{
    grid-template-columns: 1fr;
  }
  .cras-ui-v2 .cras-enc-right,
  .cras-ui-v2 .cras-enc-left{
    grid-column: 1;
    grid-row: auto;
  }
}
'''
    css_path.write_text(css.rstrip() + "\n\n" + css_add.strip() + "\n", encoding="utf-8")
    print("OK: CSS split view adicionado.")
    print("Backup CSS:", css_bak)
else:
    print("CSS já contém marker (split view).")

# --- JSX patch
txt = tela_path.read_text(encoding="utf-8", errors="ignore")
marker = "CRAS_ENC_SPLITVIEW_35_65_V1"
if marker in txt:
    print("OK: TelaCrasEncaminhamentos já está no split view.")
    raise SystemExit(0)

bak = tela_path.with_suffix(tela_path.suffix + ".bak_" + datetime.now().strftime("%Y%m%d_%H%M%S"))
bak.write_text(txt, encoding="utf-8")
print("Backup JSX:", bak)

# 1) Add class to root wrapper
txt2 = txt
txt2 = txt2.replace('className="layout-1col"', 'className="layout-1col cras-enc-split"', 1)

# 2) Insert right wrapper before msg (or before EncaminhamentosSuas if no msg)
insert_at = txt2.find("{msg ?")
if insert_at == -1:
    insert_at = txt2.find("<EncaminhamentosSuas")
    if insert_at == -1:
        raise SystemExit("Não encontrei {msg ?} nem <EncaminhamentosSuas> para inserir wrapper.")

txt2 = txt2[:insert_at] + '      <div className="cras-enc-right">\\n\\n' + txt2[insert_at:]

# 3) Close right wrapper after EncaminhamentosSuas self-closing tag
m = re.search(r"<EncaminhamentosSuas[\\s\\S]*?\\/>", txt2)
if not m:
    raise SystemExit("Não encontrei bloco <EncaminhamentosSuas ... />")

end = m.end()
txt2 = txt2[:end] + "\\n\\n      </div>\\n\\n      <div className=\\"cras-enc-left\\">\\n        <div className=\\"cras-enc-left-stack\\">\\n" + txt2[end:]

# 4) Adjust the two-column grid for the create/semDevolutiva cards to one column (left column is narrow)
txt2 = txt2.replace('gridTemplateColumns: "1fr 1fr"', 'gridTemplateColumns: "1fr"', 1)

# 5) Close left wrapper before the final root closing div
tail_pat = re.compile(r"\\n\\s*</div>\\s*\\n\\s*\\);\\s*\\n\\}", re.M)
m2 = tail_pat.search(txt2)
if not m2:
    raise SystemExit("Não consegui localizar o fechamento final do return para fechar a coluna esquerda.")

# Insert closing tags right before the last </div> that closes root
insert_pos = m2.start()
# We need to close stack + left
closing = "\\n        </div>\\n      </div>\\n"
txt2 = txt2[:insert_pos] + closing + txt2[insert_pos:]

# 6) Add marker comment near top (after imports)
if marker not in txt2:
    lines = txt2.splitlines()
    out = []
    inserted = False
    for line in lines:
        out.append(line)
        if not inserted and line.startswith("import") and "EncaminhamentosSuas" in line:
            out.append(f"// {marker}")
            inserted = True
    txt2 = "\\n".join(out) + "\\n"

tela_path.write_text(txt2, encoding="utf-8")
print("OK: Split view aplicado em TelaCrasEncaminhamentos.")
