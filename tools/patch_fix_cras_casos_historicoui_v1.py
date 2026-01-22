#!/usr/bin/env python3
"""
tools/patch_fix_cras_casos_historicoui_v1.py

Corrige erro runtime: "historicoUI is not defined" em frontend/src/TelaCrasCasos.jsx.

Estratégia:
- Se o arquivo usa historicoUI mas não declara `const historicoUI = ...`,
  insere um `const historicoUI = useMemo(...)` robusto, com fallback seguro.
- Idempotente: não duplica se já existir.
- Cria backup .bak_<timestamp>.
"""
from __future__ import annotations

from pathlib import Path
import re
from datetime import datetime
import sys


def _tag() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


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


def patch_file(p: Path) -> bool:
    s0 = p.read_text(encoding="utf-8")

    if "historicoUI" not in s0:
        # nada a fazer
        return False

    if re.search(r"\bconst\s+historicoUI\s*=", s0):
        return False

    # ponto de inserção: antes do primeiro uso em JSX, ou antes de um memo conhecido
    # preferências de âncora
    anchors = [
        r"\n\s*const\s+linhaMetroUI\s*=\s*useMemo\(",
        r"\n\s*const\s+linhaMetroView\s*=\s*useMemo\(",
        r"\n\s*const\s+evidenciasUI\s*=\s*useMemo\(",
        r"\n\s*const\s+evidenciasView\s*=\s*useMemo\(",
    ]

    ins = None
    for a in anchors:
        m = re.search(a, s0)
        if m:
            ins = m.start()
            break

    if ins is None:
        # fallback: insere após declaração do estado suasUI, se existir
        m = re.search(r"\n\s*const\s+\[suasUI,\s*setSuasUI\]\s*=\s*useState\(", s0)
        if m:
            # inserir após o bloco do useState (acha a linha seguinte vazia)
            # simples: inserir logo após a linha do useState
            line_end = s0.find("\n", m.end())
            ins = line_end + 1 if line_end >= 0 else m.end()
        else:
            # último fallback: após "function TelaCrasCasos" abertura
            m2 = re.search(r"export\s+default\s+function\s+TelaCrasCasos\([^\)]*\)\s*\{", s0)
            if not m2:
                raise RuntimeError("Não consegui localizar ponto seguro para inserir historicoUI.")
            ins = m2.end()

    s = s0[:ins] + INSERT_BLOCK + s0[ins:]

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
    print("OK: patch_fix_cras_casos_historicoui_v1 changed=" + str(changed))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
