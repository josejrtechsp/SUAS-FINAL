import React, { useEffect, useMemo, useState } from "react";
import { API_BASE } from "./config.js";

import ErrorBoundary from "./components/ErrorBoundary.jsx";
import TabHint from "./components/TabHint.jsx";
import CreasTopHeader from "./components/CreasTopHeader.jsx";

import TelaCreasPainel from "./TelaCreasPainel.jsx";
import TelaCreasNovoCaso from "./TelaCreasNovoCaso.jsx";
import TelaCreasCasos from "./TelaCreasCasos.jsx";
import TelaCreasPendencias from "./TelaCreasPendencias.jsx";
import TelaCreasAgenda from "./TelaCreasAgenda.jsx";
import TelaCreasRede from "./TelaCreasRede.jsx";
import TelaCreasDocumentos from "./TelaCreasDocumentos.jsx";
import TelaCreasRelatorios from "./TelaCreasRelatorios.jsx";
import TelaCreasConfig from "./TelaCreasConfig.jsx";

import { canAccessCreasTab } from "./domain/acl.js";
import { setCreasScope } from "./domain/creasStore.js";

export default function CreasApp({ usuarioLogado, onLogout }) {
  const [activeTab, setActiveTab] = useState(() => localStorage.getItem("creas_active_tab") || "painel");
  const [msg, setMsg] = useState("");
  const [queueNav, setQueueNav] = useState(null);

  function flash(m) {
    setMsg(m || "");
    if (!m) return;
    setTimeout(() => setMsg(""), 2600);
  }

  const [municipios, setMunicipios] = useState([]);
  const [unidades, setUnidades] = useState([]);

  const [municipioAtivoId, setMunicipioAtivoId] = useState(() => {
    const saved = localStorage.getItem("creas_municipio_ativo");
    if (saved) return saved;
    return usuarioLogado?.municipio_id ? String(usuarioLogado.municipio_id) : "";
  });

  const [unidadeAtivaId, setUnidadeAtivaId] = useState(() => localStorage.getItem("creas_unidade_ativa") || "");

  // Garante que o armazenamento do CREAS fique isolado por Município/Unidade
  setCreasScope({ municipioId: municipioAtivoId || "", unidadeId: unidadeAtivaId || "" });

  useEffect(() => {
    try {
      localStorage.setItem("creas_active_tab", activeTab);
    } catch {}
  }, [activeTab]);

  useEffect(() => {
    try {
      localStorage.setItem("creas_municipio_ativo", municipioAtivoId || "");
    } catch {}
  }, [municipioAtivoId]);

  useEffect(() => {
    try {
      localStorage.setItem("creas_unidade_ativa", unidadeAtivaId || "");
    } catch {}
  }, [unidadeAtivaId]);

  function getToken() {
    return (
      localStorage.getItem("poprua_token") ||
      localStorage.getItem("access_token") ||
      localStorage.getItem("token") ||
      ""
    );
  }

  async function apiFetch(url, options = {}) {
    const headers = new Headers(options.headers || {});
    const token = getToken();
    if (token && !headers.get("Authorization")) headers.set("Authorization", `Bearer ${token}`);

    const hasBody = options.body != null;
    const isForm = typeof FormData !== "undefined" && options.body instanceof FormData;
    if (hasBody && !isForm && !headers.get("Content-Type")) headers.set("Content-Type", "application/json");

    return fetch(url, { ...options, headers });
  }

  async function apiJson(path) {
    const res = await apiFetch(`${API_BASE}${path}`);
    const json = await res.json().catch(() => null);
    if (!res.ok) throw new Error(json?.detail || `Falha (HTTP ${res.status})`);
    return json;
  }

  useEffect(() => {
    (async () => {
      try {
        setMunicipios(await apiJson("/municipios"));
      } catch {
        setMunicipios([]);
      }
    })();
  }, []);

  useEffect(() => {
    if (!municipioAtivoId) return;
    (async () => {
      try {
        setUnidades(await apiJson(`/creas/unidades?municipio_id=${encodeURIComponent(municipioAtivoId)}`));
      } catch {
        setUnidades([]);
      }
    })();
  }, [municipioAtivoId]);

  
  const TAB_HINTS = useMemo(
    () => ({
      painel: {
        title: "Painel",
        subtitle: "Sua fila de trabalho: ativos, pendências e casos sem movimento.",
        bullets: ["Minha fila e alertas", "Risco alto e prazos", "Ações rápidas (1 clique)"],
      },
      novo: {
        title: "Novo caso",
        subtitle: "Registro rápido com risco e próximo passo (sem perder rastreabilidade).",
        bullets: ["Entrada rápida", "Risco e prioridade", "Próximo passo automático"],
      },
      casos: {
        title: "Casos",
        subtitle: "Lista + prontuário simples com linha do tempo e próximo passo.",
        bullets: ["O QUE FAZER AGORA?", "Linha de metrô por etapa", "Encaminhamentos com devolutiva"],
      },
      pendencias: {
        title: "Fila inteligente",
        subtitle: "Prioridade automática por risco, SLA, sem movimento e pendências (inclui SUAS).",
        bullets: ["Score transparente", "Filtros rápidos", "Top prioridades do dia"],
      },
      agenda: {
        title: "Agenda",
        subtitle: "Agendamentos e retornos (por técnico e por data).",
        bullets: ["Retornos sugeridos", "Lista do dia", "Sem perder prazo"],
      },
      rede: {
        title: "Rede",
        subtitle: "Encaminhamentos pendentes e retorno da rede com prazo.",
        bullets: ["Pendência de retorno", "Registrar devolutiva", "Fecha o ciclo"],
      },
      documentos: {
        title: "Documentos",
        subtitle: "Organização e anexos por caso (MVP evolutivo).",
        bullets: ["Anexos", "Modelos", "Rastreabilidade"],
      },
      relatorios: {
        title: "Relatórios",
        subtitle: "Indicadores e gestão por evidência (MVP evolutivo).",
        bullets: ["Prazos", "Risco", "Produção"],
      },
      config: {
        title: "Configurações",
        subtitle: "Workflow por município/unidade, SLAs e regras do módulo.",
        bullets: ["Workflow", "SLAs", "Padrões"],
      },
    }),
    []
  );

const TABS = useMemo(
    () => [
      { key: "painel", label: "Painel" },
      { key: "novo", label: "Novo caso" },
      { key: "casos", label: "Casos" },
      { key: "pendencias", label: "Fila inteligente" },
      { key: "agenda", label: "Agenda" },
      { key: "rede", label: "Rede" },
      { key: "documentos", label: "Documentos" },
      { key: "relatorios", label: "Relatórios" },
      { key: "config", label: "Configurações" },
    ],
    []
  );

  function portal() {
    window.location.href = "/hub";
  }

  function sair() {
    if (typeof onLogout === "function") {
      onLogout();
      return;
    }
    localStorage.removeItem("poprua_token");
    localStorage.removeItem("poprua_usuario");
    localStorage.removeItem("token");
    localStorage.removeItem("access_token");
    window.location.reload();
  }

  const canAccess = (key) => canAccessCreasTab(key, usuarioLogado);

  const setActiveTabSafe = (key) => {
    if (!canAccess(key)) {
      flash("Seu perfil não tem acesso a esta aba.");
      return;
    }
    setActiveTab(key);
  };

  // Se o usuário tiver um tab salvo no localStorage que não é do perfil dele, redireciona para a primeira aba permitida.
  useEffect(() => {
    if (canAccess(activeTab)) return;
    const firstAllowed = (TABS || []).find((t) => canAccess(t.key))?.key || "painel";
    if (firstAllowed && firstAllowed !== activeTab) setActiveTab(firstAllowed);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeTab, usuarioLogado]);

  const onNavigate = (x) => {
    if (x?.queue) {
      setQueueNav({ token: Date.now() + Math.random(), ...(x.queue || {}) });
    }
    if (x?.tab) setActiveTabSafe(x.tab);
  };

  return (
    <div className="app-root">
      <CreasTopHeader
        usuarioLogado={usuarioLogado}
        municipios={municipios}
        municipioAtivoId={municipioAtivoId}
        setMunicipioAtivoId={setMunicipioAtivoId}
        unidades={unidades}
        unidadeAtivaId={unidadeAtivaId}
        setUnidadeAtivaId={setUnidadeAtivaId}
        tabs={TABS}
        activeTab={activeTab}
        setActiveTab={setActiveTabSafe}
        onPortal={portal}
        onSair={sair}
      />

      <main className="app-main">
        <TabHint module="CREAS" title={(TAB_HINTS[activeTab]?.title) || ""} subtitle={(TAB_HINTS[activeTab]?.subtitle) || ""} bullets={(TAB_HINTS[activeTab]?.bullets) || []} />
        {activeTab === "painel" && (
          <ErrorBoundary label="CREAS · Painel">
            <>
      {msg ? (
        <div className="card" style={{ marginTop: 10, padding: 10, boxShadow: "none", border: "1px solid rgba(59,130,246,.25)", background: "rgba(59,130,246,.08)" }} role="alert">
          <b>{msg}</b>
        </div>
      ) : null}
              <div style={{ marginTop: 12 }}>
                <TelaCreasPainel
                  apiBase={API_BASE}
                  apiFetch={apiFetch}
                  apiJson={apiJson}
                  onNavigate={onNavigate}
                  usuarioLogado={usuarioLogado}
                  municipioId={municipioAtivoId || null}
                  unidadeId={unidadeAtivaId || null}
                />
              </div>
            </>
          </ErrorBoundary>
        )}

        {activeTab === "novo" && (
          <ErrorBoundary label="CREAS · Novo caso">
            <>
      {msg ? (
        <div className="card" style={{ marginTop: 10, padding: 10, boxShadow: "none", border: "1px solid rgba(59,130,246,.25)", background: "rgba(59,130,246,.08)" }} role="alert">
          <b>{msg}</b>
        </div>
      ) : null}
              <TelaCreasNovoCaso
                apiBase={API_BASE}
                apiFetch={apiFetch}
                apiJson={apiJson}
                onNavigate={onNavigate}
                municipioId={municipioAtivoId || null}
                unidadeId={unidadeAtivaId || null}
                usuarioLogado={usuarioLogado}
              />
            </>
          </ErrorBoundary>
        )}

        {activeTab === "casos" && (
          <ErrorBoundary label="CREAS · Casos">
            <>
      {msg ? (
        <div className="card" style={{ marginTop: 10, padding: 10, boxShadow: "none", border: "1px solid rgba(59,130,246,.25)", background: "rgba(59,130,246,.08)" }} role="alert">
          <b>{msg}</b>
        </div>
      ) : null}
              <TelaCreasCasos
                apiBase={API_BASE}
                apiFetch={apiFetch}
                apiJson={apiJson}
                onNavigate={onNavigate}
                municipioId={municipioAtivoId || null}
                unidadeId={unidadeAtivaId || null}
                usuarioLogado={usuarioLogado}
              />
            </>
          </ErrorBoundary>
        )}

        {activeTab === "pendencias" && (
          <ErrorBoundary label="CREAS · Pendências">
            <>
      {msg ? (
        <div className="card" style={{ marginTop: 10, padding: 10, boxShadow: "none", border: "1px solid rgba(59,130,246,.25)", background: "rgba(59,130,246,.08)" }} role="alert">
          <b>{msg}</b>
        </div>
      ) : null}
              <TelaCreasPendencias
                apiBase={API_BASE}
                apiFetch={apiFetch}
                apiJson={apiJson}
                onNavigate={onNavigate}
                usuarioLogado={usuarioLogado}
                municipioId={municipioAtivoId || null}
              queueNav={queueNav}
              />
            </>
          </ErrorBoundary>
        )}

        {activeTab === "agenda" && (
          <ErrorBoundary label="CREAS · Agenda">
            <>
      {msg ? (
        <div className="card" style={{ marginTop: 10, padding: 10, boxShadow: "none", border: "1px solid rgba(59,130,246,.25)", background: "rgba(59,130,246,.08)" }} role="alert">
          <b>{msg}</b>
        </div>
      ) : null}
              <TelaCreasAgenda
                apiBase={API_BASE}
                apiFetch={apiFetch}
                apiJson={apiJson}
                onNavigate={onNavigate}
                usuarioLogado={usuarioLogado}
                municipioId={municipioAtivoId || null}
              />
            </>
          </ErrorBoundary>
        )}

        {activeTab === "rede" && (
          <ErrorBoundary label="CREAS · Rede">
            <>
      {msg ? (
        <div className="card" style={{ marginTop: 10, padding: 10, boxShadow: "none", border: "1px solid rgba(59,130,246,.25)", background: "rgba(59,130,246,.08)" }} role="alert">
          <b>{msg}</b>
        </div>
      ) : null}
              <TelaCreasRede
                apiBase={API_BASE}
                apiFetch={apiFetch}
                apiJson={apiJson}
                onNavigate={onNavigate}
                usuarioLogado={usuarioLogado}
                municipioId={municipioAtivoId || null}
              />
            </>
          </ErrorBoundary>
        )}

        {activeTab === "documentos" && (
          <ErrorBoundary label="CREAS · Documentos">
            <>
      {msg ? (
        <div className="card" style={{ marginTop: 10, padding: 10, boxShadow: "none", border: "1px solid rgba(59,130,246,.25)", background: "rgba(59,130,246,.08)" }} role="alert">
          <b>{msg}</b>
        </div>
      ) : null}
              <TelaCreasDocumentos apiBase={API_BASE} apiFetch={apiFetch} apiJson={apiJson} municipioId={municipioAtivoId || null} />
            </>
          </ErrorBoundary>
        )}

        {activeTab === "relatorios" && (
          <ErrorBoundary label="CREAS · Relatórios">
            <>
      {msg ? (
        <div className="card" style={{ marginTop: 10, padding: 10, boxShadow: "none", border: "1px solid rgba(59,130,246,.25)", background: "rgba(59,130,246,.08)" }} role="alert">
          <b>{msg}</b>
        </div>
      ) : null}
              <TelaCreasRelatorios
                apiBase={API_BASE}
                apiFetch={apiFetch}
                apiJson={apiJson}
                usuarioLogado={usuarioLogado}
                municipioId={municipioAtivoId || null}
              />
            </>
          </ErrorBoundary>
        )}

        {activeTab === "config" && (
          <ErrorBoundary label="CREAS · Config">
            <>
      {msg ? (
        <div className="card" style={{ marginTop: 10, padding: 10, boxShadow: "none", border: "1px solid rgba(59,130,246,.25)", background: "rgba(59,130,246,.08)" }} role="alert">
          <b>{msg}</b>
        </div>
      ) : null}
              <TelaCreasConfig apiBase={API_BASE} apiFetch={apiFetch} apiJson={apiJson} municipioId={municipioAtivoId || null} />
            </>
          </ErrorBoundary>
        )}
      </main>
    </div>
  );
}