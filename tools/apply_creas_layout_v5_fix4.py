#!/usr/bin/env python3
import re
import sys
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
TS = datetime.now().strftime("%Y%m%d%H%M%S")
FILE = ROOT / "frontend/src/TelaCreasCasos.jsx"

def backup(p: Path):
    bak = p.with_name(p.name + f".bak_creas_layout_v5_fix4_{TS}")
    bak.write_text(p.read_text(encoding="utf-8", errors="ignore"), encoding="utf-8")
    return bak

def main():
    if not FILE.exists():
        print("ERRO: arquivo não encontrado:", FILE)
        sys.exit(1)

    s = FILE.read_text(encoding="utf-8", errors="ignore")
    orig = s

    # 1) Remove any FIX V5 timeline injected blocks/lines
    # remove injected let timelineUI line (with or without comment)
    s = re.sub(r"^\s*//\s*FIX_CREAS_TIMELINEUI_V5:[^\n]*\n\s*let\s+timelineUI\s*=\s*\[\s*\]\s*;\s*\n", "", s, flags=re.M)
    s = re.sub(r"^\s*let\s+timelineUI\s*=\s*\[\s*\]\s*;\s*\n", "", s, flags=re.M)

    # remove assignment markers inserted after memo
    s = re.sub(r"\n\s*//\s*FIX_CREAS_TIMELINEUI_V5:[^\n]*\n\s*timelineUI\s*=\s*Array\.isArray\(timelineUICalc\)[^\n]*\n", "\n", s)
    s = re.sub(r"^\s*timelineUI\s*=\s*Array\.isArray\(timelineUICalc\)[^\n]*\n", "", s, flags=re.M)

    # 2) Convert timelineUICalc memo var to timelineUI
    s = re.sub(r"\b(const|let|var)\s+timelineUICalc\s*=\s*useMemo\b", r"\1 timelineUI = useMemo", s, count=1)

    # 3) Remove any leftover 'const timelineUI = Array.isArray(timelineUICalc)...' lines (from older attempts)
    s = re.sub(
        r"^\s*const\s+timelineUI\s*=\s*Array\.isArray\(timelineUICalc\)[^\n]*\n",
        "",
        s,
        flags=re.M
    )

    # 4) Remove circular deps if present
    s = re.sub(r"\[\s*sel\s*,\s*timelineUI\s*\]", "[sel]", s)

    # 5) Remove any remaining 'timelineUICalc' occurrences (safe cleanup)
    s = re.sub(r"\btimelineUICalc\b", "timelineUI", s)

    if s != orig:
        backup(FILE)
        FILE.write_text(s, encoding="utf-8")
        print("OK: patched", FILE.relative_to(ROOT))
    else:
        print("NO-OP:", FILE.relative_to(ROOT), "(nenhuma alteração necessária)")

if __name__ == "__main__":
    main()
