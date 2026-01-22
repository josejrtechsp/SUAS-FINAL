# PATCH_FIX_TIMELINEUI_CLEAN_V7

Este patch corrige o erro **"timelineUI is not defined"** na tela **CREAS → Casos**.

## O que ele faz
- Faz backup do arquivo atual `TelaCreasCasos.jsx` como `.bak_broken_YYYYMMDD_HHMMSS`
- Se detectar injeções antigas (V6) que quebraram sintaxe, restaura a partir do backup `.bak_timelineui_*` mais recente
- Insere a definição de `timelineUI` **logo após** `const sel = ...` (antes do primeiro uso)

## Como usar
```bash
cd ~/POPNEWS1
unzip -o ~/Downloads/PATCH_CREAS_FIX_TIMELINEUI_CLEAN_V7.zip -d .
bash frontend/scripts/fix_creas_timelineui_clean_v7.sh
cd frontend && npm run build
npm run dev
```

## Se você não tiver `rg` (ripgrep)
Use:
```bash
grep -n "timelineUI" frontend/src/TelaCreasCasos.jsx
```
