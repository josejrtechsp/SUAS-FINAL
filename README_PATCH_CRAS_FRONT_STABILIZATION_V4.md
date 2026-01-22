# PATCH_CRAS_FRONT_STABILIZATION_V4 (CREAS timelineUI TDZ fix)

Objetivo: corrigir definitivamente o erro no Safari em **CREAS > Casos**:
- "Can't find variable: timelineUI"

## Causa provável
Mesmo após criar `timelineUI` derivado de `timelineUICalc`, ainda pode existir **uso de `timelineUI` antes da linha da declaração**
(TDZ - temporal dead zone), que no Safari pode aparecer como "Can't find variable".

## O que este patch faz
Em `frontend/src/TelaCreasCasos.jsx`:
1) Declara `let timelineUI = [];` logo após os imports (antes de qualquer hook/uso).
2) Substitui a linha derivada:
   - de: `const timelineUI = Array.isArray(timelineUICalc) ? timelineUICalc : [];`
   - para: `timelineUI = Array.isArray(timelineUICalc) ? timelineUICalc : [];`
   (assim não existe TDZ)

## Aplicar
```bash
cd ~/POPNEWS1
unzip -o ~/POPNEWS1/MÓDULOS/PATCH_CRAS_FRONT_STABILIZATION_V4.zip -d .
bash tools/apply_cras_front_stabilization_v4.sh
bash tools/verify_cras_front_smoke_v4.sh
```

Depois: reinicie o front (`Ctrl+C` e `npm run dev`). Se persistir cache, rode:
```bash
rm -rf ~/POPNEWS1/frontend/node_modules/.vite
```
