# Índices e performance (DEV)

Este patch adiciona um gerador idempotente de índices para SQLite:

- `backend/app/core/db_indexes.py`
- e injeta uma chamada em `backend/app/core/db.py` logo após `SQLModel.metadata.create_all(engine)`.

Por que isso é importante:
- `gestao/fila`, listas de casos e intermunicipal ficam lentos quando o volume cresce.
- índices compostos (municipio_id + status + datas) reduzem drasticamente o custo das queries.

Em produção (recomendado):
- PostgreSQL + migrações (Alembic).
- Este patch continua seguro (no-op para não-sqlite), mas os índices devem ser geridos via migração.
