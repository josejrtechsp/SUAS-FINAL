#!/usr/bin/env python3
import re
import sys
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
TS = datetime.now().strftime("%Y%m%d%H%M%S")

FILE = ROOT / "frontend/src/TelaCreasCasos.jsx"

def backup(p: Path):
    bak = p.with_name(p.name + f".bak_creas_layout_v5_fix2_{TS}")
    bak.write_text(p.read_text(encoding="utf-8", errors="ignore"), encoding="utf-8")
    return bak

def insert_after_imports(s: str, snippet: str) -> str:
    last = None
    for m in re.finditer(r"^\s*import\s+.*?;\s*$", s, flags=re.M):
        last = m
    if last:
        i = last.end()
        return s[:i] + "\n\n" + snippet + "\n" + s[i:]
    return snippet + "\n" + s

def ensure_css_import(s: str) -> str:
    if "creas_layout_v5.css" in s:
        return s
    return insert_after_imports(s, 'import "./creas_layout_v5.css";')

def remove_bad_inline_patch(s: str) -> str:
    # Remove o bloco indevido inserido dentro de salvarAtendimento (comentário V3 + linha timelineUI)
    s = re.sub(
        r"\n\s*//\s*PATCH_CRAS_FRONT_STABILIZATION_V3:[^\n]*\n\s*timelineUI\s*=\s*Array\.isArray\(timelineUICalc\)[^\n]*\n",
        "\n",
        s
    )
    # Remove também qualquer linha solta igual
    s = re.sub(
        r"^\s*timelineUI\s*=\s*Array\.isArray\(timelineUICalc\)[^\n]*\n",
        "",
        s,
        flags=re.M
    )
    return s

def ensure_timeline_let(s: str) -> str:
    if re.search(r"^\s*let\s+timelineUI\s*=\s*\[\s*\]\s*;\s*$", s, flags=re.M):
        return s
    return insert_after_imports(s, "// FIX_CREAS_TIMELINEUI_V5: evita TDZ no Safari\nlet timelineUI = [];")

def insert_timeline_assignment_after_memo(s: str) -> str:
    marker = "FIX_CREAS_TIMELINEUI_V5: preencher timelineUI"
    if marker in s:
        return s

    m = re.search(r"const\s+timelineUICalc\s*=\s*useMemo\s*\(", s)
    if not m:
        return s

    tail = s[m.start():]
    endm = re.search(r"\}\s*,\s*\[\s*sel\s*\]\s*\)\s*;\s*", tail)
    if not endm:
        return s

    ins_at = m.start() + endm.end()
    snippet = (
        "\n// FIX_CREAS_TIMELINEUI_V5: preencher timelineUI a partir do memo (sem TDZ no Safari)\n"
        "timelineUI = Array.isArray(timelineUICalc) ? timelineUICalc : [];\n"
    )
    return s[:ins_at] + snippet + s[ins_at:]

def apply_layout(s: str) -> str:
    # container principal com classe local
    s = s.replace(
        'className="app-main-inner" style={{ padding: 0 }}',
        'className="app-main-inner creas-casos-layout" style={{ padding: 0 }}'
    )

    # lista esquerda com scroll (apenas a primeira ocorrência do card da lista)
    s = s.replace(
        '<div className="card" style={{ padding: 12 }}>',
        '<div className="card creas-casos-list" style={{ padding: 12, maxHeight: "calc(100vh - 270px)", overflow: "auto" }}>',
        1
    )

    # header do caso (card direito) com classe
    s = s.replace(
        '<div className="card">\n                <div className="card-header-row">',
        '<div className="card creas-case-header">\n                <div className="card-header-row">',
        1
    )

    # título menor
    s = s.replace('fontWeight: 950, fontSize: 18', 'fontWeight: 950, fontSize: 16')

    # troca blocos de meta por badges + faixa último/próximo
    pat = re.compile(
        r'<div className="texto-suave">\s*'
        r'Status <b>\{sel\.status\}</b> · Risco <b>\{sel\.risco\}</b> · Etapa <b>\{sel\.etapa_atual\}</b>'
        r'\s*</div>\s*'
        r'<div className="texto-suave">\s*'
        r'Responsável: <b>\{sel\.responsavel_nome \|\| "Sem responsável"\}</b>'
        r'\s*</div>\s*'
        r'<div className="texto-suave">\s*'
        r'Último registro: <b>\{fmtDateTime\(sel\.ultimo_registro_em\)\}</b> · Próximo passo: <b>\{sel\.proximo_passo \|\| "—"\}</b> \(\{fmtDateTime\(sel\.proximo_passo_em\)\}\)'
        r'\s*</div>',
        re.S
    )

    repl = (
        '<div className="creas-case-meta">\n'
        '  <span className="creas-badge">Status: <b>{sel.status}</b></span>\n'
        '  <span className="creas-badge">Risco: <b>{sel.risco}</b></span>\n'
        '  <span className="creas-badge">Etapa: <b>{sel.etapa_atual}</b></span>\n'
        '  <span className="creas-badge">Resp.: <b>{sel.responsavel_nome || "Sem responsável"}</b></span>\n'
        '</div>\n'
        '<div className="creas-case-next">\n'
        '  <span>Último: <b>{fmtDateTime(sel.ultimo_registro_em)}</b></span>\n'
        '  <span>Próximo: <b>{sel.proximo_passo || "—"}</b> <span className="texto-suave">({fmtDateTime(sel.proximo_passo_em)})</span></span>\n'
        '</div>'
    )

    s = pat.sub(repl, s, count=1)
    return s

def main():
    if not FILE.exists():
        print("ERRO: arquivo não encontrado:", FILE)
        sys.exit(1)

    s = FILE.read_text(encoding="utf-8", errors="ignore")
    orig = s

    s = ensure_css_import(s)
    s = remove_bad_inline_patch(s)
    s = ensure_timeline_let(s)
    s = insert_timeline_assignment_after_memo(s)
    s = apply_layout(s)

    if s != orig:
        backup(FILE)
        FILE.write_text(s, encoding="utf-8")
        print("OK: patched", FILE.relative_to(ROOT))
    else:
        print("NO-OP:", FILE.relative_to(ROOT), "(nenhuma alteração necessária)")

if __name__ == "__main__":
    main()
