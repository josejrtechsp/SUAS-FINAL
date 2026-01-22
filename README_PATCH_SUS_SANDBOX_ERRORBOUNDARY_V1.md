PATCH_SUS_SANDBOX_ERRORBOUNDARY_V1

Corrige/ajuda a diagnosticar: "Gestão" (ou outra rota) aparece em branco.

O que faz:
- Adiciona ErrorBoundary para capturar erros de runtime e mostrar na tela o motivo,
  em vez de ficar em branco.
- Embrulha as rotas principais com o ErrorBoundary.

Como aplicar:
cd ~/POPNEWS1
unzip -o ~/Downloads/PATCH_SUS_SANDBOX_ERRORBOUNDARY_V1.zip -d .
bash tools/verify_sus_sandbox_errorboundary_v1.sh

Depois:
- Reinicie o Vite (frontend).
- Abra /sus/gestao e, se houver erro, ele aparece na tela e no Console.
