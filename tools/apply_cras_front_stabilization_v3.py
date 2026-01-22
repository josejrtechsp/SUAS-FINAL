#!/usr/bin/env python3
import re
import sys
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
TS = datetime.now().strftime("%Y%m%d%H%M%S")

CREAS = ROOT / "frontend/src/TelaCreasCasos.jsx"

def backup(path: Path) -> Path:
    bak = path.with_name(path.name + f".bak_pre_patch3_{TS}")
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

    # 1) remove dependência circular em qualquer lugar
    s = re.sub(r"\[\s*sel\s*,\s*timelineUI\s*\]", "[sel]", s)

    # 2) Se existir declaração timelineUI = useMemo, renomeia para timelineUICalc
    decl_pat = re.compile(r"\b(const|let|var)\s+timelineUI\s*=\s*useMemo\b")
    m = decl_pat.search(s)
    injected = False

    if m:
        s = decl_pat.sub(r"\1 timelineUICalc = useMemo", s, count=1)

        # 3) Inserir timelineUI derivado logo após o primeiro fechamento ');' do useMemo
        m2 = re.search(r"\b(const|let|var)\s+timelineUICalc\s*=\s*useMemo\b", s)
        if m2:
            start = m2.start()
            tail = s[start:]
            endm = re.search(r"\n\s*\)\s*;\s*", tail)
            if endm:
                ins_at = start + endm.end()
                if not re.search(r"\bconst\s+timelineUI\s*=\s*Array\.isArray\(timelineUICalc\)", s):
                    snippet = "\n// PATCH_CRAS_FRONT_STABILIZATION_V3: garante timelineUI sempre definido\nconst timelineUI = Array.isArray(timelineUICalc) ? timelineUICalc : [];\n"
                    s = s[:ins_at] + snippet + s[ins_at:]
                    injected = True

    # 4) Se ainda não houver declaração de timelineUI, injeta um fallback simples após imports
    if not re.search(r"\b(const|let|var)\s+timelineUI\b", s):
        s = insert_after_imports(s, "// PATCH_CRAS_FRONT_STABILIZATION_V3: fallback para evitar ReferenceError\nconst timelineUI = [];")
        injected = True

    if s != orig:
        backup(CREAS)
        CREAS.write_text(s, encoding="utf-8")
        print("OK: patched", CREAS.relative_to(ROOT), "(injected)" if injected else "")
    else:
        print("NO-OP:", CREAS.relative_to(ROOT), "(nenhuma alteração necessária)")

if __name__ == "__main__":
    main()
