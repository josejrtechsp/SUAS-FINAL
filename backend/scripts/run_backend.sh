#!/usr/bin/env bash
set -euo pipefail

# Executar do backend ou de qualquer lugar:
#   bash backend/scripts/run_backend.sh
# Opcional:
#   PORT=8001 HOST=127.0.0.1 RELOAD=1 bash backend/scripts/run_backend.sh

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
BACKEND_DIR=$(cd -- "${SCRIPT_DIR}/.." && pwd)

HOST=${HOST:-127.0.0.1}
PORT=${PORT:-8001}
RELOAD=${RELOAD:-1}

cd "$BACKEND_DIR"

if [ -f .env ]; then
  set -a
  source .env
  set +a
fi

# Se o usuário setou OPENAI_API_KEY mas não setou POPRUA_OPENAI_API_KEY,
# espelha automaticamente.
if [ -n "${OPENAI_API_KEY:-}" ] && [ -z "${POPRUA_OPENAI_API_KEY:-}" ]; then
  export POPRUA_OPENAI_API_KEY="$OPENAI_API_KEY"
fi

# mata porta se estiver em uso
if command -v lsof >/dev/null 2>&1; then
  PIDS=( $(lsof -tiTCP:${PORT} -sTCP:LISTEN 2>/dev/null || true) )
  if [ ${#PIDS[@]} -gt 0 ]; then
    kill -9 "${PIDS[@]}" || true
  fi
fi

if [ -d .venv ]; then
  # shellcheck disable=SC1091
  source .venv/bin/activate
fi

if [ "$RELOAD" = "1" ]; then
  exec uvicorn app.main:app --reload --host "$HOST" --port "$PORT"
else
  exec uvicorn app.main:app --host "$HOST" --port "$PORT"
fi
