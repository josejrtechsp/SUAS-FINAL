#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

echo ">> Verificando padrão ouro do CREAS (sem alert/prompt/confirm)..."

# Alvo: CREAS + Encaminhamentos SUAS (componente compartilhado)
FILES=()
while IFS= read -r -d '' f; do FILES+=("$f"); done < <(find "$ROOT/src" -maxdepth 1 -type f -name "CreasApp.jsx" -print0)
while IFS= read -r -d '' f; do FILES+=("$f"); done < <(find "$ROOT/src" -maxdepth 1 -type f -name "TelaCreas*.jsx" -print0)
FILES+=("$ROOT/src/components/EncaminhamentosSuas.jsx")

PAT='alert\(|prompt\(|confirm\(|window\.alert|window\.prompt|window\.confirm'

HITS=$(grep -RInE -- "${PAT}" "${FILES[@]}" || true)
if [[ -n "${HITS}" ]]; then
  echo "ERRO: ainda existem chamadas proibidas (alert/prompt/confirm):"
  echo "${HITS}"
  exit 1
fi

echo ">> Verificando CSS do modal (position: fixed)..."
CSS="$ROOT/src/App.css"
if ! grep -n "modal-backdrop" "$CSS" >/dev/null 2>&1; then
  echo "ERRO: não encontrei bloco de modal no App.css"
  exit 1
fi
# Checa se o bloco do modal contém position: fixed em uma janela próxima
if ! awk 'BEGIN{ok=0} /\.modal-backdrop/{w=12} {if(w>0){if($0~"position: fixed"){ok=1} w--}} END{exit ok?0:1}' "$CSS"; then
  echo "ERRO: modal-backdrop/modal-overlay não está com position: fixed (overlay)."
  exit 1
fi

echo "✅ OK: CREAS padrão ouro validado."
