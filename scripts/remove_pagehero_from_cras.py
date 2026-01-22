import re
from pathlib import Path
from datetime import datetime

ROOT = Path.cwd()
ts = datetime.now().strftime("%Y%m%d_%H%M%S")

targets = sorted((ROOT / "frontend/src").glob("TelaCras*.jsx"))
if not targets:
    raise SystemExit("ERRO: não encontrei arquivos TelaCras*.jsx em frontend/src")

def backup(p: Path):
    b = p.with_suffix(p.suffix + f".bak_{ts}")
    b.write_text(p.read_text(encoding="utf-8"), encoding="utf-8")
    return b

def strip_pagehero(text: str):
    # remove import PageHero (qualquer variação de caminho)
    text2 = re.sub(r"^.*\bPageHero\b.*\n", "", text, flags=re.M)

    # remove <PageHero ... />
    text2 = re.sub(r"\n\s*<PageHero\b[\s\S]*?\/>\s*\n", "\n", text2)

    # remove <PageHero ...> ... </PageHero>
    text2 = re.sub(r"\n\s*<PageHero\b[\s\S]*?>[\s\S]*?<\/PageHero>\s*\n", "\n", text2)

    # limpa excesso de linhas vazias
    text2 = re.sub(r"\n{3,}", "\n\n", text2)

    return text2

changed = []
for p in targets:
    txt = p.read_text(encoding="utf-8")
    if "PageHero" not in txt:
        continue
    new = strip_pagehero(txt)
    if new != txt:
        backup(p)
        p.write_text(new, encoding="utf-8")
        changed.append(p.name)

print("OK. PageHero removido das telas CRAS.")
print("Arquivos alterados:", len(changed))
for name in changed:
    print(" -", name)
