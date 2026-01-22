PATCH_SUS_SANDBOX_V2

Atualiza o SUS Sandbox para V2 (funcional):
- Backend com persistência local em JSON (app/data/sus_db.json)
- CRUD: programas, ações, metas, indicadores
- CRUD: tarefas + status/bloqueio
- Upload de evidências (multipart) e servidor de arquivos em /sus/files/*
- Competências (abrir/fechar) e checklist de conformidade por área (itens padrão + custom)
- Importações (registro mínimo) e Relatórios (geração mínima)

Como aplicar:
1) Coloque o ZIP no local que você usa (ou rode direto do Downloads)
2) Na raiz do projeto:
   cd ~/POPNEWS1
   unzip -o ~/Downloads/PATCH_SUS_SANDBOX_V2.zip -d .

Rodar:
- Backend:
  cd sus_sandbox_backend
  python3 -m venv .venv
  source .venv/bin/activate
  pip install -r requirements.txt
  uvicorn app.main:app --reload --port 8009

- Frontend:
  cd sus_sandbox_frontend
  npm install
  npm run dev -- --port 5174
