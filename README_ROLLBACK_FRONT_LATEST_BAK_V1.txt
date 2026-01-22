PATCH_ROLLBACK_FRONT_LATEST_BAK_V1

O que faz:
- Restaura os arquivos do FRONT para o backup mais recente (*.bak_TIMESTAMP) de cada um:
  - frontend/src/TelaCrasEncaminhamentos.jsx
  - frontend/src/TelaCrasScfv.jsx
  - frontend/src/CrasApp.jsx
  - frontend/src/components/CrasTabContextHeader.jsx
  - frontend/src/components/CrasPageHeader.jsx

Segurança:
- Antes de restaurar, salva uma cópia do arquivo atual como *.BROKEN_TIMESTAMP.

Como usar:
1) Unzip na raiz do projeto (~/POPNEWS1)
2) Rode:
   bash tools/rollback_front_latest_bak_v1.sh
3) Reinicie o Vite:
   cd ~/POPNEWS1/frontend && npm run dev
