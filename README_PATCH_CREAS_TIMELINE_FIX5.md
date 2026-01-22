# PATCH_CREAS_TIMELINE_FIX5 (Safari: Can't find variable: timelineUI)

Corrige o erro atual no Safari/CREAS > Casos:
**"Can't find variable: timelineUI"**

## Causa (comportamento típico)
`timelineUI` está sendo referenciado em algum hook (ex.: dependency array) **antes** da linha onde ele é declarado como `const`.
Isso gera erro de TDZ no Safari.

## Estratégia do FIX5
- Troca `const timelineUI = useMemo(...)` por:
  - `var timelineUI = [];` (hoisted, nunca dá "Can't find variable")
  - `const timelineUIMemo = useMemo(...)`
  - `timelineUI = Array.isArray(timelineUIMemo) ? timelineUIMemo : [];`
Assim, mesmo se algum trecho tocar `timelineUI` antes, ele existe (undefined/[]) e não quebra a tela.

## Aplicar
```bash
cd ~/POPNEWS1
unzip -o ~/POPNEWS1/MÓDULOS/PATCH_CREAS_TIMELINE_FIX5.zip -d .
bash tools/apply_creas_timeline_fix5.sh
bash tools/verify_creas_timeline_fix5.sh
```

Depois reinicie o front:
```bash
rm -rf ~/POPNEWS1/frontend/node_modules/.vite
cd ~/POPNEWS1/frontend
# Ctrl+C se estiver rodando
npm run dev
```
