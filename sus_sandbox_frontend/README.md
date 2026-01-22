# SUS Sandbox (Frontend)

## Rodar (macOS)
```bash
cd sus_sandbox_frontend
npm install
npm run dev
```

Acesse:
- http://localhost:5174

O Vite está configurado com proxy:
- Tudo que for `GET/POST /sus/*` será encaminhado para o backend em `http://127.0.0.1:8009`
