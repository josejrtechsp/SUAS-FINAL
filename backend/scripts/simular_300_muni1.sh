#!/usr/bin/env bash
set -euo pipefail

# Rodar a simulação (Município 1) criando DB separado
#
# Uso:
#   cd backend
#   bash scripts/simular_300_muni1.sh
#
# Opcional:
#   USERS_PER_MODULE=100 CASES_CRAS=200 CASES_CREAS=200 CASES_POPRUA=200 bash scripts/simular_300_muni1.sh

HERE="$(cd "$(dirname "$0")" && pwd)"
BACKEND_ROOT="$(cd "$HERE/.." && pwd)"

cd "$BACKEND_ROOT"

USERS_PER_MODULE="${USERS_PER_MODULE:-100}"
CASES_CRAS="${CASES_CRAS:-200}"
CASES_CREAS="${CASES_CREAS:-200}"
CASES_POPRUA="${CASES_POPRUA:-200}"
MUNICIPIO_ID="${MUNICIPIO_ID:-1}"
SEED="${SEED:-42}"
SENHA="${SENHA:-demo123}"

# DB separado (não mexe no poprua.db principal)
export POPRUA_DATABASE_URL="${POPRUA_DATABASE_URL:-sqlite:///./poprua_sim.db}"

echo "[SIM] POPRUA_DATABASE_URL=$POPRUA_DATABASE_URL"
echo "[SIM] muni=$MUNICIPIO_ID users_per_module=$USERS_PER_MODULE cases: cras=$CASES_CRAS creas=$CASES_CREAS poprua=$CASES_POPRUA seed=$SEED"

python -m app.seed_simulacao_muni1 \
  --reset-db \
  --municipio-id "$MUNICIPIO_ID" \
  --users-per-module "$USERS_PER_MODULE" \
  --cases-cras "$CASES_CRAS" \
  --cases-creas "$CASES_CREAS" \
  --cases-poprua "$CASES_POPRUA" \
  --seed "$SEED" \
  --senha "$SENHA"

echo
echo "[SIM] OK. Agora suba o backend apontando pro sim.db:"
echo "  cd backend"
echo "  source .venv/bin/activate"
echo "  POPRUA_DATABASE_URL=\"$POPRUA_DATABASE_URL\" uvicorn app.main:app --reload --host 127.0.0.1 --port 8001"
echo
echo "[SIM] Smoke test (opcional):"
echo "  python scripts/smoke_simulacao.py --api http://127.0.0.1:8001"
