# SUS Sandbox (Backend)

## Rodar (macOS)
```bash
cd sus_sandbox_backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8009
```

Teste:
- http://127.0.0.1:8009/sus/health
- http://127.0.0.1:8009/sus/hub
