#!/usr/bin/env python3
import re
import sys
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
TS = datetime.now().strftime("%Y%m%d%H%M%S")

CREAS = ROOT / "frontend/src/TelaCreasCasos.jsx"
CRAS  = ROOT / "frontend/src/TelaCrasCasos.jsx"

def backup(path: Path) -> Path:
    bak = path.with_name(path.name + f".bak_pre_patch2_{TS}")
    bak.write_text(path.read_text(encoding="utf-8", errors="ignore"), encoding="utf-8")
    return bak

def patch_creas():
    s = CREAS.read_text(encoding="utf-8", errors="ignore")
    orig = s

    # remove dependência circular robustamente
    s = re.sub(r"\[\s*sel\s*,\s*timelineUI\s*\]", "[sel]", s)

    # normaliza variações comuns em final de chamada
    s = re.sub(r"\}\s*,\s*\[\s*sel\s*\]\s*\)\s*;",
               "}, [sel]);", s)

    if s != orig:
        backup(CREAS)
        CREAS.write_text(s, encoding="utf-8")
        print(f"OK: patched {CREAS.relative_to(ROOT)}")
    else:
        print(f"NO-OP: {CREAS.relative_to(ROOT)} (nenhuma alteração necessária)")

def ensure_helper_in_cras(s: str) -> str:
    if "_normalizeLinhaMetro" in s:
        return s

    helper = '''
// PATCH_CRAS_FRONT_STABILIZATION_V1/V2: normalizador defensivo (evita crash do componente de linha do metrô)
const _normalizeLinhaMetro = (lm) => {
  try {
    if (!lm) return null;
    if (Array.isArray(lm)) return lm.length ? { etapas: lm } : null;

    if (typeof lm === "object") {
      if (Array.isArray(lm.etapas)) return lm;
      if (Array.isArray(lm.steps)) return { ...lm, etapas: lm.steps };
      if (Array.isArray(lm.stages)) return { ...lm, etapas: lm.stages };
      for (const k of Object.keys(lm)) {
        if (Array.isArray(lm[k])) return { ...lm, etapas: lm[k] };
      }
      return lm;
    }
    return null;
  } catch (e) {
    return null;
  }
};
'''
    patterns = [
        r"\n\s*export\s+default\s+function\s+",
        r"\n\s*function\s+TelaCrasCasos\s*\(",
        r"\n\s*const\s+TelaCrasCasos\s*=\s*",
    ]
    for p in patterns:
        m = re.search(p, s)
        if m:
            idx = m.start()
            return s[:idx] + "\n" + helper + s[idx:]

    last = None
    for m in re.finditer(r"^\s*import\s+.*?;\s*$", s, flags=re.M):
        last = m
    if last:
        return s[:last.end()] + "\n" + helper + s[last.end():]

    return helper.lstrip("\n") + s

def patch_cras():
    s = CRAS.read_text(encoding="utf-8", errors="ignore")
    orig = s

    s = re.sub(r"\bhistoricoUI\.map\s*\(", r"(historicoUI || []).map(", s)
    s = re.sub(r"!\s*historicoUI\.length\b", r"!(historicoUI || []).length", s)
    s = re.sub(r"linhaMetro\s*=\s*\{\s*linhaMetroUI\s*\}", r"linhaMetro={_normalizeLinhaMetro(linhaMetroUI)}", s)
    s = ensure_helper_in_cras(s)

    if s != orig:
        backup(CRAS)
        CRAS.write_text(s, encoding="utf-8")
        print(f"OK: patched {CRAS.relative_to(ROOT)}")
    else:
        print(f"NO-OP: {CRAS.relative_to(ROOT)} (nenhuma alteração necessária)")

def main():
    if not CREAS.exists() or not CRAS.exists():
        print("ERRO: arquivos não encontrados:")
        print(" -", CREAS)
        print(" -", CRAS)
        sys.exit(1)

    patch_creas()
    patch_cras()

if __name__ == "__main__":
    main()
