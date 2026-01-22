#!/usr/bin/env python3
import re, sys, pathlib, datetime

path = pathlib.Path(sys.argv[1])
s = path.read_text(encoding="utf-8")

# se já existir uma declaração de timelineUI, não mexe
if re.search(r'(?m)^\s*(const|let|var)\s+timelineUI\b', s):
    print("INFO: timelineUI já declarado; nenhuma alteração necessária.")
    sys.exit(0)

# tenta encontrar uma boa âncora para inserir (logo após 'const sel = ...' ou 'const caso = ...')
anchors = [
    r'(?m)^\s*const\s+sel\s*=.*;\s*$',
    r'(?m)^\s*const\s+caso\s*=.*;\s*$',
    r'(?m)^\s*const\s+selected\w*\s*=.*;\s*$',
]

inserted = False
for pat in anchors:
    m = re.search(pat, s)
    if m:
        line_end = m.end()
        insert = "\n  // FIX_TIMELINEUI: garante timelineUI antes do uso (evita ReferenceError)\n" \
                 "  const timelineUI = (sel && (sel.timelineUI || sel.timeline)) ? (sel.timelineUI || sel.timeline) : [];\n"
        # Se a âncora não for 'sel', ajusta para 'caso' ou 'selected...'
        varname = "sel"
        m2 = re.search(r'^\s*const\s+(\w+)\s*=', m.group(0))
        if m2:
            varname = m2.group(1)
        insert = insert.replace("sel && (sel.timelineUI || sel.timeline)", f"{varname} && ({varname}.timelineUI || {varname}.timeline)")
        insert = insert.replace("(sel.timelineUI || sel.timeline)", f"({varname}.timelineUI || {varname}.timeline)")
        s = s[:line_end] + insert + s[line_end:]
        inserted = True
        break

if not inserted:
    # fallback: inserir logo após a assinatura do componente
    # Procura por: function TelaCreasCasos(...){  ou export default function ...
    m = re.search(r'(export\s+default\s+)?function\s+TelaCreasCasos\s*\([^)]*\)\s*\{', s)
    if not m:
        # fallback 2: inserir após "const TelaCreasCasos = (" etc.
        m = re.search(r'(export\s+default\s+)?const\s+TelaCreasCasos\s*=\s*\([^)]*\)\s*=>\s*\{', s)
    if not m:
        print("ERRO: não consegui localizar ponto seguro para inserção.")
        sys.exit(1)
    line_end = m.end()
    insert = "\n  // FIX_TIMELINEUI: garante timelineUI antes do uso (evita ReferenceError)\n" \
             "  const timelineUI = [];\n"
    s = s[:line_end] + insert + s[line_end:]

# salva backup adicional
bak = path.with_suffix(path.suffix + ".bak_restore_insert_" + datetime.datetime.now().strftime("%Y%m%d_%H%M%S"))
bak.write_text(s, encoding="utf-8")  # temp store of modified (for debugging) - but we want original backup? Actually we already restored.
# write to main file
path.write_text(s, encoding="utf-8")
print("OK: timelineUI inserido.")
