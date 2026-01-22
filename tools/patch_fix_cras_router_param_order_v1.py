#!/usr/bin/env python3
"""
tools/patch_fix_cras_router_param_order_v1.py

Corrige SyntaxError: "parameter without a default follows parameter with a default"
no backend/app/routers/cras.py, reordenando 'payload' para ficar antes de 'municipio_id'
e de outros parâmetros com default no *mesmo* signature do def.

Idempotente e seguro:
- cria backup .bak_<timestamp> antes de salvar
- só mexe no bloco de assinatura (def ... :)
"""
from __future__ import annotations

from pathlib import Path
import re
import sys
from datetime import datetime


def _now_tag() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def _is_def_line(line: str) -> bool:
    return bool(re.match(r"^\s*def\s+\w+\s*\(", line))


def _signature_end(line: str, parens: int) -> bool:
    # termina quando parênteses fecharam e a linha termina com ':'
    return parens == 0 and line.rstrip().endswith(":")


def _paren_delta(line: str) -> int:
    # bom o suficiente para assinaturas padrão
    return line.count("(") - line.count(")")


def _find_param_line_indices(sig_lines: list[str]) -> tuple[int | None, int | None]:
    payload_idx = None
    municipio_idx = None

    # payload sem default (não pode vir depois de defaults)
    payload_re = re.compile(r"^\s*payload\s*:\s*[^=]+,\s*$")

    # municipio_id com default (Query(...) ou = None)
    municipio_re = re.compile(r"^\s*municipio_id\s*:\s*.*=\s*(Query\(|None)\s*.*,\s*$")

    for i, ln in enumerate(sig_lines):
        if payload_idx is None and payload_re.match(ln):
            payload_idx = i
        if municipio_idx is None and municipio_re.match(ln):
            municipio_idx = i

    return payload_idx, municipio_idx


def patch_file(path: Path) -> bool:
    s = path.read_text(encoding="utf-8")
    lines = s.splitlines(keepends=True)

    changed = False
    out = []
    i = 0
    n = len(lines)

    while i < n:
        ln = lines[i]
        if not _is_def_line(ln):
            out.append(ln)
            i += 1
            continue

        # capturar assinatura completa
        start = i
        par = 0
        sig = []
        while i < n:
            sig.append(lines[i])
            par += _paren_delta(lines[i])
            if _signature_end(lines[i], par):
                i += 1
                break
            i += 1

        # analisar assinatura
        payload_idx, municipio_idx = _find_param_line_indices(sig)

        if payload_idx is not None and municipio_idx is not None and payload_idx > municipio_idx:
            # mover payload para antes do municipio_id
            payload_line = sig.pop(payload_idx)
            sig.insert(municipio_idx, payload_line)
            changed = True

        out.extend(sig)

    if changed:
        bak = path.with_suffix(path.suffix + f".bak_{_now_tag()}")
        bak.write_text(s, encoding="utf-8")
        path.write_text("".join(out), encoding="utf-8")

    return changed


def main() -> int:
    root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(".").resolve()
    target = root / "backend/app/routers/cras.py"
    if not target.exists():
        print("ERRO: não achei", target)
        return 2

    changed = patch_file(target)
    print("OK: patch_fix_cras_router_param_order_v1", "changed=" + str(changed))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
