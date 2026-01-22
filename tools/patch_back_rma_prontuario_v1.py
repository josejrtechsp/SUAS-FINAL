#!/usr/bin/env python3
"""
tools/patch_back_rma_prontuario_v1.py

- Adiciona models:
  - app.models.rma_evento
- Adiciona routers:
  - app.routers.cras_rma (router as cras_rma_router)
  - app.routers.cras_prontuario (router as cras_prontuario_router)

Idempotente: não duplica.
"""
from __future__ import annotations
from pathlib import Path
import re
import sys

def patch_db(db: Path) -> bool:
    s0 = db.read_text(encoding="utf-8")
    s = s0
    if "app.models.rma_evento" in s:
        return False
    # tenta inserir na lista "modules = ["
    m = re.search(r"modules\s*=\s*\[\s*\n", s)
    if not m:
        db.write_text(s + "\n# PATCH_BACK_RMA_PRONTUARIO_V1\n", encoding="utf-8")
        return True
    ins = m.end()
    s = s[:ins] + '        "app.models.rma_evento",\n' + s[ins:]
    db.write_text(s, encoding="utf-8")
    return True

def _add_try_import(main: str, import_stmt: str, marker: str) -> str:
    if marker in main:
        return main
    block = f'\ntry:\n    {import_stmt}  # type: ignore\nexcept Exception:\n    {marker} = None\n'
    # inserir após outros imports de routers, se achar
    m = re.search(r"from app\.routers\.[a-zA-Z0-9_]+\s+import\s+router as [a-zA-Z0-9_]+\n", main)
    if m:
        # inserir após o último import de router (lazy: after first match group end? do at end of all matches)
        last = None
        for mm in re.finditer(r"from app\.routers\.[a-zA-Z0-9_]+\s+import\s+router as [a-zA-Z0-9_]+\n", main):
            last = mm
        if last:
            pos = last.end()
            return main[:pos] + block + main[pos:]
    return block + "\n" + main

def patch_main(main_py: Path) -> bool:
    s0 = main_py.read_text(encoding="utf-8")
    s = s0

    s = _add_try_import(s, "from app.routers.cras_rma import router as cras_rma_router", "cras_rma_router")
    s = _add_try_import(s, "from app.routers.cras_prontuario import router as cras_prontuario_router", "cras_prontuario_router")

    # include_router blocks
    def ensure_include(router_name: str) -> None:
        nonlocal s
        if f"app.include_router({router_name})" in s:
            return
        block = f"\nif {router_name}:\n    app.include_router({router_name})\n"
        # insere após include de cras_router ou ao final
        m = re.search(r"\napp\.include_router\(cras_router\)\n", s)
        if m:
            pos = m.end()
            s = s[:pos] + block + s[pos:]
        else:
            s = s + "\n" + block

    ensure_include("cras_rma_router")
    ensure_include("cras_prontuario_router")

    if s != s0:
        main_py.write_text(s, encoding="utf-8")
        return True
    return False

def main() -> int:
    root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(".").resolve()
    db = root / "backend/app/core/db.py"
    main_py = root / "backend/app/main.py"
    if not db.exists() or not main_py.exists():
        print("ERRO: não encontrei backend/app/core/db.py ou backend/app/main.py")
        return 2
    c1 = patch_db(db)
    c2 = patch_main(main_py)
    print("OK: patch_db=", c1, "patch_main=", c2)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
