#!/usr/bin/env python3
"""
PATCH_039: Otimiza /gestao/fila para volume alto:
- limita buscas por fonte (cap_fetch) + order_by coerente (itens mais antigos/urgentes primeiro)
- prefetch de usuarios filtrado por municipio (inclui admins com municipio_id=None)
- remove caracteres de controle não imprimíveis (evita U+0001 quebrar import)

Uso:
  ~/POPNEWS1/backend/.venv/bin/python backend/scripts/patch039_optimize_gestao_fila.py
"""
from __future__ import annotations

import re
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]  # .../backend
TARGET = ROOT / "app" / "routers" / "gestao.py"

def _clean_control_chars(s: str) -> str:
    # remove chars de controle exceto \n \r \t
    out = []
    for ch in s:
        o = ord(ch)
        if o in (9, 10, 13) or o >= 32:
            out.append(ch)
    return "".join(out)

def _replace_prefetch_usuarios(src: str) -> str:
    # troca a função inteira _prefetch_usuarios por uma versão filtrável
    pat = re.compile(r"def\s+_prefetch_usuarios\s*\(session:\s*Session\)\s*->\s*Dict\[int,\s*str\]:.*?\n\n", re.S)
    m = pat.search(src)
    if not m:
        return src
    new_fn = (
        "def _prefetch_usuarios(session: Session, municipio_id: Optional[int] = None) -> Dict[int, str]:\n"
        "    \"\"\"Mapa id->nome para evitar N+1.\n"
        "    Otimização: quando município está definido, busca só usuários daquele município + globais (None).\n"
        "    \"\"\"\n"
        "    try:\n"
        "        stmt = select(Usuario.id, Usuario.nome)\n"
        "        if municipio_id is not None:\n"
        "            stmt = stmt.where(or_(Usuario.municipio_id == int(municipio_id), Usuario.municipio_id.is_(None)))\n"
        "        rows = session.exec(stmt).all()\n"
        "        return {int(r[0]): str(r[1]) for r in rows if r and r[0] is not None}\n"
        "    except Exception:\n"
        "        return {}\n"
        "\n\n"
    )
    return src[:m.start()] + new_fn + src[m.end():]

def _ensure_cap_fetch(src: str) -> str:
    # muda chamada do user_map e injeta cap_fetch se não existir
    src = src.replace("user_map = _prefetch_usuarios(session)", "user_map = _prefetch_usuarios(session, mid)")
    if "cap_fetch =" in src:
        return src

    # inserir logo após user_map
    pat = re.compile(r"(user_map\s*=\s*_prefetch_usuarios\(\s*session\s*,\s*mid\s*\)\s*\n)", re.M)
    m = pat.search(src)
    if not m:
        return src
    insert = (
        "    # cap por fonte: evitamos varrer milhares de linhas quando a fila pede só 50 itens\n"
        "    base_n = int(offset) + int(limit)\n"
        "    cap_fetch = min(5000, max(250, base_n * 6))\n"
    )
    return src[:m.end()] + insert + src[m.end():]

def _inject_limit(src: str, model: str, var: str, order_expr: str) -> str:
    # injeta "stmt = stmt.order_by(...).limit(cap_fetch)" antes do list(session.exec(stmt).all())
    # apenas se ainda não houver limit(cap_fetch) no bloco
    pat = re.compile(
        rf"(stmt\s*=\s*select\({model}\).*?)(\n(?P<ind>\s*){re.escape(var)}\s*=\s*list\(session\.exec\(stmt\)\.all\(\)\))",
        re.S
    )
    def repl(m: re.Match) -> str:
        block = m.group(1)
        if "limit(cap_fetch)" in block:
            return m.group(0)
        ind = m.group("ind")
        return block + f"\n{ind}stmt = stmt.order_by({order_expr}).limit(cap_fetch)" + m.group(2)
    return pat.sub(repl, src, count=1)

def main() -> None:
    if not TARGET.exists():
        raise SystemExit(f"[ERRO] Não encontrei {TARGET}")

    raw = TARGET.read_text(encoding="utf-8", errors="replace")
    raw2 = _clean_control_chars(raw)

    changed = (raw2 != raw)
    src = raw2

    src2 = _replace_prefetch_usuarios(src)
    changed = changed or (src2 != src)
    src = src2

    src2 = _ensure_cap_fetch(src)
    changed = changed or (src2 != src)
    src = src2

    # Injeções por fonte (ordem: mais antigo/urgente primeiro)
    src_prev = src
    src = _inject_limit(src, "CasoCras", "casos", "CasoCras.data_inicio_etapa_atual.asc(), CasoCras.id.asc()")
    src = _inject_limit(src, "CrasTarefa", "tarefas", "CrasTarefa.data_vencimento.asc(), CrasTarefa.id.asc()")
    src = _inject_limit(src, "CadunicoPreCadastro", "rows", "CadunicoPreCadastro.criado_em.asc(), CadunicoPreCadastro.id.asc()")
    src = _inject_limit(src, "CreasCaso", "casos", "CreasCaso.data_inicio_etapa_atual.asc(), CreasCaso.id.asc()")
    src = _inject_limit(src, "CasoPopRua", "casos", "CasoPopRua.data_inicio_etapa_atual.asc(), CasoPopRua.id.asc()")
    src = _inject_limit(src, "CrasEncaminhamento", "encs", "CrasEncaminhamento.criado_em.asc(), CrasEncaminhamento.id.asc()")
    src = _inject_limit(src, "EncaminhamentoIntermunicipal", "encs", "EncaminhamentoIntermunicipal.atualizado_em.asc(), EncaminhamentoIntermunicipal.id.asc()")
    src = _inject_limit(src, "OscPrestacaoContas", "prests", "OscPrestacaoContas.prazo_entrega.asc(), OscPrestacaoContas.id.asc()")
    changed = changed or (src != src_prev)

    if not changed:
        print("[OK] Nenhuma alteração necessária (patch já aplicado).")
        return

    ts = time.strftime("%Y%m%d_%H%M%S")
    bak = TARGET.with_suffix(f".py.bak_patch039_{ts}")
    bak.write_text(raw, encoding="utf-8")
    TARGET.write_text(src, encoding="utf-8")
    print(f"[OK] Patch039 aplicado em {TARGET}")
    print(f"[OK] Backup: {bak}")

if __name__ == "__main__":
    main()
