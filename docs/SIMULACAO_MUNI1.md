# Simulação — Município 1 (300 usuários + 200/200/200 casos)

Objetivo: popular o sistema com dados realistas e **forçar erros/vácuos**.

## O que é criado
- **300 usuários** (município 1)
  - CRAS: 100
  - CREAS: 100
  - PopRua: 100
  - Perfis (distribuição): técnico, recepção, leitura, coord/secretário
- **Casos**
  - CRAS: 200 (com PIA faltando, CadÚnico pendente, tarefas vencidas, validações pendentes)
  - CREAS: 200
  - PopRua: 200 pessoas + 200 casos
- **Rede**
  - Encaminhamentos CRAS: 40
  - Intermunicipais: 30
- **OSC**
  - 1 OSC + parceria + prestações de contas em atraso

## Rodar (DB separado)
```bash
cd ~/POPNEWS1/backend
source .venv/bin/activate

bash scripts/simular_300_muni1.sh
```

Isso gera:
- `backend/poprua_sim.db`
- `backend/storage/sim/muni1_<run_id>_users.json` (credenciais)

## Subir o backend apontando para o DB simulado
```bash
cd ~/POPNEWS1/backend
source .venv/bin/activate
POPRUA_DATABASE_URL="sqlite:///./poprua_sim.db" uvicorn app.main:app --reload --host 127.0.0.1 --port 8001
```

## Smoke test (relatório de bugs + vácuos)
```bash
cd ~/POPNEWS1/backend
source .venv/bin/activate
python scripts/smoke_simulacao.py --api http://127.0.0.1:8001
```

O relatório sai em:
- `backend/storage/sim/reports/muni1_<run_id>_smoke.md`
- `backend/storage/sim/reports/muni1_<run_id>_smoke.json`
