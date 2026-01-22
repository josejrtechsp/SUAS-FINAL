#!/usr/bin/env python3
import re, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
p = ROOT / "frontend" / "src" / "TelaCreasCasos.jsx"
if not p.exists():
    raise SystemExit(f"ERRO: não achei {p}")

s = p.read_text(encoding="utf-8")

# Backup
ts = time.strftime("%Y%m%d_%H%M%S")
bak = p.with_suffix(p.suffix + f".bak_timelineui_fixv8_{ts}")
bak.write_text(s, encoding="utf-8")

# Remove anchors/comments from earlier failed patches that might have inserted literal \n or similar
s = re.sub(r".*TIMELINEUI_ANCHOR_.*\n", "", s)

# If timelineUI already declared, nothing to do.
if re.search(r"(?m)^\s*(const|let|var)\s+timelineUI\s*=", s):
    p.write_text(s, encoding="utf-8")
    print(f"OK: timelineUI já existe. Nenhuma inserção necessária.\nArquivo: {p}\nBackup: {bak}")
    raise SystemExit(0)

# Find const sel = ...;
sel_pat = re.compile(r"(?m)^\s*const\s+sel\s*=\s*[^;]+;\s*$")
m = sel_pat.search(s)

insert_block = (
    "  // timelineUI: compat (timelineUI/timeline/historico)\n"
    "  const timelineUI = (sel && (sel.timelineUI || sel.timeline || sel.linha_tempo || sel.historico))\n"
    "    ? (sel.timelineUI || sel.timeline || sel.linha_tempo || sel.historico)\n"
    "    : [];\n"
)

if m:
    ins_at = m.end()
    s = s[:ins_at] + "\n" + insert_block + s[ins_at:]
    p.write_text(s, encoding="utf-8")
    print(f"OK: timelineUI inserido após `const sel = ...`.\nArquivo: {p}\nBackup: {bak}")
    raise SystemExit(0)

# Fallback: look for selected case variable names
fallback_names = ["selected", "selectedCase", "caso", "casoAtual", "c", "caseSel", "caseSelected"]
found = None
for name in fallback_names:
    pat = re.compile(rf"(?m)^\s*const\s+{re.escape(name)}\s*=\s*[^;]+;\s*$")
    mm = pat.search(s)
    if mm:
        found = (name, mm)
        break

if found:
    name, mm = found
    insert_block2 = (
        f"  // timelineUI: compat (timelineUI/timeline/historico) — derivado de `{name}`\n"
        f"  const timelineUI = ({name} && ({name}.timelineUI || {name}.timeline || {name}.linha_tempo || {name}.historico))\n"
        f"    ? ({name}.timelineUI || {name}.timeline || {name}.linha_tempo || {name}.historico)\n"
        f"    : [];\n"
    )
    ins_at = mm.end()
    s = s[:ins_at] + "\n" + insert_block2 + s[ins_at:]
    p.write_text(s, encoding="utf-8")
    print(f"OK: timelineUI inserido após `const {name} = ...`.\nArquivo: {p}\nBackup: {bak}")
    raise SystemExit(0)

# Last resort: insert near top of function body (after function line)
func_pat = re.compile(r"export\s+default\s+function\s+TelaCreasCasos\s*\([^)]*\)\s*\{")
fm = func_pat.search(s)
if not fm:
    raise SystemExit("ERRO: não consegui achar a assinatura de TelaCreasCasos().")

ins_at = fm.end()
insert_block3 = (
    "\n  // timelineUI: compat (timelineUI/timeline/historico) — fallback seguro\n"
    "  const timelineUI = [];\n"
)
s = s[:ins_at] + insert_block3 + s[ins_at:]
p.write_text(s, encoding="utf-8")
print(f"OK: timelineUI inserido no topo do componente (fallback).\nArquivo: {p}\nBackup: {bak}")
