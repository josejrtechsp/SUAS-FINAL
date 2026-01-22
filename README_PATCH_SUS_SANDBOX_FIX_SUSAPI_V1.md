PATCH_SUS_SANDBOX_FIX_SUSAPI_V1

Corrige:
- Tela "Gestão" em branco com erro: "susApi.listProgramas is not a function"
- Ajusta o susApi completo (V2) para usar o prefixo /api/sus (proxy do Vite), evitando conflito com rotas SPA /sus.
- Normaliza URLs de arquivos (/sus/files/...) para (/api/sus/files/...) via proxy.

Como aplicar:
cd ~/POPNEWS1
unzip -o ~/Downloads/PATCH_SUS_SANDBOX_FIX_SUSAPI_V1.zip -d .
bash tools/verify_sus_sandbox_fix_susapi_v1.sh

Depois:
- Reinicie o Vite (Ctrl+C e npm run dev -- --port 5175/5176).
- Reabra: /sus/gestao
