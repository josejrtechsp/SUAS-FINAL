# PATCH_CREAS_LAYOUT_V5_FIX3

Correção pontual do FIX2: o verify falhou apenas porque não encontrou a string exata do `maxHeight`.
Este FIX3 força (de forma robusta) a lista da esquerda (card `creas-casos-list`) a ter:

- `maxHeight: "calc(100vh - 270px)"`
- `overflow: "auto"`

## Aplicar
```bash
cd ~/POPNEWS1
unzip -o ~/POPNEWS1/MÓDULOS/PATCH_CREAS_LAYOUT_V5_FIX3.zip -d .
bash tools/apply_creas_layout_v5_fix3.sh
bash tools/verify_creas_layout_v5_fix3.sh
```

Depois reinicie o front (se precisar):
```bash
rm -rf ~/POPNEWS1/frontend/node_modules/.vite
cd ~/POPNEWS1/frontend
npm run dev
```
