# SUS Sandbox Backend V2

Agora o sandbox tem persistência local em JSON:
- `app/data/sus_db.json`

Uploads de evidência:
- arquivos ficam em `app/uploads/`
- são servidos em `http://127.0.0.1:8009/sus/files/<arquivo>`

Endpoints principais:
- Plano: `/sus/plano/programas`, `/sus/plano/acoes`, `/sus/plano/metas`, `/sus/plano/indicadores`
- Execução: `/sus/tarefas`
- Evidências: `/sus/evidencias`, `/sus/evidencias/upload` (multipart)
- Competências: `/sus/competencias`, `/sus/competencias/{YYYY-MM}/abrir|fechar`
- Conformidade: `/sus/conformidade/{YYYY-MM}/itens`
- Importações: `/sus/importacoes` (mínimo)
- Relatórios: `/sus/relatorios`, `/sus/relatorios/gerar`
