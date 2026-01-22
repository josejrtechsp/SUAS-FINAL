#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import re
import sys
from datetime import datetime

def _tag() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def patch_file(p: Path) -> bool:
    s0 = p.read_text(encoding="utf-8")
    s = s0

    needle = "const [suasUI, setSuasUI] = useState({"
    i = s.find(needle)
    if i < 0:
        return False

    j = s.find("async function loadEtapas", i)
    if j < 0:
        return False

    between = s[i:j]
    # já existe fechamento `});` antes do async?
    if re.search(r"\n\s*\}\);\s*\n", between):
        return False

    # insere fechamento do useState antes do async function
    s = s[:j] + "\n  });\n\n" + s[j:]

    bak = p.with_suffix(p.suffix + f".bak_{_tag()}")
    bak.write_text(s0, encoding="utf-8")
    p.write_text(s, encoding="utf-8")
    return True

def main() -> int:
    root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(".").resolve()
    target = root / "frontend/src/TelaCrasCasos.jsx"
    if not target.exists():
        print("ERRO: não achei", target)
        return 2
    changed = patch_file(target)
    print("OK: fix_suasui_closure changed=" + str(changed))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
