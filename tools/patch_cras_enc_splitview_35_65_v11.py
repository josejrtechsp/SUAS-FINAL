#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CRAS Encaminhamentos Split View 35/65 - Patch V11 (char-level parser, self-closing div aware)

Fix for V10: handles self-closing <div .../> tags so depth counting can reach zero.

What it does:
- Finds the root <div ...cras-flow-mini...> and its matching </div> by counting <div></div>,
  ignoring occurrences inside strings and comments.
- Treats self-closing <div .../> as depth-neutral.
- Moves the <EncaminhamentosSuas ...> block to the right column.
- Puts the rest of the root inner content into the left column.
- Appends SplitView CSS into cras_ui_v2.css (with backup) if missing.
- Creates automatic backup of the JSX file before writing.

Safe: aborts without writing if it cannot find patterns reliably.
"""

from pathlib import Path
from datetime import datetime
import re
import sys

ROOT = Path.home() / "POPNEWS1"
target = ROOT / "frontend/src/TelaCrasEncaminhamentos.jsx"
css_path = ROOT / "frontend/src/cras_ui_v2.css"

MARKER = "CRAS_ENC_SPLITVIEW_35_65_V11"

def iter_scan(s: str, start: int, stop: int | None = None):
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

def find_root_start(text: str) -> int:
    m = re.search(r"<\s*div\b[^>]*cras-flow-mini", text, flags=re.S)
    return m.start() if m else -1

def find_tag_end(text: str, start: int, stop: int | None = None) -> int:
    if stop is None:
        stop = len(text)
    for i in iter_scan(text, start, stop):
        if text[i] == ">":
            return i
    return -1

def is_open_div(text: str, i: int) -> bool:
    if text.startswith("</", i):
        return False
    if not text.startswith("<div", i):
        return False
    j = i+4
    if j >= len(text):
        return False
    return text[j].isspace() or text[j] in (">", "/")

def is_close_div(text: str, i: int) -> bool:
    if not text.startswith("</div", i):
        return False
    j = i+5
    if j >= len(text):
        return True
    return text[j].isspace() or text[j] == ">"

def is_self_closing_div(text: str, i: int) -> bool:
    # assumes is_open_div(text,i) is True
    end = find_tag_end(text, i)
    if end == -1:
        return False
    k = end - 1
    while k > i and text[k].isspace():
        k -= 1
    return text[k] == "/"

def find_root_close(text: str, root_start: int) -> tuple[int,int]:
    depth = 0
    for i in iter_scan(text, root_start):
        if text[i] != "<":
            continue
        if is_open_div(text, i):
            if not is_self_closing_div(text, i):
                depth += 1
        elif is_close_div(text, i):
            depth -= 1
            if depth == 0:
                end = text.find(">", i)
                if end == -1:
                    raise SystemExit("Found </div> but no matching '>'")
                return i, end+1
    return -1, -1

def find_open_tag_end(text: str, start: int) -> int:
    return find_tag_end(text, start)

def find_component_block(text: str, start: int, end: int) -> tuple[int,int]:
    comp_start = text.find("<EncaminhamentosSuas", start, end)
    if comp_start == -1:
        return -1, -1

    gt = -1
    self_close_end = -1
    for j in iter_scan(text, comp_start, end):
        if text[j] == "/" and j+1 < end and text[j+1] == ">":
            self_close_end = j+2
            break
        if text[j] == ">":
            gt = j
            break

    if self_close_end != -1:
        return comp_start, self_close_end

    if gt == -1:
        return -1, -1

    close_tag = "</EncaminhamentosSuas>"
    close_start = text.find(close_tag, gt+1, end)
    if close_start == -1:
        m = re.search(r"</\s*EncaminhamentosSuas\s*>", text[gt+1:end])
        if not m:
            return -1, -1
        close_start = gt+1 + m.start()
        close_end = gt+1 + m.end()
        return comp_start, close_end

    close_end = close_start + len(close_tag)
    return comp_start, close_end

def append_css():
    if not css_path.exists():
        print("WARN: cras_ui_v2.css not found; skipping CSS.")
        return
    css = css_path.read_text(encoding="utf-8", errors="ignore")
    css_marker = "/* CRAS_ENC_SPLITVIEW_35_65_CSS_V11 */"
    if css_marker in css:
        print("OK: CSS already present.")
        return
    bak = css_path.with_suffix(css_path.suffix + ".bak_" + datetime.now().strftime("%Y%m%d_%H%M%S"))
    bak.write_text(css, encoding="utf-8")
    css_add = """\n\n/* CRAS_ENC_SPLITVIEW_35_65_CSS_V11 */
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
    css_path.write_text(css + css_add, encoding="utf-8")
    print("OK: CSS appended:", css_path)
    print("Backup CSS:", bak)

def main():
    if not target.exists():
        raise SystemExit(f"File not found: {target}")

    text = target.read_text(encoding="utf-8", errors="ignore")
    if MARKER in text:
        print("OK: already applied (V11).")
        return

    root_start = find_root_start(text)
    if root_start == -1:
        raise SystemExit("Could not find root <div ...cras-flow-mini...>.")

    root_open_end = find_open_tag_end(text, root_start)
    if root_open_end == -1:
        raise SystemExit("Could not find '>' for root opening tag.")

    root_close_start, root_close_end = find_root_close(text, root_start)
    if root_close_start == -1:
        raise SystemExit("Could not find matching root </div> (depth).")

    inner_start = root_open_end + 1
    inner_end = root_close_start

    enc_start, enc_end = find_component_block(text, inner_start, inner_end)
    if enc_start == -1:
        raise SystemExit("Could not find <EncaminhamentosSuas ...> within root.")

    enc_block = text[enc_start:enc_end]
    left_content = text[inner_start:enc_start] + text[enc_end:inner_end]

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

    bak = target.with_suffix(target.suffix + ".bak_" + datetime.now().strftime("%Y%m%d_%H%M%S"))
    bak.write_text(text, encoding="utf-8")
    target.write_text(new_text, encoding="utf-8")
    print("OK: SplitView V11 applied:", target)
    print("Backup:", bak)

    append_css()

if __name__ == "__main__":
    main()
