import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// SUS_SANDBOX_API_PREFIX_V1
// Problema corrigido: proxy em "/sus" intercepta a rota SPA "/sus" e devolve 404 do backend.
// Solução: API passa a usar prefixo "/api" e o proxy reescreve "/api" -> "" para o backend.
// - Rotas do FRONT continuam: /sus, /sus/gestao, ...
// - Rotas do BACK continuam: /sus/health, /sus/hub, ...
// - Chamadas do FRONT para API: /api/sus/...

const FRONTEND_PORT = Number(process.env.SUS_FRONTEND_PORT || 5174);
const BACKEND_URL = process.env.SUS_BACKEND_URL || "http://127.0.0.1:8010";

export default defineConfig({
  plugins: [react()],
  define: {
    __SUS_BACKEND_URL__: JSON.stringify(BACKEND_URL),
  },
  server: {
    port: FRONTEND_PORT,
    proxy: {
      "/api": {
        target: BACKEND_URL,
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ""),
      },
    },
  },
});
