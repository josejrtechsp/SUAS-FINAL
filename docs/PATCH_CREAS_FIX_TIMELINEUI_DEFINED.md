# PATCH_CREAS_FIX_TIMELINEUI_DEFINED_V1

Corrige erro em `CREAS → Casos`:

- `timelineUI is not defined`

O patch insere uma declaração segura de `timelineUI` dentro de `frontend/src/TelaCreasCasos.jsx`,
sem alterar a lógica do módulo, garantindo que não haverá erro de TDZ/undefined.

## Como aplicar

1) Descompacte o ZIP na raiz do projeto (POPNEWS1)
2) Rode:

```bash
bash frontend/scripts/patch_fix_timelineui_defined.sh
cd frontend && npm run build
```
