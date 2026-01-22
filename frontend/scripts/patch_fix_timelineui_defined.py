#!/usr/bin/env python3
import sys, re, pathlib

path = pathlib.Path(sys.argv[1])
s = path.read_text(encoding="utf-8")

# Se já existe declaração, não faz nada.
if re.search(r'\bconst\s+timelineUI\b|\blet\s+timelineUI\b|\bvar\s+timelineUI\b', s):
    print("INFO: timelineUI já existe, nada a fazer.")
    sys.exit(0)

lines = s.splitlines(True)

# Encontrar ponto de inserção: após `const timeline = ...` (preferido).
insert_idx = None
for i, line in enumerate(lines):
    if re.search(r'^\s*const\s+timeline\s*=', line):
        insert_idx = i + 1
        break

# Fallback: após `const caso =`
if insert_idx is None:
    for i, line in enumerate(lines):
        if re.search(r'^\s*const\s+caso\s*=', line):
            insert_idx = i + 1
            break

block = r'''
  // FIX: garante que timelineUI exista (evita TDZ/undefined)
  const timelineUI = (() => {
    try {
      // preferir `timeline` se existir no escopo; senão usar `caso.timeline`
      // (o patch insere após `const timeline =` quando presente)
      const t = (typeof timeline !== "undefined" && Array.isArray(timeline))
        ? timeline
        : (Array.isArray(caso?.timeline) ? caso.timeline : []);
      return t;
    } catch (e) {
      return [];
    }
  })();

'''

if insert_idx is None:
    # inserir no topo do arquivo
    s = block + s
else:
    lines.insert(insert_idx, block)
    s = "".join(lines)

path.write_text(s, encoding="utf-8")
print("INFO: Inserido const timelineUI com fallback seguro.")
