# Checklist de Performance (Lentidão) — IDEAL / PopRua

Este checklist serve para:
- medir **tempo de carregamento** do front (primeira carga e navegação entre módulos)
- identificar **arquivos pesados** (JS/CSS/imagens)
- detectar **travamentos** (long tasks / re-render)
- validar o backend com **carga leve** (smoke) antes de escalar.

> Observação: o projeto usa `rolldown-vite`. Algumas ferramentas baseadas em sourcemap (ex.: `source-map-explorer`) podem acusar warnings de "column Infinity". Para análise de bundle, prefira o relatório do `visualizer` (veja abaixo).

---

## 1) Frontend — build, tamanhos e análise

### 1.1 Build de produção
```bash
cd ~/POPNEWS1/frontend
rm -rf dist
npm run build
```

### 1.2 Maiores arquivos gerados (o que pesa)
```bash
find dist -type f -maxdepth 3 -print0 | xargs -0 ls -lh | sort -h | tail -n 30
```

### 1.3 Relatório visual do bundle (recomendado)
Gera `dist/stats.html` (treemap com gzip/brotli):
```bash
cd ~/POPNEWS1/frontend
npm run analyze
```
Depois abra no navegador:
- `~/POPNEWS1/frontend/dist/stats.html`

### 1.4 Medir em modo produção local (preview)
```bash
cd ~/POPNEWS1/frontend
npm run build
npm run preview
# abre: http://localhost:4173
```

### 1.5 Lighthouse (Chrome)
- Abra: `http://localhost:4173`
- DevTools → **Lighthouse** → Performance
- Rode com **Simulated throttling** (Mobile/Slow 4G)

Guarde estes números:
- **FCP** (First Contentful Paint)
- **LCP** (Largest Contentful Paint)
- **TBT** (Total Blocking Time)
- **CLS** (Cumulative Layout Shift)

---

## 2) Frontend — sintomas clássicos de lentidão (o que olhar)

### 2.1 Rede / assets
- imagens grandes no topo (logo, hero, ícones)
- múltiplas imagens duplicadas no `public/`

### 2.2 Render
- listas grandes (fila/casos/pessoas) sem paginação/virtualização
- filtros/sorts rodando dentro do render sem `useMemo`
- estados globais causando re-render em árvore grande

---

## 3) Backend — smoke test e carga leve

### 3.1 Subir API
```bash
cd ~/POPNEWS1/backend
uvicorn app.main:app --host 127.0.0.1 --port 8001
```

### 3.2 Healthcheck
```bash
curl -sS http://127.0.0.1:8001/health
```

### 3.3 Carga leve (autocannon)
Instale uma vez:
```bash
npm i -g autocannon
```
Rodar no health (exemplo):
```bash
autocannon -c 50 -d 15 http://127.0.0.1:8001/health
```

> Se o gargalo aparecer em endpoints reais (ex.: /casos, /gestao/fila), repita o autocannon nesses endpoints e observe p95/p99.

---

## 4) Banco de dados — regra de ouro
- Toda listagem grande precisa ter **paginação** (`limit/offset`) e **índices**.
- Sempre que aparecer lentidão em lista/fila, o primeiro passo é verificar se:
  - a query está filtrando por colunas indexadas
  - existe ordenação por coluna sem índice

Veja também: `docs/DB_INDEXES.md`
