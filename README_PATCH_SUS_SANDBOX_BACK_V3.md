PATCH_SUS_SANDBOX_BACK_V3 (BACKEND)

Foco: backend, mantendo o layout do frontend como está.

O que entra:
1) Competência em tarefas e evidências (YYYY-MM)
   - default: competência atual se não enviar
2) Prazos em tarefas (prazo YYYY-MM-DD) e cálculo de atraso (tarefa.atrasada no GET)
3) Conformidade "inteligente" (auto)
   - GET /sus/conformidade/{competencia}/itens?include_auto=1
   - gera itens automáticos para:
     - tarefas BLOQUEADAS
     - tarefas ATRASADAS
     - metas sem evidências (na competência), considerando tarefas da meta
4) Relatórios V1 (JSON)
   - GET /sus/relatorios
   - POST /sus/relatorios/gerar { tipo, competencia }
   - GET /sus/relatorios/{id}

Como aplicar:
cd ~/POPNEWS1
unzip -o ~/Downloads/PATCH_SUS_SANDBOX_BACK_V3.zip -d .
bash tools/verify_sus_sandbox_back_v3.sh

Depois:
- Reinicie o backend (uvicorn) em 8010.
- Testes:
  curl -sS http://127.0.0.1:8010/sus/hub
  curl -sS http://127.0.0.1:8010/sus/conformidade/2026-01/itens | head
  curl -sS -X POST http://127.0.0.1:8010/sus/relatorios/gerar -H 'Content-Type: application/json' -d '{"tipo":"pendencias","competencia":"2026-01"}' | head
