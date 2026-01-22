#!/usr/bin/env python3
import re, sys, glob, os
from pathlib import Path
from datetime import datetime

ROOT = Path(os.environ.get("POPNEWS1_ROOT", Path.cwd()))
# allow running from anywhere: prefer locating frontend/src under ROOT
candidates = [
    ROOT / "frontend" / "src" / "TelaCreasCasos.jsx",
    ROOT / "frontend" / "frontend" / "src" / "TelaCreasCasos.jsx",
]

target = None
for c in candidates:
    if c.exists():
        target = c
        break

if not target:
    print("ERRO: não encontrei TelaCreasCasos.jsx (esperado em frontend/src).")
    sys.exit(1)

src_dir = target.parent
# 1) restore latest backup if exists
bak_glob = str(target) + ".bak_timelineui_*"
baks = sorted(glob.glob(bak_glob), key=lambda p: os.path.getmtime(p), reverse=True)

backup_taken = target.with_suffix(target.suffix + f".bak_before_v4_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
backup_taken.write_text(target.read_text(encoding="utf-8"), encoding="utf-8")

restored_from = None
if baks:
    restored_from = Path(baks[0])
    target.write_text(restored_from.read_text(encoding="utf-8"), encoding="utf-8")

s = target.read_text(encoding="utf-8")

# 2) remove any existing const/let timelineUI definitions (avoid duplicates/TDZ)
s = re.sub(r'(?m)^\s*(const|let)\s+timelineUI\s*=\s*.*?;\s*$', '', s)

# 3) insert a safe timelineUI definition right after `const sel = ...` (first match)
lines = s.splitlines(True)

inserted = False
sel_line_idx = None

# find a line that defines sel (common patterns)
patterns = [
    re.compile(r'^\s*const\s+sel\s*=\s*.*;\s*$'),
    re.compile(r'^\s*const\s+selected\s*=\s*.*;\s*$'),
    re.compile(r'^\s*const\s+caseSel\s*=\s*.*;\s*$'),
]
varname = "sel"

for i, line in enumerate(lines):
    for pat in patterns:
        if pat.match(line):
            sel_line_idx = i
            if "const sel" in line:
                varname = "sel"
            elif "const selected" in line:
                varname = "selected"
            elif "const caseSel" in line:
                varname = "caseSel"
            break
    if sel_line_idx is not None:
        break

# If not found, try to detect 'sel' usage in dependency arrays and insert near top of component
if sel_line_idx is None:
    # heuristic: insert after the first occurrence of function component start: `export default function` or `function TelaCreasCasos`
    for i, line in enumerate(lines):
        if re.search(r'function\s+TelaCreasCasos\b|export\s+default\s+function\b', line):
            # insert a few lines after opening brace
            sel_line_idx = i
            varname = "sel"
            break

defn = f'  const timelineUI = Array.isArray({varname} && {varname}.timelineUI) ? {varname}.timelineUI : (Array.isArray({varname} && {varname}.timeline) ? {varname}.timeline : []);\n'

if sel_line_idx is not None:
    # insert after sel definition line (or near top fallback)
    ins_at = sel_line_idx + 1
    # avoid inserting inside import area
    if ins_at < len(lines) and re.match(r'^\s*import\b', lines[ins_at]):
        # unlikely; but if so, insert after last import
        j = 0
        while j < len(lines) and re.match(r'^\s*import\b', lines[j]):
            j += 1
        ins_at = j
    # ensure we don't double insert if already exists
    if "const timelineUI" not in "".join(lines[max(0,ins_at-3):min(len(lines),ins_at+3)]):
        lines.insert(ins_at, defn)
        inserted = True

s2 = "".join(lines)

# 4) As extra safety, replace any bare 'timelineUI' dependency in useEffect with (timelineUI) only if defined
# (No-op; the definition now exists. Keep as is.)

target.write_text(s2, encoding="utf-8")

print("OK: fix timelineUI V4 aplicado.")
print("Arquivo:", target)
print("Backup extra:", backup_taken)
if restored_from:
    print("Restaurado de:", restored_from)
print("timelineUI inserido:", inserted)
