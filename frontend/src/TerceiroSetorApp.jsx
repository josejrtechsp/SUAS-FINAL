import React, { useEffect, useMemo, useState } from "react";
import { API_BASE } from "./config.js";

import ErrorBoundary from "./components/ErrorBoundary.jsx";
import PageHero from "./components/PageHero.jsx";
import TerceiroSetorTopHeader from "./components/TerceiroSetorTopHeader.jsx";

import TelaTerceiroSetorOscs from "./TelaTerceiroSetorOscs.jsx";
import TelaTerceiroSetorParcerias from "./TelaTerceiroSetorParcerias.jsx";
import TelaTerceiroSetorPrestacao from "./TelaTerceiroSetorPrestacao.jsx";

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

export default function TerceiroSetorApp({ usuarioLogado }) {
  const [activeTab, setActiveTab] = useState(() => localStorage.getItem("terceiro_setor_active_tab") || "inicio");

  const [municipios, setMunicipios] = useState([]);
  const [municipioAtivoId, setMunicipioAtivoId] = useState(() => {
    const saved = localStorage.getItem("terceiro_setor_municipio_ativo");
    if (saved) return saved;
    return usuarioLogado?.municipio_id ? String(usuarioLogado.municipio_id) : "";
  });

  useEffect(() => {
    try { localStorage.setItem("terceiro_setor_active_tab", activeTab); } catch {}
  }, [activeTab]);

  useEffect(() => {
    try { localStorage.setItem("terceiro_setor_municipio_ativo", municipioAtivoId || ""); } catch {}
  }, [municipioAtivoId]);

  useEffect(() => {
    (async () => {
      try {
        const ms = await apiJson("/municipios");
        setMunicipios(Array.isArray(ms) ? ms : []);
      } catch {
        setMunicipios([]);
      }
    })();
  }, []);

  const municipioAtivoNome = useMemo(() => {
    const id = Number(municipioAtivoId || 0);
    const m = (municipios || []).find((x) => Number(x.id) === id);
    return m?.nome || (usuarioLogado?.municipio_nome || "");
  }, [municipios, municipioAtivoId, usuarioLogado]);

  const TABS = useMemo(
    () => [
      { key: "inicio", label: "Início" },
      { key: "oscs", label: "OSCs" },
      { key: "parcerias", label: "Parcerias" },
      { key: "prestacao", label: "Prestação de contas" },
      { key: "relatorios", label: "Relatórios" },
    ],
    []
  );

  function sair() {
    localStorage.removeItem("poprua_token");
    localStorage.removeItem("poprua_usuario");
    localStorage.removeItem("token");
    localStorage.removeItem("access_token");
    window.location.href = "/";
  }

  function portal() {
    window.location.href = "/hub";
  }

  // Mantém o topo (título + controles + abas) FIXO enquanto rola, como nos módulos CRAS/CREAS/Gestão.
  // (Sticky funciona dentro do mesmo container de scroll.)
  const headerStickyStyle = useMemo(
    () => ({
      position: "sticky",
      top: 0,
      zIndex: 80,
      backdropFilter: "blur(10px)",
      WebkitBackdropFilter: "blur(10px)",
    }),
    []
  );

  return (
    <div className="app-root">
      <div style={headerStickyStyle}>
        <TerceiroSetorTopHeader
          usuarioLogado={usuarioLogado}
          municipios={municipios}
          municipioAtivoId={municipioAtivoId}
          setMunicipioAtivoId={setMunicipioAtivoId}
          municipioAtivoNome={municipioAtivoNome}
          tabs={TABS}
          activeTab={activeTab}
          setActiveTab={setActiveTab}
          onPortal={portal}
          onSair={sair}
        />
      </div>

      <main className="app-main">
        {activeTab === "inicio" && (
          <ErrorBoundary label="Terceiro Setor · Início">
            <>
              <PageHero
                chip="ASSISTÊNCIA SOCIAL"
                title="Terceiro Setor"
                subtitle="Módulo para cadastro de OSCs, gestão de parcerias (MROSC), metas, monitoramento e prestação de contas — com evidências e auditoria."
                right={
                  <div className="card" style={{ padding: 14 }}>
                    <div style={{ fontWeight: 900, fontSize: 14 }}>Atalhos</div>
                    <div className="texto-suave" style={{ marginTop: 6 }}>Acesse rapidamente as rotinas do dia.</div>
                    <div style={{ display: "grid", gap: 8, marginTop: 10 }}>
                      <button className="btn btn-primario" type="button" onClick={() => setActiveTab("oscs")}>Gerenciar OSCs</button>
                      <button className="btn btn-secundario" type="button" onClick={() => setActiveTab("parcerias")}>Ver parcerias</button>
                      <button className="btn btn-secundario" type="button" onClick={() => setActiveTab("prestacao")}>Checklist de prestação</button>
                    </div>
                  </div>
                }
              >
                <div className="texto-suave">
                  O objetivo é deixar tudo <b>rastreável</b>: metas → execução → evidências → relatórios → auditoria.
                  Se algum endpoint ainda não estiver ativo no back-end, a tela continua abrindo e mostra o aviso de integração.
                </div>
              </PageHero>

              <div className="layout-2col" style={{ marginTop: 10 }}>
                <div className="card">
                  <div className="card-header-row">
                    <h2 style={{ margin: 0 }}>Como o módulo funciona</h2>
                  </div>
                  <div className="texto-suave">
                    <ol style={{ marginTop: 8, paddingLeft: 18 }}>
                      <li><b>OSCs</b>: cadastro, documentos e contatos.</li>
                      <li><b>Parcerias</b>: termo/convênio, objeto, metas, cronograma e valores.</li>
                      <li><b>Prestação</b>: checklist, anexos, relatórios e pareceres.</li>
                      <li><b>Relatórios</b>: visão por OSC, por parceria e por período.</li>
                    </ol>
                  </div>
                </div>

                <div className="card">
                  <div className="card-header-row">
                    <h2 style={{ margin: 0 }}>Próximos passos</h2>
                  </div>
                  <div className="texto-suave">
                    <ul style={{ marginTop: 8, paddingLeft: 18 }}>
                      <li>Conectar endpoints do back-end (OSCs / Parcerias / Prestação).</li>
                      <li>Adicionar anexos por item do checklist (PDF/Imagem).</li>
                      <li>Gerar relatórios (execução do objeto e execução financeira).</li>
                    </ul>
                  </div>
                </div>
              </div>
            </>
          </ErrorBoundary>
        )}

        {activeTab === "oscs" && (
          <ErrorBoundary label="Terceiro Setor · OSCs">
            <TelaTerceiroSetorOscs apiBase={API_BASE} apiFetch={apiFetch} municipioId={municipioAtivoId || null} />
          </ErrorBoundary>
        )}

        {activeTab === "parcerias" && (
          <ErrorBoundary label="Terceiro Setor · Parcerias">
            <TelaTerceiroSetorParcerias apiBase={API_BASE} apiFetch={apiFetch} municipioId={municipioAtivoId || null} />
          </ErrorBoundary>
        )}

        {activeTab === "prestacao" && (
          <ErrorBoundary label="Terceiro Setor · Prestação de contas">
            <TelaTerceiroSetorPrestacao municipioId={municipioAtivoId || null} />
          </ErrorBoundary>
        )}

        {activeTab === "relatorios" && (
          <ErrorBoundary label="Terceiro Setor · Relatórios">
            <div className="card card-wide">
              <div className="card-header-row">
                <h2 style={{ margin: 0 }}>Relatórios</h2>
              </div>
              <div className="texto-suave">
                Nesta etapa vamos ligar os relatórios ao back-end (por parceria, por OSC e por período) e permitir exportar PDF/CSV.
              </div>
              <div style={{ marginTop: 12, display: "grid", gap: 10 }}>
                <div className="card" style={{ padding: 14 }}>
                  <div style={{ fontWeight: 900 }}>Execução do objeto</div>
                  <div className="texto-suave" style={{ marginTop: 6 }}>Resumo de metas, entregas, evidências e ocorrências.</div>
                </div>
                <div className="card" style={{ padding: 14 }}>
                  <div style={{ fontWeight: 900 }}>Execução financeira</div>
                  <div className="texto-suave" style={{ marginTop: 6 }}>Valores previstos x realizados, conciliação e documentos.</div>
                </div>
              </div>
            </div>
          </ErrorBoundary>
        )}
      </main>
    </div>
  );
}
