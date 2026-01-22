#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pathlib import Path
from datetime import datetime
import re

ROOT = Path.home() / "POPNEWS1"
SRC = ROOT / "frontend/src"

CRASAPP = SRC / "CrasApp.jsx"
ENC = SRC / "TelaCrasEncaminhamentos.jsx"
SCFV = SRC / "TelaCrasScfv.jsx"

def stamp(): return datetime.now().strftime("%Y%m%d_%H%M%S")

def backup(p: Path):
    b = p.with_suffix(p.suffix + ".bak_" + stamp())
    b.write_text(p.read_text(encoding="utf-8", errors="ignore"), encoding="utf-8")
    return b

def replace_chips_for_title(txt: str, title: str, newchips: str):
    pos = txt.find(f'title: "{title}"')
    if pos == -1:
        return txt, False
    chips_pos = txt.find("chips:", pos)
    if chips_pos == -1:
        return txt, False
    lb = txt.find("[", chips_pos)
    if lb == -1:
        return txt, False
    depth = 0
    rb = -1
    for i in range(lb, len(txt)):
        if txt[i] == "[":
            depth += 1
        elif txt[i] == "]":
            depth -= 1
            if depth == 0:
                rb = i
                break
    if rb == -1:
        return txt, False
    return txt[:lb] + newchips + txt[rb+1:], True

def patch_crasapp():
    if not CRASAPP.exists():
        print("WARN: CrasApp.jsx não encontrado.")
        return
    txt = CRASAPP.read_text(encoding="utf-8", errors="ignore")
    if "CRAS_HEADER_SUBTABS_V1" in txt:
        print("OK: CrasApp já tem CRAS_HEADER_SUBTABS_V1.")
        return
    b = backup(CRASAPP)
    changed = False

    def setchips(title, arr):
        nonlocal txt, changed
        txt2, ok = replace_chips_for_title(txt, title, arr)
        if ok:
            txt = txt2
            changed = True
            print(f"OK: chips padronizados para '{title}'")
        else:
            print(f"WARN: não consegui ajustar chips para '{title}'")

    setchips("Encaminhamentos", '["Filtros","Novo","Sem devolutiva","Encaminhamento SUAS","Todos"]')
    setchips("Tarefas", '["Por técnico","Vencidas","Metas","Concluir em lote"]')
    setchips("CadÚnico", '["Status e histórico","Reagendamento","Pendências por prazo","Visão por unidade"]')
    setchips("SCFV", '["Chamada","Turmas","Alertas","Exportação"]')

    if changed:
        txt += "\n// CRAS_HEADER_SUBTABS_V1\n"
        CRASAPP.write_text(txt, encoding="utf-8")
        print("✅ CrasApp.jsx atualizado. Backup:", b)
    else:
        print("WARN: Nenhuma alteração feita em CrasApp.jsx. Backup:", b)

def remove_internal_bar(path: Path, labels):
    if not path.exists():
        return
    txt = path.read_text(encoding="utf-8", errors="ignore")
    if "REMOVIDO_HEADER_PADRAO_V1" in txt:
        print("OK:", path.name, "já limpo.")
        return
    b = backup(path)
    # remove um <div> que contenha os labels (na ordem) — isso elimina a barra duplicada
    pat = r"<div[^>]*>\s*(?:.|\n)*?" + r"(?:.|\n)*?".join(labels) + r"(?:.|\n)*?</div>"
    m = re.search(pat, txt, flags=re.I)
    if m:
        txt2 = txt[:m.start()] + "{/* REMOVIDO_HEADER_PADRAO_V1 */}\n" + txt[m.end():]
        path.write_text(txt2, encoding="utf-8")
        print("✅ Barra interna removida em", path.name, "| Backup:", b)
    else:
        print("WARN: Não achei barra interna em", path.name, "| Backup:", b)

def main():
    patch_crasapp()
    # Encaminhamentos: remove a barra duplicada (Filtros/Novo/Sem devolutiva) no conteúdo
    remove_internal_bar(ENC, ["Filtros", "Novo", "Sem devolutiva"])
    # SCFV: remove a barra interna antiga (Turmas/Frequência/Alertas/Exportação) no conteúdo
    remove_internal_bar(SCFV, ["Turmas", "Frequ", "Alertas", "Exporta"])
    print("✅ Concluído. Reinicie o Vite e dê Cmd+Shift+R.")

if __name__ == "__main__":
    main()
