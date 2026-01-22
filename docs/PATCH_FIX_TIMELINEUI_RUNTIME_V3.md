# PATCH CREAS — Fix timelineUI (runtime) V3

Corrige os erros:
- `timelineUI is not defined`
- `Cannot access 'timelineUI' before initialization`

O script:
1) cria backup automático do arquivo
2) remove definições antigas quebradas de `timelineUI` (se existirem)
3) insere uma definição segura **antes do primeiro uso**.

## Como aplicar

```bash
cd ~/POPNEWS1 && unzip -o ~/Downloads/PATCH_CREAS_FIX_TIMELINEUI_RUNTIME_V3.zip -d .
bash frontend/scripts/fix_timelineui_runtime_v3.sh
cd ~/POPNEWS1/frontend && npm run build
```

Depois, reinicie o `npm run dev`.
