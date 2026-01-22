#!/usr/bin/env python3
import re, sys, pathlib

path = pathlib.Path(sys.argv[1])
s = path.read_text(encoding="utf-8")

# If already has a timelineUI declaration, we do nothing.
if re.search(r"\b(const|let|var)\s+timelineUI\b", s):
    print("INFO: timelineUI ja declarado, nada a fazer.")
    sys.exit(0)

m = re.search(r"\btimelineUI\b", s)
if not m:
    print("INFO: arquivo nao referencia timelineUI, nada a fazer.")
    sys.exit(0)

first_use = m.start()

# Try to find the 'caso' variable defined before first use.
# Common patterns: const caso = ..., let caso = ...
var_name = None
for cand in ("caso", "c", "casoSel", "casoSelecionado", "selectedCase", "selected", "currentCase"):
    # find last definition before first_use
    pat = re.compile(rf"\b(const|let|var)\s+{re.escape(cand)}\s*=", re.M)
    last = None
    for mm in pat.finditer(s, 0, first_use):
        last = mm
    if last:
        var_name = cand
        insert_pos = s.find("\n", last.end())
        if insert_pos == -1:
            insert_pos = last.end()
        else:
            insert_pos += 1
        break

# Fallback: insert near start of component body
if var_name is None:
    # try to detect component start
    comp = re.search(r"(export\s+default\s+function\s+TelaCreasCasos|function\s+TelaCreasCasos)\s*\([^)]*\)\s*\{", s)
    if comp:
        insert_pos = comp.end()
        # insert after next newline for readability
        nl = s.find("\n", insert_pos)
        if nl != -1:
            insert_pos = nl + 1
    else:
        # last resort: insert at file top
        insert_pos = 0
    var_name = "undefined"

def_line = ""
if var_name != "undefined":
    def_line = (
        f"  const timelineUI = Array.isArray(({var_name} && ({var_name}.timelineUI || {var_name}.timeline_ui || {var_name}.timeline)))\n"
        f"    ? ({var_name}.timelineUI || {var_name}.timeline_ui || {var_name}.timeline)\n"
        f"    : [];\n\n"
    )
else:
    # safe module-level fallback to avoid runtime crash; keeps UI alive
    def_line = (
        "  const timelineUI = [];\n\n"
    )

# Ensure indentation: if we inserted at file top, remove two spaces
if insert_pos == 0:
    def_line = def_line.replace("  const timelineUI", "const timelineUI")

s2 = s[:insert_pos] + def_line + s[insert_pos:]

path.write_text(s2, encoding="utf-8")
print(f"PATCH: inserido timelineUI (var base: {var_name}) em offset {insert_pos}.")
