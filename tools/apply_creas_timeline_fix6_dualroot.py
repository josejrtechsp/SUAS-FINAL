#!/usr/bin/env python3
import re
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
TS = datetime.now().strftime("%Y%m%d%H%M%S")

CANDIDATES = [
    ROOT / "frontend/src/TelaCreasCasos.jsx",
    ROOT / "frontend/frontend/src/TelaCreasCasos.jsx",
]

def backup(p: Path):
    bak = p.with_name(p.name + f".bak_creas_timeline_fix6_{TS}")
    bak.write_text(p.read_text(encoding="utf-8", errors="ignore"), encoding="utf-8")
    return bak

def insert_after_imports(s: str, snippet: str) -> str:
    last = None
    for m in re.finditer(r"^\s*import\s+.*?;\s*$", s, flags=re.M):
        last = m
    if last:
        i = last.end()
        return s[:i] + "\n\n" + snippet + "\n" + s[i:]
    return snippet + "\n" + s

def patch_content(s: str) -> str:
    # remove dependência circular se existir
    s = re.sub(r"\[\s*sel\s*,\s*timelineUI\s*\]", "[sel]", s)

    # garantir var timelineUI (module scope)
    if not re.search(r"\bvar\s+timelineUI\b", s):
        s = insert_after_imports(s, "// FIX_CREAS_TIMELINEUI_FIX6: hoisted var para evitar Safari ReferenceError\nvar timelineUI = [];")

    # converter const timelineUI = useMemo -> const timelineUIMemo = useMemo
    s = re.sub(r"\bconst\s+timelineUI\s*=\s*useMemo\b", "const timelineUIMemo = useMemo", s, count=1)

    # se não houver timelineUIMemo, encerra
    if not re.search(r"\bconst\s+timelineUIMemo\s*=\s*useMemo\b", s):
        return s

    # inserir atribuição defensiva após o fechamento do memo
    if "FIX_CREAS_TIMELINEUI_FIX6: assign" not in s:
        m = re.search(r"const\s+timelineUIMemo\s*=\s*useMemo\s*\(", s)
        if m:
            tail = s[m.start():]
            endm = re.search(r"\}\s*,\s*\[\s*sel\s*\]\s*\)\s*;\s*", tail)
            if not endm:
                endm = re.search(r"\]\s*\)\s*;\s*", tail)
            if endm:
                ins_at = m.start() + endm.end()
                snippet = (
                    "\n// FIX_CREAS_TIMELINEUI_FIX6: assign\n"
                    "timelineUI = Array.isArray(timelineUIMemo) ? timelineUIMemo : [];\n"
                )
                s = s[:ins_at] + snippet + s[ins_at:]
    return s

def main():
    for p in CANDIDATES:
        if not p.exists():
            print("SKIP:", p.relative_to(ROOT), "(não existe)")
            continue
        s = p.read_text(encoding="utf-8", errors="ignore")
        s2 = patch_content(s)
        if s2 != s:
            backup(p)
            p.write_text(s2, encoding="utf-8")
            print("OK: patched", p.relative_to(ROOT))
        else:
            print("NO-OP:", p.relative_to(ROOT))

if __name__ == "__main__":
    main()
