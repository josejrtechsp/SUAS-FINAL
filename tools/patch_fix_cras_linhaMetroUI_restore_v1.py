#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import re, sys
from datetime import datetime

def _tag(): return datetime.now().strftime("%Y%m%d_%H%M%S")

NEW_BLOCK = r"""
  // FIX: linhaMetroUI deve ser OBJETO (com etapas) — e mesclar registros SUAS na etapa atual
  const linhaMetroUI = useMemo(() => {
    try {
      if (!linhaMetro) return null;

      const extraRegs = Array.isArray(suasUI?.metroRegistros) ? suasUI.metroRegistros : [];
      if (!extraRegs.length) return linhaMetro;

      const etapasArr = Array.isArray(linhaMetro?.etapas) ? linhaMetro.etapas : [];
      if (!etapasArr.length) return linhaMetro;

      const prefer = String(sel?.etapa_atual || "");
      let idx = etapasArr.findIndex((e) => String(e?.codigo || "") === prefer);
      if (idx < 0) idx = 0;

      const sorted = [...extraRegs].sort((a, b) => {
        const ta = a?.data_hora ? new Date(a.data_hora).getTime() : 0;
        const tb = b?.data_hora ? new Date(b.data_hora).getTime() : 0;
        return tb - ta;
      });

      const merged = { ...linhaMetro };
      merged.etapas = etapasArr.map((e, i) => {
        if (i !== idx) return e;
        const regs = Array.isArray(e?.registros) ? e.registros : [];
        return { ...e, registros: [...sorted, ...regs] };
      });
      return merged;
    } catch (e) {
      console.error(e);
      return linhaMetro || null;
    }
  }, [linhaMetro, sel?.etapa_atual, suasUI?.stats?.total]);
"""

def patch_file(p: Path) -> bool:
    s0 = p.read_text(encoding="utf-8")
    s = s0

    # substitui qualquer definição existente de linhaMetroUI = useMemo(...)
    m = re.search(r"\n\s*const\s+linhaMetroUI\s*=\s*useMemo\([\s\S]*?\n\s*\}\s*,\s*\[[\s\S]*?\]\s*\);\s*\n", s)
    if m:
        s = s[:m.start()] + NEW_BLOCK + s[m.end():]
    else:
        # se não existir, insere antes do return(
        mr = re.search(r"\n\s*return\s*\(\s*\n", s) or re.search(r"\n\s*return\s*\(", s)
        if not mr:
            raise RuntimeError("Não encontrei `return (` para inserir linhaMetroUI.")
        ins = mr.start()
        s = s[:ins] + NEW_BLOCK + s[ins:]

    if s == s0:
        return False

    bak = p.with_suffix(p.suffix + f".bak_{_tag()}")
    bak.write_text(s0, encoding="utf-8")
    p.write_text(s, encoding="utf-8")
    return True

def main():
    root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(".").resolve()
    target = root / "frontend/src/TelaCrasCasos.jsx"
    if not target.exists():
        print("ERRO: não achei", target)
        return 2
    changed = patch_file(target)
    print("OK: patch_fix_cras_linhaMetroUI_restore_v1 changed=" + str(changed))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
