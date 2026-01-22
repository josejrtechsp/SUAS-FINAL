SUS_SANDBOX_V1

Este ZIP cria um ambiente ISOLADO dentro do seu repositório (sem mexer no sistema atual):
- sus_sandbox_frontend/  (Vite+React, porta 5174)
- sus_sandbox_backend/   (FastAPI, porta 8009)

Como aplicar:
1) Copie o ZIP para ~/POPNEWS1/MÓDULOS
2) Na raiz do projeto:
   cd ~/POPNEWS1
   unzip -o "$HOME/POPNEWS1/MÓDULOS/SUS_SANDBOX_V1.zip" -d .

Como rodar:
- Backend:
  cd sus_sandbox_backend
  python3 -m venv .venv && source .venv/bin/activate
  pip install -r requirements.txt
  uvicorn app.main:app --reload --port 8009

- Frontend:
  cd sus_sandbox_frontend
  npm install
  npm run dev

Abrir:
- http://localhost:5174

Integração futura (acoplar no sistema principal):
- Copiar `sus_sandbox_frontend/src/sus` -> `frontend/src/sus`
- Copiar `sus_sandbox_backend/app/routers/sus.py` -> `backend/app/routers/sus.py`
- Ligar rotas no App.jsx e incluir router no main.py
