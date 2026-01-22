#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import re
import sys

MARKER = "/* ===== Gestão: Fila (layout profissional) ===== */"

CSS_BLOCK = """.gestao-fila-card .regional-table-wrapper{ background: #fff; }
.gestao-fila-card .regional-table thead{ background: #eef2ff; }
.gestao-fila-card .regional-table th{
  font-size: 12px;
  letter-spacing: .02em;
}
.gestao-fila-card .regional-table td{
  padding: 8px 10px;
  vertical-align: middle;
}
.gestao-fila-card .regional-table td:last-child{
  width: 240px;
}
.gestao-fila-card .regional-table tbody tr:hover{
  background: rgba(79,70,229,.06);
}
.gestao-fila-actions{
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
  flex-wrap: nowrap;
}
.gestao-fila-actions .btn{ box-shadow: none; }
.gestao-fila-actions .btn-secundario-mini{
  background: #fff;
  border: 1px solid rgba(2,6,23,.10);
}
.gestao-fila-actions .btn-secundario-mini:hover{
  background: #f3f4ff;
}
@media (max-width: 980px){
  .gestao-fila-card .regional-table td:last-child{ width: auto; }
  .gestao-fila-actions{ flex-wrap: wrap; justify-content: flex-start; }
}
"""


def fail(msg: str) -> None:
    print("ERRO:", msg)
    sys.exit(1)


def main() -> None:
    # project root = two levels up from frontend/scripts/
    here = Path(__file__).resolve()
    root = here.parents[2]
    gestao = root / "frontend" / "src" / "GestaoApp.jsx"
    css = root / "frontend" / "src" / "App.css"

    if not gestao.exists():
        fail(f"Arquivo não encontrado: {gestao}")
    if not css.exists():
        fail(f"Arquivo não encontrado: {css}")

    txt = gestao.read_text(encoding="utf-8")

    # Locate FILA section by tab key
    idx = txt.find('activeTab === "fila"')
    if idx == -1:
        fail('Não encontrei o bloco: activeTab === "fila"')

    # 1) Add class to the FILA card container (only the first card div after idx)
    # Prefer exact needle first
    needle = '<div className="card" style={{ marginTop: 14 }}>'
    pos = txt.find(needle, idx)
    if pos != -1:
        txt = txt.replace(needle, '<div className="card gestao-fila-card" style={{ marginTop: 14 }}>', 1)
    else:
        # fallback: allow any spaces
        m = re.search(r'<div\s+className="card"\s+style=\{\{\s*marginTop:\s*14\s*\}\}>', txt[idx:idx+6000])
        if not m:
            fail("Não encontrei o container .card da Fila para adicionar classe.")
        abs_start = idx + m.start()
        abs_end = idx + m.end()
        txt = txt[:abs_start] + m.group(0).replace('className="card"', 'className="card gestao-fila-card"') + txt[abs_end:]

    # 2) Patch actions column: container + button sizes + label
    actions_pos = txt.find('key: "acoes"', idx)
    if actions_pos == -1:
        actions_pos = txt.find('label: "Ações"', idx)
    if actions_pos == -1:
        fail('Não encontrei a coluna de ações (key: "acoes" / label: "Ações")')

    # Find actions container div (first <div style={{ display: "flex"... after actions_pos)
    mdiv = re.search(r'<div\s+style=\{\{\s*display:\s*"flex"[^}]*\}\}\>', txt[actions_pos:actions_pos+2500])
    if not mdiv:
        fail("Não encontrei o container <div style={{ display: 'flex' ... }}> das ações.")
    dstart = actions_pos + mdiv.start()
    dend = actions_pos + mdiv.end()
    txt = txt[:dstart] + '<div className="gestao-fila-actions">' + txt[dend:]

    # Narrow patch region around actions for button replacements
    region_start = dstart
    region_end = txt.find("</div>", region_start)
    if region_end == -1:
        fail("Não consegui localizar o fechamento do container de ações.")
    region_end += len("</div>")
    region = txt[region_start:region_end]

    # Replace label for rede (optional)
    region = region.replace('{isRede ? "Cobrar devolutiva" : "Ofício"}', '{isRede ? "Cobrar" : "Ofício"}')

    # Replace button classes inside this region (first 3 occurrences)
    cls = 'className="btn btn-secundario"'
    hits = [m.start() for m in re.finditer(re.escape(cls), region)]
    if len(hits) >= 3:
        region = region.replace(cls, 'className="btn btn-primario-mini"', 1)
        region = region.replace(cls, 'className="btn btn-secundario-mini"', 2)

    txt = txt[:region_start] + region + txt[region_end:]

    # 3) Append CSS (idempotent)
    css_txt = css.read_text(encoding="utf-8")
    if MARKER not in css_txt:
        css_txt = css_txt.rstrip() + "\n\n" + MARKER + "\n" + CSS_BLOCK
        css.write_text(css_txt + ("\n" if not css_txt.endswith("\n") else ""), encoding="utf-8")

    gestao.write_text(txt, encoding="utf-8")
    print("OK: Fila da Gestão ajustada (layout mais profissional).")
    print("Arquivos alterados:")
    print(" -", gestao)
    print(" -", css)


if __name__ == "__main__":
    main()
