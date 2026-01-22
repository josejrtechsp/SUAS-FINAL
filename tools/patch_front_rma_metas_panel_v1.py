#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
from datetime import datetime
import re, sys

def tag(): return datetime.now().strftime("%Y%m%d_%H%M%S")
def backup(p: Path, s: str):
    p.with_suffix(p.suffix + f".bak_{tag()}").write_text(s, encoding="utf-8")

def ensure_import(s: str, line: str) -> str:
    if line.strip() in s: return s
    last = None
    for m in re.finditer(r"^\s*import .*?$", s, flags=re.M):
        last = m
    if last:
        pos = last.end()
        return s[:pos] + "\n" + line + s[pos:]
    return line + s

def main() -> int:
    root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(".").resolve()
    p = root / "frontend/src/TelaCrasRelatorios.jsx"
    if not p.exists():
        print("ERRO: não achei", p)
        return 2

    s0 = p.read_text(encoding="utf-8")
    s = ensure_import(s0, 'import RmaMetasPanel from "./RmaMetasPanel.jsx";\n')

    snippet = '      <RmaMetasPanel apiBase={apiBase} apiFetch={apiFetch} isActive={(typeof viewKey !== "undefined") ? (viewKey === "metas") : true} />\n'
    if snippet.strip() in s:
        print("OK: noop")
        return 0

    idx = s.find("<RmaQuickPanel")
    if idx >= 0:
        endline = s.find("\n", idx)
        s = s[:endline+1] + snippet + s[endline+1:]
    else:
        m = re.search(r"\n\s*return\s*\(\s*\n\s*<div[^>]*>\s*\n", s)
        if not m:
            print("ERRO: não encontrei ponto para inserir.")
            return 2
        s = s[:m.end()] + snippet + s[m.end():]

    backup(p, s0)
    p.write_text(s, encoding="utf-8")
    print("OK: inserted")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
