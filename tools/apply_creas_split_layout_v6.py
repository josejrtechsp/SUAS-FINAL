#!/usr/bin/env python3
import re
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
TS = datetime.now().strftime("%Y%m%d%H%M%S")

CANDIDATES = [
  ROOT / "frontend/src/TelaCreasCasos.jsx",
  ROOT / "frontend/frontend/src/TelaCreasCasos.jsx",
]

def backup(p: Path):
  bak = p.with_name(p.name + f".bak_creas_split_v6_{TS}")
  bak.write_text(p.read_text(encoding="utf-8", errors="ignore"), encoding="utf-8")
  return bak

def find_tag(regex, s):
  m = re.search(regex, s)
  return m

def find_matching_div_end(s: str, open_idx: int) -> int:
  # conta <div ...> e </div> a partir de open_idx
  div_open = re.compile(r"<div\b")
  div_close = re.compile(r"</div>")
  i = open_idx
  depth = 0
  while True:
    mo = div_open.search(s, i)
    mc = div_close.search(s, i)
    if not mo and not mc:
      return -1
    # escolhe o próximo token
    if mc and (not mo or mc.start() < mo.start()):
      depth -= 1
      i = mc.end()
      if depth == 0:
        return i
    else:
      depth += 1
      i = mo.end()

def patch_one(p: Path):
  s = p.read_text(encoding="utf-8", errors="ignore")
  orig = s
  if "CREAS_SPLIT_LAYOUT_V6" in s:
    print("NO-OP:", p.relative_to(ROOT), "(já aplicado)")
    return

  # localizar abertura das colunas (JSX)
  m_left = re.search(r'<div\s+className="col-esquerda"\s*>', s)
  m_right = re.search(r'<div\s+className="col-direita"\s*>', s)
  if not m_left or not m_right:
    print("NO-OP:", p.relative_to(ROOT), "(não encontrei col-esquerda/col-direita)")
    return

  left_idx = m_left.start()
  right_idx = m_right.start()

  # achar fechamento da col-direita
  end_right = find_matching_div_end(s, right_idx)
  if end_right < 0:
    print("NO-OP:", p.relative_to(ROOT), "(não consegui fechar col-direita)")
    return

  # ajustar tags de colunas (largura)
  s = re.sub(r'<div\s+className="col-esquerda"\s*>',
             '<div className="col-esquerda" style={{ flex: "0 0 420px", maxWidth: 420 }}>', s, count=1)
  s = re.sub(r'<div\s+className="col-direita"\s*>',
             '<div className="col-direita" style={{ flex: "1 1 auto", minWidth: 0 }}>', s, count=1)

  # re-localizar índices após substituições (comprimento pode mudar antes)
  m_left = re.search(r'<div\s+className="col-esquerda"[^>]*>', s)
  m_right = re.search(r'<div\s+className="col-direita"[^>]*>', s)
  left_idx = m_left.start()
  right_idx = m_right.start()
  end_right = find_matching_div_end(s, right_idx)

  wrapper_open = '{/* CREAS_SPLIT_LAYOUT_V6 */}\n        <div className="creas-split" style={{ display: "flex", gap: 12, alignItems: "flex-start", width: "100%" }}>'
  wrapper_close = "\n        </div>\n"

  s = s[:left_idx] + wrapper_open + "\n" + s[left_idx:end_right] + wrapper_close + s[end_right:]

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
