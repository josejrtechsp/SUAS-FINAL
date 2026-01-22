# PATCH_CREAS_LAYOUT_V5_FIX2

Este patch substitui o FIX1 (que falhou por SyntaxError) e aplica corretamente:

## 1) Correção (stability)
- Remove o trecho indevido inserido dentro de `salvarAtendimento()`:
  - `// PATCH_CRAS_FRONT_STABILIZATION_V3...`
  - `timelineUI = Array.isArray(timelineUICalc) ? timelineUICalc : [];`
- Garante `timelineUI` (Safari/TDZ):
  - injeta `let timelineUI = [];` no topo do arquivo (após imports)
  - atribui `timelineUI = Array.isArray(timelineUICalc) ? timelineUICalc : [];` logo após o `useMemo` do `timelineUICalc`

## 2) Layout V5 (compacto e operável) – somente nesta tela
- Importa CSS local `frontend/src/creas_layout_v5.css`
- Coluna esquerda: lista com scroll (maxHeight + overflow)
- Cabeçalho do caso: badges (Status/Risco/Etapa/Resp.) + faixa curta (Último/Próximo)
- Card de header mais compacto

## Como aplicar
```bash
cd ~/POPNEWS1
unzip -o ~/POPNEWS1/MÓDULOS/PATCH_CREAS_LAYOUT_V5_FIX2.zip -d .
bash tools/apply_creas_layout_v5_fix2.sh
bash tools/verify_creas_layout_v5_fix2.sh
```

Depois reinicie o front:
```bash
rm -rf ~/POPNEWS1/frontend/node_modules/.vite
cd ~/POPNEWS1/frontend
# Ctrl+C se estiver rodando
npm run dev
```
