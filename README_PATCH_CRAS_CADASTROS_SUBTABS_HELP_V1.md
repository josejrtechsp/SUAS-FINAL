# PATCH_CRAS_CADASTROS_SUBTABS_HELP_V1

## Objetivo
Aplicar o padrão "produto" no CRAS → **Cadastros**:
- **Uma única barra de subtelas** no header (Você está em…)
- **Uma subtela por vez** (sem poluição)
- **Card degradê de ajuda** (recolhido) com botão **"Ver como usar"**

Subtelas:
- Pessoas
- Famílias
- Vínculos
- Atualização

## Arquivos alterados
- `frontend/src/CrasApp.jsx`
- `frontend/src/TelaCrasCadastros.jsx`

## Verificação
Inclui o script:
- `tools/verify_cras_cadastros_subtabs_help_v1.sh`

Execute:
```bash
bash tools/verify_cras_cadastros_subtabs_help_v1.sh .
```
