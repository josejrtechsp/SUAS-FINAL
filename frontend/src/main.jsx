import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter, Routes, Route, Navigate, useNavigate, useLocation, useParams } from "react-router-dom";

import "./App.css";
import ErrorBoundary from "./components/ErrorBoundary.jsx";

// ✅ LCP: a página inicial (PreLogin) é a primeira rota e define o LCP.
// Para reduzir o LCP em mobile (evitar 1 request extra em rede lenta),
// carregamos PreLoginPage de forma "eager" (sem React.lazy).
import PreLoginPage from "./PreLoginPage.jsx";

// ⚡ Code-splitting de rotas/páginas (mantém o app leve após a home)
const AppShell = React.lazy(() => import("./AppShell.jsx"));
const LoginPage = React.lazy(() => import("./LoginPage.jsx"));
const SuasHubPage = React.lazy(() => import("./SuasHubPage.jsx"));
const AtualizacoesPage = React.lazy(() => import("./AtualizacoesPage.jsx"));
const AtualizacaoDetalhePage = React.lazy(() => import("./AtualizacaoDetalhePage.jsx"));
const ModuloPage = React.lazy(() => import("./ModuloPage.jsx"));
const ServicePage = React.lazy(() => import("./ServicePage.jsx"));

function Loading({ label }) {
  return (
    <div style={{ padding: 16, fontSize: 14, color: "rgba(15,23,42,.75)" }}>
      Carregando {label || "página"}…
    </div>
  );
}

function LazyBoundary({ label, children }) {
  // Suspense lida com o lazy (Promise). ErrorBoundary lida com erros reais.
  return (
    <React.Suspense fallback={<Loading label={label} />}>
      <ErrorBoundary label={label}>{children}</ErrorBoundary>
    </React.Suspense>
  );
}

function PortalSlugRedirect() {
  const { slug } = useParams();
  const safe = slug ? encodeURIComponent(slug) : "";
  return <Navigate to={safe ? `/atualizacoes/${safe}` : "/atualizacoes"} replace />;
}

function RootRoutes() {
  const [usuarioLogado, setUsuarioLogado] = React.useState(null);
  const navigate = useNavigate();
  const location = useLocation();

  React.useEffect(() => {
    const token = localStorage.getItem("poprua_token");
    const userStr = localStorage.getItem("poprua_usuario");
    if (token && userStr) {
      try {
        setUsuarioLogado(JSON.parse(userStr));
      } catch {
        localStorage.removeItem("poprua_token");
        localStorage.removeItem("poprua_usuario");
        setUsuarioLogado(null);
      }
    }
  }, []);

  const params = new URLSearchParams(location.search);
  const modFromQuery = params.get("mod");
  const moduloAtual = (modFromQuery || localStorage.getItem("active_module") || "poprua").toLowerCase();

  function onLogin(usuario) {
    setUsuarioLogado(usuario);
    navigate(`/app?mod=${encodeURIComponent(moduloAtual)}`, { replace: true });
  }

  function onLogout() {
    localStorage.removeItem("poprua_token");
    localStorage.removeItem("poprua_usuario");
    localStorage.removeItem("token");
    localStorage.removeItem("access_token");
    setUsuarioLogado(null);
    navigate("/", { replace: true });
  }

  return (
    <Routes>
      <Route
        path="/"
        element={
          // Mantemos ErrorBoundary aqui (sem lazy)
          <ErrorBoundary label="PreLoginPage">
            <PreLoginPage onEntrar={() => navigate("/hub")} />
          </ErrorBoundary>
        }
      />

      <Route
        path="/servicos/:slug"
        element={
          <LazyBoundary label="ServicePage">
            <ServicePage onEntrar={() => navigate("/hub")} />
          </LazyBoundary>
        }
      />

      {/* Portal de Atualizações (interno) */}
      <Route
        path="/atualizacoes"
        element={
          <LazyBoundary label="AtualizacoesPage">
            <AtualizacoesPage onEntrar={() => navigate("/hub")} />
          </LazyBoundary>
        }
      />
      <Route
        path="/atualizacoes/:slug"
        element={
          <LazyBoundary label="AtualizacaoDetalhePage">
            <AtualizacaoDetalhePage onEntrar={() => navigate("/hub")} />
          </LazyBoundary>
        }
      />

      {/* Alias opcional: /portal -> /atualizacoes */}
      <Route path="/portal" element={<Navigate to="/atualizacoes" replace />} />
      <Route path="/portal/:slug" element={<PortalSlugRedirect />} />

      <Route
        path="/modulos/:id"
        element={
          <LazyBoundary label="ModuloPage">
            <ModuloPage onEntrar={() => navigate("/hub")} />
          </LazyBoundary>
        }
      />

      <Route
        path="/hub"
        element={
          <LazyBoundary label="SuasHubPage">
            <SuasHubPage
              onBack={() => navigate("/")}
              onSelect={(m) => {
                const mod = (m || "poprua").toLowerCase();
                localStorage.setItem("active_module", mod);
                navigate(`/login?mod=${encodeURIComponent(mod)}`);
              }}
            />
          </LazyBoundary>
        }
      />

      <Route
        path="/login"
        element={
          <LazyBoundary label="LoginPage">
            <LoginPage onLogin={onLogin} modulo={moduloAtual} onVoltar={() => navigate("/hub")} />
          </LazyBoundary>
        }
      />

      <Route
        path="/app/*"
        element={
          usuarioLogado ? (
            <LazyBoundary label="AppShell">
              <AppShell usuarioLogado={usuarioLogado} onLogout={onLogout} />
            </LazyBoundary>
          ) : (
            <Navigate to="/" replace />
          )
        }
      />

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <BrowserRouter>
      <ErrorBoundary label="RootRoutes">
        <RootRoutes />
      </ErrorBoundary>
    </BrowserRouter>
  </React.StrictMode>
);
