#!/usr/bin/env python3
"""Patcher idempotente para habilitar o router /suas/encaminhamentos.

- Injeta import try/except em backend/app/main.py
- Injeta include_router(...) em backend/app/main.py
- Adiciona model app.models.suas_encaminhamento em backend/app/core/db.py
"""
from __future__ import annotations

from pathlib import Path
import re
import sys


def patch_main(py: Path) -> bool:
    s = py.read_text(encoding="utf-8")
    changed = False

    if "suas_encaminhamentos_router" not in s:
        block = (
            "\ntry:\n"
            "    from app.routers.suas_encaminhamentos import router as suas_encaminhamentos_router  # type: ignore\n"
            "except Exception:\n"
            "    suas_encaminhamentos_router = None\n"
        )
        m = re.search(r"from app\.routers\.cras_encaminhamentos import router as cras_encaminhamentos_router\n", s)
        if m:
            ins = m.end()
            s = s[:ins] + block + s[ins:]
            changed = True
        else:
            m2 = re.search(r"from app\.routers\.cras_relatorios import router as cras_relatorios_router\n", s)
            if m2:
                ins = m2.end()
                s = s[:ins] + block + s[ins:]
                changed = True
            else:
                s = block + "\n" + s
                changed = True

    if "app.include_router(suas_encaminhamentos_router)" not in s:
        block2 = (
            "\nif suas_encaminhamentos_router:\n"
            "    app.include_router(suas_encaminhamentos_router)\n"
        )
        m = re.search(r"\napp\.include_router\(gestao_router\)\n", s)
        if m:
            ins = m.start()
            s = s[:ins] + block2 + s[ins:]
            changed = True
        else:
            s = s + "\n" + block2
            changed = True

    if changed:
        py.write_text(s, encoding="utf-8")
    return changed


def patch_db(py: Path) -> bool:
    s = py.read_text(encoding="utf-8")
    if "app.models.suas_encaminhamento" in s:
        return False

    m = re.search(r"\n\s*\]\n\n\s*for m in modules:", s)
    if not m:
        py.write_text(s + "\n# PATCH_BACK_SUAS_ENCAMINHAMENTOS_V1\n", encoding="utf-8")
        return True

    insert_pos = m.start()
    s2 = s[:insert_pos] + "        \"app.models.suas_encaminhamento\",\n" + s[insert_pos:]
    py.write_text(s2, encoding="utf-8")
    return True


def main() -> int:
    root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(".").resolve()
    p_main = root / "backend/app/main.py"
    p_db = root / "backend/app/core/db.py"

    if not p_main.exists():
        print("ERRO: não achei backend/app/main.py em", root)
        return 2
    if not p_db.exists():
        print("ERRO: não achei backend/app/core/db.py em", root)
        return 2

    c1 = patch_main(p_main)
    c2 = patch_db(p_db)

    print("OK: patch_main=", bool(c1), "patch_db=", bool(c2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
