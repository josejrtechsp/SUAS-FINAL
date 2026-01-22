#!/usr/bin/env python3
import re
from pathlib import Path

p = Path("frontend/src/App.css")
if not p.exists():
    raise SystemExit("ERRO: frontend/src/App.css não encontrado.")

css = p.read_text(encoding="utf-8")

marker = "/* PATCH_MODAL_OVERLAY_FIXED */"
block = marker + r"""
.modal-backdrop,
.modal-overlay,
.modal{
  position: fixed !important;
  inset: 0 !important;
}
"""

if marker in css:
    print("OK: bloco PATCH_MODAL_OVERLAY_FIXED já existe.")
else:
    # Se houver definição antiga com position: static, tenta corrigir
    css2 = re.sub(r'(\.modal-(?:backdrop|overlay)\s*\{[^}]*?)position\s*:\s*static\s*;([^}]*\})',
                  r'\1position: fixed;\2', css, flags=re.I|re.S)
    if css2 != css:
        css = css2
        print("OK: position: static -> fixed em modal-backdrop/modal-overlay.")
    # Garante um overlay fixo no final (não conflita com o resto)
    css = css.rstrip() + "\n\n" + block + "\n"
    p.write_text(css, encoding="utf-8")
    print("OK: bloco PATCH_MODAL_OVERLAY_FIXED adicionado ao App.css.")
