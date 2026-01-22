#!/usr/bin/env python3
import re, sys
from pathlib import Path

p = Path("frontend/src/TelaCreasCasos.jsx")
if not p.exists():
    print("ERRO: não achei", p)
    sys.exit(1)

s = p.read_text(encoding="utf-8")

# Evita duplicar
if re.search(r"\b(const|let|var)\s+timelineUI\b", s):
    print("OK: timelineUI já definido no arquivo (nada a fazer).")
    sys.exit(0)

lines = s.splitlines(True)

# localizar a função principal (melhor esforço)
fn_idx = None
for i, ln in enumerate(lines):
    if "function" in ln and "TelaCreasCasos" in ln:
        fn_idx = i
        break
if fn_idx is None:
    for i, ln in enumerate(lines):
        if "TelaCreasCasos" in ln and "(" in ln:
            fn_idx = i
            break
if fn_idx is None:
    fn_idx = 0

# localizar a declaração de sel
sel_decl_idx = None
sel_patterns = [
    re.compile(r"\bconst\s*\[\s*sel\s*,"),
    re.compile(r"\blet\s*\[\s*sel\s*,"),
    re.compile(r"\bconst\s+sel\s*="),
    re.compile(r"\blet\s+sel\s*="),
]
for i in range(fn_idx, min(len(lines), fn_idx + 600)):
    if any(pat.search(lines[i]) for pat in sel_patterns):
        sel_decl_idx = i
        break

if sel_decl_idx is None:
    for i, ln in enumerate(lines):
        if any(pat.search(ln) for pat in sel_patterns):
            sel_decl_idx = i
            break

if sel_decl_idx is None:
    print("ERRO: não consegui localizar a declaração de 'sel' no arquivo.")
    sys.exit(2)

insert_at = sel_decl_idx + 1

block = [
    "\n",
    "  // timelineUI: compat (evita ReferenceError após patches)\n",
    "  const timelineUI = (() => {\n",
    "    const x = sel || null;\n",
    "    if (!x) return [];\n",
    "    if (Array.isArray(x.timelineUI)) return x.timelineUI;\n",
    "    if (Array.isArray(x.timeline)) return x.timeline;\n",
    "    if (Array.isArray(x.linha_tempo)) return x.linha_tempo;\n",
    "    if (Array.isArray(x.historico)) return x.historico;\n",
    "    return [];\n",
    "  })();\n",
]

lines[insert_at:insert_at] = block
p.write_text("".join(lines), encoding="utf-8")
print("OK: timelineUI definido logo após a declaração de 'sel'.")
print("Arquivo:", str(p))
