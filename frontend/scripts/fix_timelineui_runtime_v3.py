#!/usr/bin/env python3
import re, sys, time
from pathlib import Path

CANDIDATE_ROOTS = [
  Path.home() / "POPNEWS1" / "frontend",
  Path.home() / "POPNEWS1" / "frontend" / "frontend",
]

def find_frontend_root():
  cwd = Path.cwd()
  for p in [cwd, cwd/"frontend", cwd/"frontend/frontend"]:
    if (p/"src").is_dir() and (p/"package.json").is_file():
      return p
  for p in CANDIDATE_ROOTS:
    if (p/"src").is_dir() and (p/"package.json").is_file():
      return p
  return None

def backup_file(fp: Path):
  ts = time.strftime("%Y%m%d_%H%M%S")
  bak = fp.with_suffix(fp.suffix + f".bak_timelineui_{ts}")
  bak.write_text(fp.read_text(encoding="utf-8"), encoding="utf-8")
  return bak

def main():
  root = find_frontend_root()
  if not root:
    print("ERRO: não achei a pasta frontend (com src/ e package.json). Rode a partir de ~/POPNEWS1 ou ~/POPNEWS1/frontend.", file=sys.stderr)
    sys.exit(1)

  fp = root/"src"/"TelaCreasCasos.jsx"
  if not fp.exists():
    print(f"ERRO: arquivo não encontrado: {fp}", file=sys.stderr)
    sys.exit(1)

  s = fp.read_text(encoding="utf-8")
  if "timelineUI" not in s:
    print("OK: Não encontrei 'timelineUI' no arquivo. Nada a fazer.")
    return

  lines = s.splitlines(True)

  # find first usage (any occurrence)
  usage_idxs = [i for i,l in enumerate(lines) if "timelineUI" in l]
  first_use = usage_idxs[0] if usage_idxs else None

  # remove any previous timelineUI definitions
  def_re = re.compile(r'^\s*(const|let|var)\s+timelineUI\s*=')
  new_lines = []
  removed = 0
  for l in lines:
    if def_re.search(l):
      removed += 1
      continue
    new_lines.append(l)
  lines = new_lines

  usage_idxs = [i for i,l in enumerate(lines) if "timelineUI" in l]
  if not usage_idxs:
    print("OK: Não há uso de timelineUI após limpeza. Nada a fazer.")
    bak = backup_file(fp)
    fp.write_text("".join(lines), encoding="utf-8")
    print("Backup:", bak)
    return
  first_use = usage_idxs[0]

  # find candidate case variable declared before first_use
  candidate_names = [
    "casoAtual", "caso", "c", "selectedCase", "selCase", "caseSel", "casoSel", "selecionado", "selected", "item"
  ]
  decl_re = re.compile(r'^\s*(const|let)\s+([A-Za-z_$][\w$]*)\s*=')
  last_decl_before = {}
  for i in range(0, first_use+1):
    m = decl_re.match(lines[i])
    if m:
      last_decl_before[m.group(2)] = i

  chosen = None
  chosen_i = None
  for nm in candidate_names:
    if nm in last_decl_before:
      chosen = nm
      chosen_i = last_decl_before[nm]
      break

  if chosen is None:
    for nm, i in last_decl_before.items():
      if ("caso" in nm.lower()) or ("case" in nm.lower()):
        chosen = nm
        chosen_i = i
        break

  # choose insertion point
  if chosen_i is not None:
    insert_at = chosen_i + 1
  else:
    # insert after function opening brace
    func_start = None
    for i,l in enumerate(lines[:200]):
      if ("TelaCreasCasos" in l) and ("function" in l):
        func_start = i
        break
    if func_start is None:
      func_start = 0
    brace_i = None
    for i in range(func_start, min(func_start+120, len(lines))):
      if "{" in lines[i]:
        brace_i = i
        break
    insert_at = (brace_i + 1) if brace_i is not None else 1

  # build block
  if chosen:
    block = (
      "  // FIX: garante timelineUI definido antes de usar (evita ReferenceError)\n"
      "  const timelineUI = (() => {\n"
      f"    const base = {chosen};\n"
      "    const t = base && (base.timelineUI || base.timeline_ui || base.timeline);\n"
      "    return Array.isArray(t) ? t : [];\n"
      "  })();\n"
    )
  else:
    block = (
      "  // FIX: garante timelineUI definido antes de usar (evita ReferenceError)\n"
      "  const timelineUI = [];\n"
    )

  lines.insert(insert_at, block)

  bak = backup_file(fp)
  fp.write_text("".join(lines), encoding="utf-8")

  print("OK: timelineUI corrigido.")
  print("Arquivo:", fp)
  print("Backup:", bak)

if __name__ == "__main__":
  main()
