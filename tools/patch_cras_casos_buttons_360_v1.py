#!/usr/bin/env python3
"""
tools/patch_cras_casos_buttons_360_v1.py

Adiciona botões "Pessoa 360" e "Família 360" no detalhe do caso (CRAS > Casos),
e garante que TelaCrasCasos receba onNavigate do CrasApp.

- Modifica frontend/src/CrasApp.jsx: passa onNavigate para <TelaCrasCasos ...>
- Modifica frontend/src/TelaCrasCasos.jsx:
  - aceita prop onNavigate
  - cria handlers openPessoa360/openFamilia360 (seta localStorage cras_ficha_* e navega para tab "ficha")
  - insere botões no header do detalhe do caso (logo abaixo da linha de Status)

Idempotente e cria .bak_<timestamp>.
"""
from __future__ import annotations

from pathlib import Path
from datetime import datetime
import re
import sys

def tag():
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def backup(path: Path, original: str):
    path.with_suffix(path.suffix + f".bak_{tag()}").write_text(original, encoding="utf-8")

def patch_cras_app(root: Path) -> bool:
    path = root / "frontend/src/CrasApp.jsx"
    if not path.exists():
        return False
    s0 = path.read_text(encoding="utf-8")
    s = s0

    # localizar bloco do case "casos" e o componente TelaCrasCasos dentro
    i = s.find('case "casos":')
    if i < 0:
        return False
    j = s.find('case "', i + 1)
    block = s[i:j] if j > i else s[i:]

    # já tem onNavigate?
    if "onNavigate={onNavigate}" in block:
        return False

    # inserir onNavigate dentro da tag TelaCrasCasos
    m = re.search(r"(<TelaCrasCasos\b[^>]*)(\/>)", block)
    if not m:
        return False

    tag_open = m.group(1)
    if "onNavigate=" in tag_open:
        return False

    tag_open2 = tag_open.rstrip() + " onNavigate={onNavigate} "
    block2 = block[:m.start(1)] + tag_open2 + block[m.end(1):]
    s2 = s[:i] + block2 + s[i+len(block):]

    if s2 != s0:
        backup(path, s0)
        path.write_text(s2, encoding="utf-8")
        return True
    return False

def ensure_onNavigate_prop(s: str) -> str:
    # adiciona onNavigate na lista de props do componente, se ainda não existir
    m = re.search(r"export\s+default\s+function\s+TelaCrasCasos\s*\(\s*\{\s*([^}]*)\}\s*\)", s, re.S)
    if not m:
        return s
    props = m.group(1)
    if "onNavigate" in props:
        return s
    new_props = props.strip()
    if new_props and not new_props.endswith(","):
        new_props += ","
    new_props += " onNavigate"
    return s[:m.start(1)] + new_props + s[m.end(1):]

def patch_tela_casos(root: Path) -> bool:
    path = root / "frontend/src/TelaCrasCasos.jsx"
    if not path.exists():
        return False
    s0 = path.read_text(encoding="utf-8")
    s = s0

    # 1) prop
    s = ensure_onNavigate_prop(s)

    # 2) inserir handlers antes do return(
    if "function openPessoa360()" not in s:
        mr = re.search(r"\n\s*return\s*\(\s*\n", s) or re.search(r"\n\s*return\s*\(", s)
        if not mr:
            return False

        handlers = r"""
  // Abrir Ficha 360 diretamente a partir do caso
  function openPessoa360() {
    const pid = sel?.pessoa_id != null ? Number(sel.pessoa_id) : null;
    if (!pid) return;
    try { localStorage.setItem("cras_ficha_pessoa_id", String(pid)); } catch {}
    try { localStorage.setItem("cras_active_tab", "ficha"); } catch {}
    if (typeof onNavigate === "function") onNavigate("ficha");
  }

  function openFamilia360() {
    const fid = sel?.familia_id != null ? Number(sel.familia_id) : null;
    if (!fid) return;
    try { localStorage.setItem("cras_ficha_familia_id", String(fid)); } catch {}
    try { localStorage.setItem("cras_active_tab", "ficha"); } catch {}
    if (typeof onNavigate === "function") onNavigate("ficha");
  }
"""
        s = s[:mr.start()] + handlers + s[mr.start():]

    # 3) inserir botões no header do detalhe (logo após a linha "Status: ...")
    if "Pessoa 360" not in s:
        # tenta achar o fim da linha de status (div texto-suave) e inserir logo após
        patt = r'(<div\s+className="texto-suave">Status:\s*<strong>\{sel\.status\}</strong>\s*·\s*Tipo:\s*<strong>\{sel\.tipo_caso\}</strong></div>)'
        m = re.search(patt, s)
        if m:
            buttons = r"""
                  <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginTop: 8 }}>
                    <button className="btn btn-secundario" type="button" disabled={!sel?.pessoa_id} onClick={openPessoa360}>
                      Pessoa 360
                    </button>
                    <button className="btn btn-secundario" type="button" disabled={!sel?.familia_id} onClick={openFamilia360}>
                      Família 360
                    </button>
                  </div>
"""
            s = s[:m.end()] + buttons + s[m.end():]
        else:
            # fallback: insere após a linha que contém "Status: <strong>{sel.status}</strong>"
            anchor = "Status: <strong>{sel.status}</strong>"
            k = s.find(anchor)
            if k > 0 and "Pessoa 360" not in s[k:k+800]:
                # encontrar fechamento do </div> dessa linha
                end = s.find("</div>", k)
                if end > 0:
                    end2 = end + len("</div>")
                    buttons = r"""
                  <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginTop: 8 }}>
                    <button className="btn btn-secundario" type="button" disabled={!sel?.pessoa_id} onClick={openPessoa360}>
                      Pessoa 360
                    </button>
                    <button className="btn btn-secundario" type="button" disabled={!sel?.familia_id} onClick={openFamilia360}>
                      Família 360
                    </button>
                  </div>
"""
                    s = s[:end2] + buttons + s[end2:]

    if s != s0:
        backup(path, s0)
        path.write_text(s, encoding="utf-8")
        return True
    return False

def main() -> int:
    root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(".").resolve()
    changed = {
        "CrasApp.jsx": patch_cras_app(root),
        "TelaCrasCasos.jsx": patch_tela_casos(root),
    }
    print("OK:", changed)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
