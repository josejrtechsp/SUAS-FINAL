PATCH_SUS_SANDBOX_BACK_V4 (BACKEND)

Mantém o layout do frontend (básico). Evolução focada no BACK:

1) Lock por competência (status "fechada"):
   - bloqueia criação/edição/remoção em:
     - tarefas
     - evidências (upload)
     - conformidade (itens manuais)
     - importações
   - retorna HTTP 409 com mensagem clara.

2) Auditoria simples:
   - GET /sus/auditoria?limit=100

3) Fechamento de competência gera "Termo de Fechamento" automaticamente:
   - POST /sus/competencias/{YYYY-MM}/fechar
   - retorna { competencia, termo_evidencia }
   - termo é TXT salvo em uploads e acessível via /sus/files/{id}/...

4) Download de relatórios:
   - GET /sus/relatorios/{id}/download?format=json|csv

Como aplicar:
cd ~/POPNEWS1
unzip -o ~/Downloads/PATCH_SUS_SANDBOX_BACK_V4.zip -d .
bash tools/verify_sus_sandbox_back_v4.sh

Depois:
- Reinicie o backend (uvicorn) em 8010.
