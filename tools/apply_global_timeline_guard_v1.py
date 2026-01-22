#!/usr/bin/env python3
import re
import sys
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
TS = datetime.now().strftime("%Y%m%d%H%M%S")
FILE = ROOT / "frontend/index.html"

SNIPPET = '''  <!-- GLOBAL_TIMELINE_GUARD_V1: evita "Can't find variable: timelineUI" no Safari -->\n  <script>\n    window.timelineUI = window.timelineUI || [];\n    // cria binding global para acesso por identificador (timelineUI)\n    var timelineUI = window.timelineUI;\n  </script>\n'''

def backup(p: Path):
    bak = p.with_name(p.name + f".bak_global_timeline_guard_v1_{TS}")
    bak.write_text(p.read_text(encoding="utf-8", errors="ignore"), encoding="utf-8")
    return bak

def main():
    if not FILE.exists():
        print("ERRO: arquivo não encontrado:", FILE)
        sys.exit(1)

    s = FILE.read_text(encoding="utf-8", errors="ignore")

    if "GLOBAL_TIMELINE_GUARD_V1" in s:
        print("NO-OP: guard já existe em", FILE.relative_to(ROOT))
        return

    m = re.search(r"</head\s*>", s, flags=re.I)
    if not m:
        print("ERRO: não encontrei </head> em", FILE)
        sys.exit(1)

    s2 = s[:m.start()] + SNIPPET + s[m.start():]

    backup(FILE)
    FILE.write_text(s2, encoding="utf-8")
    print("OK: patched", FILE.relative_to(ROOT))

if __name__ == "__main__":
    main()
