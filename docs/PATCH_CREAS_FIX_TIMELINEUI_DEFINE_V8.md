# PATCH_CREAS_FIX_TIMELINEUI_DEFINE_V8

Este patch corrige o erro runtime `timelineUI is not defined` no módulo CREAS (TelaCreasCasos.jsx).

## Como aplicar
1. Descompacte o zip na raiz do projeto (~/POPNEWS1):
   unzip -o ~/Downloads/PATCH_CREAS_FIX_TIMELINEUI_DEFINE_V8.zip -d .

2. Rode o script:
   bash frontend/scripts/fix_creas_timelineui_define_v8.sh

3. Valide:
   cd frontend && npm run build
   cd frontend && npm run dev

Se quiser reverter, use o backup gerado no mesmo diretório do arquivo.
