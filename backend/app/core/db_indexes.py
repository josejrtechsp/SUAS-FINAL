# app/core/db_indexes.py
"""
Criação idempotente de índices (principalmente para SQLite em DEV).
Objetivo: evitar travamentos quando o volume cresce (fila/casos/intermunicipal).

- Não depende de migração.
- Só cria índices se a tabela e as colunas existirem.
- Seguro para rodar em startup (CREATE INDEX IF NOT EXISTS).
"""

from __future__ import annotations

from typing import Iterable, List, Set, Tuple

from sqlalchemy import text
from sqlalchemy.engine import Engine


def _table_exists(conn, table: str) -> bool:
    row = conn.execute(
        text("SELECT name FROM sqlite_master WHERE type='table' AND name = :t LIMIT 1"),
        {"t": table},
    ).fetchone()
    return bool(row)


def _cols(conn, table: str) -> Set[str]:
    cols: Set[str] = set()
    try:
        rows = conn.execute(text(f"PRAGMA table_info('{table}')")).fetchall()
        for r in rows:
            # PRAGMA table_info: (cid, name, type, notnull, dflt_value, pk)
            cols.add(str(r[1]))
    except Exception:
        return set()
    return cols


def _mk_index_sql(name: str, table: str, cols: Iterable[str]) -> str:
    cols_sql = ", ".join([c for c in cols])
    return f"CREATE INDEX IF NOT EXISTS {name} ON {table} ({cols_sql})"


def ensure_indexes(engine: Engine, database_url: str) -> List[str]:
    """
    Cria índices idempotentes no SQLite. Retorna lista de índices criados (ou tentados).

    Obs: em PostgreSQL, o ideal é usar migrações (Alembic). Aqui a função é no-op.
    """
    created: List[str] = []
    if not (database_url or "").startswith("sqlite"):
        return created

    # Lista de índices desejados (tabela, nome, colunas)
    desired: List[Tuple[str, str, Tuple[str, ...]]] = [
        # PopRua - casos
        ("casopoprua", "idx_casopoprua_muni_status_ativo", ("municipio_id", "status", "ativo")),
        ("casopoprua", "idx_casopoprua_muni_etapa", ("municipio_id", "etapa_atual")),
        ("casopoprua", "idx_casopoprua_muni_upd", ("municipio_id", "data_ultima_atualizacao")),
        ("casopoprua", "idx_casopoprua_prox_acao", ("municipio_id", "data_prevista_proxima_acao")),
        ("casopoprua", "idx_casopoprua_estagnado", ("municipio_id", "estagnado")),

        # Intermunicipal
        ("encaminhamentos_intermunicipais", "idx_intermun_dest_status_upd", ("municipio_destino_id", "status", "atualizado_em")),
        ("encaminhamentos_intermunicipais", "idx_intermun_orig_status_upd", ("municipio_origem_id", "status", "atualizado_em")),
        ("encaminhamentos_intermunicipais", "idx_intermun_pessoa", ("pessoa_id",)),
        ("encaminhamentos_eventos", "idx_intermun_eventos_enc_em", ("encaminhamento_id", "em")),

        # Pessoas (busca/listagem)
        ("pessoarua", "idx_pessoarua_muni_nome", ("municipio_origem_id", "nome_civil")),
        ("pessoarua", "idx_pessoarua_muni_nome_social", ("municipio_origem_id", "nome_social")),

        # Usuários (login/listas)
        ("usuarios", "idx_usuarios_email", ("email",)),
        ("usuarios", "idx_usuarios_muni_perfil", ("municipio_id", "perfil")),
    ]

    with engine.begin() as conn:
        for table, idx_name, cols in desired:
            if not _table_exists(conn, table):
                continue
            existing_cols = _cols(conn, table)
            if not existing_cols:
                continue
            if any(c not in existing_cols for c in cols):
                continue
            sql = _mk_index_sql(idx_name, table, cols)
            try:
                conn.execute(text(sql))
                created.append(idx_name)
            except Exception:
                # índice pode falhar por nome duplicado em schema velho; ignoramos
                continue

    return created
