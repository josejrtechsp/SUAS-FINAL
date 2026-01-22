import React from "react";
import "./Portal.css";

import ArtigoPage from "./ArtigoPage.jsx";
import IdealAreas from "./components/IdealAreas.jsx";

export default function PreLoginPage({ onEntrar }) {
  const u = new URL(window.location.href);
  const artigo = u.searchParams.get("artigo");

  // Qualquer artigo abre na mesma tela (modelo "Biblioteca & Artigos")
  if (artigo) return <ArtigoPage />;

  const goHub = () => {
    if (typeof onEntrar === "function") return onEntrar();
    window.location.href = "/hub";
  };

  const goAtualizacoes = () => {
    window.location.href = "/atualizacoes";
  };

  const goAreas = () => {
    const el = document.getElementById("areas");
    if (el && typeof el.scrollIntoView === "function") {
      el.scrollIntoView({ behavior: "smooth", block: "start" });
      return;
    }
    window.location.hash = "#areas";
  };

  const artigoUrl = (slug) => {
    const u2 = new URL(window.location.href);
    u2.searchParams.set("artigo", slug);
    return u2.toString();
  };

  const openArtigo = (slug) => {
    window.location.href = artigoUrl(slug);
  };

  return (
    <div className="portal3-root">
      <header className="portal3-topbar">
        <div className="portal3-topbar-inner portal3-topbarCard">
          <div className="portal3-brandRow">
            <img className="portal3-mark" src="/ideal-icon.png" alt="IDEAL" width="60" height="60" loading="eager" decoding="async" fetchPriority="high" />
            <div className="portal3-brand">
              <div className="portal3-brand-tag">PORTAL MUNICIPAL</div>
              <div className="portal3-brand-title">
                Plataforma Municipal <span className="portal3-brand-highlight">Integrada</span>
              </div>
              <div className="portal3-brand-sub">Diagnóstico → execução com dados, fluxos, SLAs e indicadores.</div>
            </div>
          </div>

          <div className="portal3-actions">
            <button className="btn btn-secundario btn-secundario-mini" type="button" onClick={goAtualizacoes}>
              Portal
            </button>
            <button className="btn btn-primario btn-primario-mini" type="button" onClick={goHub}>
              Acessar o painel
            </button>
          </div>
        </div>
      </header>

      <main className="portal3-main">
        <section className="portal3-hero">
          <div className="portal3-hero-inner">
            <div className="portal3-hero-left">
	              <h1
	                className="portal3-h1 portal3-h1Link"
	                role="link"
	                tabIndex={0}
	                onClick={() => openArtigo("diagnostico-execucao")}
	                onKeyDown={(e) => {
	                  if (e.key === "Enter" || e.key === " ") {
	                    e.preventDefault();
	                    openArtigo("diagnostico-execucao");
	                  }
	                }}
	              >
	                Do diagnóstico à execução: <span className="portal3-h1-highlight">governança de dados</span> e software para entregar resultado.
	              </h1>

	              <p
	                className="portal3-lead portal3-leadLink"
	                role="link"
	                tabIndex={0}
	                onClick={() => openArtigo("diagnostico-execucao")}
	                onKeyDown={(e) => {
	                  if (e.key === "Enter" || e.key === " ") {
	                    e.preventDefault();
	                    openArtigo("diagnostico-execucao");
	                  }
	                }}
	              >
	                Todo prefeito já viveu isso: o município faz diagnóstico, define prioridades, publica plano e anuncia metas — e, mesmo assim, a execução não acontece no
	                ritmo esperado. Quando a ponte entre <b>planejar</b> e <b>executar</b> é fraca, a política pública existe, mas se perde no caminho.
	              </p>

	              <div className="portal3-chips" aria-label="Recursos principais">
	                <button type="button" className="portal3-chip portal3-chipBtn" onClick={goAreas}>
	                  Governança de dados (LGPD)
	                </button>
	                <button type="button" className="portal3-chip portal3-chipBtn" onClick={goAreas}>
	                  Fluxo e responsabilidades
	                </button>
	                <button type="button" className="portal3-chip portal3-chipBtn" onClick={goAreas}>
	                  SLA e gargalos
	                </button>
	                <button type="button" className="portal3-chip portal3-chipBtn" onClick={goAreas}>
	                  Indicadores e painéis
	                </button>
	              </div>
            </div>

            <div className="portalV3-feature">
              <div className="portal3-feature-title">Artigo em destaque</div>
              <div className="portal3-feature-subtitle" style={{ marginTop: 6, opacity: 0.85 }}>
                Leitura curta sobre o gargalo que trava projetos: estrutura para planejar, executar e medir.
              </div>

	              <div
	                className="portal3-articleCard"
	                role="button"
	                tabIndex={0}
	                onClick={() => openArtigo("no-estrutural")}
	                onKeyDown={(e) => {
	                  if (e.key === "Enter" || e.key === " ") {
	                    e.preventDefault();
	                    openArtigo("no-estrutural");
	                  }
	                }}
	              >
                <div className="portal3-articlePill">GESTÃO MUNICIPAL</div>
                <div className="portal3-articleTitle">O Nó Estrutural da Gestão nas Prefeituras</div>
                <div className="portal3-articleDeck">Por que bons projetos travam — e o que muda quando diagnóstico vira rotina, com dados e governança.</div>
	                <div className="portal3-articleText">
	                  O problema central não é só recurso: é a estrutura (processos, sistemas e governança) que não sustenta o ciclo completo da política pública — e faz a
	                  gestão virar reativa.
	                </div>
              </div>

              {/* Preenche o “vazio” do hero com um preview visual (linha de execução) */}
              <div className="portalV3-preview">
                <div className="portal3-previewPanel" aria-label="Como a execução vira rotina">
                  <div className="portal3-previewTitle">Como a execução vira rotina</div>
                  <div className="portal3-previewLine">
                    <div className="portal3-previewStep">
                      <div className="portal3-previewDot" />
                      <div className="portal3-previewLabel">Diagnóstico</div>
                    </div>
                    <div className="portal3-previewStep">
                      <div className="portal3-previewDot" />
                      <div className="portal3-previewLabel">Plano</div>
                    </div>
                    <div className="portal3-previewStep">
                      <div className="portal3-previewDot" />
                      <div className="portal3-previewLabel">Execução</div>
                    </div>
                    <div className="portal3-previewStep">
                      <div className="portal3-previewDot" />
                      <div className="portal3-previewLabel">Indicadores</div>
                    </div>
                  </div>
                  <div className="portal3-previewNote">Fluxo + SLA + evidência em cada etapa — com visão por território, equipe e serviço.</div>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section className="portal3-section" id="areas">
          <IdealAreas />
        </section>
      </main>
    </div>
  );
}