# PATCH_CREAS_FIX_TIMELINEUI_ANCHOR_V6

Corrige o erro em runtime: **`timelineUI is not defined`** na aba **CREAS → Casos**.

## O que faz
- Insere `var timelineUI = [];` no topo do componente `TelaCreasCasos` (antes de qualquer uso).
- Se existir `const sel = ...`, vincula `timelineUI` ao caso selecionado (`sel.timelineUI` / `sel.timeline` / etc.).
- Faz backup automático do arquivo antes de alterar.

## Como aplicar
```bash
cd ~/POPNEWS1 && unzip -o ~/Downloads/PATCH_CREAS_FIX_TIMELINEUI_ANCHOR_V6.zip -d .
bash frontend/scripts/fix_timelineui_anchor_v6.sh
cd ~/POPNEWS1/frontend && npm run build
cd ~/POPNEWS1/frontend && npm run dev
```

Se estiver com o dev server aberto, faça hard refresh no navegador (Cmd+Shift+R).
