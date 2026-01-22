import React, { useState } from "react";

const azul = "#151a3b";
const dourado = "#c78d0a";
const fundo = "#f3f4f6";

// Hook de breakpoint para deixar tudo responsivo
function useBreakpoint() {
  const [width, setWidth] = React.useState(
    typeof window !== "undefined" ? window.innerWidth : 1024
  );

  React.useEffect(() => {
    function handleResize() {
      setWidth(window.innerWidth);
    }
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  const isMobile = width < 640;
  const isTablet = width >= 640 && width < 1024;

  return { width, isMobile, isTablet };
}

export default function App() {
  const { isMobile } = useBreakpoint();
  const [pagina, setPagina] = useState("inicio");
  const [homeView, setHomeView] = useState({ mode: "lista", artigo: null });
  const [menuAberto, setMenuAberto] = useState(false);

  function irPara(p) {
    setPagina(p);
    if (p === "inicio") {
      setHomeView({ mode: "lista", artigo: null });
    }
    setMenuAberto(false);
  }

  const itensMenu = [
    { id: "inicio", label: "Início" },
    { id: "quemSomos", label: "Quem Somos" },
    { id: "pesquisas", label: "Pesquisas" },
    { id: "servicos", label: "Serviços" },
    { id: "contato", label: "Contato" },
  ];

  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        flexDirection: "column",
        backgroundColor: fundo,
        fontFamily:
          '-apple-system, BlinkMacSystemFont, "SF Pro Text", system-ui, sans-serif',
      }}
    >
      {/* HEADER */}
      <header style={{ backgroundColor: fundo, position: "sticky", top: 0, zIndex: 20 }}>
        {/* faixinha dourada no topo */}
        <div style={{ height: 4, backgroundColor: dourado }} />

        {/* barra azul com logo + menu */}
        <div
          style={{
            boxShadow: "0 2px 4px rgba(15,23,42,0.12)",
            background: `linear-gradient(90deg, ${azul} 0%, #101528 60%, #0b1024 100%)`,
            borderBottom: `3px solid ${dourado}`,
          }}
        >
          <div
            style={{
              width: "100%",
              maxWidth: 1160,
              margin: "0 auto",
              padding: "10px 16px",
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              gap: 24,
            }}
          >
            {/* LOGO À ESQUERDA (SEM TEXTO) */}
            <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
              <img
                src="/ideal-logo.png"
                alt="Ideal Desenvolvimento Estratégico"
                style={{ height: 40, objectFit: "contain" }}
              />
            </div>

            {/* MENU DESKTOP */}
            {!isMobile && (
              <nav
                style={{
                  display: "flex",
                  gap: 24,
                  fontSize: 14,
                  color: "#e5e7eb",
                  alignItems: "center",
                }}
              >
                {itensMenu.map((item) => (
                  <button
                    key={item.id}
                    onClick={() => irPara(item.id)}
                    style={{
                      background: "transparent",
                      border: "none",
                      color: pagina === item.id ? "#ffffff" : "#e5e7eb",
                      borderBottom:
                        pagina === item.id
                          ? `2px solid ${dourado}`
                          : "2px solid transparent",
                      padding: "4px 0",
                      cursor: "pointer",
                      fontSize: 14,
                      fontWeight: pagina === item.id ? 600 : 400,
                    }}
                  >
                    {item.label}
                  </button>
                ))}
              </nav>
            )}

            {/* MENU MOBILE – ÍCONE DE 3 TRACINHOS */}
  {isMobile && (
  <button
    type="button"
    onClick={() => setMenuAberto((aberto) => !aberto)}
    aria-label="Abrir menu"
    style={{
      background: "transparent",
      border: "none",
      padding: 8,
      marginRight: 16,     // AUMENTA o espaçamento da borda
      cursor: "pointer",
      display: "flex",
      flexDirection: "column",
      gap: 5,
      alignItems: "flex-end", // garante alinhamento perfeito à direita
    }}
  >
    <span
      style={{
        width: 22,          // aumenta um pouco → mais proporcional
        height: 3,
        borderRadius: 999,
        backgroundColor: "#f9fafb",
      }}
    />
    <span
      style={{
        width: 22,
        height: 3,
        borderRadius: 999,
        backgroundColor: "#f9fafb",
      }}
    />
    <span
      style={{
        width: 22,
        height: 3,
        borderRadius: 999,
        backgroundColor: "#f9fafb",
      }}
    />
  </button>
)}
          </div>

          {/* MENU MOBILE DROPDOWN */}
          {isMobile && menuAberto && (
            <nav
              style={{
                width: "100%",
                maxWidth: 1160,
                margin: "0 auto",
                padding: "8px 16px 10px",
                borderTop: "1px solid rgba(148,163,184,0.35)",
              }}
            >
              <div
                style={{
                  display: "flex",
                  flexDirection: "column",
                  gap: 6,
                }}
              >
                {itensMenu.map((item) => (
                  <button
                    key={item.id}
                    onClick={() => irPara(item.id)}
                    style={{
                      background: "transparent",
                      border: "none",
                      textAlign: "left",
                      padding: "4px 0",
                      color: pagina === item.id ? "#ffffff" : "#e5e7eb",
                      fontSize: 14,
                      fontWeight: pagina === item.id ? 600 : 400,
                    }}
                  >
                    {item.label}
                  </button>
                ))}
              </div>
            </nav>
          )}
        </div>
      </header>

      {/* CONTEÚDO PRINCIPAL */}
      <main style={{ flex: 1, padding: "24px 12px 40px" }}>
        <div style={{ maxWidth: 1160, margin: "0 auto" }}>
          {pagina === "inicio" && (
            <HomePage view={homeView} setView={setHomeView} />
          )}
          {pagina === "quemSomos" && <QuemSomosPage />}
          {pagina === "pesquisas" && <PesquisasPage />}
          {pagina === "servicos" && <ServicosPage />}
          {pagina === "contato" && <ContatoPage />}
        </div>
      </main>

      {/* RODAPÉ */}
      <footer
        style={{
          borderTop: "1px solid #e5e7eb",
          padding: "16px 12px 20px",
          backgroundColor: "#f9fafb",
        }}
      >
        <div
          style={{
            maxWidth: 1160,
            margin: "0 auto",
            textAlign: "center",
            fontSize: 12,
            color: "#6b7280",
          }}
        >
          <div style={{ fontWeight: 600, color: azul }}>
            Ideal Desenvolvimento Estratégico
          </div>
          <div style={{ marginTop: 2 }}>
            Pesquisas eleitorais, de opinião pública, mercado e inteligência para
            gestão.
          </div>
          <div style={{ marginTop: 4, fontSize: 11 }}>
            © 2025 Ideal Desenvolvimento Estratégico — Versão demonstrativa do
            site.
          </div>
        </div>
      </footer>
    </div>
  );
}

/* ==========================
   PÁGINA INÍCIO
========================== */

function HomePage({ view, setView }) {
  const { isMobile, isTablet } = useBreakpoint();
  const [hoveredId, setHoveredId] = React.useState(null);

  // Artigo específico do HERO
  const heroArticle = {
    id: 0,
    categoria: "ANÁLISE",
    titulo:
      "Dados para entender o que as pessoas pensam e transformar em decisão de governo",
    olho:
      "Quando o gestor passa a olhar a cidade pelos olhos de quem vive nela, números deixam de ser abstração e viram bússola para as próximas decisões.",
    resumo:
      "O texto discute o papel das pesquisas de opinião e dos diagnósticos quantitativos e qualitativos na construção de políticas públicas mais realistas, territorializadas e transparentes.",
    texto1:
      "Nos últimos anos, cresceu o consenso de que não é mais possível governar apenas com base em impressões pessoais, conversas de gabinete ou leitura esporádica de redes sociais. Ao mesmo tempo, aumentou a desconfiança da população em relação a decisões que parecem tomadas de forma distante, sem diálogo. A ponte entre esses dois mundos é construída por pesquisas de opinião, diagnósticos quantitativos e escutas qualitativas que devolvem ao governante uma imagem menos filtrada da cidade.",
    texto2:
      "Quando uma prefeitura, consórcio ou empresa passa a trabalhar com dados sistemáticos sobre avaliação, prioridades, percepção de serviços e expectativas de futuro, ganha algo que a experiência cotidiana não oferece: comparabilidade. É possível observar como determinados bairros, públicos e nichos reagem de maneira diferente à mesma política ou estratégia. Não se trata de substituir a sensibilidade de quem comanda, mas de ancorá-la em evidências.",
    texto3:
      "Ao organizar esse conjunto de informações em painéis, mapas e relatórios acionáveis, a gestão deixa de ser refém do improviso. A população e os clientes passam a enxergar coerência entre discurso e prática, porque conseguem identificar que as prioridades anunciadas têm correspondência com aquilo que os dados apontam. A proposta da Ideal é exatamente essa: transformar o que as pessoas pensam em orientação concreta para definir prioridades, comunicar melhor e organizar entregas ao longo do ciclo de mandato ou de negócio.",
    resumoBox: [
      "Pesquisas de opinião complementam – e não substituem – a sensibilidade política e empresarial.",
      "Dados comparáveis por bairro, faixa etária, grupo social ou nicho de mercado permitem decisões mais justas e eficientes.",
      "Relatórios e painéis devem apontar próximos passos, e não apenas descrever a realidade observada.",
    ],
  };

  const artigos = [
    {
      id: 1,
      categoria: "MUNICÍPIOS",
      titulo: "O que a população enxerga como prioridade para 2025",
      olho:
        "Saúde, emprego e segurança aparecem na frente quando o cidadão é convidado a elencar o que espera da gestão municipal.",
      resumo:
        "Saúde, emprego e segurança seguem no topo da agenda. Pesquisas mostram onde a pressão é maior e ajudam a organizar entregas ao longo do mandato.",
      texto1:
        "O primeiro recado que aparece quando se abre o questionário para a população é direto: a cidade quer enxergar resultados concretos em saúde, geração de renda e segurança pública. Em diferentes municípios, a combinação desses três temas varia de intensidade, mas permanece no centro das respostas.",
      texto2:
        "Na prática, isso significa que gestores que desejam organizar um plano de governo para 2025 precisam olhar para além das obras isoladas. As pesquisas de opinião permitem identificar onde estão as maiores lacunas: se é a falta de médicos, a espera por especialistas, a qualidade do asfalto ou a iluminação em regiões específicas.",
      texto3:
        "Quando os resultados são traduzidos em mapas, painéis e metas claras, a prefeitura ganha uma bússola para o mandato. A Ideal atua justamente neste ponto: transformar a opinião do cidadão em informação organizada, capaz de orientar o ritmo e a ordem das entregas.",
      resumoBox: [
        "Saúde, emprego e segurança formam o núcleo das prioridades percebidas.",
        "Pesquisas mostram variações importantes entre bairros e grupos sociais.",
        "Organizar o plano de governo a partir desses dados reduz ruído político.",
      ],
    },
    {
      id: 2,
      categoria: "SERVIÇOS PÚBLICOS",
      titulo: "Avaliar atendimento não é só medir fila, é ouvir o cidadão",
      olho:
        "Tempo de espera importa, mas a experiência do usuário começa na recepção e termina quando o problema é, de fato, resolvido.",
      resumo:
        "Pesquisas de satisfação revelam desde a qualidade do acolhimento nas unidades até a clareza das informações oferecidas ao usuário.",
      texto1:
        "Por muito tempo, a avaliação de serviços públicos se resumiu a medir o tamanho da fila ou o número de senhas distribuídas. Esse olhar é importante, mas não é suficiente.",
      texto2:
        "Quando a Ideal aplica pesquisas de satisfação, o objetivo é mapear cada etapa da jornada do usuário: chegada, acolhimento, espera, comunicação, infraestrutura e solução do problema.",
      texto3:
        "O resultado é um plano de ação mais preciso, com ajustes práticos que podem ser feitos em curto prazo e impactam diretamente a percepção da população.",
      resumoBox: [
        "A experiência do usuário é composta por etapas: acolhimento, espera, atendimento e solução.",
        "Medir apenas o tempo de fila não mostra onde está o real problema.",
        "Pesquisas bem desenhadas orientam ações simples que elevam a satisfação geral.",
      ],
    },
    {
      id: 3,
      categoria: "ESTRATÉGIA",
      titulo: "Da planilha ao território: dados que viram prioridade concreta",
      olho:
        "Números ganham sentido quando são colocados em um mapa e conectados às histórias de quem vive em cada bairro.",
      resumo:
        "O trabalho da Ideal conecta números, mapas e relatos do campo para montar um quadro claro da cidade — bairro por bairro.",
      texto1:
        "Gestores lidam diariamente com relatórios, indicadores e demandas políticas. O desafio é transformar esse volume de informações em escolhas objetivas.",
      texto2:
        "Ao cruzar opinião da população, dados sociais e mapas, surgem padrões que permitem decisões mais justas e eficientes.",
      texto3:
        "Relatórios da Ideal apontam prioridades e sugerem agendas, servindo como roteiro para organizar investimentos ao longo do mandato.",
      resumoBox: [
        "Dados ganham força quando são lidos por bairro e não apenas por média da cidade.",
        "Mapa, pesquisa e trabalho de campo formam um tripé de inteligência territorial.",
        "Relatórios precisam apontar próximos passos, não só descrever a realidade.",
      ],
    },
    {
      id: 4,
      categoria: "OPINIÃO E GOVERNO",
      titulo: "Escutar cedo evita crises mais à frente",
      olho:
        "Monitorar o humor da população ao longo do mandato é mais barato do que administrar crises já instaladas.",
      resumo:
        "Pesquisa recorrente de opinião permite corrigir rotas antes que um problema vire desgaste permanente na imagem da gestão.",
      texto1:
        "Crises de imagem raramente surgem do nada. Em geral, são precedidas por sinais em pesquisas, redes sociais e contato direto com a população.",
      texto2:
        "Ao acompanhar indicadores de avaliação de governo e prioridades, é possível agir antes que o desgaste se consolide.",
      texto3:
        "A Ideal ajuda a construir esse monitoramento contínuo, transformando cada rodada de pesquisa em insumo para decisão.",
      resumoBox: [
        "Crises costumam dar sinais prévios em pesquisas e no contato com a população.",
        "Monitoramento recorrente permite correção de rota com menor custo político.",
        "Pesquisa deixa de ser fotografia isolada e vira linha do tempo do mandato.",
      ],
    },
    {
      id: 5,
      categoria: "EMPRESAS",
      titulo: "Quando o cliente fala, a estratégia muda de lugar",
      olho:
        "Estudos de mercado revelam que a concorrência muitas vezes não está onde a empresa imagina – e que o cliente enxerga coisas que o gestor não vê.",
      resumo:
        "Pesquisas de mercado e de marca ajudam empresas a identificar nichos, ajustar produtos e reposicionar comunicação com base em evidências.",
      texto1:
        "Empresas que atuam em cidades médias e pequenas costumam ter uma percepção muito intuitiva de seu público. Esse contato é valioso, mas não substitui uma escuta estruturada.",
      texto2:
        "Pesquisas de mercado realizadas pela Ideal permitem entender quais fatores realmente pesam na decisão de compra: preço, qualidade, confiança na marca, indicação de terceiros ou atendimento.",
      texto3:
        "Com essas informações, a empresa ajusta mix de produtos, preços, comunicação e posicionamento em redes sociais com base em dados, e não apenas em feeling.",
      resumoBox: [
        "Contato cotidiano com o cliente é importante, mas pode esconder padrões maiores.",
        "Pesquisas revelam quem é a concorrência real e o que pesa na decisão de compra.",
        "Estratégia comercial ganha solidez quando é desenhada a partir de dados.",
      ],
    },
    {
      id: 6,
      categoria: "INTELIGÊNCIA DE DADOS",
      titulo: "Relatório bonito não basta: é preciso ser acionável",
      olho:
        "Gráficos e tabelas são apenas o começo; o que muda a gestão é a capacidade de transformar diagnóstico em agenda de trabalho.",
      resumo:
        "Os estudos da Ideal são pensados para virar decisão prática: prioridades, mapas, agendas e metas claras para o próximo ciclo de gestão.",
      texto1:
        "Não faltam relatórios bem diagramados circulando entre gabinetes e diretorias. O problema é quando eles não se traduzem em decisões concretas.",
      texto2:
        "A Ideal parte de uma pergunta simples: o que o gestor ou a empresa precisa decidir ao final deste trabalho?",
      texto3:
        "A partir daí, o relatório é estruturado para responder a essa necessidade, com cenários, prioridades e próximos passos claros.",
      resumoBox: [
        "Relatórios cheios de gráficos, mas sem síntese, pouco ajudam na decisão.",
        "Cada estudo precisa responder a perguntas concretas do gestor.",
        "O objetivo é entregar um roteiro que acompanhe a execução das ações.",
      ],
    },
  ];

  // Tela em modo ARTIGO (hero ou cards)
  if (view.mode === "artigo" && view.artigo) {
    const a = view.artigo;

    return (
      <div style={{ display: "flex", flexDirection: "column", gap: 18 }}>
        <button
          onClick={() => setView({ mode: "lista", artigo: null })}
          style={{
            alignSelf: "flex-start",
            marginBottom: 4,
            backgroundColor: "transparent",
            border: "none",
            color: azul,
            cursor: "pointer",
            fontSize: 13,
          }}
        >
          ← Voltar para os destaques
        </button>

        <article
          style={{
            backgroundColor: "#ffffff",
            borderRadius: 12,
            border: "1px solid #e5e7eb",
            boxShadow: "0 1px 3px rgba(15,23,42,0.06)",
            overflow: "hidden",
          }}
        >
          {/* capa */}
          <div
            style={{
              height: 220,
              backgroundImage:
                'url("https://images.unsplash.com/photo-1520607162513-77705c0f0d4a?auto=format&fit=crop&w=1400&q=70")',
              backgroundSize: "cover",
              backgroundPosition: "center",
            }}
          />

          <div
            style={{
              display: "grid",
              gridTemplateColumns: isMobile
                ? "minmax(0, 1fr)"
                : "minmax(0, 2.2fr) minmax(0, 1fr)",
              gap: 22,
              padding: 24,
            }}
          >
            <div>
              <div
                style={{
                  fontSize: 12,
                  textTransform: "uppercase",
                  letterSpacing: 0.6,
                  color: "#6b7280",
                  marginBottom: 6,
                }}
              >
                {a.categoria}
              </div>
              <h1
                style={{
                  fontSize: 24,
                  margin: 0,
                  marginBottom: 8,
                  color: "#111827",
                }}
              >
                {a.titulo}
              </h1>
              <p
                style={{
                  fontSize: 14,
                  color: "#4b5563",
                  margin: 0,
                  marginBottom: 12,
                  fontWeight: 500,
                }}
              >
                {a.olho}
              </p>

              <p
                style={{
                  fontSize: 14,
                  color: "#4b5563",
                  lineHeight: 1.6,
                  marginBottom: 12,
                }}
              >
                {a.texto1}
              </p>
              <p
                style={{
                  fontSize: 14,
                  color: "#4b5563",
                  lineHeight: 1.6,
                  marginBottom: 12,
                }}
              >
                {a.texto2}
              </p>
              <p
                style={{
                  fontSize: 14,
                  color: "#4b5563",
                  lineHeight: 1.6,
                  marginBottom: 0,
                }}
              >
                {a.texto3}
              </p>
            </div>

            <aside
              style={{
                alignSelf: "flex-start",
                backgroundColor: "#f9fafb",
                borderRadius: 10,
                border: "1px solid #e5e7eb",
                padding: 14,
                fontSize: 13,
                color: "#374151",
              }}
            >
              <div
                style={{
                  fontSize: 12,
                  fontWeight: 600,
                  textTransform: "uppercase",
                  letterSpacing: 0.6,
                  marginBottom: 6,
                  color: "#6b7280",
                }}
              >
                Em resumo
              </div>
              <ul
                style={{
                  paddingLeft: 18,
                  margin: 0,
                  display: "flex",
                  flexDirection: "column",
                  gap: 4,
                }}
              >
                {a.resumoBox.map((item, idx) => (
                  <li key={idx}>{item}</li>
                ))}
              </ul>
              <p
                style={{
                  marginTop: 10,
                  marginBottom: 0,
                  fontSize: 12,
                  color: "#6b7280",
                }}
              >
                Texto demonstrativo produzido para ilustrar o estilo de análise
                baseada em pesquisas e diagnósticos realizados pela Ideal.
              </p>
            </aside>
          </div>
        </article>
      </div>
    );
  }

  // Tela em modo LISTA (hero + blocos institucionais + 6 cards)
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
      {/* HERO */}
      <section
        style={{
          backgroundColor: "#ffffff",
          borderRadius: 16,
          overflow: "hidden",
          border: "1px solid #e5e7eb",
          boxShadow: "0 6px 18px rgba(15,23,42,0.12)",
          display: "grid",
          gridTemplateColumns: isMobile
            ? "minmax(0, 1fr)"
            : "minmax(0, 1.4fr) minmax(0, 1fr)",
        }}
      >
        <div
          style={{
            minHeight: isMobile ? 200 : 260,
            backgroundImage:
              'url("https://images.unsplash.com/photo-1516321318423-f06f85e504b3?auto=format&fit=crop&w=1200&q=70")',
            backgroundSize: "cover",
            backgroundPosition: "center",
          }}
        />
        <div
          style={{
            padding: 24,
            display: "flex",
            flexDirection: "column",
          }}
        >
          <div
            style={{
              fontSize: 13,
              textTransform: "uppercase",
              letterSpacing: 0.6,
              color: "#6b7280",
              marginBottom: 6,
            }}
          >
            OPINIÃO PÚBLICA, MERCADO E GESTÃO
          </div>
          <h1
            style={{
              fontSize: 24,
              margin: 0,
              marginBottom: 8,
              color: hoveredId === heroArticle.id ? dourado : "#111827",
              lineHeight: 1.25,
              cursor: "pointer",
              transition: "color 0.15s ease",
            }}
            title={heroArticle.olho}
            onMouseEnter={() => setHoveredId(heroArticle.id)}
            onMouseLeave={() => setHoveredId(null)}
            onClick={() => setView({ mode: "artigo", artigo: heroArticle })}
          >
            Dados para entender o que as pessoas pensam e transformar em decisão
            de governo e de negócio.
          </h1>
          <p
            style={{
              fontSize: 14,
              color: "#4b5563",
              margin: 0,
              marginBottom: 10,
            }}
          >
            A Ideal Desenvolvimento Estratégico realiza pesquisas eleitorais,
            estudos de opinião, pesquisas de mercado e diagnósticos sob medida
            para prefeituras, consórcios, empresas e campanhas que precisam
            enxergar a realidade para além da percepção do gabinete ou do balcão.
          </p>
          <p
            style={{
              fontSize: 13,
              color: "#4b5563",
              margin: 0,
              marginBottom: 14,
            }}
          >
            O objetivo é simples: entregar informação confiável, em linguagem
            clara, para apoiar decisões sobre prioridades, comunicação e
            investimentos — tanto no setor público quanto no privado.
          </p>
          <button
            onClick={() => setView({ mode: "artigo", artigo: heroArticle })}
            style={{
              alignSelf: "flex-start",
              backgroundColor: azul,
              color: "#ffffff",
              borderRadius: 999,
              border: "none",
              padding: "8px 16px",
              fontSize: 13,
              cursor: "pointer",
              marginTop: "auto",
            }}
          >
            Ler análise completa
          </button>
        </div>
      </section>

            {/* QUEM É A IDEAL */}
      

{/* Bloco amarelo + cards lado a lado */}
<div
  style={{
    display: "flex",
    flexDirection: isMobile ? "column" : "row",
    gap: isMobile ? 12 : 16,
    alignItems: "stretch",
    marginBottom: 9,
  }}
>
  {/* Caixa amarela – meia tela, mais cheia e organizada */}
  <div
    style={{
      flex: 1,
      borderRadius: 12,
      padding: 18,
      backgroundColor: "#F5C145",
      boxShadow: "0 1px 3px rgba(15,23,42,0.12)",
      display: "flex",
      flexDirection: "column",
      justifyContent: "center",
    }}
  >
    {/* Label */}
    <div
      style={{
        fontSize: 11,
        fontWeight: 600,
        textTransform: "uppercase",
        letterSpacing: 0.8,
        marginBottom: 6,
        color: "#1f2933",
      }}
    >
      Diagnóstico e estratégia
    </div>

    {/* Título principal */}
    <h3
      style={{
        margin: 0,
        marginBottom: 8,
        fontSize: 18,
        fontWeight: 700,
        color: "#111827",
      }}
    >
      A Ideal transforma dados em direção para o governo e para o negócio
    </h3>

    {/* Conteúdo em duas colunas (ou uma no mobile) */}
    <div
      style={{
        display: "grid",
        gridTemplateColumns: isMobile ? "1fr" : "1.2fr 1fr",
        gap: 10,
        alignItems: "start",
      }}
    >
      {/* Texto corrido */}
      <div>
        <p
          style={{
            margin: 0,
            marginBottom: 6,
            fontSize: 13,
            lineHeight: 1.5,
            color: "#111827",
          }}
        >
          Com pesquisa de opinião, análise de base de dados e leitura de
          território, a Ideal organiza informações que normalmente estão
          dispersas em diferentes áreas da prefeitura, do consórcio ou da
          empresa.
        </p>
        <p
          style={{
            margin: 0,
            fontSize: 13,
            lineHeight: 1.5,
            color: "#111827",
          }}
        >
          O resultado é um diagnóstico que aponta prioridades, riscos e
          oportunidades de forma comparável entre bairros, territórios e
          públicos atendidos.
        </p>
      </div>

      {/* Lista de pontos fortes (preenche o lado direito) */}
      <ul
        style={{
          listStyle: "none",
          padding: 0,
          margin: 0,
          fontSize: 13,
          lineHeight: 1.5,
          color: "#111827",
        }}
      >
        <li style={{ display: "flex", gap: 6, marginBottom: 4 }}>
          <span style={{ fontSize: 14 }}>✔</span>
          <span>Integra dados administrativos, pesquisa e indicadores externos.</span>
        </li>
        <li style={{ display: "flex", gap: 6, marginBottom: 4 }}>
          <span style={{ fontSize: 14 }}>✔</span>
          <span>Entrega um quadro claro de prioridades por território e público.</span>
        </li>
        <li style={{ display: "flex", gap: 6 }}>
          <span style={{ fontSize: 14 }}>✔</span>
          <span>
            Gera base para planos, PPAs, contratos, campanhas e decisões de investimento.
          </span>
        </li>
      </ul>
    </div>
  </div>

  {/* Cards de diferenciais – meia tela ao lado (mantidos) */}
  <div
    style={{
      flex: 1,
      display: "grid",
      gridTemplateColumns: isMobile ? "1fr" : "repeat(2, minmax(0, 1fr))",
      gap: 12,
    }}
  >
    {[
      {
        icone: "🏙️",
        titulo: "Olhar territorial",
        texto:
          "Leitura por bairro, distrito, zona urbana e rural, cruzando pesquisa de opinião com dados socioeconômicos para definir onde agir primeiro.",
      },
      {
        icone: "🗣️",
        titulo: "Linguagem clara",
        texto:
          "Relatórios pensados para prefeitos, equipes técnicas e conselhos, com síntese visual, ranking de prioridades e indicação objetiva dos próximos passos.",
      },
      {
        icone: "🎯",
        titulo: "Decisão acionável",
        texto:
          "Cada estudo termina em um plano de ação com metas, indicadores, responsáveis e prazos, facilitando o acompanhamento ao longo do mandato ou projeto.",
      },
      {
        icone: "🤝",
        titulo: "Setor público e privado",
        texto:
          "Experiência com prefeituras, consórcios, empresas e terceiro setor, conectando visão de território, de gestão e de mercado em um mesmo diagnóstico.",
      },
    ].map((card, idx) => (
      <div
        key={idx}
        style={{
          borderRadius: 12,
          border: "1px solid rgba(15,23,42,0.08)",
          backgroundColor: "#ffffff",
          boxShadow: "0 1px 2px rgba(15,23,42,0.05)",
          overflow: "hidden",
          display: "flex",
          flexDirection: "column",
        }}
      >
        <div
          style={{
            height: 6,
            backgroundColor: azul,
          }}
        />
        <div
          style={{
            padding: 10,
            display: "flex",
            flexDirection: "column",
            gap: 4,
          }}
        >
          <div
            style={{
              fontSize: 18,
              lineHeight: 1,
            }}
          >
            {card.icone}
          </div>
          <div
            style={{
              fontSize: 13,
              fontWeight: 600,
              color: "#111827",
            }}
          >
            {card.titulo}
          </div>
          <p
            style={{
              fontSize: 12,
              color: "#4b5563",
              margin: 0,
              lineHeight: 1.5,
            }}
          >
            {card.texto}
          </p>
        </div>
      </div>
    ))}
  </div>
</div>

      
     {/* SEÇÃO: Para quem é a Ideal */}
<section
  style={{
    marginTop: 32,
    marginBottom: 6,
    display: "flex",
    flexDirection: "column",
    gap: 16,
  }}
>
  {/* Cabeçalho da seção */}
  <div
    style={{
      maxWidth: 720,
    }}
  >
    <div
      style={{
        fontSize: 11,
        fontWeight: 600,
        textTransform: "uppercase",
        letterSpacing: 0.8,
        marginBottom: 6,
        color: "#64748b",
      }}
    >
      Para quem a Ideal trabalha
    </div>

    <h3
      style={{
        margin: 0,
        marginBottom: 8,
        fontSize: 18,
        fontWeight: 700,
        color: "#0f172a",
      }}
    >
      Projetos sob medida para governo local, consórcios, marcas e campanhas
    </h3>

    <p
      style={{
        margin: 0,
        fontSize: 13,
        lineHeight: 1.6,
        color: "#4b5563",
      }}
    >
      A Ideal desenha estudos e estratégias a partir das perguntas de cada
      cliente: avaliar governo, entender o cidadão, posicionar marcas ou
      organizar uma campanha eleitoral com base em dados.
    </p>
  </div>

  {/* Cards de públicos atendidos */}
  <div
    style={{
      display: "grid",
      gridTemplateColumns: isMobile ? "1fr" : "repeat(3, minmax(0, 1fr))",
      gap: 12,
    }}
  >
    {[
      {
        icone: "🏛️",
        titulo: "Prefeituras e consórcios",
        texto:
          "Avaliação de governo, prioridades da população, satisfação com serviços públicos, diagnósticos territoriais e monitoramento recorrente ao longo do mandato.",
      },
      {
        icone: "📊",
        titulo: "Empresas e marcas",
        texto:
          "Pesquisas de marca, posicionamento em redes sociais, estudo de concorrência, hábitos de consumo e oportunidades de crescimento em nichos específicos.",
      },
      {
        icone: "🗳️",
        titulo: "Campanhas eleitorais",
        texto:
          "Intenção de voto, tracking, testes de mensagem, segmentação por público e por território e apoio à estratégia de comunicação ao longo de todo o período eleitoral.",
      },
    ].map((card, idx) => (
      <div
        key={idx}
        style={{
          borderRadius: 12,
          border: "1px solid rgba(15,23,42,0.08)",
          backgroundColor: "#ffffff",
          boxShadow: "0 1px 2px rgba(15,23,42,0.04)",
          padding: 12,
          display: "flex",
          flexDirection: "column",
          gap: 6,
        }}
      >
        <div
          style={{
            fontSize: 20,
            lineHeight: 1,
          }}
        >
          {card.icone}
        </div>
        <div
          style={{
            fontSize: 14,
            fontWeight: 600,
            color: "#111827",
          }}
        >
          {card.titulo}
        </div>
        <p
          style={{
            margin: 0,
            fontSize: 12,
            lineHeight: 1.6,
            color: "#4b5563",
          }}
        >
          {card.texto}
        </p>
      </div>
    ))}
  </div>
</section>

  {/* SEÇÃO: Como trabalhamos */}
<section
  style={{
    marginTop: 18, // aproximar da seção de cima
    marginBottom: 28,
    display: "flex",
    flexDirection: "column",
    gap: 16,
  }}
>
  {/* Cabeçalho da seção */}
  <div
    style={{
      maxWidth: 720,
    }}
  >
    <div
      style={{
        fontSize: 11,
        fontWeight: 600,
        textTransform: "uppercase",
        letterSpacing: 0.8,
        marginBottom: 6,
        color: "#64748b",
      }}
    >
      Como trabalhamos
    </div>

    <h3
      style={{
        margin: 0,
        marginBottom: 8,
        fontSize: 18,
        fontWeight: 700,
        color: "#0f172a",
      }}
    >
      Etapas de um projeto com a Ideal
    </h3>

    <p
      style={{
        margin: 0,
        fontSize: 13,
        lineHeight: 1.6,
        color: "#4b5563",
      }}
    >
      Cada estudo segue um roteiro claro, da primeira conversa até a entrega
      de recomendações acionáveis para o governo, o consórcio ou a empresa.
    </p>
  </div>

  {/* Etapas */}
  <div
    style={{
      display: "grid",
      gridTemplateColumns: isMobile ? "1fr" : "repeat(4, minmax(0, 1fr))",
      gap: 12,
    }}
  >
    {[
      {
        numero: "1",
        titulo: "Entendimento do problema",
        texto:
          "Reunião inicial para compreender o contexto, os objetivos, o público-alvo e as restrições de cada projeto — seja público ou privado.",
      },
      {
        numero: "2",
        titulo: "Desenho metodológico",
        texto:
          "Definição de amostra, questionário, instrumentos qualitativos, plano de campo e recortes territoriais ou de nicho de mercado.",
      },
      {
        numero: "3",
        titulo: "Campo, análise e visualização",
        texto:
          "Coleta de dados, checagens de qualidade, análise estatística e qualitativa e montagem de painéis, mapas e relatórios.",
      },
      {
        numero: "4",
        titulo: "Entrega acionável",
        texto:
          "Apresentação dos resultados com prioridades, recomendações e próximos passos, para apoiar decisões concretas no governo ou na empresa.",
      },
    ].map((etapa) => (
      <div
        key={etapa.numero}
        style={{
          borderRadius: 12,
          border: "1px solid rgba(15,23,42,0.08)",
          backgroundColor: "#ffffff",
          boxShadow: "0 1px 2px rgba(15,23,42,0.04)",
          padding: 10, // um pouco menor pra box ficar mais compacto
          display: "flex",
          flexDirection: "column",
          gap: 6,
        }}
      >
        {/* Linha com bolinha + título lado a lado */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 8,
            marginBottom: 2,
          }}
        >
          <div
            style={{
              display: "inline-flex",
              alignItems: "center",
              justifyContent: "center",
              width: 24,
              height: 24,
              borderRadius: "999px",
              backgroundColor: "#F5C145",
              fontSize: 13,
              fontWeight: 700,
              color: "#111827",
              flexShrink: 0,
            }}
          >
            {etapa.numero}
          </div>
          <div
            style={{
              fontSize: 13,
              fontWeight: 600,
              color: "#111827",
            }}
          >
            {etapa.titulo}
          </div>
        </div>

        {/* Texto */}
        <p
          style={{
            margin: 0,
            fontSize: 12,
            lineHeight: 1.6,
            color: "#4b5563",
          }}
        >
          {etapa.texto}
        </p>
      </div>
    ))}
  </div>
</section>

      {/* CTA – FALAR COM A IDEAL */}
      <section
        style={{
          borderRadius: 12,
          padding: 18,
          backgroundColor: azul,
          border: `1px solid ${dourado}`,
          display: "flex",
          flexDirection: isMobile ? "column" : "row",
          alignItems: isMobile ? "stretch" : "center",
          justifyContent: "space-between",
          gap: 12,
        }}
      >
        <div>
          <div
            style={{
              fontSize: 14,
              fontWeight: 600,
              color: "#f9fafb",
              marginBottom: 4,
            }}
          >
            Precisa de uma pesquisa ou diagnóstico?
          </div>
          <p
            style={{
              fontSize: 13,
              color: "#e5e7eb",
              margin: 0,
            }}
          >
            Conte em poucas linhas qual é o desafio da sua prefeitura, consórcio,
            empresa ou campanha — a Ideal desenha um estudo sob medida.
          </p>
        </div>
        <a
          href="#contato-ancora"
          style={{
            textDecoration: "none",
            alignSelf: isMobile ? "flex-start" : "auto",
          }}
        >
          <button
            style={{
              padding: "8px 18px",
              borderRadius: 999,
              border: "none",
              backgroundColor: dourado,
              color: "#111827",
              fontSize: 13,
              fontWeight: 600,
              cursor: "pointer",
              whiteSpace: "nowrap",
            }}
          >
            Falar com a Ideal
          </button>
        </a>
      </section>

      {/* 6 CARDS EM 3 COLUNAS (ARTIGOS) */}
      <section
        style={{
          display: "grid",
          gridTemplateColumns: isMobile
            ? "1fr"
            : isTablet
            ? "repeat(2, minmax(0, 1fr))"
            : "repeat(3, minmax(0, 1fr))",
          gap: 18,
        }}
      >
        {artigos.map((card) => (
          <article
            key={card.id}
            style={{
              backgroundColor: "#ffffff",
              borderRadius: 12,
              padding: 16,
              border: "1px solid #e5e7eb",
              boxShadow: "0 1px 2px rgba(15,23,42,0.04)",
              display: "flex",
              flexDirection: "column",
            }}
          >
            <div
              style={{
                fontSize: 12,
                textTransform: "uppercase",
                color: "#6b7280",
                marginBottom: 4,
              }}
            >
              {card.categoria}
            </div>
            <h2
              style={{
                fontSize: 17,
                margin: 0,
                marginBottom: 6,
                color: hoveredId === card.id ? dourado : "#111827",
                cursor: "pointer",
                transition: "color 0.15s ease",
              }}
              title={card.olho}
              onMouseEnter={() => setHoveredId(card.id)}
              onMouseLeave={() => setHoveredId(null)}
              onClick={() => setView({ mode: "artigo", artigo: card })}
            >
              {card.titulo}
            </h2>
            <p
              style={{
                fontSize: 13,
                color: "#4b5563",
                margin: 0,
                marginBottom: 10,
                lineHeight: 1.45,
              }}
            >
              {card.resumo}
            </p>
            <button
              onClick={() => setView({ mode: "artigo", artigo: card })}
              style={{
                marginTop: "auto",
                alignSelf: "flex-start",
                backgroundColor: azul,
                color: "#ffffff",
                borderRadius: 999,
                border: "none",
                padding: "7px 14px",
                fontSize: 13,
                cursor: "pointer",
              }}
            >
              Ler matéria completa
            </button>
          </article>
        ))}
      </section>
    </div>
  );
}

function StageCard({ numero, titulo, texto }) {
  return (
    <div
      style={{
        borderRadius: 10,
        border: "1px solid #e5e7eb",
        padding: 12,
        backgroundColor: "#f9fafb",
      }}
    >
      <div
        style={{
          width: 22,
          height: 22,
          borderRadius: "999px",
          backgroundColor: dourado,
          color: "#111827",
          fontSize: 12,
          fontWeight: 700,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          marginBottom: 6,
        }}
      >
        {numero}
      </div>
      <div
        style={{
          fontSize: 14,
          fontWeight: 600,
          marginBottom: 4,
          color: "#111827",
        }}
      >
        {titulo}
      </div>
      <p
        style={{
          fontSize: 13,
          color: "#4b5563",
          margin: 0,
          lineHeight: 1.5,
        }}
      >
        {texto}
      </p>
    </div>
  );
}

/* ==========================
   PÁGINA QUEM SOMOS
========================== */

function QuemSomosPage() {
  const { isMobile, isTablet } = useBreakpoint();

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        gap: 20,
      }}
    >
      {/* BLOCO PRINCIPAL */}
      <section
        style={{
          backgroundColor: "#ffffff",
          borderRadius: 12,
          border: "1px solid #e5e7eb",
          boxShadow: "0 1px 3px rgba(15,23,42,0.06)",
          padding: 24,
        }}
      >
        <h1
          style={{
            fontSize: 22,
            margin: 0,
            marginBottom: 8,
            color: "#111827",
          }}
        >
          Sobre a Ideal Desenvolvimento Estratégico
        </h1>
        <p
          style={{
            fontSize: 14,
            color: "#4b5563",
            lineHeight: 1.7,
            margin: "0 0 10px",
          }}
        >
          A Ideal Desenvolvimento Estratégico nasce da combinação entre experiência
          em gestão pública, prática em consórcios intermunicipais, atuação em
          políticas sociais e formação acadêmica em ciência política, sociologia e
          áreas afins. O foco é um só: produzir informação confiável para que
          gestores públicos, empresas e campanhas tomem decisões com base em
          evidências, e não apenas em impressões ou pressões do dia a dia.
        </p>
        <p
          style={{
            fontSize: 14,
            color: "#4b5563",
            lineHeight: 1.7,
            margin: "0 0 10px",
          }}
        >
          A atuação da Ideal está voltada tanto para o setor público — prefeituras,
          consórcios, câmaras municipais — quanto para o setor privado, com
          pesquisas de mercado, marca, posicionamento e hábitos de consumo. Em
          campanhas eleitorais, o trabalho se concentra em medir cenário,
          identificar oportunidades, testar mensagens e organizar o mapa de riscos
          e potencialidades ao longo do período eleitoral.
        </p>
        <p
          style={{
            fontSize: 13,
            color: "#6b7280",
            lineHeight: 1.6,
            margin: 0,
          }}
        >
          Este site apresenta, de forma resumida, a lógica de trabalho da Ideal e
          alguns exemplos de conteúdos que podem ser gerados a partir de pesquisas
          e diagnósticos. Quando os projetos forem realizados com clientes reais,
          estas áreas poderão exibir estudos de caso, depoimentos e resultados
          autorizados para divulgação.
        </p>
      </section>

      {/* MISSÃO, VISÃO, VALORES */}
      <section
        style={{
          display: "grid",
          gridTemplateColumns: isMobile
            ? "1fr"
            : isTablet
            ? "repeat(2, minmax(0,1fr))"
            : "repeat(3, minmax(0,1fr))",
          gap: 16,
        }}
      >
        <InfoCard
          titulo="Missão"
          texto="Transformar dados de opinião, mercado e território em decisões concretas, ajudando governos e empresas a entregar resultados que façam sentido para quem vive a cidade e consome os serviços."
        />
        <InfoCard
          titulo="Visão"
          texto="Ser referência em pesquisa aplicada à gestão pública e à estratégia de negócios em municípios e regiões metropolitanas, conectando academia, prática de governo e realidade do mercado."
        />
        <InfoCard
          titulo="Valores"
          texto="Ética, transparência, rigor metodológico, responsabilidade com quem responde às pesquisas e compromisso com o uso responsável dos dados em favor do interesse público e do desenvolvimento local."
        />
      </section>

      {/* DIFERENCIAIS */}
      <section
        style={{
          backgroundColor: "#ffffff",
          borderRadius: 12,
          border: "1px solid #e5e7eb",
          boxShadow: "0 1px 2px rgba(15,23,42,0.04)",
          padding: 20,
        }}
      >
        <h2
          style={{
            fontSize: 20,
            margin: "0 0 8px",
            color: "#111827",
          }}
        >
          O que diferencia a Ideal
        </h2>
        <ul
          style={{
            margin: 0,
            paddingLeft: 18,
            fontSize: 14,
            color: "#4b5563",
            lineHeight: 1.6,
          }}
        >
          <li>
            Integração entre pesquisa quantitativa, escutas qualitativas e leitura
            territorial da cidade.
          </li>
          <li>
            Experiência prática em consórcios públicos e na gestão de políticas
            sociais, saúde, educação e desenvolvimento econômico.
          </li>
          <li>
            Capacidade de dialogar tanto com prefeitos, secretários e equipes
            técnicas quanto com empresários, equipes comerciais e coordenações de
            campanha.
          </li>
          <li>
            Entregas pensadas para o dia a dia: relatórios, painéis e
            apresentações que ajudam a organizar a agenda, e não apenas acumular
            documentos.
          </li>
        </ul>
      </section>
    </div>
  );
}

function InfoCard({ titulo, texto }) {
  return (
    <article
      style={{
        backgroundColor: "#ffffff",
        borderRadius: 12,
        border: "1px solid #e5e7eb",
        boxShadow: "0 1px 2px rgba(15,23,42,0.06)",
        padding: 16,
      }}
    >
      <h3
        style={{
          fontSize: 16,
          margin: "0 0 6px",
          color: "#111827",
        }}
      >
        {titulo}
      </h3>
      <p
        style={{
          fontSize: 13,
          color: "#4b5563",
          margin: 0,
          lineHeight: 1.6,
        }}
      >
        {texto}
      </p>
    </article>
  );
}

/* ==========================
   PÁGINA PESQUISAS
========================== */

function PesquisasPage() {
  const { isMobile, isTablet } = useBreakpoint();
  const [view, setView] = React.useState({ mode: "lista", artigo: null });
  const [hoveredId, setHoveredId] = React.useState(null);

  const botaoPrimario = {
    padding: "8px 14px",
    borderRadius: 999,
    border: "none",
    backgroundColor: "#111827",
    color: "#ffffff",
    fontSize: 13,
    fontWeight: 500,
    cursor: "pointer",
    whiteSpace: "nowrap",
  };

  const pesquisasMock = [
    {
      id: 1,
      cidade: "BRASIL – JUVENTUDE",
      titulo: "Jovens, redes sociais e democracia",
      subtitulo:
        "Estudos mostram que grande parte da juventude se informa principalmente pelas redes sociais, apoia a democracia, mas demonstra baixa confiança em partidos e instituições.",
      dataCampo: "Levantamentos entre 2015 e 2024",
      amostra: "Mais de 2.000 jovens em diferentes pesquisas",
      margemErro: "Em torno de ±3 p.p.",
      contratante: "Universidades e institutos de pesquisa",
      fonte:
        "Pesquisas acadêmicas sobre cultura política juvenil e uso de redes sociais no Brasil.",
      texto1:
        "A literatura recente sobre cultura política juvenil no Brasil tem insistido em um ponto central: a juventude não é apática, mas se engaja de forma distinta das gerações anteriores.",
      texto2:
        "Esse deslocamento do debate público para o ambiente digital produz efeitos ambíguos, ampliando o contato com temas políticos, mas também expondo a juventude à desinformação.",
      texto3:
        "Para quem governa, dialogar com a juventude exige combinar pesquisa, escuta qualificada e novas linguagens.",
      resumoBox: [
        "Jovens apoiam a democracia, mas desconfiam de partidos e instituições tradicionais.",
        "Redes sociais são o principal ambiente de informação e sociabilidade política.",
        "Gestores que desejam dialogar com a juventude precisam combinar pesquisa, escuta e novas linguagens.",
      ],
    },
    {
      id: 2,
      cidade: "BRASIL – MULHERES E POLÍTICA",
      titulo: "Participação feminina e barreiras persistentes",
      subtitulo:
        "Pesquisas indicam que a maioria das brasileiras apoia mais mulheres na política, mas reconhece barreiras como machismo, falta de apoio partidário e dupla jornada.",
      dataCampo: "Levantamentos acadêmicos e institucionais (2016–2024)",
      amostra: "Estudos com eleitoras e mulheres em mandatos",
      margemErro: "Variável conforme o estudo",
      contratante: "Universidades, órgãos públicos e organizações da sociedade civil",
      fonte:
        "Pesquisas sobre representação feminina, campanhas eleitorais e participação política de mulheres no Brasil.",
      texto1:
        "Os estudos sobre participação feminina na política brasileira mostram um paradoxo conhecido: embora as mulheres sejam maioria do eleitorado, seguem sub-representadas.",
      texto2:
        "Violência política de gênero, distribuição desigual de recursos e cultura partidária pouco inclusiva aparecem com frequência como barreiras estruturais.",
      texto3:
        "Políticas de incentivo e monitoramento permanente são fundamentais para ampliar a presença de mulheres na política.",
      resumoBox: [
        "Mulheres são maioria do eleitorado, mas minoria nos espaços de decisão.",
        "A violência política de gênero atua como barreira à entrada e à permanência.",
        "Mudanças partidárias e institucionais precisam ser acompanhadas por pesquisa e monitoramento contínuo.",
      ],
    },
    {
      id: 3,
      cidade: "BRASIL – ELEIÇÕES 2026",
      titulo: "Prioridades do eleitorado para as próximas eleições",
      subtitulo:
        "Levantamentos recentes apontam corrupção, segurança pública e economia como principais problemas do país, seguidos por saúde e educação.",
      dataCampo: "Pesquisas nacionais de opinião em 2024–2025",
      amostra: "Cerca de 3.000 entrevistas presenciais e online",
      margemErro: "Em torno de ±2 p.p.",
      contratante: "Institutos de opinião pública",
      fonte:
        "Pesquisas nacionais divulgadas por institutos de opinião sobre maiores problemas do Brasil e agenda de prioridades.",
      texto1:
        "Quando o entrevistador pergunta qual é o principal problema do país, as respostas se concentram em corrupção, segurança pública e economia.",
      texto2:
        "Saúde e educação aparecem associadas à experiência concreta com serviços públicos, como filas, atendimento e infraestrutura.",
      texto3:
        "Candidaturas competitivas tendem a ser aquelas que conseguem articular propostas realistas nesses eixos centrais.",
      resumoBox: [
        "Corrupção, segurança e economia formam o núcleo das preocupações nacionais.",
        "Saúde e educação aparecem associadas à experiência concreta com serviços públicos.",
        "Gestores que acompanham essas prioridades em nível local têm mais condições de organizar agendas realistas.",
      ],
    },
  ];

  // Tela de ARTIGO (uma das 3 pesquisas)
  if (view.mode === "artigo" && view.artigo) {
    const p = view.artigo;

    return (
      <div
        style={{
          padding: "8px 4px 24px",
          maxWidth: 1200,
          margin: "0 auto",
          fontFamily: "system-ui, -apple-system, BlinkMacSystemFont, sans-serif",
        }}
      >
        <button
          onClick={() => setView({ mode: "lista", artigo: null })}
          style={{
            marginBottom: 10,
            backgroundColor: "transparent",
            border: "none",
            color: azul,
            cursor: "pointer",
            fontSize: 13,
          }}
        >
          ← Voltar para a lista de pesquisas
        </button>

        <article
          style={{
            backgroundColor: "#ffffff",
            borderRadius: 12,
            border: "1px solid #e5e7eb",
            boxShadow: "0 1px 3px rgba(15, 23, 42, 0.06)",
            overflow: "hidden",
          }}
        >
          {/* imagem de capa genérica */}
          <div
            style={{
              height: 220,
              backgroundImage:
                'url("https://images.unsplash.com/photo-1529101091764-c3526daf38fe?auto=format&fit=crop&w=1400&q=70")',
              backgroundSize: "cover",
              backgroundPosition: "center",
            }}
          />

          <div
            style={{
              display: "grid",
              gridTemplateColumns: isMobile
                ? "minmax(0, 1fr)"
                : "minmax(0, 2.2fr) minmax(0, 1fr)",
              gap: 22,
              padding: 24,
            }}
          >
            <div>
              <div
                style={{
                  fontSize: 12,
                  textTransform: "uppercase",
                  letterSpacing: 0.6,
                  color: "#6b7280",
                  marginBottom: 6,
                }}
              >
                {p.cidade}
              </div>
              <h1
                style={{
                  fontSize: 24,
                  margin: 0,
                  marginBottom: 8,
                  color: "#111827",
                }}
              >
                {p.titulo}
              </h1>
              <p
                style={{
                  fontSize: 14,
                  color: "#4b5563",
                  margin: 0,
                  marginBottom: 12,
                  fontWeight: 500,
                }}
              >
                {p.subtitulo}
              </p>

              <p
                style={{
                  fontSize: 14,
                  color: "#4b5563",
                  lineHeight: 1.6,
                  marginBottom: 12,
                }}
              >
                {p.texto1}
              </p>
              <p
                style={{
                  fontSize: 14,
                  color: "#4b5563",
                  lineHeight: 1.6,
                  marginBottom: 12,
                }}
              >
                {p.texto2}
              </p>
              <p
                style={{
                  fontSize: 14,
                  color: "#4b5563",
                  lineHeight: 1.6,
                  marginBottom: 0,
                }}
              >
                {p.texto3}
              </p>
            </div>

            <aside
              style={{
                alignSelf: "flex-start",
                backgroundColor: "#f9fafb",
                borderRadius: 10,
                border: "1px solid #e5e7eb",
                padding: 14,
                fontSize: 13,
                color: "#374151",
              }}
            >
              <div
                style={{
                  fontSize: 12,
                  fontWeight: 600,
                  textTransform: "uppercase",
                  letterSpacing: 0.6,
                  marginBottom: 6,
                  color: "#6b7280",
                }}
              >
                Em resumo
              </div>
              <ul
                style={{
                  paddingLeft: 18,
                  margin: 0,
                  display: "flex",
                  flexDirection: "column",
                  gap: 4,
                }}
              >
                {p.resumoBox.map((item, idx) => (
                  <li key={idx}>{item}</li>
                ))}
              </ul>

              <div
                style={{
                  marginTop: 10,
                  fontSize: 12,
                  color: "#6b7280",
                  lineHeight: 1.5,
                }}
              >
                <p style={{ margin: 0 }}>
                  <strong>Nota metodológica:</strong> o texto foi elaborado a
                  partir de resultados e tendências descritos em pesquisas já
                  divulgadas por diferentes institutos e estudos acadêmicos
                  sobre o tema.
                </p>
                <p style={{ margin: "6px 0 0" }}>
                  <strong>Fonte de inspiração:</strong> estudos nacionais sobre
                  cultura política, representação feminina e prioridades do
                  eleitorado brasileiro.
                </p>
              </div>
            </aside>
          </div>
        </article>
      </div>
    );
  }

  // Tela LISTA (3 cards + texto geral)
  return (
    <div
      style={{
        padding: "8px 4px 24px",
        maxWidth: 1200,
        margin: "0 auto",
        fontFamily: "system-ui, -apple-system, BlinkMacSystemFont, sans-serif",
      }}
    >
      {/* TÍTULO + INTRO */}
      <section
        style={{
          backgroundColor: "#f9fafb",
          borderRadius: 12,
          padding: 20,
          border: "1px solid #e5e7eb",
          marginBottom: 24,
        }}
      >
        <h1
          style={{
            margin: 0,
            fontSize: 22,
            fontWeight: 700,
            color: "#111827",
          }}
        >
          Pesquisas eleitorais e de opinião
        </h1>

        <p
          style={{
            marginTop: 10,
            fontSize: 14,
            color: "#4b5563",
            lineHeight: 1.6,
          }}
        >
          Abaixo estão três exemplos de temas amplamente pesquisados por
          universidades e institutos de opinião: política e juventude, mulheres e
          política e prioridades do eleitorado para as próximas eleições. Os
          resumos se baseiam em estudos já divulgados, com indicação de fonte, e
          servem apenas como demonstração de conteúdo para a página da Ideal.
        </p>
      </section>

      {/* GRID 3 COLUNAS */}
      <section
        style={{
          display: "grid",
          gridTemplateColumns: isMobile
            ? "1fr"
            : isTablet
            ? "repeat(2, minmax(0, 1fr))"
            : "repeat(3, minmax(0, 1fr))",
          gap: 20,
          alignItems: "stretch",
          marginBottom: 28,
        }}
      >
        {pesquisasMock.map((pesquisa) => (
          <article
            key={pesquisa.id}
            style={{
              backgroundColor: "#ffffff",
              borderRadius: 12,
              padding: 18,
              boxShadow: "0 1px 3px rgba(15, 23, 42, 0.06)",
              border: "1px solid #e5e7eb",
              display: "flex",
              flexDirection: "column",
              justifyContent: "space-between",
              minHeight: 260,
            }}
          >
            <div>
              <div
                style={{
                  fontSize: 12,
                  fontWeight: 600,
                  color: "#6b7280",
                  letterSpacing: 0.6,
                  textTransform: "uppercase",
                  marginBottom: 6,
                }}
              >
                {pesquisa.cidade}
              </div>

              <h2
                style={{
                  fontSize: 17,
                  margin: "0 0 8px",
                  color: hoveredId === pesquisa.id ? dourado : "#111827",
                  lineHeight: 1.35,
                  cursor: "pointer",
                  transition: "color 0.15s ease",
                }}
                title={pesquisa.subtitulo}
                onMouseEnter={() => setHoveredId(pesquisa.id)}
                onMouseLeave={() => setHoveredId(null)}
                onClick={() => setView({ mode: "artigo", artigo: pesquisa })}
              >
                {pesquisa.titulo}
              </h2>

              <p
                style={{
                  fontSize: 14,
                  color: "#4b5563",
                  lineHeight: 1.5,
                  margin: "0 0 10px",
                }}
              >
                {pesquisa.subtitulo}
              </p>

              <div
                style={{
                  fontSize: 12,
                  color: "#4b5563",
                  lineHeight: 1.4,
                  marginBottom: 6,
                }}
              >
                <strong>Período de campo:</strong> {pesquisa.dataCampo}
                <br />
                <strong>Amostra:</strong> {pesquisa.amostra}
                <br />
                <strong>Margem de erro:</strong> {pesquisa.margemErro}
                <br />
                <strong>Contratante:</strong> {pesquisa.contratante}
              </div>

              <div
                style={{
                  fontSize: 11,
                  color: "#6b7280",
                  marginTop: 4,
                }}
              >
                <strong>Fonte:</strong> {pesquisa.fonte}
              </div>
            </div>

            <div
              style={{
                marginTop: 14,
                display: "flex",
              }}
            >
              <button
                style={botaoPrimario}
                onClick={() => setView({ mode: "artigo", artigo: pesquisa })}
              >
                Ler matéria completa
              </button>
            </div>
          </article>
        ))}
      </section>

      {/* BLOCO JORNALÍSTICO GERAL */}
      <section
        style={{
          backgroundColor: "#ffffff",
          borderRadius: 12,
          padding: 20,
          border: "1px solid #e5e7eb",
          boxShadow: "0 1px 2px rgba(15, 23, 42, 0.04)",
        }}
      >
        <div
          style={{
            fontSize: 12,
            fontWeight: 600,
            color: "#6b7280",
            letterSpacing: 0.6,
            textTransform: "uppercase",
            marginBottom: 4,
          }}
        >
          PANORAMA – TEXTO DEMONSTRATIVO
        </div>

        <h2
          style={{
            fontSize: 20,
            margin: "0 0 10px",
            color: "#111827",
          }}
        >
          Corrupção, segurança e economia concentram as principais preocupações do
          eleitorado brasileiro
        </h2>

        <p
          style={{
            fontSize: 14,
            color: "#4b5563",
            lineHeight: 1.7,
            margin: "0 0 10px",
          }}
        >
          Levantamentos nacionais recentes indicam que a corrupção voltou a ocupar o
          topo da lista de problemas do país para a maioria dos brasileiros, seguida
          de perto pela criminalidade e pela situação econômica. Na prática, isso
          significa que o eleitorado tende a avaliar candidaturas para 2026 à luz da
          capacidade percebida de enfrentar esses três eixos centrais: combate à
          corrupção, segurança pública e geração de renda.
        </p>

        <p
          style={{
            fontSize: 14,
            color: "#4b5563",
            lineHeight: 1.7,
            margin: "0 0 10px",
          }}
        >
          Questões clássicas como saúde e educação continuam presentes no radar, mas
          muitas vezes aparecem associadas a experiências concretas do dia a dia:
          tempo de espera para consultas, qualidade do atendimento básico,
          disponibilidade de vagas em creches e escolas. Em cenários eleitorais,
          propostas que conectam esses temas a soluções locais tendem a dialogar
          melhor com as preocupações reais da população.
        </p>

        <p
          style={{
            fontSize: 13,
            color: "#6b7280",
            lineHeight: 1.6,
            margin: 0,
          }}
        >
          <strong>Nota metodológica:</strong> o texto acima é um exemplo
          jornalístico produzido a partir de pesquisas nacionais já divulgadas por
          institutos de opinião. Quando a Ideal começar a publicar seus próprios
          levantamentos, este espaço será usado para apresentar análises detalhadas
          de cada estudo.
        </p>
      </section>
    </div>
  );
}

/* ==========================
   PÁGINA SERVIÇOS
========================== */

function ServicosPage() {
  const { isMobile, isTablet } = useBreakpoint();

  const cards = [
    {
      titulo: "Pesquisas eleitorais e de opinião pública",
      icone: "🗳️",
      texto:
        "Estudos quantitativos e qualitativos para campanhas e mandatos: intenção de voto, avaliação de governo, temas prioritários e testes de mensagem. Ajudam a ajustar estratégia, discurso e posicionamento com base em dados.",
    },
    {
      titulo: "Clima organizacional e satisfação do servidor",
      icone: "🏛️",
      texto:
        "Pesquisas internas em prefeituras, câmaras e organizações privadas para medir motivação, engajamento, relacionamento com chefias e condições de trabalho. Os resultados apontam caminhos concretos para melhorar gestão de pessoas.",
    },
    {
      titulo: "Satisfação do cidadão e efetividade das políticas públicas",
      icone: "📊",
      texto:
        "Avaliação da experiência do cidadão com saúde, educação, assistência social, transporte e outros serviços. Permite enxergar gargalos, prioridades e a percepção real da população sobre o que está chegando na ponta.",
    },
    {
      titulo: "Pesquisa de mercado, marca e produto",
      icone: "🧩",
      texto:
        "Mapeamento de hábitos de consumo, posicionamento de marca, concorrência e testes de conceito. Indicado para empresas que querem entender melhor seus clientes e orientar estratégia de vendas, comunicação e presença digital.",
    },
    {
      titulo: "Cursos, capacitação e consultoria para prefeituras",
      icone: "🎓",
      texto:
        "Formação de equipes nas áreas de assistência social, educação, saúde e gestão pública. Conteúdos pensados para a realidade dos municípios, com foco em prática, legislação atualizada e melhoria da entrega ao cidadão.",
    },
    {
      titulo: "Projetos especiais e regularização fundiária",
      icone: "📍",
      texto:
        "Apoio técnico em diagnósticos socioeconômicos, cadastros de famílias em áreas ocupadas, projetos de regularização fundiária e estudos específicos para decisões estratégicas em política urbana e habitação.",
    },
  ];

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        gap: 20,
      }}
    >
      <section
        style={{
          backgroundColor: "#ffffff",
          borderRadius: 12,
          padding: 24,
          border: "1px solid #e5e7eb",
          boxShadow: "0 1px 3px rgba(15,23,42,0.06)",
        }}
      >
        <h1
          style={{
            fontSize: 22,
            margin: 0,
            marginBottom: 8,
            color: "#111827",
          }}
        >
          O que a Ideal entrega para governos e empresas
        </h1>
        <p style={{ fontSize: 14, color: "#4b5563", margin: 0, lineHeight: 1.6 }}>
          A Ideal Desenvolvimento Estratégico atua combinando pesquisa,
          inteligência de dados e experiência em gestão pública e privada. Abaixo
          estão as principais linhas de serviço, pensadas para apoiar quem governa,
          quem empreende e quem coordena campanhas eleitorais, sempre com foco em
          decisão baseada em evidências.
        </p>
      </section>

      <section
        style={{
          display: "grid",
          gridTemplateColumns: isMobile
            ? "1fr"
            : isTablet
            ? "repeat(2, minmax(0, 1fr))"
            : "repeat(3, minmax(0, 1fr))",
          gap: 18,
        }}
      >
        {cards.map((card, idx) => (
          <article
            key={idx}
            style={{
              backgroundColor: "#ffffff",
              borderRadius: 14,
              padding: 18,
              border: "1px solid #e5e7eb",
              boxShadow: "0 2px 4px rgba(15,23,42,0.06)",
              display: "flex",
              flexDirection: "column",
              position: "relative",
              overflow: "hidden",
            }}
          >
            <div
              style={{
                position: "absolute",
                inset: 0,
                borderLeft: `4px solid ${dourado}`,
                opacity: 0.9,
                pointerEvents: "none",
              }}
            />
            <div style={{ position: "relative", zIndex: 1 }}>
              <div
                style={{
                  fontSize: 24,
                  marginBottom: 6,
                }}
              >
                {card.icone}
              </div>
              <h2
                style={{
                  fontSize: 16,
                  margin: 0,
                  marginBottom: 6,
                  color: "#111827",
                }}
              >
                {card.titulo}
              </h2>
              <p
                style={{
                  fontSize: 13,
                  color: "#4b5563",
                  margin: 0,
                  lineHeight: 1.5,
                }}
              >
                {card.texto}
              </p>
            </div>
          </article>
        ))}
      </section>

      <p style={{ fontSize: 13, color: "#6b7280", marginTop: 4 }}>
        Todos os projetos podem ser adaptados à realidade de cada município ou
        empresa, com desenho metodológico sob medida e entregas que vão de
        relatórios técnicos detalhados a apresentações executivas para conselhos,
        secretarias, diretoria e equipes internas.
      </p>
    </div>
  );
}

/* ==========================
   PÁGINA CONTATO
========================== */

function ContatoPage() {
  const { isMobile } = useBreakpoint();

  const [form, setForm] = React.useState({
    nome: "",
    email: "",
    telefone: "",
    tipo: "prefeitura",
    assunto: "",
    mensagem: "",
  });

  const [status, setStatus] = React.useState("idle"); // idle | sending | sent
  const [erro, setErro] = React.useState("");

  function onChange(campo, valor) {
    setForm((f) => ({ ...f, [campo]: valor }));
    if (status === "sent") setStatus("idle");
    if (erro) setErro("");
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setStatus("sending");
    setErro("");

    try {
      // futuro: integrar com backend / e-mail
      await new Promise((resolve) => setTimeout(resolve, 600));

      setStatus("sent");
      setForm({
        nome: "",
        email: "",
        telefone: "",
        tipo: "prefeitura",
        assunto: "",
        mensagem: "",
      });
    } catch (e2) {
      setErro(
        "Não foi possível enviar a mensagem agora. Tente novamente em alguns minutos."
      );
      setStatus("idle");
    }
  }

  // estilo base para todos os campos (evita “estourar” a coluna)
  const baseFieldStyle = {
    marginTop: 4,
    width: "100%",
    maxWidth: "100%",
    padding: "7px 9px",
    borderRadius: 6,
    border: "1px solid #d1d5db",
    fontSize: 13,
    boxSizing: "border-box",
    display: "block",
  };

  return (
    <div
      id="contato-ancora"
      style={{
        backgroundColor: "#ffffff",
        borderRadius: 12,
        padding: 24,
        border: "1px solid #e5e7eb",
        boxShadow: "0 1px 2px rgba(15,23,42,0.04)",
        maxWidth: 1100,
        margin: "0 auto",
      }}
    >
      <h1
        style={{
          fontSize: 22,
          margin: 0,
          marginBottom: 8,
          color: "#111827",
        }}
      >
        Fale com a Ideal
      </h1>

      <p
        style={{
          fontSize: 14,
          color: "#4b5563",
          marginBottom: 16,
          maxWidth: 720,
        }}
      >
        Use o formulário abaixo para enviar dúvidas, solicitar orçamentos ou
        propor projetos. A mensagem é organizada com os principais dados para
        que a equipe da Ideal possa responder de forma objetiva.
      </p>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: isMobile
            ? "1fr"
            : "minmax(0, 2fr) minmax(0, 1.2fr)",
          gap: 24,
          alignItems: "flex-start",
        }}
      >
        {/* FORMULÁRIO */}
        <form
          onSubmit={handleSubmit}
          style={{
            display: "flex",
            flexDirection: "column",
            gap: 10,
          }}
        >
          <div
            style={{
              display: "grid",
              gridTemplateColumns: isMobile
                ? "1fr"
                : "minmax(0, 1.4fr) minmax(0, 1fr)",
              gap: 10,
            }}
          >
            <label style={{ fontSize: 13, color: "#374151" }}>
              Nome completo
              <input
                type="text"
                required
                value={form.nome}
                onChange={(e) => onChange("nome", e.target.value)}
                style={baseFieldStyle}
              />
            </label>

            <label style={{ fontSize: 13, color: "#374151" }}>
              E-mail
              <input
                type="email"
                required
                value={form.email}
                onChange={(e) => onChange("email", e.target.value)}
                style={baseFieldStyle}
              />
            </label>
          </div>

          <div
            style={{
              display: "grid",
              gridTemplateColumns: isMobile ? "1fr" : "minmax(0, 1fr) minmax(0, 1fr)",
              gap: 10,
            }}
          >
            <label style={{ fontSize: 13, color: "#374151" }}>
              Telefone / WhatsApp
              <input
                type="text"
                value={form.telefone}
                onChange={(e) => onChange("telefone", e.target.value)}
                placeholder="(   ) _____-____"
                style={baseFieldStyle}
              />
            </label>

            <label style={{ fontSize: 13, color: "#374151" }}>
              Tipo de demanda
              <select
                value={form.tipo}
                onChange={(e) => onChange("tipo", e.target.value)}
                style={{
                  ...baseFieldStyle,
                  backgroundColor: "#ffffff",
                  WebkitAppearance: "none",
                  MozAppearance: "none",
                  appearance: "none",
                }}
              >
                <option value="prefeitura">Prefeitura / Consórcio público</option>
                <option value="empresa">Empresa privada</option>
                <option value="campanha">Campanha eleitoral</option>
                <option value="outro">Outro tipo de demanda</option>
              </select>
            </label>
          </div>

          <label style={{ fontSize: 13, color: "#374151" }}>
            Assunto
            <input
              type="text"
              required
              value={form.assunto}
              onChange={(e) => onChange("assunto", e.target.value)}
              placeholder="Ex.: Pesquisa de opinião para 2026, diagnóstico de serviços, pesquisa de mercado, etc."
              style={baseFieldStyle}
            />
          </label>

          <label style={{ fontSize: 13, color: "#374151" }}>
            Mensagem
            <textarea
              required
              rows={6}
              value={form.mensagem}
              onChange={(e) => onChange("mensagem", e.target.value)}
              placeholder="Descreva brevemente o contexto, o município ou organização e o tipo de estudo ou apoio desejado."
              style={{
                ...baseFieldStyle,
                resize: "vertical",
              }}
            />
          </label>

          {erro && (
            <div
              style={{
                fontSize: 12,
                color: "#b91c1c",
                backgroundColor: "#fee2e2",
                borderRadius: 6,
                padding: "6px 8px",
                marginTop: 4,
              }}
            >
              {erro}
            </div>
          )}

          {status === "sent" && (
            <div
              style={{
                fontSize: 12,
                color: "#166534",
                backgroundColor: "#dcfce7",
                borderRadius: 6,
                padding: "6px 8px",
                marginTop: 4,
              }}
            >
              Mensagem enviada com sucesso. Em uma implantação real, ela já teria
              sido encaminhada para o e-mail da Ideal.
            </div>
          )}

          <button
            type="submit"
            disabled={status === "sending"}
            style={{
              marginTop: 8,
              alignSelf: "flex-start",
              padding: "8px 18px",
              borderRadius: 999,
              border: "none",
              backgroundColor: status === "sending" ? "#6b7280" : "#151a3b",
              color: "#ffffff",
              fontSize: 13,
              fontWeight: 500,
              cursor: status === "sending" ? "default" : "pointer",
            }}
          >
            {status === "sending" ? "Enviando..." : "Enviar mensagem"}
          </button>
        </form>

        {/* LATERAL EXPLICATIVA */}
        <aside
          style={{
            backgroundColor: "#f9fafb",
            borderRadius: 10,
            border: "1px solid #e5e7eb",
            padding: 14,
            fontSize: 13,
            color: "#374151",
          }}
        >
          <h2
            style={{
              fontSize: 15,
              margin: "0 0 8px",
              color: "#111827",
            }}
          >
            Como este formulário será usado
          </h2>
          <p
            style={{
              margin: 0,
              marginBottom: 8,
              lineHeight: 1.6,
            }}
          >
            Na versão final do sistema, cada mensagem enviada por aqui será
            encaminhada automaticamente para o e-mail institucional da Ideal ou
            registrada em um painel interno de atendimento.
          </p>
          <p
            style={{
              margin: 0,
              marginBottom: 8,
              lineHeight: 1.6,
            }}
          >
            Os campos foram pensados para que a equipe já receba as principais
            informações: quem está entrando em contato, de que tipo de
            organização, qual a demanda e qual o contexto inicial do projeto.
          </p>
          <p
            style={{
              margin: 0,
              fontSize: 12,
              color: "#6b7280",
            }}
          >
            Em uma próxima fase, é possível integrar este formulário a um backend
            próprio, com painel de acompanhamento de contatos, histórico e
            estatísticas de demanda por tipo de projeto.
          </p>
        </aside>
      </div>
    </div>
  );
}