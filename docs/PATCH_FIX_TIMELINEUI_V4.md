PATCH FIX TIMELINEUI V4
======================

Objetivo:
- Reverter a alteração que quebrou o build (restore do backup .bak_timelineui_* mais recente)
- Inserir uma definição segura de `timelineUI` logo após `const sel = ...` (ou equivalente),
  evitando `timelineUI is not defined` em runtime.

Como aplicar:
  cd ~/POPNEWS1
  unzip -o ~/Downloads/PATCH_CREAS_FIX_TIMELINEUI_V4.zip -d .
  bash frontend/scripts/fix_timelineui_v4.sh
  cd ~/POPNEWS1/frontend && npm run build

O script faz backup adicional antes de mexer.
