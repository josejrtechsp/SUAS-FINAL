# PATCH_CRAS_SUBTABS_V1 (Frontend)

Objetivo: **estabilizar o padrão Apple** no CRAS (módulo piloto) com:

- Header "Você está em…" + **uma única barra de subtelas (botões)**
- Conteúdo mostrando **somente 1 subtela por vez**

Implementado nesta versão:

## 1) Encaminhamentos (subtelas)
- Filtros
- Novo
- Sem devolutiva
- Encaminhamento SUAS
- Todos

## 2) Tarefas (subtelas)
- Por técnico (seleciona o técnico e abre a fila)
- Vencidas
- Metas
- Concluir em lote

---

## Arquivos alterados
- `frontend/src/CrasApp.jsx`
- `frontend/src/components/CrasPageHeader.jsx`
- `frontend/src/components/CrasTabContextHeader.jsx` (legado, corrigido)
- `frontend/src/TelaCrasEncaminhamentos.jsx`
- `frontend/src/TelaCrasTarefas.jsx`
- `frontend/src/cras_ui_v2.css`

---

## Como aplicar (macOS)
Na raiz do seu projeto:

```bash
cd ~/POPNEWS1

# Backup rápido dos arquivos do patch
ts=$(date +%Y%m%d_%H%M%S)
mkdir -p _bak_patch_$ts/frontend/src/components
mkdir -p _bak_patch_$ts/tools

cp -f frontend/src/CrasApp.jsx _bak_patch_$ts/frontend/src/ 2>/dev/null || true
cp -f frontend/src/TelaCrasEncaminhamentos.jsx _bak_patch_$ts/frontend/src/ 2>/dev/null || true
cp -f frontend/src/TelaCrasTarefas.jsx _bak_patch_$ts/frontend/src/ 2>/dev/null || true
cp -f frontend/src/cras_ui_v2.css _bak_patch_$ts/frontend/src/ 2>/dev/null || true
cp -f frontend/src/components/CrasPageHeader.jsx _bak_patch_$ts/frontend/src/components/ 2>/dev/null || true
cp -f frontend/src/components/CrasTabContextHeader.jsx _bak_patch_$ts/frontend/src/components/ 2>/dev/null || true

# Aplicar patch (descompactar na raiz)
unzip -o PATCH_CRAS_SUBTABS_V1.zip -d .

# Verificar
bash tools/verify_cras_subtabs_v1.sh .
```

Depois:
```bash
cd ~/POPNEWS1/frontend
npm run dev
```

---

## Rollback
Se precisar reverter, use a pasta `_bak_patch_<timestamp>` criada acima:

```bash
cp -f _bak_patch_<ts>/frontend/src/CrasApp.jsx frontend/src/ 
# ...repita para os demais arquivos
```
