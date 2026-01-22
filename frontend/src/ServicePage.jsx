import React from "react";

export default function ServicePage() {
  return (
    <div className="portal3-root">
      <header className="portal3-topbar">
        <div className="portal3-topbar-inner">
          <div className="portal3-brandRow">
            <img className="portal3-logo" src="/ideal-logo-alpha.png" alt="IDEAL" />
            <div className="portal3-brand">
              <div className="portal3-brand-tag">IDEAL · INTELIGÊNCIA PÚBLICA E DE MERCADO</div>
              <div className="portal3-brand-title">
                Plataforma Municipal <span className="portal3-brand-highlight">Integrada</span>
              </div>
              <div className="portal3-brand-sub">GovTech • Pesquisa • Diagnóstico • Monitoramento • Execução</div>
            </div>
          </div>

          <div className="portal3-actions">
            <button className="btn btn-secundario btn-secundario-mini" type="button" onClick={() => window.history.back()}>
              Voltar
            </button>
          </div>
        </div>
      </header>

      <main className="portal3-main">
        <section className="portal3-section">
          <h2 className="portal3-h2">Serviço</h2>
          <p className="portal3-lead">Página em construção. Aqui ficará a leitura completa dos serviços.</p>
        </section>
      </main>
    </div>
  );
}
