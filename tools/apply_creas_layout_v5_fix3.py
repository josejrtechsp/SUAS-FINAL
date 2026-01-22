#!/usr/bin/env python3
import re
import sys
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
TS = datetime.now().strftime("%Y%m%d%H%M%S")
FILE = ROOT / "frontend/src/TelaCreasCasos.jsx"

def backup(p: Path):
    bak = p.with_name(p.name + f".bak_creas_layout_v5_fix3_{TS}")
    bak.write_text(p.read_text(encoding="utf-8", errors="ignore"), encoding="utf-8")
    return bak

def ensure_list_scroll(s: str) -> str:
    # procura o div do card da lista já marcado
    # Ex.: <div className="card creas-casos-list" style={{ ... }}>
    m = re.search(r'<div\s+className="card\s+creas-casos-list"(\s+style=\{\{.*?\}\})?\s*>', s, flags=re.S)
    if not m:
        return s

    full = m.group(0)

    # se não tiver style, adiciona um style completo
    if "style={{" not in full:
        repl = '<div className="card creas-casos-list" style={{ padding: 12, maxHeight: "calc(100vh - 270px)", overflow: "auto" }}>'
        return s[:m.start()] + repl + s[m.end():]

    # se tiver style, garante maxHeight e overflow dentro do objeto
    style_obj = re.search(r'style=\{\{(.*?)\}\}', full, flags=re.S)
    if not style_obj:
        return s

    inner = style_obj.group(1)

    if 'maxHeight:' not in inner:
        # injeta após padding se existir
        if re.search(r'padding\s*:\s*12', inner):
            inner = re.sub(r'(padding\s*:\s*12\s*,?)', r'\1 maxHeight: "calc(100vh - 270px)",', inner, count=1)
        else:
            inner = 'maxHeight: "calc(100vh - 270px)", ' + inner

    # força o valor exato
    inner = re.sub(r'maxHeight\s*:\s*["\']calc\(100vh\s*-\s*\d+px\)["\']', 'maxHeight: "calc(100vh - 270px)"', inner)

    if 'overflow:' not in inner:
        inner = inner.rstrip() + ' overflow: "auto",'

    # normaliza possíveis duplicatas de overflow
    # mantém o primeiro e remove os demais
    parts = re.split(r'(overflow\s*:\s*["\']auto["\']\s*,?)', inner)
    # recompor mantendo o primeiro match de overflow auto
    if len(parts) > 1:
        # parts alterna texto / match / texto...
        seen = False
        new = []
        for i, p in enumerate(parts):
            if i % 2 == 1:  # match
                if not seen:
                    new.append('overflow: "auto",')
                    seen = True
                else:
                    pass
            else:
                new.append(p)
        inner = ''.join(new)

    new_full = re.sub(r'style=\{\{.*?\}\}', f'style={{{{{inner}}}}}', full, flags=re.S)
    return s[:m.start()] + new_full + s[m.end():]

def main():
    if not FILE.exists():
        print("ERRO: arquivo não encontrado:", FILE)
        sys.exit(1)

    s = FILE.read_text(encoding="utf-8", errors="ignore")
    orig = s
    s = ensure_list_scroll(s)

    if s != orig:
        backup(FILE)
        FILE.write_text(s, encoding="utf-8")
        print("OK: patched", FILE.relative_to(ROOT))
    else:
        print("NO-OP:", FILE.relative_to(ROOT), "(nenhuma alteração necessária)")

if __name__ == "__main__":
    main()
