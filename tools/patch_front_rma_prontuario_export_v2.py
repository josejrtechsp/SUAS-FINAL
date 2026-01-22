\
#!/usr/bin/env python3
# tools/patch_front_rma_prontuario_export_v2.py
#
# Mais robusto: NÃO depende de `if (viewKey === "exportar")`.
# - Insere helpers (downloadRmaCsv / downloadProntuario...) antes do primeiro `return (`
# - Insere botões ao lado do bloco existente de exportação (âncora "CSV (Painel)" ou "relatorio_overview.csv")
# - Usa typeof para não quebrar se mesAno/unidadeId não existirem (cai para prompt)
#
# Alvo: frontend/src/TelaCrasRelatorios.jsx
#
# Idempotente + cria backup .bak_<timestamp>.

from __future__ import annotations

from pathlib import Path
from datetime import datetime
import re
import sys

FILE = Path("frontend/src/TelaCrasRelatorios.jsx")
MARK = "// RMA_PRONTUARIO_EXPORT_V2"

def tag():
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def backup(p: Path, s: str):
    p.with_suffix(p.suffix + f".bak_{tag()}").write_text(s, encoding="utf-8")

HELPERS = """
  // RMA_PRONTUARIO_EXPORT_V2
  async function _downloadBlob(name, resp) {
    const blob = await resp.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = name;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  }

  async function downloadRmaCsv() {
    try {
      const mesVar = (typeof mesAno !== "undefined") ? mesAno : "";
      const unidadeVar = (typeof unidadeId !== "undefined") ? unidadeId : "";
      const mes = String(mesVar || "").trim() || prompt("Mês do RMA (YYYY-MM):", new Date().toISOString().slice(0,7));
      if (!mes) return;
      const unidade = String(unidadeVar || "").trim();
      const qs = new URLSearchParams();
      qs.set("mes", mes);
      if (unidade) qs.set("unidade_id", unidade);
      const url = `${apiBase}/cras/rma/export.csv?${qs.toString()}`;
      const r = await apiFetch(url);
      if (!r.ok) throw new Error(await r.text());
      await _downloadBlob(`rma_${mes}${unidade ? `_unidade_${unidade}` : ""}.csv`, r);
    } catch (e) {
      console.error(e);
      alert("Não foi possível baixar o RMA. Verifique se o backend está atualizado.");
    }
  }

  async function downloadProntuarioPessoaCsv() {
    const pid = prompt("ID da Pessoa (PessoaSUAS) para exportar prontuário:");
    if (!pid) return;
    try {
      const url = `${apiBase}/cras/prontuario/export.csv?pessoa_id=${encodeURIComponent(String(pid))}&include_suas=1`;
      const r = await apiFetch(url);
      if (!r.ok) throw new Error(await r.text());
      await _downloadBlob(`prontuario_pessoa_${pid}.csv`, r);
    } catch (e) {
      console.error(e);
      alert("Falha ao exportar prontuário da pessoa.");
    }
  }

  async function downloadProntuarioFamiliaCsv() {
    const fid = prompt("ID da Família (FamiliaSUAS) para exportar prontuário:");
    if (!fid) return;
    try {
      const url = `${apiBase}/cras/prontuario/export.csv?familia_id=${encodeURIComponent(String(fid))}&include_suas=1`;
      const r = await apiFetch(url);
      if (!r.ok) throw new Error(await r.text());
      await _downloadBlob(`prontuario_familia_${fid}.csv`, r);
    } catch (e) {
      console.error(e);
      alert("Falha ao exportar prontuário da família.");
    }
  }
"""

BUTTONS = """
            <button className="btn btn-secundario" type="button" onClick={downloadRmaCsv}>
              RMA (CSV do mês)
            </button>
            <button className="btn btn-secundario" type="button" onClick={downloadProntuarioPessoaCsv}>
              Prontuário Pessoa (CSV)
            </button>
            <button className="btn btn-secundario" type="button" onClick={downloadProntuarioFamiliaCsv}>
              Prontuário Família (CSV)
            </button>
"""

def patch(p: Path) -> bool:
    s0 = p.read_text(encoding="utf-8")
    s = s0
    if MARK in s:
        return False

    # 1) inserir helpers antes do primeiro return(
    m_ret = re.search(r"\n\s*return\s*\(\s*\n", s)
    if not m_ret:
        m_ret = re.search(r"\n\s*return\s*\(", s)
    if not m_ret:
        raise RuntimeError("Não encontrei return( em TelaCrasRelatorios.jsx")

    # evitar duplicação se funções já existirem
    if "downloadRmaCsv" not in s:
        s = s[:m_ret.start()] + HELPERS + s[m_ret.start():]

    # 2) inserir botões junto do bloco de export (âncora)
    a = s.find("CSV (Painel)")
    if a < 0:
        a = s.find('relatorio_overview.csv')
    if a < 0:
        a = s.find('downloadCsv("relatorio_overview.csv"')
    if a < 0:
        # sem âncora, não tenta mexer no JSX pra não quebrar
        raise RuntimeError("Não encontrei âncora de export (CSV (Painel)/relatorio_overview.csv).")

    b = s.rfind("<button", 0, a)
    if b < 0:
        raise RuntimeError("Não encontrei <button antes da âncora de export.")

    s = s[:b] + BUTTONS + s[b:]

    backup(p, s0)
    p.write_text(s, encoding="utf-8")
    return True

def main() -> int:
    root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(".").resolve()
    p = root / FILE
    if not p.exists():
        print("ERRO: não achei", p)
        return 2
    try:
        ch = patch(p)
        print("OK: patch_front_rma_prontuario_export_v2 changed=" + str(ch))
        return 0
    except Exception as e:
        print("ERRO:", str(e))
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
