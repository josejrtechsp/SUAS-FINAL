#!/usr/bin/env python3
import re
import sys
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
TS = datetime.now().strftime("%Y%m%d%H%M%S")

TARGET_CREAS = ROOT / "frontend/src/TelaCreasCasos.jsx"
TARGET_CRAS  = ROOT / "frontend/src/TelaCrasCasos.jsx"

def backup(path: Path) -> Path:
    bak = path.with_name(path.name + f".bak_pre_patch1_{TS}")
    bak.write_text(path.read_text(encoding="utf-8", errors="ignore"), encoding="utf-8")
    return bak

def patch_creas(path: Path):
    s = path.read_text(encoding="utf-8", errors="ignore")
    orig = s

    # Corrige o caso clássico:
    # const timelineUI = useMemo(..., [sel, timelineUI]);
    # Isso dá erro por "temporal dead zone" (referência antes da inicialização).
    s = re.sub(
        r"\}\s*,\s*\[\s*sel\s*,\s*timelineUI\s*\]\s*\)\s*;",
        r"}, [sel]);",
        s,
        flags=re.M
    )

    if s != orig:
        backup(path)
        path.write_text(s, encoding="utf-8")
        print(f"OK: patched {path.relative_to(ROOT)}")
    else:
        print(f"NO-OP: {path.relative_to(ROOT)} (nenhuma alteração necessária)")

def ensure_helper_in_cras(s: str) -> str:
    if "_normalizeLinhaMetro" in s:
        return s

    helper = '''
// PATCH_CRAS_FRONT_STABILIZATION_V1: normalizador defensivo (evita crash do componente de linha do metrô)
const _normalizeLinhaMetro = (lm) => {
  try {
    if (!lm) return null;
    if (Array.isArray(lm)) return lm.length ? { etapas: lm } : null;

    if (typeof lm === "object") {
      if (Array.isArray(lm.etapas)) return lm;
      if (Array.isArray(lm.steps)) return { ...lm, etapas: lm.steps };
      if (Array.isArray(lm.stages)) return { ...lm, etapas: lm.stages };
      // último recurso: se vier com alguma lista, tenta achar a primeira propriedade array
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
    # Inserir antes do componente principal (padrões comuns)
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

    # fallback: após o último import
    last = None
    for m in re.finditer(r"^\s*import\s+.*?;\s*$", s, flags=re.M):
        last = m
    if last:
        idx = last.end()
        return s[:idx] + "\n" + helper + s[idx:]

    # fallback final
    return helper.lstrip("\n") + s

def patch_cras(path: Path):
    s = path.read_text(encoding="utf-8", errors="ignore")
    orig = s

    # 1) null-safety no histórico
    s = re.sub(r"\bhistoricoUI\.map\s*\(", r"(historicoUI || []).map(", s)
    s = re.sub(r"!\s*historicoUI\.length\b", r"!(historicoUI || []).length", s)

    # 2) normaliza linhaMetroUI antes de passar ao componente (evita crash do componente quando shape varia)
    s = re.sub(r"linhaMetro\s*=\s*\{\s*linhaMetroUI\s*\}", r"linhaMetro={_normalizeLinhaMetro(linhaMetroUI)}", s)

    # 3) injeta helper se necessário
    s = ensure_helper_in_cras(s)

    if s != orig:
        backup(path)
        path.write_text(s, encoding="utf-8")
        print(f"OK: patched {path.relative_to(ROOT)}")
    else:
        print(f"NO-OP: {path.relative_to(ROOT)} (nenhuma alteração necessária)")

def main():
    if not TARGET_CREAS.exists() or not TARGET_CRAS.exists():
        print("ERRO: não encontrei arquivos-alvo esperados:")
        print(" -", TARGET_CREAS)
        print(" -", TARGET_CRAS)
        sys.exit(1)

    patch_creas(TARGET_CREAS)
    patch_cras(TARGET_CRAS)

if __name__ == "__main__":
    main()
