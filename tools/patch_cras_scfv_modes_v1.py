#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Patch SCFV - modos (default: CHAMADA) - V1

Este patch:
- Encontra o arquivo do SCFV no frontend/src (procurando 'SCFV — Turmas' e 'SCFV — Participantes').
- Adiciona useState e estado scfvView = 'chamada'.
- Insere uma barra de modos (Chamada/Turmas/Alertas/Exportação).
- Envolve os dois blocos principais em wrappers com classes:
    scfv-only-turmas  (bloco de turmas)
    scfv-not-turmas   (bloco de participantes/chamada/relatórios)
- Importa um CSS local: cras_scfv_modes.css
- Faz backup automático do arquivo antes de alterar.

Se não achar os padrões, aborta imprimindo o arquivo alvo encontrado e os trechos relevantes.
"""

from pathlib import Path
from datetime import datetime
import re
import sys

ROOT = Path.home() / "POPNEWS1"
SRC = ROOT / "frontend/src"

def find_scfv_file():
    candidates = []
    for p in SRC.glob("**/*.jsx"):
        try:
            t = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        if ("SCFV — Turmas" in t or "SCFV - Turmas" in t) and ("SCFV — Participantes" in t or "SCFV - Participantes" in t):
            candidates.append(p)
        elif ("VOCÊ ESTÁ EM" in t and "SCFV" in t and ("Turmas" in t and "Frequência" in t and "Alertas" in t and "Exportação" in t)):
            candidates.append(p)
    return candidates[0] if candidates else None

p = find_scfv_file()
if not p:
    raise SystemExit("Não encontrei o arquivo do SCFV em frontend/src. Procure por 'SCFV — Turmas' e 'SCFV — Participantes'.")

txt = p.read_text(encoding="utf-8", errors="ignore")
if "SCFV_MODES_V1" in txt:
    print("OK: SCFV_MODES_V1 já aplicado.")
    raise SystemExit(0)

bak = p.with_suffix(p.suffix + ".bak_" + datetime.now().strftime("%Y%m%d_%H%M%S"))
bak.write_text(txt, encoding="utf-8")
print("Arquivo SCFV:", p)
print("Backup:", bak)

# 1) Import CSS
css_import = 'import "./cras_scfv_modes.css"; // SCFV_MODES_V1\n'
if css_import not in txt:
    # insert after first import line
    txt2 = re.sub(r'^(import[^\n]*\n)', r'\1' + css_import, txt, count=1, flags=re.M)
    txt = txt2

# 2) Ensure useState in react import
if "useState" not in txt:
    # cases:
    # import React from "react";
    # import React, { useMemo } from "react";
    # import { useMemo } from "react";
    if re.search(r'import\s+React\s*,\s*\{[^}]*\}\s*from\s*["\']react["\']', txt):
        txt = re.sub(r'(import\s+React\s*,\s*\{)([^}]*)(\}\s*from\s*["\']react["\'])',
                     lambda m: m.group(1) + m.group(2).rstrip() + (", useState" if m.group(2).strip() else "useState") + m.group(3),
                     txt, count=1)
    elif re.search(r'import\s+\{[^}]*\}\s*from\s*["\']react["\']', txt):
        txt = re.sub(r'(import\s+\{)([^}]*)(\}\s*from\s*["\']react["\'])',
                     lambda m: m.group(1) + m.group(2).rstrip() + (", useState" if m.group(2).strip() else "useState") + m.group(3),
                     txt, count=1)
    else:
        # fallback: add import line
        txt = 'import { useState } from "react";\n' + txt

# 3) Add state inside component (first export default function)
mfun = re.search(r'export\s+default\s+function\s+([A-Za-z0-9_]+)\s*\([^)]*\)\s*\{', txt)
if not mfun:
    raise SystemExit("Não encontrei 'export default function' no arquivo SCFV.")
insert_pos = mfun.end()

state_line = '\n  const [scfvView, setScfvView] = useState("chamada"); // SCFV_MODES_V1\n'
if "setScfvView" not in txt:
    txt = txt[:insert_pos] + state_line + txt[insert_pos:]

# 4) Insert modebar near header chips area: place before first "SCFV — Turmas"
idx = txt.find("SCFV — Turmas")
if idx == -1:
    idx = txt.find("SCFV - Turmas")
if idx == -1:
    raise SystemExit("Não achei 'SCFV — Turmas' para ancorar a inserção da barra de modos.")

# find start of line containing the title; then find a safe insertion point a few lines above: after the page header closing.
# We'll insert right before the line that contains the title.
line_start = txt.rfind("\n", 0, idx) + 1

modebar_jsx = '''
      {/* SCFV_MODES_V1: barra de modos (Apple-like) */}
      <div className="scfv-modebar">
        <button type="button" className={"scfv-modebtn" + (scfvView === "chamada" ? " is-active" : "")} onClick={() => setScfvView("chamada")}>Chamada</button>
        <button type="button" className={"scfv-modebtn" + (scfvView === "turmas" ? " is-active" : "")} onClick={() => setScfvView("turmas")}>Turmas</button>
        <button type="button" className={"scfv-modebtn" + (scfvView === "alertas" ? " is-active" : "")} onClick={() => setScfvView("alertas")}>Alertas</button>
        <button type="button" className={"scfv-modebtn" + (scfvView === "export" ? " is-active" : "")} onClick={() => setScfvView("export")}>Exportação</button>
      </div>
'''

txt = txt[:line_start] + modebar_jsx + txt[line_start:]

# 5) Wrap Turmas block card and Main block card using headings as anchors
# Wrap nearest containing <div className="card"...> for each heading by simple div-depth within a window.

def wrap_card_by_heading(text, heading, wrapper_class):
    pos = text.find(heading)
    if pos == -1:
        return text, False
    # search backward for '<div' with 'card' in same line within 1500 chars
    back = text.rfind("<div", max(0, pos-1500), pos)
    if back == -1:
        return text, False
    # ensure it's a card-ish div
    line_end = text.find("\n", back)
    if line_end == -1: line_end = min(len(text), back+200)
    if "card" not in text[back:line_end]:
        # try earlier
        for _ in range(6):
            back = text.rfind("<div", max(0, back-1500), back)
            if back == -1: break
            line_end = text.find("\n", back)
            if line_end == -1: line_end = min(len(text), back+200)
            if "card" in text[back:line_end]:
                break
        else:
            return text, False
        if back == -1 or "card" not in text[back:line_end]:
            return text, False

    # find matching </div> for this opening by counting <div and </div> tokens (best-effort)
    i = back
    depth = 0
    while i < len(text):
        nxt_div = text.find("<div", i)
        nxt_close = text.find("</div", i)
        if nxt_close == -1:
            return text, False
        if nxt_div != -1 and nxt_div < nxt_close:
            # check self closing <div .../>
            gt = text.find(">", nxt_div)
            if gt != -1 and text[gt-1] == "/":
                i = gt+1
                continue
            depth += 1
            i = nxt_div + 4
        else:
            depth -= 1
            end_gt = text.find(">", nxt_close)
            if end_gt == -1:
                return text, False
            i = end_gt + 1
            if depth == 0:
                close_end = i
                open_tag = f'<div className="{wrapper_class}">' + "\n"
                close_tag = "\n</div>\n"
                return text[:back] + open_tag + text[back:close_end] + close_tag + text[close_end:], True
    return text, False

txt, ok1 = wrap_card_by_heading(txt, "SCFV — Turmas", "scfv-only-turmas")
txt, ok2 = wrap_card_by_heading(txt, "SCFV — Participantes", "scfv-not-turmas")

# 6) Ensure stage wrapper exists around the main content area after the header (wrap first occurrence of modebar)
if 'className="scfv-stage"' not in txt:
    # wrap the first modebar occurrence and everything after it until end of the main return block isn't safe.
    # Instead, add a simple wrapper around the two blocks by injecting opening before first wrapper class occurrence.
    first_block = txt.find('className="scfv-only-turmas"')
    second_block = txt.find('className="scfv-not-turmas"')
    start = min([x for x in [first_block, second_block] if x != -1], default=-1)
    if start != -1:
        # insert opening wrapper before the <div className="scfv-only-turmas"> tag
        tag_start = txt.rfind("<div", 0, start)
        if tag_start != -1:
            txt = txt[:tag_start] + f'<div className="scfv-stage" data-scfv-view={{scfvView}}>' + "\n" + txt[tag_start:]
            # close wrapper near end of file before final ');' of return: best-effort insert before last '</div>'
            last_div = txt.rfind("</div>")
            if last_div != -1:
                txt = txt[:last_div] + "</div>\n" + txt[last_div:]

# 7) Hide the original chips row in header for SCFV by scoping CSS (user sees only one navigation layer)
# We'll rely on CSS selecting .scfv-modebar and not touching others.

p.write_text(txt, encoding="utf-8")
print("✅ OK: SCFV modos aplicados.")
print("Turmas wrapper:", ok1, "| Main wrapper:", ok2)
