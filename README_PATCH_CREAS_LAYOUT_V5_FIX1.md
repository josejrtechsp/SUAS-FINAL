# PATCH_CREAS_LAYOUT_V5_FIX1

Este patch faz 2 coisas:
1) **Correção de estabilidade** (CREAS/Casos):
   - Remove um trecho indevido inserido em `salvarAtendimento()`:
     `// PATCH_CRAS_FRONT_STABILIZATION_V3...` + `timelineUI = ...`
   - Garante que `timelineUI` seja preenchido corretamente a partir de `timelineUICalc` logo após o `useMemo`,
     sem TDZ no Safari.

2) **Melhoria de layout/operabilidade** (CREAS/Casos):
   - Lista da esquerda com rolagem (não vira “parede”)
   - Cabeçalho do caso mais compacto (badges em linha + “último/próximo” em faixa curta)
   - Ajustes leves de espaçamento e densidade visual via CSS local (somente nessa tela)

## Aplicação
```bash
cd ~/POPNEWS1
unzip -o ~/POPNEWS1/MÓDULOS/PATCH_CREAS_LAYOUT_V5_FIX1.zip -d .
bash tools/apply_creas_layout_v5_fix1.sh
bash tools/verify_creas_layout_v5_fix1.sh
```

Depois reinicie o front:
```bash
cd ~/POPNEWS1/frontend
# Ctrl+C se estiver rodando
npm run dev
```

Se quiser limpar cache do Vite:
```bash
rm -rf ~/POPNEWS1/frontend/node_modules/.vite
```
