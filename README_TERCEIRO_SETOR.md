# Terceiro Setor (Frontend MVP) — Patch automático

Este ZIP inclui:
- Telas do módulo Terceiro Setor (OSCs, Parcerias, Plano & Metas, Precificação, Desembolso)
- Script automático que integra o módulo no seu `frontend/src/App.jsx` (sem você procurar nada).

## Aplicar
1) Unzip por cima do projeto:
   unzip -o PATCH_FRONT_TERCEIRO_SETOR_MVP_TUDO.zip

2) Rodar o script de integração:
   bash tools/APLICAR_TERCEIRO_SETOR.sh

3) Subir o front:
   cd frontend && npm run dev

## Acessar
- Via Hub (se o script conseguir inserir card automaticamente), ou
- Diretamente: ?mod=terceiro_setor
