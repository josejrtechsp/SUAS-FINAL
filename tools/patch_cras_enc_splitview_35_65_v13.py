#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CRAS Encaminhamentos SplitView 35/65 - Patch V13 (robust parent div selection)

Goal:
- Convert the Encaminhamentos page into a 35/65 split view (Apple Mail-like).
- Left column: everything except EncaminhamentosSuas.
- Right column: EncaminhamentosSuas block.

Why V12 failed:
- EncaminhamentosSuas is not necessarily inside the first <div> after return(.
This version:
- Parses all <div> ... </div> pairs (ignoring strings/comments, handling self-closing divs).
- Finds EncaminhamentosSuas block position.
- Chooses a parent <div> that contains the block (prefers one that also contains keywords like "Sem devolutiva" or "Novo").
- Rewrites ONLY the inner content of that parent div into the split layout.
- Adds CSS to cras_ui_v2.css (with backup) if missing.
- Creates backup of TelaCrasEncaminhamentos.jsx before writing.

Safe: aborts without writing if it cannot find what it needs.
"""

from pathlib import Path
from datetime import datetime
import re
import sys

ROOT = Path.home() / "POPNEWS1"
TARGET = ROOT / "frontend/src/TelaCrasEncaminhamentos.jsx"
CSS_PATH = ROOT / "frontend/src/cras_ui_v2.css"

MARKER = "CRAS_ENC_SPLITVIEW_35_65_V13"
CSS_MARKER = "/* CRAS_ENC_SPLITVIEW_35_65_CSS_V13 */"

def iter_scan(s, start, stop=None):
    if stop is None:
        stop = len(s)
    i = start
    in_sq = in_dq = in_bt = False
    in_lc = in_bc = False
    esc = False
    while i < stop:
        ch = s[i]
        nxt = s[i+1] if i+1 < stop else ""
        if in_lc:
            if ch == "\n":
                in_lc = False
            i += 1
            continue
        if in_bc:
            if ch == "*" and nxt == "/":
                in_bc = False
                i += 2
                continue
            i += 1
            continue
        if in_sq:
            if not esc and ch == "'":
                in_sq = False
            esc = (ch == "\\" and not esc)
            i += 1
            continue
        if in_dq:
            if not esc and ch == '"':
                in_dq = False
            esc = (ch == "\\" and not esc)
            i += 1
            continue
        if in_bt:
            if not esc and ch == "`":
                in_bt = False
            esc = (ch == "\\" and not esc)
            i += 1
            continue

        if ch == "/" and nxt == "/":
            in_lc = True
            i += 2
            continue
        if ch == "/" and nxt == "*":
            in_bc = True
            i += 2
            continue
        if ch == "'":
            in_sq = True
            esc = False
            i += 1
            continue
        if ch == '"':
            in_dq = True
            esc = False
            i += 1
            continue
        if ch == "`":
            in_bt = True
            esc = False
            i += 1
            continue

        yield i
        i += 1

def find_tag_end(text, start, stop=None):
    if stop is None:
        stop = len(text)
    for i in iter_scan(text, start, stop):
        if text[i] == ">":
            return i
    return -1

def is_open_div(text, i):
    if text.startswith("</", i):
        return False
    if not text.startswith("<div", i):
        return False
    j = i + 4
    if j >= len(text):
        return False
    return text[j].isspace() or text[j] in (">", "/")

def is_close_div(text, i):
    if not text.startswith("</div", i):
        return False
    j = i + 5
    if j >= len(text):
        return True
    return text[j].isspace() or text[j] == ">"

def is_self_closing_div(text, i):
    end = find_tag_end(text, i)
    if end == -1:
        return False
    k = end - 1
    while k > i and text[k].isspace():
        k -= 1
    return text[k] == "/"

def parse_div_pairs(text):
    stack = []
    pairs = []  # (open_start, open_end, close_start, close_end)
    for i in iter_scan(text, 0):
        if text[i] != "<":
            continue
        if is_open_div(text, i):
            open_end = find_tag_end(text, i)
            if open_end == -1:
                continue
            if is_self_closing_div(text, i):
                # self-closing: ignore for nesting
                continue
            stack.append((i, open_end+1))
        elif is_close_div(text, i):
            close_end = text.find(">", i)
            if close_end == -1:
                continue
            if stack:
                open_start, open_end = stack.pop()
                pairs.append((open_start, open_end, i, close_end+1))
    return pairs

def find_enc_block(text):
    s = text.find("<EncaminhamentosSuas")
    if s == -1:
        return (-1, -1)
    # scan to end of tag (self-closing or paired)
    end_limit = len(text)
    gt = -1
    self_end = -1
    for j in iter_scan(text, s, end_limit):
        if text[j] == "/" and j+1 < end_limit and text[j+1] == ">":
            self_end = j+2
            break
        if text[j] == ">":
            gt = j
            break
    if self_end != -1:
        return (s, self_end)
    if gt == -1:
        return (-1, -1)
    close_tag = "</EncaminhamentosSuas>"
    c = text.find(close_tag, gt+1)
    if c != -1:
        return (s, c + len(close_tag))
    m = re.search(r"</\s*EncaminhamentosSuas\s*>", text[gt+1:])
    if not m:
        return (-1, -1)
    return (s, gt+1 + m.end())

def choose_parent_div(text, pairs, enc_pos):
    candidates = [p for p in pairs if p[0] < enc_pos < p[2]]
    if not candidates:
        return None
    # Sort by span (smallest first)
    candidates.sort(key=lambda p: (p[2]-p[0]))
    keywords = ["Sem devolutiva", "Novo", "Criar", "Encaminhamento criado", "Novo encaminhamento"]
    # choose first that contains any keyword outside the Enc tag itself
    for p in candidates:
        inner = text[p[1]:p[2]]
        if any(k in inner for k in keywords):
            return p
    # else use a slightly larger container (not the smallest) if smallest is too tight (contains only the component)
    smallest = candidates[0]
    inner_small = text[smallest[1]:smallest[2]]
    if "<EncaminhamentosSuas" in inner_small and inner_small.strip().startswith("<EncaminhamentosSuas") and len(inner_small.strip().splitlines()) < 15:
        # likely wrapper around only Enc; pick next if exists
        if len(candidates) > 1:
            return candidates[1]
    return smallest

def append_css():
    if not CSS_PATH.exists():
        print("WARN: cras_ui_v2.css not found; skipping CSS.")
        return
    css = CSS_PATH.read_text(encoding="utf-8", errors="ignore")
    if CSS_MARKER in css:
        print("OK: CSS already present.")
        return
    bak = CSS_PATH.with_suffix(CSS_PATH.suffix + ".bak_" + datetime.now().strftime("%Y%m%d_%H%M%S"))
    bak.write_text(css, encoding="utf-8")
    css_add = """\n\n/* CRAS_ENC_SPLITVIEW_35_65_CSS_V13 */
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
"""
    CSS_PATH.write_text(css + css_add, encoding="utf-8")
    print("OK: CSS appended:", CSS_PATH)
    print("Backup CSS:", bak)

def main():
    if not TARGET.exists():
        raise SystemExit(f"File not found: {TARGET}")
    text = TARGET.read_text(encoding="utf-8", errors="ignore")
    if MARKER in text:
        print("OK: already applied (V13).")
        return

    enc_start, enc_end = find_enc_block(text)
    if enc_start == -1:
        raise SystemExit("Could not find <EncaminhamentosSuas ...> in the file.")
    enc_block = text[enc_start:enc_end]

    pairs = parse_div_pairs(text)
    if not pairs:
        raise SystemExit("Could not parse any <div> pairs (unexpected).")

    parent = choose_parent_div(text, pairs, enc_start)
    if not parent:
        raise SystemExit("Could not find a parent <div> containing EncaminhamentosSuas.")
    open_start, open_end, close_start, close_end = parent

    inner_start = open_end
    inner_end = close_start

    # Ensure enc is within this inner
    if not (inner_start < enc_start < inner_end):
        raise SystemExit("Selected parent div does not actually contain EncaminhamentosSuas (safety).")

    # Create left content by removing enc block from the parent inner content
    left_content = text[inner_start:enc_start] + text[enc_end:inner_end]

    # Indent based on enc line
    line_start = text.rfind("\n", 0, enc_start) + 1
    indent = re.match(r"^\s*", text[line_start:enc_start]).group(0)

    new_inner = (
        f"\n{indent}{{/* {MARKER} */}}\n"
        f"{indent}<div className=\"cras-enc-split\">\n"
        f"{indent}  <div className=\"cras-enc-left\">\n"
        f"{indent}    <div className=\"cras-enc-left-stack\">\n"
        + left_content.rstrip()
        + f"\n{indent}    </div>\n"
        f"{indent}  </div>\n"
        f"{indent}  <div className=\"cras-enc-right\">\n"
        f"{indent}{enc_block.rstrip()}\n"
        f"{indent}  </div>\n"
        f"{indent}</div>\n"
    )

    new_text = text[:inner_start] + new_inner + text[inner_end:]

    bak = TARGET.with_suffix(TARGET.suffix + ".bak_" + datetime.now().strftime("%Y%m%d_%H%M%S"))
    bak.write_text(text, encoding="utf-8")
    TARGET.write_text(new_text, encoding="utf-8")
    print("OK: SplitView V13 applied:", TARGET)
    print("Backup:", bak)

    append_css()

if __name__ == "__main__":
    main()
