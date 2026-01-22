PATCH_SUS_SANDBOX_API_PREFIX_V1

Corrige: abrir http://localhost:5175/sus retornando {"detail":"Not Found"}.

Causa:
- O Vite estava com proxy em "/sus", e isso intercepta a rota SPA "/sus" (frontend),
  enviando para o backend, que não tem endpoint "/sus" (tem /sus/hub, /sus/health...).

Solução:
- API passa a usar prefixo "/api".
- Proxy do Vite vira "/api" -> BACKEND_URL (com rewrite removendo "/api").
- Rotas do frontend continuam em "/sus".

Arquivos alterados:
- sus_sandbox_frontend/vite.config.js
- sus_sandbox_frontend/src/sus/susApi.js
- sus_sandbox_frontend/src/App.jsx

Como aplicar:
cd ~/POPNEWS1
unzip -o ~/Downloads/PATCH_SUS_SANDBOX_API_PREFIX_V1.zip -d .

Depois:
1) Pare e suba o frontend novamente (Ctrl+C e npm run dev).
2) Teste:
   - http://localhost:5175/sus           (deve abrir o app)
   - http://localhost:5175/api/sus/health (deve mostrar JSON)
