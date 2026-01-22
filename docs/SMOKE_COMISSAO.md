# Smoke test PopRua (pré-comissão) + Performance

Este smoke test simula o **fluxo completo de demonstração** do PopRua em um **banco isolado**, e agora mede também **latência das rotas críticas** (guardrails), gerando um ranking de **TOP rotas mais lentas**.

## O que ele testa (P0)
- Login (4 perfis): operador A, operador B, coordenação municipal, consórcio
- Criar pessoa + criar caso PopRua
- Intermunicipal ponta-a-ponta: solicitado → contato → aceito → agendado → passagem → contrarreferência → concluído
- Gestão: dashboard + fila (mede p95 com repetições)
- Documentos: gerar ofício + relatório
- Consórcio: acesso mínimo via Gestão

Rotas opcionais (se existirem no seu backend) são checadas como **SKIP** (não derrubam o teste).

## Como rodar
Na raiz do projeto:

```bash
cd ~/POPNEWS1
~/POPNEWS1/backend/.venv/bin/python backend/scripts/smoke_comissao.py
```

## Saída
- imprime um resumo `PASS / FAIL / SKIP`
- imprime também **TOP rotas mais lentas**
- salva um relatório JSON em:

`backend/storage/smoke/smoke_comissao_report.json`

O JSON inclui:
- `perf.summary` (p95/avg/max por rota)
- `perf.top_slow` (top 10 amostras mais lentas)
- `perf.samples` (todas as amostras)

## Budgets (guardrails)
Os budgets (ms) ficam no topo do script em `BUDGETS_MS`.

- Se alguma rota passar do budget no **p95**, aparece **WARN**, mas o smoke não falha.
- A ideia é detectar regressão de performance cedo, antes de virar “sistema pesado”.

## Banco isolado
O script usa:

`backend/storage/smoke/smoke_comissao.db`

Ele **não altera** seu `poprua.db`.

## Dependências
Este smoke usa `TestClient` e requer `httpx` no venv do backend.

```bash
~/POPNEWS1/backend/.venv/bin/pip install httpx
```


## Modo STRESS (volume)

Para medir performance com volume realista (sem sujar poprua.db):

```bash
SMOKE_STRESS=1 SMOKE_STRESS_CASOS=2000 SMOKE_STRESS_INTERMUN=300 \
  ~/POPNEWS1/backend/.venv/bin/python backend/scripts/smoke_comissao.py
```

Dicas:
- Aumente `SMOKE_P95_REPEAT` (ex.: 15) para um p95 mais estável.
- Se demorar muito, reduza `SMOKE_STRESS_CASOS`.

### Parâmetros de dataset (opcionais)
- `SMOKE_STRESS_MUNICIPIOS` (default: 2) — quantos municípios criar (1..N).
- `SMOKE_STRESS_DISTRIB` (default: `spread`) — como distribuir os casos:
  - `spread`: espalha entre os municípios
  - `mun1`: concentra tudo no município 1 (pior caso)
  - `skew`: 70% no município 1 e o restante espalhado
- `SMOKE_STRESS_INTERMUN_MODE` (default: `mun1to2`) — como gerar intermunicipais:
  - `mun1to2`: origem=1, destino=2 (pior caso para esses 2)
  - `ring`: origens/destinos em anel (1→2→3→...→N→1)

Exemplo “30 municípios” (volume total):
```bash
SMOKE_STRESS=1 SMOKE_STRESS_MUNICIPIOS=30 SMOKE_STRESS_DISTRIB=spread \
  SMOKE_STRESS_CASOS=6000 SMOKE_STRESS_INTERMUN=600 SMOKE_P95_REPEAT=15 \
  ~/POPNEWS1/backend/.venv/bin/python backend/scripts/smoke_comissao.py
```
