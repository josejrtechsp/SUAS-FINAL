#!/usr/bin/env python3
import sys, re, glob, os, time
from pathlib import Path

target = Path(sys.argv[1]).resolve()
root = target.parent
ts = time.strftime("%Y%m%d_%H%M%S")

# Backup current file always
bak_broken = target.with_suffix(target.suffix + f".bak_broken_{ts}")
bak_broken.write_text(target.read_text(encoding="utf-8"), encoding="utf-8")

s = target.read_text(encoding="utf-8")

# If file contains broken anchor markers or literal \n sequences in signature, restore from latest backup
need_restore = ("TIMELINEUI_ANCHOR_V6" in s) or (r"\n var timelineUI" in s) or ("Expected `:` but found `\\`" in s)

# also restore if file contains 'var timelineUI' within the function signature line (common break)
if re.search(r"export\s+default\s+function\s+TelaCreasCasos\(\{[^}]*\\n", s):
    need_restore = True

if need_restore:
    backups = sorted(glob.glob(str(target) + ".bak_timelineui_*"), key=lambda p: os.path.getmtime(p), reverse=True)
    if backups:
        s = Path(backups[0]).read_text(encoding="utf-8")
    else:
        # no backup; attempt to remove the broken injected sequences inline as last resort
        s = s.replace(r"\n", " ")

# Remove any previously injected V6 marker fragments in-line (defensive)
s = re.sub(r"//\s*TIMELINEUI_ANCHOR_V6:[^\n]*", "//", s)

# If timelineUI already defined, keep as-is (but ensure it is after sel)
if re.search(r"(?m)^\s*(const|let|var)\s+timelineUI\s*=", s):
    target.write_text(s, encoding="utf-8")
    print(f"OK: timelineUI já existia. Arquivo preservado.\nBackup do estado anterior: {bak_broken}")
    sys.exit(0)

lines = s.splitlines(True)

# Find insertion point: after 'const sel =' (most common)
insert_idx = None
sel_pat = re.compile(r"^\s*const\s+sel\s*=")
for i, line in enumerate(lines):
    if sel_pat.match(line):
        insert_idx = i + 1
        break

# Fallback: after 'const selected' or 'const casoSel'
if insert_idx is None:
    for pat in [
        re.compile(r"^\s*const\s+casoSel\s*="),
        re.compile(r"^\s*const\s+selectedCase\s*="),
        re.compile(r"^\s*const\s+selected\s*="),
    ]:
        for i, line in enumerate(lines):
            if pat.match(line):
                insert_idx = i + 1
                break
        if insert_idx is not None:
            break

if insert_idx is None:
    # As a last resort, insert after first useState declarations
    for i, line in enumerate(lines):
        if "useState" in line:
            insert_idx = i + 1
    if insert_idx is None:
        insert_idx = 0

insertion = (
    "  // timelineUI: visão normalizada da linha do tempo (evita ReferenceError)\n"
    "  const timelineUI = (sel && (sel.timelineUI || sel.timeline || sel.linha_tempo || sel.historico)) || [];\n"
)

lines.insert(insert_idx, insertion)

out = "".join(lines)
target.write_text(out, encoding="utf-8")

print("OK: timelineUI inserido de forma segura.")
print("Arquivo:", target)
print("Backup do estado anterior:", bak_broken)
