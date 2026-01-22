# POPNEWS1 — Contexto sincronizado

Este diretório contém o **log de contexto** e os **scripts de replay** do projeto POPNEWS1, para referência e auditoria.

## Arquivos copiados
- docs/popnews1_context/CONTEXT_LOG.md e CONTEXT_LOG.json — histórico dos patches aplicados
- tools/popnews1_context/replay_all_patches.sh — script para refazer o histórico de patches
- tools/popnews1_context/context_emit.sh — utilitário para listar o log
- _releases/popnews1_patches/ — cópias dos zips de patches (se localizados em ~/Downloads)

## Como reproduzir o histórico de patches no repositório de destino
```bash
cd /caminho/para/seu/repo  # ajuste para o seu repositório de destino
bash tools/popnews1_context/replay_all_patches.sh
```
