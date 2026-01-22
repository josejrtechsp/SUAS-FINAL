# Patch (Gestão → Fila): ocupar espaço + identidade visual

Este patch:
- Aumenta a largura do conteúdo da Gestão (maxWidth 980 → 1180) para reduzir o "vazio" lateral.
- Corrige os botões da coluna Ações para usar as cores do sistema (roxo/índigo):
  - **Abrir** = primário (gradiente)
  - **Cobrar/Ofício** = secundário com destaque (índigo)
  - **Relatório** = secundário mini
- Mantém as alterações restritas à **Gestão**.

## Aplicação (terminal)

```bash
cd ~/POPNEWS1
unzip -o ~/Downloads/Arquivo4_gestao_fila_fill_colors.zip -d .
chmod +x frontend/scripts/patch_gestao_fila_fill_colors.sh
frontend/scripts/patch_gestao_fila_fill_colors.sh

cd frontend
npm run dev
```
