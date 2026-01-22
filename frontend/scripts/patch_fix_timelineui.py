#!/usr/bin/env python3
# Fix "Cannot access 'timelineUI' before initialization." in TelaCreasCasos.jsx
# Strategy:
# - Locate the first usage of `timelineUI` in the module.
# - Locate the definition block that starts with `const timelineUI =` (or `let timelineUI =`).
# - If the definition appears AFTER the first usage, move the entire definition block
#   to just BEFORE the first usage line (same indentation), preserving code.
# - If no definition is found, do nothing (prints a message).
# - Always writes a .bak_TIMESTAMP backup next to the file.

from __future__ import annotations
import re, sys, pathlib, datetime

PATH = pathlib.Path("frontend/src/TelaCreasCasos.jsx")

def die(msg: str, code: int = 1):
    print(msg)
    sys.exit(code)

def main():
    if not PATH.exists():
        die(f"ERRO: arquivo não encontrado: {PATH}")

    s = PATH.read_text(encoding="utf-8", errors="replace")

    # Find first usage of timelineUI (excluding its own declaration).
    # We'll look for word boundary, but skip the declaration itself.
    decl_pat = re.compile(r'(?m)^\s*(const|let)\s+timelineUI\s*=')
    use_pat  = re.compile(r'\btimelineUI\b')

    decl_m = decl_pat.search(s)
    if not decl_m:
        print("OK: não encontrei declaração `const timelineUI = ...` (nada a corrigir).")
        return

    # Determine the first usage index that is not within the declaration line itself
    decl_line_start = s.rfind("\n", 0, decl_m.start()) + 1
    decl_line_end = s.find("\n", decl_m.start())
    if decl_line_end == -1: decl_line_end = len(s)

    first_use = None
    for m in use_pat.finditer(s):
        if decl_line_start <= m.start() <= decl_line_end:
            continue
        first_use = m
        break

    if not first_use:
        print("OK: não encontrei uso de timelineUI (nada a corrigir).")
        return

    if decl_m.start() < first_use.start():
        print("OK: timelineUI já está declarado antes do primeiro uso.")
        return

    # Extract the whole definition block.
    # We assume it is a single statement ending with ');' or ');\\n' (useMemo, etc.)
    # We'll capture from declaration start to the end of that statement.
    start = decl_m.start()

    # Heuristic to find end: scan forward for a line that ends with ');' at same or lower indentation.
    # Fallback: find the next blank line after a line containing ');'
    lines = s.splitlines(True)
    # compute line index of start
    acc = 0
    start_line_idx = 0
    for i, ln in enumerate(lines):
        if acc + len(ln) > start:
            start_line_idx = i
            break
        acc += len(ln)

    # Determine indentation of decl line
    decl_indent = re.match(r'^(\s*)', lines[start_line_idx]).group(1)

    end_line_idx = None
    # search from start_line_idx forward
    for j in range(start_line_idx, min(len(lines), start_line_idx + 200)):  # within 200 lines
        txt = lines[j].rstrip("\n")
        if txt.strip().endswith(");"):
            # accept end if indentation is same or less (avoid inner closures)
            indent = re.match(r'^(\s*)', lines[j]).group(1)
            if len(indent) <= len(decl_indent):
                end_line_idx = j
                break
    if end_line_idx is None:
        # fallback: first line that is blank after seeing a ');'
        saw = False
        for j in range(start_line_idx, min(len(lines), start_line_idx + 400)):
            if ");" in lines[j]:
                saw = True
            if saw and lines[j].strip() == "":
                end_line_idx = j - 1
                break
    if end_line_idx is None:
        die("ERRO: não consegui identificar o fim do bloco de timelineUI para mover (heurística falhou).")

    block = "".join(lines[start_line_idx:end_line_idx+1])

    # Remove the block from original position
    before = "".join(lines[:start_line_idx])
    after  = "".join(lines[end_line_idx+1:])

    # Insert block before the line containing first_use
    # Find the line index of first_use
    # recompute over original lines indices
    acc = 0
    use_line_idx = 0
    for i, ln in enumerate(lines):
        if acc + len(ln) > first_use.start():
            use_line_idx = i
            break
        acc += len(ln)

    # Build new content: insert block before use_line_idx in the "before+after" version.
    new_lines = (before + after).splitlines(True)

    # But the removal changed indices; safer: compute insertion point by searching for the exact line text
    target_line = lines[use_line_idx]
    ins_idx = None
    for i, ln in enumerate(new_lines):
        if ln == target_line:
            ins_idx = i
            break
    if ins_idx is None:
        # fallback: insert at start of file (safe, though not ideal)
        ins_idx = 0

    new_lines.insert(ins_idx, block if block.endswith("\n") else block + "\n")
    new_s = "".join(new_lines)

    # Backup & write
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    bak = PATH.with_suffix(PATH.suffix + f".bak_fix_timelineUI_{ts}")
    bak.write_text(s, encoding="utf-8")
    PATH.write_text(new_s, encoding="utf-8")
    print(f"OK: timelineUI movido para antes do primeiro uso. Backup: {bak.name}")

if __name__ == "__main__":
    main()
