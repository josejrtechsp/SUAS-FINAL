#!/usr/bin/env python3
import sys, re, os, datetime

MARKER = "TIMELINEUI_ANCHOR_V6"

def insert_after_brace(s, start_idx, insert_text):
    # find next '{' after start_idx
    i = s.find("{", start_idx)
    if i == -1:
        return s, False
    # insert after brace + newline
    j = i + 1
    # if immediate newline already, keep; else add newline
    if j < len(s) and s[j] == "\n":
        ins_pos = j + 1
        prefix = ""
    else:
        ins_pos = j
        prefix = "\n"
    return s[:ins_pos] + prefix + insert_text + s[ins_pos:], True

def main(path):
    p = path
    txt = open(p, "r", encoding="utf-8").read()
    if MARKER in txt:
        print("OK: já aplicado.")
        return 0

    # backup
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    bak = p + f".bak_{MARKER.lower()}_{ts}"
    open(bak, "w", encoding="utf-8").write(txt)

    # locate component function start
    # common patterns:
    patterns = [
        r'export\s+default\s+function\s+TelaCreasCasos\s*\(',
        r'function\s+TelaCreasCasos\s*\(',
        r'const\s+TelaCreasCasos\s*=\s*\(',
        r'const\s+TelaCreasCasos\s*=\s*function\s*\(',
    ]
    m = None
    for pat in patterns:
        m = re.search(pat, txt)
        if m:
            break
    if not m:
        print("ERRO: não encontrei a declaração do componente TelaCreasCasos.")
        print("Backup:", bak)
        return 2

    inject_top = (
        f'  // {MARKER}: fallback para evitar ReferenceError em runtime\\n'
        f'  var timelineUI = [];\\n'
    )
    txt, ok = insert_after_brace(txt, m.start(), inject_top)
    if not ok:
        print("ERRO: não consegui inserir após a chave '{'.")
        print("Backup:", bak)
        return 3

    # try to bind after "const sel ="
    msel = re.search(r'(?m)^\\s*const\\s+sel\\s*=.*$', txt)
    if msel:
        # insert after that line
        line_end = txt.find("\\n", msel.end())
        if line_end == -1:
            line_end = len(txt)
        bind = (
            f'\\n  // {MARKER}: vincula timelineUI ao caso selecionado\\n'
            f'  try {{\\n'
            f'    const __src = (sel && (sel.timelineUI || sel.timeline || sel.linha_tempo || sel.historico || sel.historicos)) || [];\\n'
            f'    timelineUI = Array.isArray(__src) ? __src : (__src && Array.isArray(__src.items) ? __src.items : []);\\n'
            f'  }} catch (e) {{ /* ignore */ }}\\n'
        )
        txt = txt[:line_end] + bind + txt[line_end:]

    open(p, "w", encoding="utf-8").write(txt)
    print("OK: aplicado.")
    print("Arquivo:", p)
    print("Backup:", bak)
    return 0

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: fix_timelineui_anchor_v6.py <caminho_para_TelaCreasCasos.jsx>")
        sys.exit(1)
    sys.exit(main(sys.argv[1]))
