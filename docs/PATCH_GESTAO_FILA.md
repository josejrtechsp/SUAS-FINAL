# Patch — Gestão: Fila de pendências (layout profissional)

Este patch melhora o layout da "Fila de pendências" no módulo Gestão:

- botões menores e alinhados horizontalmente
- coluna de ações compacta
- hover em linhas e espaçamento mais profissional

## Como aplicar (terminal)

```bash
cd ~/POPNEWS1
unzip -o ~/Downloads/Arquivo4_gestao_fila_layout_profissional.zip -d .
chmod +x frontend/scripts/patch_gestao_fila_layout.sh
frontend/scripts/patch_gestao_fila_layout.sh
```

Depois reinicie o front:

```bash
cd ~/POPNEWS1/frontend
npm run dev
```
