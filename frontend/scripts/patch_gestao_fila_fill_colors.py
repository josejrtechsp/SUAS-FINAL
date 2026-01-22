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
  width: 260px;
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
.gestao-fila-actions .btn-primario{ box-shadow: none; }
.gestao-fila-actions .btn-primario:hover{ transform: none; filter: brightness(1.02); }
.gestao-fila-actions .btn-secundario{ box-shadow: none; }
.gestao-fila-actions .btn-secundario:hover{ transform: none; }

.gestao-fila-actions .btn-secundario-mini{
  background: #fff;
  border: 1px solid rgba(2,6,23,.10);
}
.gestao-fila-actions .btn-secundario-mini:hover{
  background: #f3f4ff;
}

.gestao-fila-btn-doc{
  background: rgba(79,70,229,.10) !important;
  border-color: rgba(79,70,229,.24) !important;
  color: #3730a3 !important;
}
.gestao-fila-btn-doc:hover{
  background: rgba(79,70,229,.14) !important;
}

@media (max-width: 1100px){
  .gestao-fila-card .regional-table td:last-child{ width: auto; }
  .gestao-fila-actions{ flex-wrap: wrap; justify-content: flex-start; }
}
"""


def fail(msg: str) -> None:
    print("ERRO:", msg)
    sys.exit(1)


def patch_max_width(txt: str) -> str:
    # widen Gestao main column to occupy empty space
    # 1) exact match
    pat = r'<div\s+className="col-esquerda"\s+style=\{\{\s*maxWidth:\s*(\d+)\s*,\s*width:\s*"100%"\s*\}\}>'
    m = re.search(pat, txt)
    if m:
        old = m.group(1)
        repl = f'<div className="col-esquerda" style={{{{ maxWidth: 1180, width: "100%", margin: "0 auto" }}}}>'
        txt = txt[: m.start()] + repl + txt[m.end() :]
        return txt

    # 2) fallback: replace first maxWidth occurrence near col-esquerda
    idx = txt.find('className="col-esquerda"')
    if idx != -1:
        # replace first maxWidth number after idx
        sub = txt[idx : idx + 400]
        sub2, n = re.subn(r'maxWidth:\s*\d+', 'maxWidth: 1180', sub, count=1)
        if n:
            # ensure margin exists
            if 'margin:' not in sub2:
                sub2 = re.sub(r'width:\s*"100%"\s*\}\}', 'width: "100%", margin: "0 auto" }}', sub2, count=1)
            return txt[:idx] + sub2 + txt[idx + 400 :]

    # 3) if already widened via other patch, do nothing
    if 'maxWidth: 1180' in txt:
        return txt

    return txt


def patch_actions(txt: str) -> str:
    # Prefer the professional patch container
    act = txt.find('className="gestao-fila-actions"')
    if act == -1:
        # fallback: locate FILA column actions and transform
        idx = txt.find('activeTab === "fila"')
        if idx == -1:
            fail('Não encontrei o bloco: activeTab === "fila"')
        actions_pos = txt.find('key: "acoes"', idx)
        if actions_pos == -1:
            actions_pos = txt.find('label: "Ações"', idx)
        if actions_pos == -1:
            fail('Não encontrei a coluna de ações (key: "acoes" / label: "Ações")')
        mdiv = re.search(r'<div\s+style=\{\{\s*display:\s*"flex"[^}]*\}\}\>', txt[actions_pos : actions_pos + 2500])
        if not mdiv:
            fail('Não encontrei o container <div style={{ display: "flex" ... }}> das ações.')
        dstart = actions_pos + mdiv.start()
        dend = actions_pos + mdiv.end()
        txt = txt[:dstart] + '<div className="gestao-fila-actions">' + txt[dend:]
        act = dstart

    # find region (assume first closing </div> closes the actions container)
    end = txt.find('</div>', act)
    if end == -1:
        fail('Não encontrei o fechamento do container de ações.')
    end += len('</div>')
    region = txt[act:end]

    # Ensure button variant classes include base
    region = region.replace('btn btn-primario-mini', 'btn btn-primario btn-primario-mini')
    region = region.replace('btn btn-secundario-mini', 'btn btn-secundario btn-secundario-mini')

    # If still old class present, convert first/others
    cls = 'className="btn btn-secundario"'
    if cls in region:
        # first button becomes primario
        region = region.replace(cls, 'className="btn btn-primario btn-primario-mini"', 1)
        # remaining secondary buttons become secundario-mini
        region = region.replace(cls, 'className="btn btn-secundario btn-secundario-mini"')

    # Shorten label if still long
    region = region.replace('{isRede ? "Cobrar devolutiva" : "Ofício"}', '{isRede ? "Cobrar" : "Ofício"}')

    # Add doc accent class to the oficio/cobrar button
    key = 'gerarOficioOuCobranca(r)'
    kpos = region.find(key)
    if kpos != -1:
        # search backward for className="..."
        cstart = region.rfind('className="', 0, kpos)
        if cstart != -1:
            cend = region.find('"', cstart + len('className="'))
            if cend != -1:
                classes = region[cstart + len('className="') : cend]
                if 'gestao-fila-btn-doc' not in classes:
                    classes2 = classes + ' gestao-fila-btn-doc'
                    region = region[: cstart + len('className="')] + classes2 + region[cend:]

    return txt[:act] + region + txt[end:]


def patch_css(css_txt: str) -> str:
    if MARKER not in css_txt:
        return css_txt.rstrip() + "\n\n" + MARKER + "\n" + CSS_BLOCK + ("\n" if not css_txt.endswith("\n") else "")

    # replace existing block after marker (up to next marker or EOF)
    parts = css_txt.split(MARKER)
    if len(parts) < 2:
        return css_txt
    before = parts[0].rstrip()
    after = parts[1]
    # Remove old block content up to next marker-like comment or end
    m = re.search(r"\n/\* =====", after)
    if m:
        rest = after[m.start():]
    else:
        rest = ""
    new_css = before + "\n\n" + MARKER + "\n" + CSS_BLOCK + "\n" + rest.lstrip("\n")
    return new_css


def main() -> None:
    here = Path(__file__).resolve()
    root = here.parents[2]
    gestao = root / "frontend" / "src" / "GestaoApp.jsx"
    css = root / "frontend" / "src" / "App.css"

    if not gestao.exists():
        fail(f"Arquivo não encontrado: {gestao}")
    if not css.exists():
        fail(f"Arquivo não encontrado: {css}")

    txt = gestao.read_text(encoding="utf-8")
    txt = patch_max_width(txt)
    txt = patch_actions(txt)

    gestao.write_text(txt, encoding="utf-8")

    css_txt = css.read_text(encoding="utf-8")
    css2 = patch_css(css_txt)
    if css2 != css_txt:
        css.write_text(css2 if css2.endswith("\n") else css2 + "\n", encoding="utf-8")

    print("OK: Gestão (Fila) — ocupação de espaço + cores/identidade ajustadas.")
    print("Arquivos alterados:")
    print(" -", gestao)
    print(" -", css)


if __name__ == "__main__":
    main()
