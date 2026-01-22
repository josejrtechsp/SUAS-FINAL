#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
from datetime import datetime
import re, sys

def tag(): return datetime.now().strftime("%Y%m%d_%H%M%S")
def backup(p: Path, s: str):
    p.with_suffix(p.suffix + f".bak_{tag()}").write_text(s, encoding="utf-8")

def ensure_import(s: str, line: str) -> str:
    if line.strip() in s: return s
    last = None
    for m in re.finditer(r"^\s*import .*?$", s, flags=re.M):
        last = m
    if last:
        pos = last.end()
        return s[:pos] + "\n" + line + s[pos:]
    return line + s

def patch_relatorios(p: Path) -> bool:
    s0 = p.read_text(encoding="utf-8")
    s = s0
    if "RMA_PRESTACAO_EXPORT_V1" in s:
        return False

    helper = r'''
// RMA_PRESTACAO_EXPORT_V1
async function __downloadPrestacaoCsv(apiBase, apiFetch, mesMaybe, unidadeMaybe) {
  try {
    let mes = String(mesMaybe || "").trim();
    if (!mes || mes.length < 7) {
      mes = prompt("Mês da prestação (YYYY-MM):", new Date().toISOString().slice(0, 7)) || "";
      mes = mes.trim();
    }
    if (!mes) return;
    const unidade = String(unidadeMaybe || "").trim();
    const qs = new URLSearchParams();
    qs.set("mes", mes);
    if (unidade) qs.set("unidade_id", unidade);

    const url = `${apiBase}/cras/rma/prestacao.csv?${qs.toString()}`;
    const r = await apiFetch(url);
    if (!r.ok) throw new Error(await r.text());
    const blob = await r.blob();
    const obj = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = obj;
    a.download = `prestacao_rma_${mes}${unidade ? `_unidade_${unidade}` : ""}.csv`;
    document.body.appendChild(a); a.click(); a.remove(); URL.revokeObjectURL(obj);
  } catch (e) {
    console.error(e);
    alert("Falha ao baixar prestação de contas.");
  }
}
'''
    m = re.search(r"\nexport\s+default\s+", s)
    s = (s[:m.start()] + "\n" + helper + "\n" + s[m.start():]) if m else (helper + "\n" + s)

    anchor = s.find("RMA (CSV do mês)")
    if anchor < 0: anchor = s.find("Prontuário Pessoa")
    if anchor < 0: anchor = s.find("CSV (Painel)")

    btn = r'''
            <button className="btn btn-secundario" type="button"
              onClick={() => __downloadPrestacaoCsv(apiBase, apiFetch, (typeof mesAno !== "undefined" ? mesAno : ""), (typeof unidadeId !== "undefined" ? unidadeId : ""))}>
              Prestação de contas (CSV)
            </button>
'''
    if anchor > 0:
        b = s.rfind("<button", 0, anchor)
        if b > 0:
            s = s[:b] + btn + s[b:]

    backup(p, s0); p.write_text(s, encoding="utf-8")
    return True

def patch_pessoa360(p: Path) -> bool:
    s0 = p.read_text(encoding="utf-8")
    s = s0
    if "PesProntuarioPanel" in s:
        return False
    s = ensure_import(s, 'import PesProntuarioPanel from "./PesProntuarioPanel.jsx";\n')
    snippet = '      <PesProntuarioPanel apiBase={apiBase} apiFetch={apiFetch} pessoaId={pessoaSel} familiaId={data?.familia?.id || null} />\n'
    m = re.search(r"\n\s*return\s*\(\s*\n\s*<div[^>]*className=\{?\"layout-1col\"[^>]*\}?>\s*\n", s)
    if not m: m = re.search(r"\n\s*return\s*\(\s*\n\s*<div[^>]*>\s*\n", s)
    if not m: return False
    if snippet.strip() not in s:
        s = s[:m.end()] + snippet + s[m.end():]
    backup(p, s0); p.write_text(s, encoding="utf-8")
    return True

def main() -> int:
    root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(".").resolve()
    out = {}
    rel = root / "frontend/src/TelaCrasRelatorios.jsx"
    pes = root / "frontend/src/TelaCrasFichaPessoa360.jsx"
    if rel.exists(): out["relatorios"] = patch_relatorios(rel)
    if pes.exists(): out["pessoa360"] = patch_pessoa360(pes)
    print("OK:", out)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
