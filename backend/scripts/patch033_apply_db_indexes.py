#!/usr/bin/env python3
"""PATCH033 - aplica chamada ensure_indexes() dentro de backend/app/core/db.py (idempotente).

Este script existe apenas para DEV. Para aplicar o patch, prefira o ZIP que já substitui o db.py.
"""
from __future__ import annotations

import re
from pathlib import Path

def main() -> int:
    backend_dir = Path(__file__).resolve().parents[1]  # .../backend
    target = backend_dir / "app" / "core" / "db.py"
    if not target.exists():
        print(f"[ERRO] Não encontrei {target}")
        return 2

    txt = target.read_text(encoding="utf-8")

    # Remover caracteres de controle invisíveis (ex.: \x01) se existirem
    txt = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", txt)

    if "ensure_indexes(engine" in txt or "db_indexes" in txt:
        target.write_text(txt, encoding="utf-8")
        print("[OK] db.py já contém ensure_indexes/db_indexes. (limpeza aplicada)")
        return 0

    pattern = r"(SQLModel\.metadata\.create_all\(engine\)\s*)"
    insert = (
        r"\1\n"
        r"    # PERF: cria índices idempotentes (principalmente SQLite em DEV)\n"
        r"    try:\n"
        r"        from app.core.db_indexes import ensure_indexes\n"
        r"        ensure_indexes(engine, DATABASE_URL)\n"
        r"    except Exception:\n"
        r"        pass\n"
    )

    new_txt, n = re.subn(pattern, insert, txt, count=1)
    if n == 0:
        print("[ERRO] Não encontrei SQLModel.metadata.create_all(engine) no db.py. Não alterei nada.")
        return 1

    target.write_text(new_txt, encoding="utf-8")
    print("[OK] Inserido ensure_indexes() em backend/app/core/db.py")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
