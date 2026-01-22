# PATCH 039 — Otimização do /gestao/fila (volume alto)

Este patch aplica melhorias de performance no endpoint **GET /gestao/fila**:

- **cap_fetch**: limita a quantidade de linhas buscadas por fonte (CRAS/CREAS/PopRua/Rede/OSC) para evitar varrer milhares de linhas quando a UI pede 50 itens.
- **order_by coerente**: busca primeiro itens mais antigos (maior chance de atraso/risco).
- **prefetch de usuários filtrado** por município (inclui usuários globais `municipio_id=None`).
- Remove caracteres de controle não imprimíveis que podem quebrar o import (`U+0001`).

## Aplicar
```bash
cd ~/POPNEWS1 && unzip -o ~/Downloads/PATCH_039_optimize_gestao_fila_backend.zip -d . && ~/POPNEWS1/backend/.venv/bin/python backend/scripts/patch039_optimize_gestao_fila.py
```

## Medir
Rode o smoke/perf stress (30 municípios) e compare `fila_p95_50`.

