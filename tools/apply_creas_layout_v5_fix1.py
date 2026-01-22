#!/usr/bin/env python3
import re
import sys
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
TS = datetime.now().strftime("%Y%m%d%H%M%S")

FILE = ROOT / "frontend/src/TelaCreasCasos.jsx"
CSS  = ROOT / "frontend/src/creas_layout_v5.css"

def backup(p: Path):
    bak = p.with_name(p.name + f".bak_creas_layout_v5_fix1_{TS}")
    bak.write_text(p.read_text(encoding="utf-8", errors="ignore"), encoding="utf-8")
    return bak

def ensure_css_file():
    if CSS.exists():
        return
    CSS.write_text(\"\"\"/* CREAS Layout V5 (local only) */
.creas-casos-layout{ display:flex; gap:12px; align-items:flex-start; }
.creas-casos-layout .col-esquerda{ flex:0 0 360px; max-width:360px; }
.creas-casos-layout .col-direita{ flex:1 1 auto; min-width:0; }

/* Lista mais “densa” */
.creas-casos-layout .creas-casos-list .btn{ padding:8px 10px; border-radius:12px; }
.creas-casos-layout .creas-casos-list .btn .texto-suave{ font-size:12px; }

/* Cabeçalho do caso mais compacto */
.creas-case-header{ padding:12px 14px; }
.creas-case-header .card-header-row{ align-items:flex-start; }
.creas-case-title{ font-weight:950; font-size:16px; line-height:1.2; }
.creas-case-meta{ display:flex; flex-wrap:wrap; gap:8px; margin-top:6px; }
.creas-badge{ border:1px solid rgba(0,0,0,.08); background:rgba(0,0,0,.03); padding:4px 8px; border-radius:999px; font-size:12px; font-weight:800; }
.creas-case-next{ margin-top:6px; display:flex; flex-wrap:wrap; gap:12px; font-size:12px; opacity:.85; }

/* Alerta “sem responsável” mais compacto */
.creas-alert-row{ margin-top:10px; padding:10px 12px; border-radius:12px; border:1px solid rgba(122,92,255,0.22); background:rgba(122,92,255,0.08);
  display:flex; gap:12px; align-items:center; justify-content:space-between; flex-wrap:wrap; }
.creas-alert-row .btn-primario{ padding:10px 14px; font-size:14px; border-radius:12px; font-weight:950; }
\"\"\", encoding="utf-8")

def ensure_css_import(s: str) -> str:
    if "creas_layout_v5.css" in s:
        return s
    # insere após o último import
    imports = list(re.finditer(r"^\\s*import\\s+.*?;\\s*$", s, flags=re.M))
    if imports:
        i = imports[-1].end()
        return s[:i] + "\\nimport \\"./creas_layout_v5.css\\";\\n" + s[i:]
    return 'import "./creas_layout_v5.css";\\n' + s

def remove_bad_patch_lines(s: str) -> str:
    # remove o bloco indevido onde quer que esteja
    s = re.sub(r"\\n\\s*//\\s*PATCH_CRAS_FRONT_STABILIZATION_V3:.*?\\n\\s*(const\\s+timelineUI\\s*=|timelineUI\\s*=).*?\\n", "\\n", s, flags=re.S)
    return s

def fix_timeline_assignment(s: str) -> str:
    # garante timelineUI assignment logo após o fechamento do useMemo do timelineUICalc
    if "FIX_CREAS_TIMELINEUI_V5" in s:
        return s

    m = re.search(r"const\\s+timelineUICalc\\s*=\\s*useMemo\\s*\\(\\s*\\(\\)\\s*=>\\s*\\{", s)
    if not m:
        return s

    start = m.start()
    tail = s[start:]
    # acha o primeiro fechamento do useMemo: "}, [sel]);" (com variações)
    endm = re.search(r"\\}\\s*,\\s*\\[\\s*sel\\s*\\]\\s*\\)\\s*;\\s*", tail)
    if not endm:
        return s

    ins_at = start + endm.end()
    snippet = "\\n// FIX_CREAS_TIMELINEUI_V5: preencher timelineUI a partir do memo (sem TDZ no Safari)\\n" \
              "timelineUI = Array.isArray(timelineUICalc) ? timelineUICalc : [];\\n"
    return s[:ins_at] + snippet + s[ins_at:]

def apply_layout_changes(s: str) -> str:
    # adiciona classe no app-main-inner (mantém style existente)
    s = s.replace('className="app-main-inner" style={{ padding: 0 }}',
                  'className="app-main-inner creas-casos-layout" style={{ padding: 0 }}')

    # marca card de filtros (primeiro card na coluna esquerda)
    s = s.replace('{/* COLUNA ESQUERDA */}\\n        <div className="col-esquerda">\\n          <div className="card">',
                  '{/* COLUNA ESQUERDA */}\\n        <div className="col-esquerda">\\n          <div className="card creas-casos-filtros">')

    # lista esquerda com scroll
    s = s.replace('<div className="card" style={{ padding: 12 }}>',
                  '<div className="card creas-casos-list" style={{ padding: 12, maxHeight: "calc(100vh - 270px)", overflow: "auto" }}>')

    # header card class
    s = s.replace('<div className="card">\\n                <div className="card-header-row">',
                  '<div className="card creas-case-header">\\n                <div className="card-header-row">')

    # título um pouco menor
    s = s.replace('fontSize: 18', 'fontSize: 16')

    # troca bloco de meta (3 linhas) por badges + faixa de próximo passo
    meta_pat = re.compile(
        r'(\\s*<div className="texto-suave">\\s*\\n\\s*Status <b>\\{sel\\.status\\}</b> · Risco <b>\\{sel\\.risco\\}</b> · Etapa <b>\\{sel\\.etapa_atual\\}</b>\\s*\\n\\s*</div>\\s*\\n\\s*<div className="texto-suave">\\s*\\n\\s*Responsável: <b>\\{sel\\.responsavel_nome \\|\\| "Sem responsável"\\}</b>\\s*\\n\\s*</div>\\s*\\n\\s*<div className="texto-suave">\\s*\\n\\s*Último registro: <b>\\{fmtDateTime\\(sel\\.ultimo_registro_em\\)\\}</b> · Próximo passo: <b>\\{sel\\.proximo_passo \\|\\| "—"\\}</b> \\(\\{fmtDateTime\\(sel\\.proximo_passo_em\\)\\}\\)\\s*\\n\\s*</div>)',
        flags=re.S
    )
    replacement = (
        '                  <div className="creas-case-meta">\\n'
        '                    <span className="creas-badge">Status: <b>{sel.status}</b></span>\\n'
        '                    <span className="creas-badge">Risco: <b>{sel.risco}</b></span>\\n'
        '                    <span className="creas-badge">Etapa: <b>{sel.etapa_atual}</b></span>\\n'
        '                    <span className="creas-badge">Resp.: <b>{sel.responsavel_nome || "Sem responsável"}</b></span>\\n'
        '                  </div>\\n'
        '                  <div className="creas-case-next">\\n'
        '                    <span>Último: <b>{fmtDateTime(sel.ultimo_registro_em)}</b></span>\\n'
        '                    <span>Próximo: <b>{sel.proximo_passo || "—"}</b> <span className="texto-suave">({fmtDateTime(sel.proximo_passo_em)})</span></span>\\n'
        '                  </div>'
    )
    s = meta_pat.sub(replacement, s, count=1)

    # semResponsavel: troca style gigante por classe (mantém botão)
    s = re.sub(r'<div\\s*\\n\\s*style=\\{\\{\\s*\\n\\s*marginTop: 10,\\s*\\n\\s*padding: 12,\\s*\\n\\s*borderRadius: 14,\\s*\\n',
               '<div\\n                    className="creas-alert-row"\\n                    style={{\\n                      marginTop: 10,\\n                      padding: 10,\\n                      borderRadius: 12,\\n',
               s, count=1)

    # botão assumir caso um pouco menor (se existir exatamente)
    s = s.replace('padding: "12px 16px",', 'padding: "10px 14px",')
    s = s.replace('fontSize: 15,', 'fontSize: 14,')
    s = s.replace('borderRadius: 14,', 'borderRadius: 12,')

    return s

def main():
    if not FILE.exists():
        print("ERRO: arquivo não encontrado:", FILE)
        sys.exit(1)

    ensure_css_file()
    s = FILE.read_text(encoding="utf-8", errors="ignore")
    orig = s

    s = ensure_css_import(s)
    s = remove_bad_patch_lines(s)
    # garante existência de timelineUI (se já existir let timelineUI, mantém; se não, injeta após imports)
    if not re.search(r"\\b(let|var|const)\\s+timelineUI\\b", s):
        # injeta após imports
        imports = list(re.finditer(r"^\\s*import\\s+.*?;\\s*$", s, flags=re.M))
        ins = imports[-1].end() if imports else 0
        s = s[:ins] + "\\n\\n// FIX_CREAS_TIMELINEUI_V5: fallback\\nlet timelineUI = [];\\n" + s[ins:]

    s = fix_timeline_assignment(s)
    s = apply_layout_changes(s)

    if s != orig:
        backup(FILE)
        FILE.write_text(s, encoding="utf-8")
        print("OK: patched", FILE.relative_to(ROOT))
    else:
        print("NO-OP:", FILE.relative_to(ROOT), "(nenhuma alteração necessária)")

if __name__ == "__main__":
    main()
