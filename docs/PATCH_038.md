# Patch 038 — Cache TTL para Gestão (fila + dashboard)

Este patch adiciona cache em memória (TTL curto) nos endpoints:

- GET /gestao/fila (TTL ~ 8s)
- GET /gestao/dashboard/resumo (TTL ~ 12s)

Objetivo: reduzir custo de recomputar a fila e agregações do dashboard em refreshs e filtros repetidos do front.

Também aplica cache simples do mapa de usuários (id->nome) por 60s.

## Bypass (debug/perf)
Para medir custo "real" sem cache, use:

- /gestao/fila?nocache=1
- /gestao/dashboard/resumo?nocache=1

O patch adiciona campo opcional `_cached=true` quando a resposta vier do cache.
