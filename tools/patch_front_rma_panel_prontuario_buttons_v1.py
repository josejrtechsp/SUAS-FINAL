#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
from datetime import datetime
import re, sys

def tag(): return datetime.now().strftime("%Y%m%d_%H%M%S")

def backup(p: Path, s: str):
    p.with_suffix(p.suffix + f".bak_{tag()}").write_text(s, encoding="utf-8")

def ensure_import(s: str, import_line: str) -> str:
    if import_line.strip() in s:
        return s
    last = None
    for m in re.finditer(r"^\s*import .*?$", s, flags=re.M):
        last = m
    if last:
        pos = last.end()
        return s[:pos] + "\n" + import_line + s[pos:]
    return import_line + s

def insert_after_wrapper_open(s: str, jsx_snippet: str):
    patterns = [
        r"\n\s*return\s*\(\s*\n\s*<div[^>]*className=\{?\"layout-1col\"[^>]*\}?>\s*\n",
        r"\n\s*return\s*\(\s*\n\s*<div[^>]*className=\{?\"layout-2col\"[^>]*\}?>\s*\n",
        r"\n\s*return\s*\(\s*\n\s*<div[^>]*>\s*\n",
    ]
    for pat in patterns:
        m = re.search(pat, s)
        if m:
            if jsx_snippet.strip() in s:
                return s, False
            pos = m.end()
            return s[:pos] + jsx_snippet + s[pos:], True
    return s, False

def patch_file(path: Path, import_line: str, snippet: str) -> bool:
    if not path.exists():
        return False
    s0 = path.read_text(encoding="utf-8")
    s = ensure_import(s0, import_line)
    s, _ = insert_after_wrapper_open(s, snippet)
    if s != s0:
        backup(path, s0)
        path.write_text(s, encoding="utf-8")
        return True
    return False

def main():
    root = Path(".").resolve()
    changed = {}
    changed["relatorios"] = patch_file(root / "frontend/src/TelaCrasRelatorios.jsx",
                                      'import RmaQuickPanel from "./RmaQuickPanel.jsx";\n',
                                      '      <RmaQuickPanel apiBase={apiBase} apiFetch={apiFetch} />\n')
    changed["ficha_pessoa"] = patch_file(root / "frontend/src/TelaCrasFichaPessoa360.jsx",
                                        'import ProntuarioQuickExport from "./ProntuarioQuickExport.jsx";\n',
                                        '      <ProntuarioQuickExport apiBase={apiBase} apiFetch={apiFetch} pessoaId={pessoaSel} familiaId={data?.familia?.id || null} />\n')
    changed["ficha_familia"] = patch_file(root / "frontend/src/TelaCrasFichaFamilia360.jsx",
                                         'import ProntuarioQuickExport from "./ProntuarioQuickExport.jsx";\n',
                                         '      <ProntuarioQuickExport apiBase={apiBase} apiFetch={apiFetch} familiaId={famSel} />\n')
    print("OK:", changed)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
