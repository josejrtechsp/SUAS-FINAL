#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pathlib import Path
from datetime import datetime
import re
import sys

ROOT = Path.home() / "POPNEWS1"
CRASAPP = ROOT / "frontend/src/CrasApp.jsx"
HEADER1 = ROOT / "frontend/src/components/CrasTabContextHeader.jsx"
HEADER2 = ROOT / "frontend/src/components/CrasPageHeader.jsx"
ENC = ROOT / "frontend/src/TelaCrasEncaminhamentos.jsx"
CSS = ROOT / "frontend/src/cras_ui_v2.css"

CSS_APPEND = r'''/* CRAS_ENC_VIEW_MODES_V1 */
.cras-enc-split{ overflow-x: hidden; }
.cras-enc-left, .cras-enc-right{ min-width:0; overflow-x:hidden; }

/* telas únicas: vira 1 coluna e some o painel direito */
.cras-enc-split[data-enc-view="filtros"],
.cras-enc-split[data-enc-view="novo"],
.cras-enc-split[data-enc-view="semdev"]{
  grid-template-columns: 1fr !important;
}
.cras-enc-split[data-enc-view="filtros"] .cras-enc-right,
.cras-enc-split[data-enc-view="novo"]    .cras-enc-right,
.cras-enc-split[data-enc-view="semdev"]  .cras-enc-right{
  display:none !important;
}

/* SUAS e TODOS: mostra direita; esquerda vira apoio (sem novo/semdev) */
.cras-enc-split[data-enc-view="suas"]  .cras-enc-left .enc-panel-novo,
.cras-enc-split[data-enc-view="suas"]  .cras-enc-left .enc-panel-semdev{ display:none !important; }
.cras-enc-split[data-enc-view="todos"] .cras-enc-left .enc-panel-novo,
.cras-enc-split[data-enc-view="todos"] .cras-enc-left .enc-panel-semdev{ display:none !important; }

/* telas únicas: deixa só 1 painel na esquerda */
.cras-enc-split[data-enc-view="filtros"] .cras-enc-left .enc-panel-novo,
.cras-enc-split[data-enc-view="filtros"] .cras-enc-left .enc-panel-semdev{ display:none !important; }

.cras-enc-split[data-enc-view="novo"] .cras-enc-left .enc-panel-filtros,
.cras-enc-split[data-enc-view="novo"] .cras-enc-left .enc-panel-semdev{ display:none !important; }

.cras-enc-split[data-enc-view="semdev"] .cras-enc-left .enc-panel-filtros,
.cras-enc-split[data-enc-view="semdev"] .cras-enc-left .enc-panel-novo{ display:none !important; }

/* Chips do header viram botões de modo (apenas em Encaminhamentos) */
.cras-ui-v2 .chip.is-enc-mode{ cursor:pointer; user-select:none; }
.cras-ui-v2 .chip.is-enc-mode.is-active{
  background: rgba(99,102,241,.14);
  border-color: rgba(99,102,241,.22);
  color: rgba(55,48,163,1);
}
'''

def stamp():
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def backup(p: Path):
    b = p.with_suffix(p.suffix + ".bak_" + stamp())
    b.write_text(p.read_text(encoding="utf-8", errors="ignore"), encoding="utf-8")
    return b

def patch_crasapp():
    if not CRASAPP.exists():
        print("WARN: CrasApp.jsx não encontrado.")
        return
    txt = CRASAPP.read_text(encoding="utf-8", errors="ignore")
    if "ENC_CHIPS_V1" in txt:
        print("OK: CrasApp Encaminhamentos chips já ajustado.")
        return
    b = backup(CRASAPP)
    pos = txt.find('title: "Encaminhamentos"')
    if pos == -1:
        pos = txt.find('title: "Encaminhamento"')
    if pos == -1:
        raise SystemExit("Não achei o tab meta de Encaminhamentos em CrasApp.jsx.")
    chips_pos = txt.find("chips:", pos)
    if chips_pos == -1:
        raise SystemExit("Não achei chips: perto do Encaminhamentos em CrasApp.jsx.")
    lb = txt.find("[", chips_pos)
    depth=0; rb=-1
    for i in range(lb, len(txt)):
        if txt[i]=="[": depth+=1
        elif txt[i]=="]":
            depth-=1
            if depth==0: rb=i; break
    if rb == -1:
        raise SystemExit("Não consegui fechar o array chips do Encaminhamentos.")
    newchips = '["Filtros","Novo","Sem devolutiva","Encaminhamento SUAS","Todos"] /* ENC_CHIPS_V1 */'
    txt = txt[:lb] + newchips + txt[rb+1:]
    CRASAPP.write_text(txt, encoding="utf-8")
    print("OK: CrasApp Encaminhamentos chips atualizado. Backup:", b)

def patch_enc_panels():
    if not ENC.exists():
        print("WARN: TelaCrasEncaminhamentos.jsx não encontrado.")
        return
    txt = ENC.read_text(encoding="utf-8", errors="ignore")
    if "ENC_PANELS_V1" in txt:
        print("OK: Encaminhamentos panels já marcados.")
        return
    b = backup(ENC)
    out = txt

    def mark(title, cls):
        nonlocal out
        tpos = out.find(title)
        if tpos == -1:
            return
        cpos = out.rfind('className="card', 0, tpos)
        if cpos != -1 and 'enc-panel' not in out[cpos:cpos+140]:
            out = out[:cpos] + f'className="enc-panel {cls} card /* ENC_PANELS_V1 */' + out[cpos+len('className="card'):]

    mark("Unidade CRAS", "enc-panel-filtros")
    mark("Novo encaminhamento", "enc-panel-novo")
    mark("Sem devolutiva (atras", "enc-panel-semdev")
    mark("Sem devolutiva", "enc-panel-semdev")

    ENC.write_text(out, encoding="utf-8")
    print("OK: TelaCrasEncaminhamentos panels marcados. Backup:", b)

def ensure_css():
    if not CSS.exists():
        print("WARN: cras_ui_v2.css não encontrado.")
        return
    css = CSS.read_text(encoding="utf-8", errors="ignore")
    if "CRAS_ENC_VIEW_MODES_V1" in css:
        print("OK: CSS já contém modos Encaminhamentos.")
        return
    b = backup(CSS)
    CSS.write_text(css + "\n\n" + CSS_APPEND + "\n", encoding="utf-8")
    print("OK: CSS modos Encaminhamentos adicionado. Backup:", b)

def patch_header(path: Path) -> bool:
    if not path.exists():
        return False
    txt = path.read_text(encoding="utf-8", errors="ignore")
    if "CRAS_ENC_HEADER_MODES_V1" in txt:
        print("OK: Header já tem CRAS_ENC_HEADER_MODES_V1:", path.name)
        return True
    b = backup(path)

    if ("useEffect" not in txt) or ("useState" not in txt):
        m = re.search(r'import\s+React\s*,\s*\{([^}]*)\}\s*from\s*["\']react["\']\s*;', txt)
        if m:
            inner = m.group(1)
            need=[]
            if "useEffect" not in inner: need.append("useEffect")
            if "useState" not in inner: need.append("useState")
            if need:
                new_inner = inner.strip()
                if new_inner: new_inner += ", "
                new_inner += ", ".join(need)
                repl = f'import React, {{{new_inner}}} from "react";'
                txt = txt[:m.start()] + repl + txt[m.end():]
        else:
            txt = 'import { useEffect, useState } from "react";\n' + txt

    inject = r'''
  // CRAS_ENC_HEADER_MODES_V1
  const isEnc = String(title || "").toLowerCase().includes("encaminh");
  const [encView, setEncView] = useState(() => {
    try { return localStorage.getItem("cras_enc_view") || "suas"; } catch(e){ return "suas"; }
  });

  useEffect(() => {
    if (!isEnc) return;
    try { localStorage.setItem("cras_enc_view", encView); } catch(e){}
    const apply = () => {
      const el = document.querySelector(".cras-enc-split");
      if (el) el.setAttribute("data-enc-view", encView);
    };
    apply();
    setTimeout(apply, 0);
    setTimeout(apply, 120);
  }, [encView, isEnc]);

  function chipToEncView(label){
    const t = String(label || "").toLowerCase();
    if (t.includes("filtro")) return "filtros";
    if (t === "novo" || t.includes("novo")) return "novo";
    if (t.includes("sem devol")) return "semdev";
    if (t.includes("suas")) return "suas";
    if (t.includes("todo")) return "todos";
    return "suas";
  }
'''
    mfun = re.search(r'function\s+[A-Za-z0-9_]+\s*\([^)]*\)\s*\{', txt)
    if not mfun:
        raise SystemExit("Não encontrei a função componente no header para injetar hooks.")
    ins = mfun.end()
    txt = txt[:ins] + "\n" + inject + "\n" + txt[ins:]

    span_repl = (
        '<span className={"chip" + (isEnc ? " is-enc-mode" : "") + ((isEnc && chipToEncView(chip)===encView) ? " is-active" : "")}'
        ' onClick={() => { if(isEnc) setEncView(chipToEncView(chip)); }}>'
    )
    txt = txt.replace('<span className="chip">', span_repl, 1)

    path.write_text(txt, encoding="utf-8")
    print("OK: Header chips clicáveis (Encaminhamentos). Backup:", b)
    return True

def main():
    patch_crasapp()
    patch_enc_panels()
    ensure_css()
    if not patch_header(HEADER1):
        patch_header(HEADER2)
    print("✅ OK: Patch aplicado. Reinicie o Vite (Ctrl+C; npm run dev) e dê Cmd+Shift+R.")

if __name__ == "__main__":
    main()
