#!/usr/bin/env python3
import re
import sys
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
TS = datetime.now().strftime("%Y%m%d%H%M%S")
CREAS = ROOT / "frontend/src/TelaCreasCasos.jsx"

def backup(path: Path):
    bak = path.with_name(path.name + f".bak_pre_patch4_{TS}")
    bak.write_text(path.read_text(encoding="utf-8", errors="ignore"), encoding="utf-8")
    return bak

def insert_after_imports(s: str, snippet: str) -> str:
    last = None
    for m in re.finditer(r"^\s*import\s+.*?;\s*$", s, flags=re.M):
        last = m
    if last:
        i = last.end()
        return s[:i] + "\n\n" + snippet + "\n" + s[i:]
    return snippet + "\n" + s

def main():
    if not CREAS.exists():
        print("ERRO: arquivo não encontrado:", CREAS)
        sys.exit(1)

    s = CREAS.read_text(encoding="utf-8", errors="ignore")
    orig = s

    # 1) garantir declaração let timelineUI = []; no topo (após imports)
    if not re.search(r"^\s*let\s+timelineUI\s*=\s*\[\s*\]\s*;\s*$", s, flags=re.M):
        s = insert_after_imports(s, "// PATCH_CRAS_FRONT_STABILIZATION_V4: evita TDZ no Safari\nlet timelineUI = [];")

    # 2) trocar derivação const timelineUI por atribuição a let timelineUI
    s = re.sub(
        r"^\s*const\s+timelineUI\s*=\s*Array\.isArray\(timelineUICalc\)\s*\?\s*timelineUICalc\s*:\s*\[\s*\]\s*;\s*$",
        "timelineUI = Array.isArray(timelineUICalc) ? timelineUICalc : [];",
        s,
        flags=re.M
    )

    # 3) se ainda houver qualquer 'const timelineUI =' (variações), converte para assignment
    s = re.sub(r"^\s*const\s+timelineUI\s*=", "timelineUI =", s, flags=re.M)

    if s != orig:
        backup(CREAS)
        CREAS.write_text(s, encoding="utf-8")
        print("OK: patched", CREAS.relative_to(ROOT))
    else:
        print("NO-OP:", CREAS.relative_to(ROOT), "(nenhuma alteração necessária)")

if __name__ == "__main__":
    main()
