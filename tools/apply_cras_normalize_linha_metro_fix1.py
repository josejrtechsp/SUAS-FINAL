#!/usr/bin/env python3
import re
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
TS = datetime.now().strftime("%Y%m%d%H%M%S")

CANDIDATES = [
  ROOT / "frontend/src/TelaCrasCasos.jsx",
  ROOT / "frontend/frontend/src/TelaCrasCasos.jsx",
]

HELPER = '''
// PATCH_CRAS_NORMALIZE_LINHAMETRO_FIX1: normalizador defensivo (evita crash do componente de linha do metrô)
const _normalizeLinhaMetro = (lm) => {
  try {
    if (!lm) return null;
    // Se vier como lista, converte para shape esperado
    if (Array.isArray(lm)) return lm.length ? { etapas: lm } : null;

    if (typeof lm === "object") {
      // padrão esperado
      if (Array.isArray(lm.etapas)) return lm;
      // tolera variações comuns
      if (Array.isArray(lm.steps)) return { ...lm, etapas: lm.steps };
      if (Array.isArray(lm.stages)) return { ...lm, etapas: lm.stages };
      // último recurso: achar primeira propriedade array e tratá-la como etapas
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

def backup(p: Path):
  bak = p.with_name(p.name + f".bak_cras_linha_metro_fix1_{TS}")
  bak.write_text(p.read_text(encoding="utf-8", errors="ignore"), encoding="utf-8")
  return bak

def insert_after_imports(s: str, snippet: str) -> str:
  last = None
  for m in re.finditer(r"^\s*import\s+.*?;\s*$", s, flags=re.M):
    last = m
  if last:
    i = last.end()
    return s[:i] + "\n\n" + snippet + "\n" + s[i:]
  return snippet + "\n" + s

def patch_one(p: Path):
  s = p.read_text(encoding="utf-8", errors="ignore")
  orig = s

  # 1) injeta helper se não existir
  if "_normalizeLinhaMetro" not in s:
    s = insert_after_imports(s, HELPER)

  # 2) tornar uso de linhaMetro 100% seguro
  # troca apenas quando houver o padrão direto
  s = s.replace(
    "linhaMetro={_normalizeLinhaMetro(linhaMetroUI)}",
    'linhaMetro={typeof _normalizeLinhaMetro === "function" ? _normalizeLinhaMetro(linhaMetroUI) : linhaMetroUI}'
  )

  # se houver outras variações com espaços
  s = re.sub(
    r"linhaMetro\s*=\s*\{\s*_normalizeLinhaMetro\(\s*linhaMetroUI\s*\)\s*\}",
    'linhaMetro={typeof _normalizeLinhaMetro === "function" ? _normalizeLinhaMetro(linhaMetroUI) : linhaMetroUI}',
    s
  )

  if s != orig:
    backup(p)
    p.write_text(s, encoding="utf-8")
    print("OK: patched", p.relative_to(ROOT))
  else:
    print("NO-OP:", p.relative_to(ROOT))

def main():
  for p in CANDIDATES:
    if not p.exists():
      print("SKIP:", p.relative_to(ROOT), "(não existe)")
      continue
    patch_one(p)

if __name__ == "__main__":
  main()
