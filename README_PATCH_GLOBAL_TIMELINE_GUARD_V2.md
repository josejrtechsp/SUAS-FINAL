# PATCH_GLOBAL_TIMELINE_GUARD_V2

Corrige o erro atual no navegador:
- **"timelineUIMemo is not defined"**
e reforça o guard anterior do Safari:
- **"Can't find variable: timelineUI"**

## O que faz
Atualiza `frontend/index.html` para criar bindings globais (antes do Vite carregar):

- `window.timelineUI = window.timelineUI || [];`
- `window.timelineUIMemo = window.timelineUIMemo || [];`
- `var timelineUI = window.timelineUI;`
- `var timelineUIMemo = window.timelineUIMemo;`

Isso impede crash caso exista alguma referência solta a `timelineUI`/`timelineUIMemo` em qualquer chunk.

## Aplicar
```bash
cd ~/POPNEWS1
unzip -o ~/POPNEWS1/MÓDULOS/PATCH_GLOBAL_TIMELINE_GUARD_V2.zip -d .
bash tools/apply_global_timeline_guard_v2.sh
bash tools/verify_global_timeline_guard_v2.sh
```

Depois reinicie o Vite:
```bash
# Ctrl+C
cd ~/POPNEWS1/frontend
rm -rf node_modules/.vite .vite
npm run dev -- --host 127.0.0.1 --force
```

E no Safari/Chrome: hard reload (Cmd+Shift+R).
