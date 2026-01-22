import React from "react";
import { useLocation, Navigate } from "react-router-dom";

import PopRuaApp from "./App.jsx";
import CrasApp from "./CrasApp.jsx";
import CreasApp from "./CreasApp.jsx";
import GestaoApp from "./GestaoApp.jsx";
import TerceiroSetorApp from "./TerceiroSetorApp.jsx";

export default function AppShell({ usuarioLogado, onLogout }) {
  const location = useLocation();

  const mod = React.useMemo(() => {
    const params = new URLSearchParams(location.search);
    return (params.get("mod") || localStorage.getItem("active_module") || "poprua").toLowerCase();
  }, [location.search]);

  React.useEffect(() => {
    try { localStorage.setItem("active_module", mod); } catch (e) {}
  }, [mod]);

  // Hub é uma rota própria (/hub). Se alguém abrir /app?mod=hub, redireciona.
  if (mod === "hub") return <Navigate to="/hub" replace />;

  if (mod === "cras") return <CrasApp usuarioLogado={usuarioLogado} onLogout={onLogout} />;
  if (mod === "creas") return <CreasApp usuarioLogado={usuarioLogado} onLogout={onLogout} />;
  if (mod === "gestao") return <GestaoApp usuarioLogado={usuarioLogado} onLogout={onLogout} />;
  if (mod === "terceiro_setor" || mod === "terceirosetor" || mod === "osc" || mod === "oscs") {
    return <TerceiroSetorApp usuarioLogado={usuarioLogado} onLogout={onLogout} />;
  }

  return <PopRuaApp usuarioLogado={usuarioLogado} onLogout={onLogout} />;
}
