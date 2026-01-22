#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime

ROOT = Path.home() / "POPNEWS1"
target = ROOT / "frontend/src/components/EncaminhamentosSuas.jsx"
css_path = ROOT / "frontend/src/cras_actions_kebab_card.css"

if not target.exists():
    raise SystemExit(f"Arquivo não encontrado: {target}")

text = target.read_text(encoding="utf-8", errors="ignore")

# 1) Importar CSS se não existir
import_line = 'import "../cras_actions_kebab_card.css"; // CRAS_ACTIONS_KEBAB_CARD_V1'
if import_line not in text:
    # inserir após import React
    lines = text.splitlines()
    out = []
    inserted = False
    for i, line in enumerate(lines):
        out.append(line)
        if not inserted and line.startswith("import React"):
            out.append(import_line)
            inserted = True
    text = "\n".join(out) + ("\n" if not text.endswith("\n") else "")

# 2) Substituir bloco do Cancelar (apenas o botão secundário)
needle = (
'                    {podeCancelar ? (\n'
'                      <button className="btn btn-secundario" type="button" onClick={() => cancelar(item)}>\n'
'                        Cancelar\n'
'                      </button>\n'
'                    ) : null}'
)

replacement = (
'                    {podeCancelar ? (\n'
'                      <details className="cras-kebab-menu">\n'
'                        <summary className="cras-kebab-btn" aria-label="Mais ações">⋯</summary>\n'
'                        <div className="cras-kebab-pop">\n'
'                          <button\n'
'                            className="btn btn-secundario btn-secundario-mini"\n'
'                            type="button"\n'
'                            onClick={(e) => {\n'
'                              cancelar(item);\n'
'                              const d = e.currentTarget && e.currentTarget.closest("details");\n'
'                              if (d) d.removeAttribute("open");\n'
'                            }}\n'
'                          >\n'
'                            Cancelar\n'
'                          </button>\n'
'                        </div>\n'
'                      </details>\n'
'                    ) : null}'
)

if needle not in text:
    raise SystemExit("Não encontrei o bloco exato do botão 'Cancelar' em EncaminhamentosSuas.jsx (abortando por segurança).")

text2 = text.replace(needle, replacement, 1)

bak = target.with_suffix(target.suffix + ".bak_" + datetime.now().strftime("%Y%m%d_%H%M%S"))
bak.write_text(text, encoding="utf-8")
target.write_text(text2, encoding="utf-8")

print("✅ OK: EncaminhamentosSuas: 'Cancelar' movido para menu ⋯.")
print("Backup:", bak)
