#!/usr/bin/env python3
import re
import sys
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
TS = datetime.now().strftime("%Y%m%d%H%M%S")
FILE = ROOT / "frontend/src/TelaCreasCasos.jsx"

def backup(p: Path):
    bak = p.with_name(p.name + f".bak_creas_timeline_fix5_{TS}")
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

def insert_var_inside_component(s: str) -> str:
    # Tenta inserir logo após a abertura do componente
    patterns = [
        r"(export\s+default\s+function\s+\w+\s*\([^)]*\)\s*\{)",
        r"(function\s+TelaCreasCasos\s*\([^)]*\)\s*\{)",
        r"(const\s+TelaCreasCasos\s*=\s*\([^)]*\)\s*=>\s*\{)",
    ]
    for pat in patterns:
        m = re.search(pat, s)
        if m:
            ins = m.end()
            # evita duplicar
            if re.search(r"\bvar\s+timelineUI\b", s[m.start():m.start()+400]):
                return s
            snippet = "\n  // FIX_CREAS_TIMELINEUI_FIX5: var hoisted evita Safari TDZ (Can't find variable)\n  var timelineUI = [];\n"
            return s[:ins] + snippet + s[ins:]
    # fallback: top-level (ainda ajuda para 'Can't find variable' mas preferimos dentro)
    if "var timelineUI" not in s:
        s = insert_after_imports(s, "// FIX_CREAS_TIMELINEUI_FIX5: fallback\nvar timelineUI = [];")
    return s

def convert_memo(s: str) -> str:
    # 1) renomeia 'const timelineUI = useMemo' -> 'const timelineUIMemo = useMemo'
    s2, n = re.subn(r"\bconst\s+timelineUI\s*=\s*useMemo\b", "const timelineUIMemo = useMemo", s, count=1)
    s = s2

    # 2) garante que não haja outro const timelineUI = useMemo (variações)
    s = re.sub(r"\b(let|var)\s+timelineUI\s*=\s*useMemo\b", r"const timelineUIMemo = useMemo", s)

    # 3) insere atribuição após o fechamento do useMemo (primeira ocorrência)
    if "FIX_CREAS_TIMELINEUI_FIX5: assign" in s:
        return s

    m = re.search(r"const\s+timelineUIMemo\s*=\s*useMemo\s*\(", s)
    if not m:
        return s

    tail = s[m.start():]
    endm = re.search(r"\}\s*,\s*\[\s*sel\s*\]\s*\)\s*;\s*", tail)
    if not endm:
        # tenta outra forma: "]);" (sem depender de sel)
        endm = re.search(r"\]\s*\)\s*;\s*", tail)
    if not endm:
        return s

    ins_at = m.start() + endm.end()
    snippet = (
        "\n  // FIX_CREAS_TIMELINEUI_FIX5: assign (defensivo)\n"
        "  // FIX_CREAS_TIMELINEUI_FIX5\n"
        "  timelineUI = Array.isArray(timelineUIMemo) ? timelineUIMemo : [];\n"
    )
    return s[:ins_at] + snippet + s[ins_at:]

def main():
    if not FILE.exists():
        print("ERRO: arquivo não encontrado:", FILE)
        sys.exit(1)

    s = FILE.read_text(encoding="utf-8", errors="ignore")
    orig = s

    s = insert_var_inside_component(s)
    s = convert_memo(s)

    if s != orig:
        backup(FILE)
        FILE.write_text(s, encoding="utf-8")
        print("OK: patched", FILE.relative_to(ROOT))
    else:
        print("NO-OP:", FILE.relative_to(ROOT), "(nenhuma alteração necessária)")

if __name__ == "__main__":
    main()
