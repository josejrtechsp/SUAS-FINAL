#!/usr/bin/env python3
import os, re, sys, shutil
from pathlib import Path

def find_project_root(start: Path) -> Path:
    cur = start.resolve()
    for _ in range(10):
        if (cur / "frontend" / "src" / "App.jsx").exists():
            return cur
        cur = cur.parent
    raise SystemExit("Não encontrei frontend/src/App.jsx. Rode este script na raiz do projeto (POPNEWS1).")

def backup(path: Path):
    bak = path.with_suffix(path.suffix + ".bak_terceiro_setor")
    if not bak.exists():
        shutil.copy2(path, bak)

def insert_import(app: str) -> str:
    if "TerceiroSetorApp" in app:
        return app
    m = list(re.finditer(r"^import .*?;\s*$", app, flags=re.M))
    line = 'import TerceiroSetorApp from "./TerceiroSetorApp.jsx";'
    if not m:
        return line + "\n" + app
    last = m[-1]
    return app[:last.end()] + "\n" + line + app[last.end():]

def insert_into_switch(app: str) -> str:
    def add_case(block: str) -> str:
        if re.search(r"case\s*['\"]terceiro_setor['\"]", block):
            return block
        if "default" in block:
            return re.sub(r"(default\s*:)", 'case "terceiro_setor":\n        return <TerceiroSetorApp usuarioLogado={usuarioLogado} />;\n\n      \\1', block, count=1)
        return block
    m = re.search(r"(switch\s*\(\s*[A-Za-z0-9_]+\s*\)\s*\{[\s\S]*?\n\})", app)
    if not m:
        return app
    blk = m.group(1)
    blk2 = add_case(blk)
    if blk2 == blk:
        return app
    return app.replace(blk, blk2)

def insert_if_chain(app: str) -> str:
    m = re.search(r"if\s*\(\s*([A-Za-z0-9_]+)\s*===\s*['\"]cras['\"]\s*\)\s*\{?\s*return\s*<CrasApp", app)
    if not m:
        return app
    var = m.group(1)
    insertion = f'if ({var} === "terceiro_setor") {{\n      return <TerceiroSetorApp usuarioLogado={{usuarioLogado}} />;\n    }}\n\n    '
    return re.sub(rf"(if\s*\(\s*{re.escape(var)}\s*===\s*['\"]cras['\"]\s*\)\s*\{{?\s*return\s*<CrasApp)", insertion + r"\1", app, count=1)

def insert_route(app: str) -> str:
    if "<Route" not in app or "CrasApp" not in app:
        return app
    if "TerceiroSetorApp" in app:
        return app
    return re.sub(
        r"(<Route[^>]+path=['\"]/cras['\"][^>]+element=\{\s*<CrasApp[^}]+\}\s*/>\s*)",
        r"\1\n        <Route path=\"/terceiro-setor\" element={<TerceiroSetorApp usuarioLogado={usuarioLogado} />} />\n",
        app,
        count=1,
        flags=re.I
    )

def patch_appjsx(app_path: Path):
    backup(app_path)
    app = app_path.read_text(encoding="utf-8")
    app = insert_import(app)

    # Try strategies
    before = app
    app = insert_into_switch(app)
    if app == before:
        app = insert_if_chain(app)
    if app == before:
        app = insert_route(app)

    if "TerceiroSetorApp" not in app:
        print("⚠️ Não consegui integrar automaticamente no App.jsx. Backup criado. Edite manualmente se quiser.")
        sys.exit(2)

    app_path.write_text(app, encoding="utf-8")

def main():
    proj = find_project_root(Path(os.getcwd()))
    patch_appjsx(proj / "frontend" / "src" / "App.jsx")
    print("✅ Terceiro Setor integrado no App.jsx. Backup criado ao lado do arquivo.")

if __name__ == "__main__":
    main()
