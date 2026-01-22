#!/usr/bin/env python3
# tools/patch_front_rma_prontuario_export_v3.py
#
# Fix runtime: "downloadRmaCsv is not defined" in TelaCrasRelatorios.jsx.
# Strategy:
# 1) Inject module-scope helpers (marker V3).
# 2) Rewrite onClick handlers to inline arrows calling module helpers.
#    Uses typeof guards for optional mesAno/unidadeId identifiers.
#
# Target: frontend/src/TelaCrasRelatorios.jsx
# Idempotent + creates .bak_<timestamp>.

from __future__ import annotations

from pathlib import Path
from datetime import datetime
import re
import sys

FILE = Path("frontend/src/TelaCrasRelatorios.jsx")
MARK = "// RMA_PRONTUARIO_EXPORT_V3"

def tag():
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def backup(p: Path, s: str):
    p.with_suffix(p.suffix + f".bak_{tag()}").write_text(s, encoding="utf-8")

HELPERS = """\n// RMA_PRONTUARIO_EXPORT_V3
async function __downloadBlob(resp, filename) {
  const blob = await resp.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

async function __downloadRmaCsv(apiBase, apiFetch, mesMaybe, unidadeMaybe) {
  try {
    let mes = String(mesMaybe || "").trim();
    if (!mes || mes.length < 7) {
      mes = prompt("Mês do RMA (YYYY-MM):", new Date().toISOString().slice(0, 7)) || "";
      mes = mes.trim();
    }
    if (!mes) return;

    const unidade = String(unidadeMaybe || "").trim();
    const qs = new URLSearchParams();
    qs.set("mes", mes);
    if (unidade) qs.set("unidade_id", unidade);

    const url = `${apiBase}/cras/rma/export.csv?${qs.toString()}`;
    const r = await apiFetch(url);
    if (!r.ok) throw new Error(await r.text());
    await __downloadBlob(r, `rma_${mes}${unidade ? `_unidade_${unidade}` : ""}.csv`);
  } catch (e) {
    console.error(e);
    alert("Não foi possível baixar o RMA. Verifique se o backend está atualizado.");
  }
}

async function __downloadProntuarioPessoaCsv(apiBase, apiFetch) {
  const pid = prompt("ID da Pessoa (PessoaSUAS) para exportar prontuário:");
  if (!pid) return;
  try {
    const url = `${apiBase}/cras/prontuario/export.csv?pessoa_id=${encodeURIComponent(String(pid))}&include_suas=1`;
    const r = await apiFetch(url);
    if (!r.ok) throw new Error(await r.text());
    await __downloadBlob(r, `prontuario_pessoa_${pid}.csv`);
  } catch (e) {
    console.error(e);
    alert("Falha ao exportar prontuário da pessoa.");
  }
}

async function __downloadProntuarioFamiliaCsv(apiBase, apiFetch) {
  const fid = prompt("ID da Família (FamiliaSUAS) para exportar prontuário:");
  if (!fid) return;
  try {
    const url = `${apiBase}/cras/prontuario/export.csv?familia_id=${encodeURIComponent(String(fid))}&include_suas=1`;
    const r = await apiFetch(url);
    if (!r.ok) throw new Error(await r.text());
    await __downloadBlob(r, `prontuario_familia_${fid}.csv`);
  } catch (e) {
    console.error(e);
    alert("Falha ao exportar prontuário da família.");
  }
}
\n"""

def inject_helpers(s: str) -> tuple[str, bool]:
    if MARK in s:
        return s, False
    m = re.search(r"\nexport\s+default\s+", s)
    if not m:
        # fallback after last import
        last = None
        for mm in re.finditer(r"^\s*import .*?$", s, flags=re.M):
            last = mm
        if last:
            pos = last.end()
            return s[:pos] + "\n\n" + HELPERS + "\n" + s[pos:], True
        raise RuntimeError("Não encontrei export default nem imports para inserir helpers.")
    pos = m.start()
    return s[:pos] + "\n" + HELPERS + "\n" + s[pos:], True

def rewrite_handlers(s: str) -> tuple[str, bool]:
    changed = False
    repl_rma = 'onClick={() => __downloadRmaCsv(apiBase, apiFetch, (typeof mesAno !== "undefined" ? mesAno : ""), (typeof unidadeId !== "undefined" ? unidadeId : ""))}'
    s2, n = re.subn(r'onClick=\{\s*downloadRmaCsv\s*\}', repl_rma, s)
    if n:
        s = s2
        changed = True

    repl_p = 'onClick={() => __downloadProntuarioPessoaCsv(apiBase, apiFetch)}'
    s2, n = re.subn(r'onClick=\{\s*downloadProntuarioPessoaCsv\s*\}', repl_p, s)
    if n:
        s = s2
        changed = True

    repl_f = 'onClick={() => __downloadProntuarioFamiliaCsv(apiBase, apiFetch)}'
    s2, n = re.subn(r'onClick=\{\s*downloadProntuarioFamiliaCsv\s*\}', repl_f, s)
    if n:
        s = s2
        changed = True

    return s, changed

def main() -> int:
    root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(".").resolve()
    p = root / FILE
    if not p.exists():
        print("ERRO: não achei", p)
        return 2

    s0 = p.read_text(encoding="utf-8")
    s = s0

    try:
        s, _ = inject_helpers(s)
        s, _ = rewrite_handlers(s)
    except Exception as e:
        print("ERRO:", str(e))
        return 2

    if s != s0:
        backup(p, s0)
        p.write_text(s, encoding="utf-8")
        print("OK: patch_front_rma_prontuario_export_v3 changed=True")
    else:
        print("OK: patch_front_rma_prontuario_export_v3 changed=False")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
