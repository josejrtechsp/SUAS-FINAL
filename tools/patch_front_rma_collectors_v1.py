#!/usr/bin/env python3
# tools/patch_front_rma_collectors_v1.py
# Insere coletores invisíveis do RMA nas ações principais do CRAS.
# Idempotente + backups .bak_<timestamp>.

from __future__ import annotations

from pathlib import Path
from datetime import datetime
import re
import sys

ROOT_FILES = {
    "casos": Path("frontend/src/TelaCrasCasos.jsx"),
    "triagem": Path("frontend/src/TelaCras.jsx"),
    "enc": Path("frontend/src/TelaCrasEncaminhamentos.jsx"),
    "tarefas": Path("frontend/src/TelaCrasTarefas.jsx"),
    "docs": Path("frontend/src/TelaCrasDocumentos.jsx"),
}

IMPORT_LINE = 'import { rmaCollect } from "./domain/rmaCollector.js";\n'
MARK = "// RMA_COLLECT_V1"

def tag():
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def backup(p: Path, s: str):
    p.with_suffix(p.suffix + f".bak_{tag()}").write_text(s, encoding="utf-8")

def ensure_import(s: str) -> str:
    if "rmaCollector" in s:
        return s
    if IMPORT_LINE.strip() in s:
        return s
    last = None
    for m in re.finditer(r"^\s*import .*?$", s, flags=re.M):
        last = m
    if last:
        pos = last.end()
        return s[:pos] + "\n" + IMPORT_LINE + s[pos:]
    return IMPORT_LINE + s

def patch_casos(s: str) -> tuple[str, bool]:
    if f"{MARK} CASOS" in s:
        return s, False
    m = re.search(r"\n\s*setSel\(\s*created\s*\)\s*;\s*\n", s)
    if not m:
        return s, False
    block = f"""      {MARK} CASOS
      try {{
        await rmaCollect({{
          apiBase,
          apiFetch,
          servico: "CASOS",
          acao: "criar",
          unidade_id: (typeof unidadeAtiva !== "undefined" && unidadeAtiva) ? Number(unidadeAtiva) : null,
          pessoa_id: created?.pessoa_id ?? null,
          familia_id: created?.familia_id ?? null,
          caso_id: created?.id ?? null,
          alvo_tipo: "caso",
          alvo_id: created?.id ?? null,
          meta: {{ tipo_caso: (typeof tipoCaso !== "undefined" ? tipoCaso : null) }},
        }});
      }} catch {{}}
"""
    s2 = s[:m.end()] + block + s[m.end():]
    return s2, True

def patch_triagem(s: str) -> tuple[str, bool]:
    if f"{MARK} TRIAGEM" in s:
        return s, False
    m = re.search(r'setMsg\("Convertido em PAIF ✅"\);\s*\n', s)
    if not m:
        return s, False
    block = f"""    {MARK} TRIAGEM
    try {{
      const casoId = data?.caso?.id ?? data?.caso_id ?? null;
      const pessoaId = data?.paif?.pessoa_suas_id ?? data?.paif?.pessoa_id ?? t?.pessoa_id ?? null;
      await rmaCollect({{
        apiBase,
        apiFetch,
        servico: "PAIF",
        acao: "converter",
        unidade_id: (typeof unidadeSel !== "undefined" && unidadeSel) ? Number(unidadeSel) : null,
        pessoa_id: pessoaId ? Number(pessoaId) : null,
        caso_id: casoId ? Number(casoId) : null,
        alvo_tipo: "triagem",
        alvo_id: t?.id ?? null,
        meta: {{ triagem_id: t?.id ?? null, paif_id: data?.paif?.id ?? null }},
      }});
    }} catch {{}}
"""
    s2 = s[:m.end()] + block + s[m.end():]
    return s2, True

def patch_enc(s: str) -> tuple[str, bool]:
    changed = False

    if f"{MARK} ENC_CRIAR" not in s:
        m = re.search(r'setMsg\("Encaminhamento criado ✅"\);\s*\n', s)
        if m:
            block = f"""    {MARK} ENC_CRIAR
    try {{
      await rmaCollect({{
        apiBase,
        apiFetch,
        servico: "ENCAMINHAMENTO",
        acao: "criar",
        unidade_id: (typeof unidadeId !== "undefined" && unidadeId) ? Number(unidadeId) : null,
        pessoa_id: payload?.pessoa_id ?? null,
        alvo_tipo: "encaminhamento",
        meta: {{ destino_tipo: payload?.destino_tipo, destino_nome: payload?.destino_nome, prazo_dias: payload?.prazo_devolutiva_dias }},
      }});
    }} catch {{}}
"""
            s = s[:m.end()] + block + s[m.end():]
            changed = True

    if f"{MARK} ENC_COBRAR" not in s:
        m = re.search(r'setMsg\("Cobrança registrada ✅"\);\s*\n', s)
        if m:
            block = f"""    {MARK} ENC_COBRAR
    try {{
      await rmaCollect({{
        apiBase,
        apiFetch,
        servico: "ENCAMINHAMENTO",
        acao: "cobrar",
        unidade_id: (typeof unidadeId !== "undefined" && unidadeId) ? Number(unidadeId) : null,
        alvo_tipo: "encaminhamento",
        alvo_id: enc?.id ?? null,
        meta: {{ detalhe }},
      }});
    }} catch {{}}
"""
            s = s[:m.end()] + block + s[m.end():]
            changed = True

    if f"{MARK} ENC_DEVOLUTIVA" not in s:
        mfun = re.search(r"async function registrarDevolutiva\(enc\)\s*\{", s)
        if mfun:
            m = re.search(r"await\s+loadList\(\);\s*\n", s[mfun.end():])
            if m:
                pos = mfun.end() + m.end()
                block = f"""    {MARK} ENC_DEVOLUTIVA
    try {{
      await rmaCollect({{
        apiBase,
        apiFetch,
        servico: "ENCAMINHAMENTO",
        acao: "devolutiva",
        unidade_id: (typeof unidadeId !== "undefined" && unidadeId) ? Number(unidadeId) : null,
        alvo_tipo: "encaminhamento",
        alvo_id: enc?.id ?? null,
        meta: {{ detalhe }},
      }});
    }} catch {{}}
"""
                s = s[:pos] + block + s[pos:]
                changed = True

    return s, changed

def patch_tarefas(s: str) -> tuple[str, bool]:
    if f"{MARK} TAREFA_CONCLUIR" in s:
        return s, False
    m = re.search(r'setMsg\("Concluída ✅"\);\s*\n', s)
    if not m:
        return s, False
    block = f"""      {MARK} TAREFA_CONCLUIR
      try {{
        await rmaCollect({{
          apiBase,
          apiFetch,
          servico: "TAREFA",
          acao: "concluir",
          unidade_id: (typeof unidadeId !== "undefined" && unidadeId) ? Number(unidadeId) : null,
          alvo_tipo: "tarefa",
          alvo_id: row?.id ?? null,
          meta: {{ responsavel_id: row?.responsavel_id ?? null }},
        }});
      }} catch {{}}
"""
    s2 = s[:m.end()] + block + s[m.end():]
    return s2, True

def patch_docs(s: str) -> tuple[str, bool]:
    if f"{MARK} DOC_EMITIR" in s:
        return s, False
    m = re.search(r"\n\s*const\s+j\s*=\s*await\s+r\.json\(\)\s*;\s*\n", s)
    if not m:
        return s, False
    block = f"""      {MARK} DOC_EMITIR
      try {{
        const meta = {{
          tipo: selected?.tipo ?? null,
          numero: j?.numero ?? null,
          modelo_id: selected?.id ?? null,
        }};
        await rmaCollect({{
          apiBase,
          apiFetch,
          servico: "DOCUMENTO",
          acao: "emitir",
          unidade_id: (typeof unidadeId !== "undefined" && unidadeId) ? Number(unidadeId) : null,
          pessoa_id: payload?.pessoa_id ?? null,
          familia_id: payload?.familia_id ?? null,
          caso_id: payload?.caso_id ?? null,
          alvo_tipo: "documento",
          alvo_id: j?.id ?? null,
          meta,
        }});
      }} catch {{}}
"""
    s2 = s[:m.end()] + block + s[m.end():]
    return s2, True

def main() -> int:
    root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(".").resolve()
    results = {}
    any_changed = False

    for key, rel in ROOT_FILES.items():
        p = root / rel
        if not p.exists():
            results[key] = "missing"
            continue

        s0 = p.read_text(encoding="utf-8")
        s = ensure_import(s0)
        changed = (s != s0)

        if key == "casos":
            s, c = patch_casos(s)
        elif key == "triagem":
            s, c = patch_triagem(s)
        elif key == "enc":
            s, c = patch_enc(s)
        elif key == "tarefas":
            s, c = patch_tarefas(s)
        elif key == "docs":
            s, c = patch_docs(s)
        else:
            c = False

        changed = changed or c
        results[key] = "changed" if changed else "noop"

        if changed:
            backup(p, s0)
            p.write_text(s, encoding="utf-8")
            any_changed = True

    print("OK:", results, "any_changed=" + str(any_changed))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
