# PATCH_CRAS_FRONT_STABILIZATION_V3 (HOTFIX)

Objetivo: eliminar o crash do Safari/React em **CREAS > Casos**:
- "Can't find variable: timelineUI"

## O que este patch faz (robusto)
No arquivo `frontend/src/TelaCreasCasos.jsx`, ele garante que **timelineUI sempre exista e seja um array**.

Ele cobre 2 cenários comuns:
1) Existe `const timelineUI = useMemo(...)` mas há dependência circular / uso antes da inicialização:
   - Renomeia a declaração para `timelineUICalc` (mantém o useMemo intacto)
   - Remove qualquer `[sel, timelineUI]` do dependency array (vira `[sel]`)
   - Cria a linha: `const timelineUI = Array.isArray(timelineUICalc) ? timelineUICalc : [];`
     logo após o bloco do useMemo.
2) Não existe nenhuma declaração de `timelineUI` no arquivo:
   - Injeta `const timelineUI = [];` em local seguro (após os imports)

> Resultado: não existe mais ReferenceError e a tela renderiza mesmo que a timeline esteja vazia.

## Como aplicar
```bash
cd ~/POPNEWS1
unzip -o ~/POPNEWS1/MÓDULOS/PATCH_CRAS_FRONT_STABILIZATION_V3.zip -d .
bash tools/apply_cras_front_stabilization_v3.sh
bash tools/verify_cras_front_smoke_v3.sh
```

## Observação
Após aplicar, reinicie o `npm run dev` do front.
