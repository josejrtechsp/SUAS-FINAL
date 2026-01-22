# PATCH – Fix CREAS/Casos: timelineUI

Este patch resolve o erro em runtime:

- `timelineUI is not defined`
- e evita quebrar build, restaurando primeiro o último backup criado pelos fixes anteriores.

## Como aplicar

1. Descompacte o ZIP na raiz do projeto (~/POPNEWS1)
2. Rode:

```bash
bash frontend/scripts/fix_creas_casos_restore_and_define_timelineui.sh
```

3. Valide:

```bash
cd frontend && npm run build
```
