#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import re
import sys
from datetime import datetime

MARKER = "// FIX: garantir linhaMetroUI definido (evita crash geral do ErrorBoundary)"

INSERT = r"""
  // FIX: garantir linhaMetroUI definido (evita crash geral do ErrorBoundary)
  const linhaMetroUI = useMemo(() => {
    try {
      if (typeof linhaMetro !== "undefined" && Array.isArray(linhaMetro)) return linhaMetro;
    } catch {}
    try {
      if (typeof linhaMetroBase !== "undefined" && Array.isArray(linhaMetroBase)) return linhaMetroBase;
    } catch {}
    try {
      if (typeof linhaMetroView !== "undefined" && Array.isArray(linhaMetroView)) return linhaMetroView;
    } catch {}
    try {
      if (typeof linhaMetroUI2 !== "undefined" && Array.isArray(linhaMetroUI2)) return linhaMetroUI2;
    } catch {}
    return [];
  }, [sel?.id, suasUI?.stats?.total]); // deps leves
"""

def _tag() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def patch_file(p: Path) -> bool:
    s0 = p.read_text(encoding="utf-8")
    s = s0

    # se não usa linhaMetroUI, não mexe
    if "linhaMetroUI" not in s:
        return False

    # se já existe definição, não mexe
    if re.search(r"\bconst\s+linhaMetroUI\s*=\s*useMemo\(", s):
        return False

    # remove inserção antiga (se houver)
    if MARKER in s:
        s = re.sub(r"\n\s*// FIX: garantir linhaMetroUI definido.*?\n\s*\},\s*\[[^\]]*\]\s*\);\s*\n", "\n", s, flags=re.S, count=1)

    # inserir imediatamente antes do return(
    m = re.search(r"\n\s*return\s*\(\s*\n", s)
    if not m:
        m = re.search(r"\n\s*return\s*\(", s)
    if not m:
        raise RuntimeError("Não encontrei `return (` para inserir linhaMetroUI.")

    ins = m.start()
    s = s[:ins] + INSERT + s[ins:]

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
    print("OK: fix_linhaMetroUI changed=" + str(changed))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
