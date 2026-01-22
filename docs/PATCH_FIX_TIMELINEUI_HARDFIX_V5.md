# PATCH_CREAS_FIX_TIMELINEUI_HARDFIX_V5

Corrige o erro em runtime na aba **CREAS → Casos**:

- `timelineUI is not defined` (ou variantes)

## O que faz
- Backup do arquivo `frontend/src/TelaCreasCasos.jsx`
- Insere uma definição segura de `timelineUI` **logo após a declaração de `sel`**, com fallback para:
  - `sel.timelineUI`
  - `sel.timeline`
  - `sel.linha_tempo`
  - `sel.historico`
  - `[]`

## Como aplicar
```bash
cd ~/POPNEWS1 && unzip -o ~/Downloads/PATCH_CREAS_FIX_TIMELINEUI_HARDFIX_V5.zip -d .
bash frontend/scripts/fix_timelineui_hardfix_v5.sh
cd ~/POPNEWS1/frontend && npm run build
cd ~/POPNEWS1/frontend && npm run dev
```

Depois, faça hard refresh no navegador (Ctrl+Shift+R).
