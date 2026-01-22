# PATCH_CREAS_TIMELINE_FIX6_DUALROOT

Objetivo: corrigir definitivamente o erro no Safari **CREAS > Casos**:
- "Can't find variable: timelineUI"

## Contexto
Há indícios de **duas raízes de front** no seu projeto (ex.: `frontend/src` e `frontend/frontend/src`).
Se o Vite/rotas carregarem a outra árvore, o erro continua.

Este patch aplica o FIX de timeline nas duas possíveis cópias de `TelaCreasCasos.jsx` (se existirem):
- `frontend/src/TelaCreasCasos.jsx`
- `frontend/frontend/src/TelaCreasCasos.jsx`

## O que ele faz (em cada arquivo encontrado)
- Garante `var timelineUI = [];` (hoisted; Safari não quebra)
- Usa `const timelineUIMemo = useMemo(...)` e depois:
  `timelineUI = Array.isArray(timelineUIMemo) ? timelineUIMemo : [];`
- Remove dependency circular `[sel, timelineUI]` -> `[sel]`

## Aplicar
```bash
cd ~/POPNEWS1
unzip -o ~/POPNEWS1/MÓDULOS/PATCH_CREAS_TIMELINE_FIX6_DUALROOT.zip -d .
bash tools/apply_creas_timeline_fix6_dualroot.sh
bash tools/verify_creas_timeline_fix6_dualroot.sh
```

Depois reinicie o front:
```bash
rm -rf ~/POPNEWS1/frontend/node_modules/.vite ~/POPNEWS1/frontend/.vite
cd ~/POPNEWS1/frontend
# Ctrl+C se estiver rodando
npm run dev -- --host 127.0.0.1 --force
```
