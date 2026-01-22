# PATCH_CREAS_LAYOUT_V5_FIX4 (Timeline Safari crash)

Corrige o crash atual no Safari:
**"Can't find variable: timelineUICalc"**

## Causa
O arquivo `TelaCreasCasos.jsx` ficou com referência a `timelineUICalc` em algum ponto fora do escopo correto.
Para eliminar a classe inteira de erros, este patch remove o padrão `timelineUICalc` e volta ao modelo simples:

- `const timelineUI = useMemo(..., [sel]);`
- sem variáveis intermediárias
- sem atribuições extras

## O que este patch faz
Em `frontend/src/TelaCreasCasos.jsx`:
1) Converte `const timelineUICalc = useMemo(...)` -> `const timelineUI = useMemo(...)`
2) Remove qualquer linha/bloco relacionado ao FIX anterior:
   - `let timelineUI = [];` (injetado)
   - marcadores `FIX_CREAS_TIMELINEUI_V5`
   - linhas `timelineUI = Array.isArray(timelineUICalc) ...`
3) Remove qualquer ocorrência de `[sel, timelineUI]` (vira `[sel]`)
4) Garante que não reste `timelineUICalc` no arquivo.

## Aplicar
```bash
cd ~/POPNEWS1
unzip -o ~/POPNEWS1/MÓDULOS/PATCH_CREAS_LAYOUT_V5_FIX4.zip -d .
bash tools/apply_creas_layout_v5_fix4.sh
bash tools/verify_creas_layout_v5_fix4.sh
```

Depois reinicie o front:
```bash
rm -rf ~/POPNEWS1/frontend/node_modules/.vite
cd ~/POPNEWS1/frontend
# Ctrl+C se estiver rodando
npm run dev
```
