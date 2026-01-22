# PATCH_CRAS_NORMALIZE_LINHAMETRO_FIX1

Corrige o erro no **CRAS > Casos**:
- `Detail: _normalizeLinhaMetro is not defined`

## O que faz
Em `frontend/src/TelaCrasCasos.jsx` (e, se existir, `frontend/frontend/src/TelaCrasCasos.jsx`):
1) Injeta o helper `_normalizeLinhaMetro` (defensivo) após os imports, se ainda não existir.
2) Troca (quando aplicável) o uso de `linhaMetro={_normalizeLinhaMetro(linhaMetroUI)}` por uma versão 100% segura:
   `linhaMetro={typeof _normalizeLinhaMetro === "function" ? _normalizeLinhaMetro(linhaMetroUI) : linhaMetroUI}`
   (evita crash mesmo se alguém remover o helper no futuro).

## Aplicar
```bash
cd ~/POPNEWS1
unzip -o ~/POPNEWS1/MÓDULOS/PATCH_CRAS_NORMALIZE_LINHAMETRO_FIX1.zip -d .
bash tools/apply_cras_normalize_linha_metro_fix1.sh
bash tools/verify_cras_normalize_linha_metro_fix1.sh
```

Depois reinicie o front:
```bash
rm -rf ~/POPNEWS1/frontend/node_modules/.vite ~/POPNEWS1/frontend/.vite
cd ~/POPNEWS1/frontend
# Ctrl+C se estiver rodando
npm run dev -- --host 127.0.0.1 --force
```
