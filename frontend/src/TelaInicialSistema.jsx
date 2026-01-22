import React, { useMemo } from "react";
import { getSuasOverdueForModulo } from "./domain/suasEncaminhamentosStore.js";

/**
 * Tela inicial moderna do Sistema Pop Rua
 *
 * Props:
 * - pessoas: array de pessoas (do App)
 * - casos: array de casos (do App)
 * - navegar: objeto de navegação (funções) para abrir hubs e módulos
 */
export default function TelaInicialSistema({ pessoas, casos, navegar }) {
  const totalPessoas = pessoas?.length || 0;
  const totalCasos = casos?.length || 0;
  const casosEmAndamento = casos?.filter((c) => c.status !== "encerrado").length || 0;
  const casosEncerrados = totalCasos - casosEmAndamento;

  const goto = (k) => {
    if (navegar && typeof navegar[k] === "function") navegar[k]();
  };

  // ✅ Encaminhamentos SUAS (internos) com prazo vencido (localStorage)
  const suasOverdue = useMemo(() => getSuasOverdueForModulo("POPRUA"), [pessoas, casos]);
  const suasIn = useMemo(() => (suasOverdue || []).filter((x) => String(x?.destino_modulo || "").toUpperCase() === "POPRUA"), [suasOverdue]);
  const suasOut = useMemo(() => (suasOverdue || []).filter((x) => String(x?.origem_modulo || "").toUpperCase() === "POPRUA"), [suasOverdue]);

  function openSuas(view) {
    try {
      localStorage.setItem("suas_nav_modulo", "POPRUA");
      localStorage.setItem("suas_nav_view", view);
      const first = view === "inbox" ? suasIn?.[0] : suasOut?.[0];
      if (first?.id) localStorage.setItem("suas_nav_selected_id", String(first.id));
    } catch {}
    goto("encaminhamentos");
  }

  return (
    <div className="layout-1col tela-inicial-root">
      {(suasOverdue || []).length ? (
        <section
          className="card"
          style={{
            padding: 12,
            borderRadius: 16,
            marginBottom: 12,
            boxShadow: "none",
            border: "1px solid rgba(239, 68, 68, .25)",
            background: "rgba(239, 68, 68, 0.06)",
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", gap: 10, flexWrap: "wrap", alignItems: "center" }}>
            <div>
              <div style={{ fontWeight: 950 }}>⚠️ Atrasados (SUAS)</div>
              <div className="texto-suave">Encaminhamentos internos com prazo vencido (CRAS/CREAS/PopRua).</div>
              <div className="texto-suave" style={{ marginTop: 6 }}>
                Recebidos: <b>{suasIn.length}</b> · Enviados: <b>{suasOut.length}</b>
              </div>
            </div>

            <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
              {suasIn.length ? (
                <button type="button" className="btn btn-primario" onClick={() => openSuas("inbox")}>
                  Abrir Recebidos
                </button>
              ) : null}
              {suasOut.length ? (
                <button type="button" className="btn btn-primario" onClick={() => openSuas("outbox")}>
                  Abrir Enviados
                </button>
              ) : null}
              <button type="button" className="btn btn-secundario" onClick={() => goto("encaminhamentos")}>
                Abrir Encaminhamentos
              </button>
            </div>
          </div>
        </section>
      ) : null}

      {/* HERO */}
      <section className="card tela-inicial-hero">
        <div className="tela-inicial-hero-texto">
          <h1 className="tela-inicial-title">Olá, bem-vindo ao Pop Rua</h1>
          <p className="tela-inicial-subtitle">
            Acompanhe pessoas em situação de rua, organize o fluxo de casos e
            fortaleça a rede SUAS de forma simples e visual.
          </p>

          <div className="tela-inicial-cta-row">
            <button type="button" className="btn btn-primario tela-inicial-cta" onClick={() => goto("atendimento")}>
              Começar um atendimento
            </button>
            <button type="button" className="btn btn-secundario tela-inicial-cta-sec" onClick={() => goto("cadastroPessoa")}>
              Cadastrar nova pessoa
            </button>
          </div>
        </div>

        <div className="tela-inicial-metricas">
          <div className="tela-inicial-metrica">
            <div className="tela-inicial-metrica-icone">👤</div>
            <div className="tela-inicial-metrica-numero">{totalPessoas}</div>
            <div className="tela-inicial-metrica-label">Pessoas em situação de rua cadastradas</div>
          </div>

          <div className="tela-inicial-metrica">
            <div className="tela-inicial-metrica-icone">📂</div>
            <div className="tela-inicial-metrica-numero">{casosEmAndamento}</div>
            <div className="tela-inicial-metrica-label">Casos Pop Rua em andamento</div>
          </div>

          <div className="tela-inicial-metrica">
            <div className="tela-inicial-metrica-icone">✅</div>
            <div className="tela-inicial-metrica-numero">{casosEncerrados}</div>
            <div className="tela-inicial-metrica-label">Casos encerrados com registro de saída</div>
          </div>
        </div>
      </section>

      {/* GRID: passo a passo + notas SUAS */}
      <section className="tela-inicial-grid">
        {/* Passo a passo visual */}
        <div className="card tela-inicial-passos">
          <div className="card-header-row">
            <h2>Como usar o sistema no dia a dia</h2>
          </div>

          <ol className="tela-inicial-passos-lista">
            <li>
              <div className="passo-titulo">Cadastre a pessoa</div>
              <div className="passo-texto">
                Use <strong>Pessoas → Novo cadastro</strong> para registrar nome,
                município de origem, tempo de rua e local de referência.
              </div>
              <button type="button" className="btn btn-secundario btn-pequeno" onClick={() => goto("cadastroPessoa")}>
                Ir para Cadastro
              </button>
            </li>

            <li>
              <div className="passo-titulo">Abra o caso Pop Rua</div>
              <div className="passo-texto">
                Em <strong>Atendimento</strong>, selecione a pessoa e crie o caso.
                A partir daí a linha de metrô mostra o fluxo do atendimento.
              </div>
              <button type="button" className="btn btn-secundario btn-pequeno" onClick={() => goto("atendimento")}>
                Ir para Atendimento
              </button>
            </li>

            <li>
              <div className="passo-titulo">Registre os atendimentos</div>
              <div className="passo-texto">
                Em <strong>Atendimento → Ficha</strong>, registre abordagens,
                atendimentos em CRAS/CREAS, Centro POP, acolhimento etc.
              </div>
              <button type="button" className="btn btn-secundario btn-pequeno" onClick={() => goto("fichaAtendimento")}>
                Ir para Ficha
              </button>
            </li>

            <li>
              <div className="passo-titulo">Complete com família, benefícios e PIA</div>
              <div className="passo-texto">
                Utilize <strong>“Família & Benefícios”</strong> e o <strong>Protocolo do Caso</strong> para registrar redes, PIA e
                encaminhamentos intersetoriais.
              </div>
              <div className="passo-botoes">
                <button type="button" className="btn btn-secundario btn-pequeno" onClick={() => goto("familia")}>
                  Ir para Família & Benefícios
                </button>
                <button type="button" className="btn btn-secundario btn-pequeno" onClick={() => goto("protocolo")}>
                  Ir para Protocolo do Caso
                </button>
              </div>
            </li>
          </ol>
        </div>

        {/* Notas SUAS / Pop Rua compactas */}
        <div className="card tela-inicial-notas">
          <div className="card-header-row">
            <h2>Pop Rua & SUAS em poucas linhas</h2>
          </div>

          <ul className="tela-inicial-notas-lista">
            <li>
              <span className="nota-icone">📜</span>
              <div>
                <div className="nota-titulo">Base legal</div>
                <div className="nota-texto">
                  Inspirado na <strong>Política Nacional para a População em Situação de Rua</strong> (Decreto 7.053/2009) e na
                  <strong> Tipificação Nacional de Serviços Socioassistenciais</strong>.
                </div>
              </div>
            </li>

            <li>
              <span className="nota-icone">🧩</span>
              <div>
                <div className="nota-titulo">Serviços envolvidos</div>
                <div className="nota-texto">
                  Abordagem Social, Centro POP, acolhimento, CRAS/CREAS, em
                  diálogo com saúde, habitação, trabalho, justiça e outras
                  políticas.
                </div>
              </div>
            </li>

            <li>
              <span className="nota-icone">📈</span>
              <div>
                <div className="nota-titulo">Para que servem os registros</div>
                <div className="nota-texto">
                  Garantir direitos, acompanhar trajetórias e produzir
                  evidências para defesa da política pública de assistência
                  social e do consórcio.
                </div>
              </div>
            </li>

            <li>
              <span className="nota-icone">🤝</span>
              <div>
                <div className="nota-titulo">Trabalho em rede</div>
                <div className="nota-texto">
                  O sistema ajuda a enxergar a pessoa no centro, conectando os
                  registros dos municípios e dos serviços em uma mesma linha de
                  cuidado.
                </div>
              </div>
            </li>
          </ul>
        </div>
      </section>
    </div>
  );
}
