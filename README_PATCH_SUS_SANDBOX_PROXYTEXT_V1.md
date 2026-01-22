PATCH_SUS_SANDBOX_PROXYTEXT_V1

O que corrige:
- Atualiza o texto da Home do SUS Sandbox que estava fixo em (5174 -> 8009).
- Agora o texto mostra o origin real do navegador e o backend configurado (SUS_BACKEND_URL).

Inclui:
- sus_sandbox_frontend/vite.config.js (expondo __SUS_BACKEND_URL__)
- sus_sandbox_frontend/src/App.jsx (texto dinâmico)

Como aplicar:
cd ~/POPNEWS1
unzip -o ~/Downloads/PATCH_SUS_SANDBOX_PROXYTEXT_V1.zip -d .

Depois reinicie o frontend (Vite) para carregar as mudanças.
