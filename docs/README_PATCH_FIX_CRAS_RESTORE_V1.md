# PATCH_FIX_CRAS_RESTORE_V1

Restaura dois arquivos do CRAS que estão quebrando o build do Vite:
- frontend/src/TelaCrasEncaminhamentos.jsx
- frontend/src/TelaCrasScfv.jsx

Uso:
1) unzip -o PATCH_FIX_CRAS_RESTORE_V1.zip -d ~/POPNEWS1
2) bash frontend/scripts/restore_cras_files_v1.sh
3) cd frontend && npm run build
