#!/usr/bin/env python3
import re
import sys
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
TS = datetime.now().strftime("%Y%m%d%H%M%S")
FILE = ROOT / "frontend/index.html"

SNIPPET_V2 = '''  <!-- GLOBAL_TIMELINE_GUARD_V2: evita ReferenceError (timelineUI/timelineUIMemo) -->\n  <script>\n    window.timelineUI = window.timelineUI || [];\n    window.timelineUIMemo = window.timelineUIMemo || [];\n    // bindings globais acessíveis por identificador\n    var timelineUI = window.timelineUI;\n    var timelineUIMemo = window.timelineUIMemo;\n  </script>\n'''

def backup(p: Path):
    bak = p.with_name(p.name + f".bak_global_timeline_guard_v2_{TS}")
    bak.write_text(p.read_text(encoding="utf-8", errors="ignore"), encoding="utf-8")
    return bak

def main():
    if not FILE.exists():
        print("ERRO: arquivo não encontrado:", FILE)
        sys.exit(1)

    s = FILE.read_text(encoding="utf-8", errors="ignore")

    # se já tem V2, no-op
    if "GLOBAL_TIMELINE_GUARD_V2" in s:
        print("NO-OP: guard V2 já existe em", FILE.relative_to(ROOT))
        return

    # se tem V1, remover o bloco V1 inteiro
    s2 = s
    s2 = re.sub(
        r"\s*<!--\s*GLOBAL_TIMELINE_GUARD_V1.*?-->\s*\n\s*<script>.*?</script>\s*\n",
        "\n",
        s2,
        flags=re.S
    )

    # inserir V2 antes de </head>
    m = re.search(r"</head\s*>", s2, flags=re.I)
    if not m:
        print("ERRO: não encontrei </head> em", FILE)
        sys.exit(1)

    s2 = s2[:m.start()] + SNIPPET_V2 + s2[m.start():]

    backup(FILE)
    FILE.write_text(s2, encoding="utf-8")
    print("OK: patched", FILE.relative_to(ROOT))

if __name__ == "__main__":
    main()
