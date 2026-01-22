# PATCH_GLOBAL_TIMELINE_GUARD_V1

Objetivo: eliminar definitivamente o erro no Safari:
**"Can't find variable: timelineUI"**

## Diagnóstico
O Vite está servindo `TelaCreasCasos.jsx` com `var timelineUI = []` corretamente, mas o Safari ainda acusa
que `timelineUI` não existe. Isso indica que **algum outro chunk/arquivo** ainda referencia `timelineUI`
como variável global livre (sem declaração), ou há resíduo de cache/rota.

## Solução (defensiva e definitiva)
Adicionar um *guard global* antes do bundle do Vite rodar, criando um binding global:

- `window.timelineUI = window.timelineUI || [];`
- `var timelineUI = window.timelineUI;`  (cria variável global acessível por identificador `timelineUI`)

Isso garante que qualquer referência solta a `timelineUI` não derrube a tela no Safari.

## Arquivo alterado
- `frontend/index.html` (inserido dentro do `<head>`)

## Aplicar
```bash
cd ~/POPNEWS1
unzip -o ~/POPNEWS1/MÓDULOS/PATCH_GLOBAL_TIMELINE_GUARD_V1.zip -d .
bash tools/apply_global_timeline_guard_v1.sh
bash tools/verify_global_timeline_guard_v1.sh
```

Depois reinicie o Vite:
```bash
# Ctrl+C
cd ~/POPNEWS1/frontend
npm run dev -- --host 127.0.0.1 --force
```

E no Safari:
- Desenvolvedor -> Esvaziar caches
- Desenvolvedor -> Desabilitar caches
- Cmd+Shift+R
