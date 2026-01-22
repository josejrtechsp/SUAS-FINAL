#!/usr/bin/env python3
"""
tools/patch_fix_casos_dedup_metro_historico_v1.py

Objetivo: parar o ciclo de erro no TelaCrasCasos.jsx (CRAS > Casos):
- Remove TODAS as definições duplicadas de `linhaMetroUI` e `historicoUI` (useMemo)
- Insere 1 definição correta de cada, no lugar seguro: imediatamente antes do primeiro `return (` do componente.

Por quê:
- Você teve "linhaMetroUI already been declared" (duas const)
- Depois linha do metrô "sumiu" porque linhaMetroUI virou array/fallback errado
- E o ErrorBoundary derruba o módulo.

Este patch é idempotente e cria backups `.bak_<timestamp>`.
"""
from __future__ import annotations

from pathlib import Path
from datetime import datetime
import sys
import re

TARGET = Path("frontend/src/TelaCrasCasos.jsx")

def _tag():
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def _find_return_pos(s: str) -> int:
    m = re.search(r"\n\s*return\s*\(\s*\n", s)
    if m:
        return m.start()
    m = re.search(r"\n\s*return\s*\(", s)
    if m:
        return m.start()
    raise RuntimeError("Não encontrei `return (` no componente para inserir os blocos.")

def _remove_const_useMemo(s: str, name: str) -> tuple[str, int]:
    """
    Remove todas as ocorrências de:
      const <name> = useMemo( ... );
    usando scan de parênteses, para não depender de regex frágil.
    """
    count = 0
    while True:
        m = re.search(rf"\bconst\s+{re.escape(name)}\s*=\s*useMemo\s*\(", s)
        if not m:
            break
        start = m.start()
        # encontrar parêntese de abertura de useMemo(
        open_paren = s.find("(", m.end()-1)
        if open_paren < 0:
            break
        # scan de parênteses até fechar
        i = open_paren
        par = 0
        while i < len(s):
            ch = s[i]
            if ch == "(":
                par += 1
            elif ch == ")":
                par -= 1
                if par == 0:
                    i += 1
                    break
            i += 1
        # consumir até ';'
        j = i
        while j < len(s) and s[j] in " \t\r\n":
            j += 1
        if j < len(s) and s[j] == ";":
            j += 1
        # também remover comentário imediatamente anterior se for um FIX nosso
        # volta até início da linha
        line_start = s.rfind("\n", 0, start) + 1
        prev = s.rfind("\n", 0, max(0, line_start-1))
        prev_line = s[prev+1:line_start].strip()
        if "FIX:" in prev_line and name in s[line_start:j]:
            start = prev+1
        s = s[:start] + "\n" + s[j:]
        count += 1
    return s, count

INSERT_BLOCK = r"""
  // ✅ UI derivada (segura): histórico + SUAS
  const historicoUI = useMemo(() => {
    const base = Array.isArray(historico) ? historico : [];
    const extra = Array.isArray(suasUI?.timeline) ? suasUI.timeline : [];
    const all = [...extra, ...base];
    all.sort((a, b) => {
      const ta = a?.criado_em ? new Date(a.criado_em).getTime() : (a?.quando ? new Date(a.quando).getTime() : 0);
      const tb = b?.criado_em ? new Date(b.criado_em).getTime() : (b?.quando ? new Date(b.quando).getTime() : 0);
      return tb - ta;
    });
    return all;
  }, [historico, suasUI]);

  // ✅ UI derivada (segura): Linha do Metrô como OBJETO e mescla registros SUAS na etapa atual
  const linhaMetroUI = useMemo(() => {
    if (!linhaMetro) return null;

    const extraRegs = Array.isArray(suasUI?.metroRegistros) ? suasUI.metroRegistros : [];
    if (!extraRegs.length) return linhaMetro;

    const etapasArr = Array.isArray(linhaMetro?.etapas) ? linhaMetro.etapas : [];
    if (!etapasArr.length) return linhaMetro;

    const prefer = String(sel?.etapa_atual || "");
    let idx = etapasArr.findIndex((e) => String(e?.codigo || "") === prefer);
    if (idx < 0) idx = 0;

    const sorted = [...extraRegs].sort((a, b) => {
      const ta = a?.data_hora ? new Date(a.data_hora).getTime() : 0;
      const tb = b?.data_hora ? new Date(b.data_hora).getTime() : 0;
      return tb - ta;
    });

    const merged = { ...linhaMetro };
    merged.etapas = etapasArr.map((e, i) => {
      if (i !== idx) return e;
      const regs = Array.isArray(e?.registros) ? e.registros : [];
      return { ...e, registros: [...sorted, ...regs] };
    });
    return merged;
  }, [linhaMetro, sel?.etapa_atual, suasUI?.stats?.total]);
"""

def patch_file(root: Path) -> dict:
    p = root / TARGET
    if not p.exists():
        raise RuntimeError(f"Arquivo não encontrado: {p}")

    s0 = p.read_text(encoding="utf-8")
    s = s0

    # remover duplicações (histórico e metrô)
    s, n_hist = _remove_const_useMemo(s, "historicoUI")
    s, n_metro = _remove_const_useMemo(s, "linhaMetroUI")

    # inserir blocos uma vez
    pos = _find_return_pos(s)
    s = s[:pos] + INSERT_BLOCK + s[pos:]

    changed = (s != s0)
    if changed:
        bak = p.with_suffix(p.suffix + f".bak_{_tag()}")
        bak.write_text(s0, encoding="utf-8")
        p.write_text(s, encoding="utf-8")

    return {"changed": changed, "removed_historicoUI": n_hist, "removed_linhaMetroUI": n_metro}

def main() -> int:
    root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(".").resolve()
    try:
        info = patch_file(root)
        print("OK:", info)
        return 0
    except Exception as e:
        print("ERRO:", str(e))
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
