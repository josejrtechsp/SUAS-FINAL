# PATCH_CRAS_FRONT_STABILIZATION_V2

Este patch é um **hotfix** para eliminar o erro na tela **CREAS > Casos**:
**"Can't find variable: timelineUI"** (Safari) / ReferenceError.

## Causa (real)
No arquivo `frontend/src/TelaCreasCasos.jsx` havia (ou pode haver) uma dependência circular no próprio `useMemo`:
`useMemo(..., [sel, timelineUI])`

Isso faz o runtime avaliar `timelineUI` **antes** da própria declaração existir, gerando ReferenceError.

## O que este patch faz
1) Em `TelaCreasCasos.jsx`:
- substitui **qualquer ocorrência** de `[sel, timelineUI]` por `[sel]` (robusto contra variações de espaçamento/linhas).
- também substitui `}, [ sel , timelineUI ]);` (variações) por `}, [sel]);`.

2) Mantém o patch V1 para CRAS (`TelaCrasCasos.jsx`) **sem mudanças** (null-safety + normalização de linhaMetro).

## Aplicação
```bash
cd ~/POPNEWS1
unzip -o ~/POPNEWS1/MÓDULOS/PATCH_CRAS_FRONT_STABILIZATION_V2.zip -d .
bash tools/apply_cras_front_stabilization_v2.sh
bash tools/verify_cras_front_smoke_v2.sh
```

## Observação importante
Depois de aplicar, reinicie o dev server do front (se estiver rodando):
- pare com Ctrl+C e rode `npm run dev` de novo.
