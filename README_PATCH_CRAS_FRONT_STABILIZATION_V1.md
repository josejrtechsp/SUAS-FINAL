# PATCH_CRAS_FRONT_STABILIZATION_V1

Objetivo: estabilizar o FRONT do CRAS/CREAS (Casos/Timeline) removendo causas comuns de crash
(Related: `timelineUI` em dependency array do próprio `useMemo`, e null-safety em histórico/linha do metrô no CRAS).

## O que este patch faz
1) **CREAS / Casos**
- Corrige o bug de referência circular no `useMemo`:
  - de: `useMemo(..., [sel, timelineUI])`
  - para: `useMemo(..., [sel])`
  Isso evita erro em runtime do tipo **"Cannot access 'timelineUI' before initialization"** / "timelineUI is not defined".

2) **CRAS / Casos**
- Garante null-safety no histórico:
  - troca `historicoUI.map(...)` por `(historicoUI || []).map(...)`
  - troca `!historicoUI.length` por `!(historicoUI || []).length`
- Normaliza `linhaMetroUI` antes de passar ao componente:
  - troca `linhaMetro={linhaMetroUI}` por `linhaMetro={_normalizeLinhaMetro(linhaMetroUI)}`
  - injeta helper `_normalizeLinhaMetro` no arquivo se ainda não existir

## Como aplicar (padrão POPNEWS1)
1. Copie o ZIP para `~/POPNEWS1/MÓDULOS`
2. Aplique na raiz do projeto:
   ```bash
   cd ~/POPNEWS1
   unzip -o ~/POPNEWS1/MÓDULOS/PATCH_CRAS_FRONT_STABILIZATION_V1.zip -d .
   ```
3. Rode o aplicador (ele cria backups .bak_pre_patch1_YYYYMMDDHHMMSS):
   ```bash
   cd ~/POPNEWS1
   bash tools/apply_cras_front_stabilization_v1.sh
   ```
4. Rode o verificador:
   ```bash
   cd ~/POPNEWS1
   bash tools/verify_cras_front_smoke_v1.sh
   ```

## Rollback
O aplicador cria backups ao lado dos arquivos originais com sufixo:
`.bak_pre_patch1_YYYYMMDDHHMMSS`

Para voltar, basta restaurar o backup mais recente para o nome original.

## Arquivos-alvo
- `frontend/src/TelaCreasCasos.jsx`
- `frontend/src/TelaCrasCasos.jsx`
