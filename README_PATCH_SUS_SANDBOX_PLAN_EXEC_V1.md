PATCH_SUS_SANDBOX_PLAN_EXEC_V1

Entrega:
- Gestão → Plano: árvore Programa → Ação → Meta → Indicador (com CRUD básico)
- Botão "Gerar tarefa" a partir de uma Meta (cria uma tarefa vinculada por meta_id)
- Gestão → Execução: Kanban simples (5 colunas) + criação e mudança de status
- Indicadores/Evidências: abas simples (V1) para manter o fluxo funcionando

Como aplicar:
cd ~/POPNEWS1
unzip -o ~/Downloads/PATCH_SUS_SANDBOX_PLAN_EXEC_V1.zip -d .
bash tools/verify_sus_sandbox_plan_exec_v1.sh

Depois:
- Reinicie o Vite (Ctrl+C e npm run dev -- --port 5175/5176).
- Acesse: /sus/gestao → aba Plano.
