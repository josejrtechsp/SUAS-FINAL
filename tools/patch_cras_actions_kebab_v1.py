#!/usr/bin/env python3
import re
from pathlib import Path
from datetime import datetime

ROOT = Path.home() / "POPNEWS1"
target = ROOT / "frontend/src/TelaCrasTarefas.jsx"
css_path = ROOT / "frontend/src/cras_actions_kebab.css"

if not target.exists():
    raise SystemExit(f"Arquivo não encontrado: {target}")

text = target.read_text(encoding="utf-8", errors="ignore")

marker = "CRAS_ACTIONS_KEBAB_V1"
if marker in text:
    print("OK: TelaCrasTarefas.jsx já está com o menu kebab.")
    raise SystemExit(0)

# 1) Adicionar import do CSS (se não existir)
if 'import "./cras_actions_kebab.css";' not in text:
    # inserir após as imports React
    lines = text.splitlines()
    inserted = False
    out = []
    for i, line in enumerate(lines):
        out.append(line)
        # após a última linha de import no topo
        if not inserted and line.startswith("import ") and (i+1 < len(lines) and not lines[i+1].startswith("import ")):
            out.append('import "./cras_actions_kebab.css"; // CRAS_ACTIONS_KEBAB_V1')
            inserted = True
    text = "\n".join(out) + ("\n" if text.endswith("\n") else "")
    if not inserted:
        # fallback: coloca no começo
        text = 'import "./cras_actions_kebab.css"; // CRAS_ACTIONS_KEBAB_V1\n' + text

# 2) Trocar bloco de ações
pattern = re.compile(
    r'<td\s+style=\{\{\s*padding:\s*8,\s*borderBottom:\s*"1px solid rgba\(2,6,23,\.06\)"\s*\}\}>\s*'
    r'<div\s+style=\{\{\s*display:\s*"flex",\s*gap:\s*10,\s*flexWrap:\s*"wrap"\s*\}\}>\s*'
    r'(?P<body>[\s\S]*?)'
    r'</div>\s*</td>',
    re.M
)

m = pattern.search(text)
if not m:
    raise SystemExit("Não consegui localizar o bloco de ações (td com flexWrap).")

body = m.group("body")

# garantir que contém Concluir/Editar/Excluir
if "Concluir" not in body or "Editar" not in body or "Excluir" not in body:
    raise SystemExit("Bloco de ações encontrado não contém Concluir/Editar/Excluir. Abortando por segurança.")

replacement = r'''<td style={{ padding: 8, borderBottom: "1px solid rgba(2,6,23,.06)" }}>
                      <div className="cras-actions-cell">
                        {String(r.status || "") !== "concluida" ? (
                          <button className="btn btn-primario btn-primario-mini" type="button" onClick={() => concluir(r)}>
                            Concluir
                          </button>
                        ) : null}

                        <details className="cras-actions-menu">
                          <summary className="cras-actions-kebab" aria-label="Mais ações">⋯</summary>
                          <div className="cras-actions-pop">
                            <button
                              className="btn btn-secundario btn-secundario-mini"
                              type="button"
                              onClick={(e) => {
                                openEditModal(r);
                                const d = e.currentTarget && e.currentTarget.closest("details");
                                if (d) d.removeAttribute("open");
                              }}
                            >
                              Editar
                            </button>
                            <button
                              className="btn btn-secundario btn-secundario-mini"
                              type="button"
                              onClick={(e) => {
                                excluir(r);
                                const d = e.currentTarget && e.currentTarget.closest("details");
                                if (d) d.removeAttribute("open");
                              }}
                            >
                              Excluir
                            </button>
                          </div>
                        </details>
                      </div>
                    </td>'''

text2 = pattern.sub(replacement, text, count=1)

# 3) Backup e escrever
bak = target.with_suffix(target.suffix + ".bak_" + datetime.now().strftime("%Y%m%d_%H%M%S"))
bak.write_text(text, encoding="utf-8")
target.write_text(text2, encoding="utf-8")

print("OK: aplicado menu de 3 pontinhos na coluna Ações.")
print("Backup:", bak)
