#!/usr/bin/env python3
"""
tools/patch_fix_cras_casos_historicoui_v2.py

Corrige build error após patch anterior:
- Remove bloco inserido no lugar errado (marker "FIX: garantir historicoUI definido").
- Reinsere `const historicoUI = useMemo(...)` no lugar seguro: imediatamente ANTES do `return (` do componente.

Idempotente + cria backup .bak_<timestamp>.
"""
from __future__ import annotations

from pathlib import Path
import re
import sys
from datetime import datetime

MARKER_LINE = "// FIX: garantir historicoUI definido (evita crash geral do ErrorBoundary)"

INSERT_BLOCK = r"""
  // FIX: garantir historicoUI definido (evita crash geral do ErrorBoundary)
  const historicoUI = useMemo(() => {
    // tenta usar variáveis existentes, mas sem quebrar se não existirem
    try {
      if (typeof historico !== "undefined" && Array.isArray(historico)) return historico;
    } catch {}
    try {
      if (typeof historicoBase !== "undefined" && Array.isArray(historicoBase)) return historicoBase;
    } catch {}
    try {
      if (typeof tl !== "undefined" && Array.isArray(tl)) return tl;
    } catch {}
    try {
      if (typeof tlBase !== "undefined" && Array.isArray(tlBase)) return tlBase;
    } catch {}
    try {
      if (typeof timelineUI !== "undefined" && Array.isArray(timelineUI)) return timelineUI;
    } catch {}
    return [];
  }, [sel?.id, suasUI?.stats?.total]); // deps leves
"""

def _tag() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def _strip_bad_block(s: str) -> tuple[str, bool]:
    if MARKER_LINE not in s:
        return s, False
    # Remove from marker line up to the end of the useMemo block `]);`
    pattern = re.compile(r"\n\s*// FIX: garantir historicoUI definido.*?\n\s*\},\s*\[[^\]]*\]\s*\);\s*\n", re.S)
    s2, n = pattern.subn("\n", s, count=1)
    if n == 0:
        # fallback: remove from marker to next blank line
        i = s.find(MARKER_LINE)
        if i >= 0:
            j = s.find("\n\n", i)
            if j > i:
                s2 = s[:i] + s[j+2:]
                return s2, True
        return s, False
    return s2, True

def _insert_before_return(s: str) -> tuple[str, bool]:
    if re.search(r"\bconst\s+historicoUI\s*=\s*useMemo\(", s):
        return s, False
    # Find first top-level return( of component
    m = re.search(r"\n\s*return\s*\(\s*\n", s)
    if not m:
        # fallback: any return(
        m = re.search(r"\n\s*return\s*\(", s)
    if not m:
        raise RuntimeError("Não encontrei `return (` em TelaCrasCasos.jsx para inserir historicoUI.")
    ins = m.start()
    s2 = s[:ins] + INSERT_BLOCK + s[ins:]
    return s2, True

def patch_file(p: Path) -> bool:
    s0 = p.read_text(encoding="utf-8")
    s = s0
    changed = False

    s, c1 = _strip_bad_block(s)
    changed = changed or c1

    s, c2 = _insert_before_return(s)
    changed = changed or c2

    if changed:
        bak = p.with_suffix(p.suffix + f".bak_{_tag()}")
        bak.write_text(s0, encoding="utf-8")
        p.write_text(s, encoding="utf-8")
    return changed

def main() -> int:
    root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(".").resolve()
    target = root / "frontend/src/TelaCrasCasos.jsx"
    if not target.exists():
        print("ERRO: não achei", target)
        return 2
    ch = patch_file(target)
    print("OK: patch_fix_cras_casos_historicoui_v2 changed=" + str(ch))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
