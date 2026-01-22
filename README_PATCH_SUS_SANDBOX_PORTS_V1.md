PATCH_SUS_SANDBOX_PORTS_V1

O que este patch faz:
- Atualiza o proxy do Vite do sandbox SUS para NÃO depender da porta 8009.
- Agora o padrão é:
  - Backend: 8010
  - Frontend: 5174
- E permite configurar por variáveis de ambiente:
  - SUS_BACKEND_URL (ex.: http://127.0.0.1:8011)
  - SUS_FRONTEND_PORT (ex.: 5175)

Como aplicar:
1) Copie o ZIP para ~/POPNEWS1/MÓDULOS (ou use ~/Downloads).
2) Na raiz do projeto:
   cd ~/POPNEWS1
   unzip -o ~/Downloads/PATCH_SUS_SANDBOX_PORTS_V1.zip -d .

Como rodar (recomendado):
- Backend:
  cd ~/POPNEWS1/sus_sandbox_backend
  source .venv/bin/activate
  uvicorn app.main:app --reload --port 8010

- Frontend:
  cd ~/POPNEWS1/sus_sandbox_frontend
  npm run dev -- --port 5174

Abrir:
- http://localhost:5174/sus
