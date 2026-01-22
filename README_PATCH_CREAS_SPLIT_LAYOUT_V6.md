# PATCH_CREAS_SPLIT_LAYOUT_V6

Objetivo: corrigir o layout do **CREAS > Casos** para voltar ao split correto (coluna esquerda + coluna direita),
eliminando o “buraco”/espaço vazio e evitando que o conteúdo da direita (incl. Linha de metrô) caia lá embaixo.

## O que faz
Em `frontend/src/TelaCreasCasos.jsx` (e `frontend/frontend/src/...` se existir):
1) Envolve as colunas `col-esquerda` e `col-direita` em um wrapper flex:
   - `<div className="creas-split" style={{ display:'flex', gap:12, alignItems:'flex-start', width:'100%' }}> ... </div>`
2) Força larguras úteis:
   - esquerda: `flex: "0 0 420px", maxWidth: 420`
   - direita: `flex: "1 1 auto", minWidth: 0`
3) Insere marcador `{/* CREAS_SPLIT_LAYOUT_V6 */}` para facilitar auditoria/rollback.

## Aplicar
```bash
cd ~/POPNEWS1
unzip -o ~/POPNEWS1/MÓDULOS/PATCH_CREAS_SPLIT_LAYOUT_V6.zip -d .
bash tools/apply_creas_split_layout_v6.sh
bash tools/verify_creas_split_layout_v6.sh
```

Depois reinicie o front:
```bash
rm -rf ~/POPNEWS1/frontend/node_modules/.vite ~/POPNEWS1/frontend/.vite
cd ~/POPNEWS1/frontend
# Ctrl+C se estiver rodando
npm run dev -- --host 127.0.0.1 --force
```
