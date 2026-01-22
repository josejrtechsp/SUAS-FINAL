import React, { useEffect, useMemo, useState } from "react";

/* ---------- helpers ---------- */
function useWindowWidth() {
  const [w, setW] = useState(() => (typeof window === "undefined" ? 1200 : window.innerWidth));
  useEffect(() => {
    const on = () => setW(window.innerWidth);
    window.addEventListener("resize", on);
    return () => window.removeEventListener("resize", on);
  }, []);
  return w;
}

function useAreaParam(defaultKey = "suas") {
  const read = () => {
    try {
      const u = new URL(window.location.href);
      return u.searchParams.get("area") || defaultKey;
    } catch {
      return defaultKey;
    }
  };
  const [area, setArea] = useState(read);

  useEffect(() => {
    const onPop = () => setArea(read());
    window.addEventListener("popstate", onPop);
    return () => window.removeEventListener("popstate", onPop);
  }, []);

  const go = (next) => {
    const u = new URL(window.location.href);
    u.searchParams.set("area", next);
    window.history.pushState({}, "", u.toString());
    setArea(next);
    
  };

  return { area, go };
}

function Pill({ children }) {
  return (
    <span
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 8,
        padding: "6px 10px",
        borderRadius: 999,
        border: "1px solid rgba(122,92,255,0.18)",
        background: "rgba(122,92,255,0.10)",
        color: "rgba(90,70,210,1)",
        fontWeight: 900,
        fontSize: 12,
        letterSpacing: 0.4,
        textTransform: "uppercase",
      }}
    >
      {children}
    </span>
  );
}

function CardBox({ title, icon, children }) {
  return (
    <div
      style={{
        border: "1px solid rgba(0,0,0,0.06)",
        background: "rgba(255,255,255,0.70)",
        borderRadius: 18,
        padding: 14,
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 10 }}>
        <span style={{ fontSize: 16 }}>{icon}</span>
        <div style={{ fontWeight: 980 }}>{title}</div>
      </div>
      <div style={{ fontSize: 14, color: "rgba(15,23,42,0.92)" }}>{children}</div>
    </div>
  );
}

function ItemList({ items, bullet = "✅" }) {
  return (
    <div style={{ display: "grid", gap: 8 }}>
      {items.map((t, idx) => (
        <div key={idx} style={{ display: "flex", gap: 10, alignItems: "flex-start" }}>
          <div style={{ lineHeight: "18px" }}>{bullet}</div>
          <div style={{ lineHeight: "18px" }}>{t}</div>
        </div>
      ))}
    </div>
  );
}

function Step({ n, title, desc }) {
  return (
    <div
      style={{
        border: "1px solid rgba(0,0,0,0.06)",
        background: "rgba(255,255,255,0.70)",
        borderRadius: 18,
        padding: 14,
        display: "flex",
        gap: 12,
        alignItems: "flex-start",
      }}
    >
      <div
        style={{
          width: 28,
          height: 28,
          borderRadius: 999,
          display: "grid",
          placeItems: "center",
          fontWeight: 980,
          color: "rgba(90,70,210,1)",
          border: "1px solid rgba(122,92,255,0.22)",
          background: "rgba(122,92,255,0.10)",
          flex: "0 0 auto",
        }}
      >
        {n}
      </div>
      <div>
        <div style={{ fontWeight: 980 }}>{title}</div>
        <div style={{ marginTop: 4, fontSize: 13, opacity: 0.85 }}>{desc}</div>
      </div>
    </div>
  );
}

function Button({ kind = "primary", children, onClick }) {
  const base = {
    borderRadius: 999,
    padding: "10px 14px",
    fontWeight: 900,
    fontSize: 14,
    border: "1px solid rgba(0,0,0,0.08)",
    background: "rgba(255,255,255,0.75)",
    cursor: "pointer",
    boxShadow: "0 10px 24px rgba(0,0,0,0.08)",
  };
  const primary = {
    border: "1px solid rgba(122,92,255,0.25)",
    background: "rgba(122,92,255,0.95)",
    color: "white",
  };
  return (
    <button type="button" onClick={onClick} style={{ ...base, ...(kind === "primary" ? primary : {}) }}>
      {children}
    </button>
  );
}

/* ---------- component ---------- */
export default function IdealAreas() {
  const { area, go } = useAreaParam("suas");
  const w = useWindowWidth();
  const mobile = w < 980;

  const defs = useMemo(
    () => ({
      suas: {
        key: "suas",
        icon: "🤝",
        menuTitle: "SUAS",
        menuDesc: "Fluxo, SLA, evidências e rede (CRAS/CREAS/PopRua).",
        pill: "SUAS",
        title: "Assistência Social (SUAS)",
        tagline:
          "Do atendimento ao relatório: padroniza a rotina, cria continuidade e dá visibilidade de prazos, etapas e resultados.",
        why: [
          "Processo sai do “invisível”: etapas, prazos e responsáveis ficam claros.",
          "Caso parado vira pendência com prazo e próxima ação obrigatória.",
          "Rede organizada com devolutiva e evidências (sem perder histórico).",
        ],
        delivers: [
          "Prontuário simples + linha do tempo",
          "Pendências/SLA + justificativa de estagnação",
          "Encaminhamentos com retorno e alertas",
          "Relatórios (produção, gargalos, rede, demanda)",
        ],
        indicators: [
          "SLA cumprido vs vencido por etapa",
          "Casos ativos/novos/encerrados por período",
          "Tempo médio por etapa e por técnico",
          "Demandas por tema/detalhe e território",
        ],
        steps: [
          { title: "Desenhar o fluxo", desc: "Etapas, SLA e responsáveis por unidade/serviço." },
          { title: "Executar e registrar", desc: "Registro padronizado com evidências anexadas." },
          { title: "Monitorar e cobrar", desc: "Pendências, alertas e indicadores para decisão." },
        ],
        take: [
          "Templates de fluxos e relatórios por serviço",
          "Governança por perfil (LGPD) e auditoria",
          "Integração intersetorial (rede) quando necessário",
          "Configuração por unidade e equipe",
        ],
      },

      saude: {
        key: "saude",
        icon: "🩺",
        menuTitle: "Saúde",
        menuDesc: "Processos por etapa, evidências e indicadores para reduzir fila e gargalos.",
        pill: "Saúde",
        title: "Saúde (gestão e execução)",
        tagline:
          "Processos por etapa, evidências e indicadores para reduzir fila, corrigir gargalos e entregar resultado com rastreabilidade.",
        why: [
          "Fila sob controle: tempo por etapa/serviço com gargalos visíveis.",
          "Processo auditável: registro padronizado + evidências anexadas.",
          "SLA e pendências: atraso vira alerta + justificativa + próxima ação.",
        ],
        delivers: [
          "Trilhas por processo (SLA) com responsáveis",
          "Pendências automáticas + justificativa de estagnação",
          "Dashboards (fila, produção, tempo, gargalos)",
          "Relatórios para gestão e prestação de contas",
        ],
        indicators: [
          "Tempo de espera por etapa/serviço",
          "Backlog e taxa de resolução",
          "Produção por unidade/equipe",
          "Gargalos por etapa e motivo",
        ],
        steps: [
          { title: "Mapear o processo", desc: "Fila, etapas, responsáveis e pontos de estrangulamento." },
          { title: "Operar com evidência", desc: "Registro padronizado e anexos para auditoria." },
          { title: "Gerir por indicador", desc: "Painel do gestor para priorizar e redistribuir." },
        ],
        take: [
          "Fluxos por serviço prontos (SLA)",
          "Painéis acionáveis para decisão rápida",
          "Auditoria e trilha completa",
          "Relatórios por unidade e equipe",
        ],
      },

      educacao: {
        key: "educacao",
        icon: "🎓",
        menuTitle: "Educação",
        menuDesc: "Fluxos, registros e indicadores para presença, evasão e execução com evidências.",
        pill: "Educação",
        title: "Educação (gestão e execução)",
        tagline: "Presença, evasão, transporte e execução com registros e indicadores — com evidências.",
        why: [
          "Alerta de risco: faltas e sinais de evasão viram fluxo de ação.",
          "Execução rastreável: manutenção, transporte e demandas com prazo.",
          "Gestão por escola/turma/bairro com indicadores acionáveis.",
        ],
        delivers: [
          "Fluxos de busca ativa e acompanhamento",
          "Registro e anexos (documentos/ocorrências)",
          "Pendências/SLA por escola e equipe",
          "Relatórios e indicadores por território",
        ],
        indicators: [
          "Frequência por escola/turma",
          "Alertas de risco e acompanhamento",
          "Demandas de transporte e rotas",
          "Chamados e tempo de resolução",
        ],
        steps: [
          { title: "Definir rotinas", desc: "Busca ativa, manutenção, transporte e prazos." },
          { title: "Registrar e acompanhar", desc: "Ações com evidência e responsáveis claros." },
          { title: "Cobrar resultado", desc: "Indicadores por escola e território." },
        ],
        take: [
          "Rotinas padronizadas por processo",
          "Painéis por escola/turma/bairro",
          "Trilha de evidências e auditoria",
          "Relatórios prontos para gestão",
        ],
      },

      pesquisas: {
        key: "pesquisas",
        icon: "📊",
        menuTitle: "Pesquisas",
        menuDesc: "Eleitoral, mercado e qualidade do serviço público — método + execução + recomendação.",
        pill: "Pesquisas",
        title: "Pesquisas (pública e de mercado)",
        tagline: "Eleitoral, mercado e políticas públicas — diagnóstico, método, execução e recomendação.",
        why: [
          "Diagnóstico rápido com método e recorte territorial.",
          "Leitura acionável: prioridades e plano de ação.",
          "Acompanhamento recorrente (tracking) para corrigir rota.",
        ],
        delivers: [
          "Questionário + plano amostral + campo",
          "Relatórios executivos e técnicos",
          "Dashboards e recortes por território",
          "Recomendações e plano de execução",
        ],
        indicators: [
          "Satisfação e percepção por bairro",
          "Atributos (saúde/educação/infra/assistência)",
          "Tendências e variações (tracking)",
          "Mapa de problemas e prioridades",
        ],
        steps: [
          { title: "Desenhar pesquisa", desc: "Objetivo, recortes, amostra e instrumentos." },
          { title: "Executar campo", desc: "Coleta, limpeza e consistência dos dados." },
          { title: "Entregar plano", desc: "Relatório + recomendações e metas." },
        ],
        take: [
          "Diagnóstico com mapa e prioridades",
          "Relatórios prontos para decisão",
          "Dashboard com recortes",
          "Plano de ação orientado por evidência",
        ],
      },

      projetos: {
        key: "projetos",
        icon: "💼",
        menuTitle: "Projetos",
        menuDesc: "Gestão de projetos públicos: planejamento → execução → monitoramento → entrega.",
        pill: "Projetos",
        title: "Projetos (gestão e entrega)",
        tagline: "Do plano à entrega: gestão por fluxo, prazos, responsáveis e evidências.",
        why: [
          "Cada entrega com dono, prazo e evidência.",
          "Gargalos visíveis (SLA) e cobrança automática.",
          "Transparência: trilha auditável do que foi feito.",
        ],
        delivers: [
          "Plano de execução por etapa",
          "Pendências e alertas (SLA)",
          "Relatórios de status e riscos",
          "Dashboard de entregas por área",
        ],
        indicators: [
          "Entregas no prazo vs vencidas",
          "Backlog e capacidade da equipe",
          "Tempo médio por etapa",
          "Riscos e bloqueios recorrentes",
        ],
        steps: [
          { title: "Definir escopo", desc: "Entregáveis, responsáveis e prazos." },
          { title: "Executar em fluxo", desc: "Etapas padronizadas e evidências." },
          { title: "Monitorar e fechar", desc: "Relatórios e cobrança por SLA." },
        ],
        take: [
          "Modelo de governança por projeto",
          "Dashboards de acompanhamento",
          "Trilha de auditoria",
          "Relatórios executivos",
        ],
      },
ouvidoria: {
        key: "ouvidoria",
        icon: "📣",
        menuTitle: "Ouvidoria",
        menuDesc: "Mapa em tempo real + SLA + backlog por bairro/tema (asfalto, iluminação, energia, remédios etc.).",
        pill: "Ouvidoria",
        title: "Ouvidoria (gestão de demandas)",
        tagline:
          "Ouvidoria digital com triagem, SLA e mapa em tempo real: cada demanda vira tarefa com prazo, responsável e devolutiva ao cidadão.",
        why: [
          "Tempo de resposta cai porque toda demanda entra em fluxo com SLA, responsável e alertas de atraso.",
          "Mapa/heatmap em tempo real mostra onde estão os problemas (por bairro/rua) e ajuda a priorizar.",
          "Categorias padronizadas (asfalto, iluminação, lixo, energia, água, remédios, transporte etc.) viram relatório e decisão.",
        ],
        delivers: [
          "Canais: portal/app/WhatsApp + protocolo + anexos (foto/arquivo) + localização",
          "Triagem por tema e secretaria + fila por responsável (sem perder demanda no WhatsApp)",
          "SLA, pendências e justificativa de atraso + próxima ação obrigatória",
          "Painéis: ranking por bairro, tipos de demanda, reincidência e tempo médio de resposta",
        ],
        indicators: [
          "Tempo médio de 1ª resposta e tempo médio de resolução",
          "% dentro do SLA vs vencido (por tema e por secretaria)",
          "Backlog por categoria (asfalto, iluminação, saúde, remédios etc.) e por bairro/rua",
          "Reincidência por local/problema e taxa de resolução",
        ],
        steps: [
          { title: "Configurar categorias e SLAs", desc: "Temas, secretarias responsáveis, prazos e regras de triagem." },
          { title: "Operar a fila com devolutiva", desc: "Protocolo, responsável, anexos, andamento e retorno ao cidadão." },
          { title: "Gerir por mapa e indicadores", desc: "Hotspots, prioridades, cobrança e relatórios para gabinete e secretarias." },
        ],
        take: [
          "Canal único com protocolo e histórico por endereço/cidadão",
          "Gestão por SLA (cobrança automática) + transparência do andamento",
          "Mapa em tempo real + ranking por bairro e categoria",
          "Relatórios prontos para tomada de decisão e prestação de contas",
        ],
      },
    }),
    []
  );

  const order = ["suas", "saude", "educacao", "pesquisas", "projetos", "ouvidoria"];
  const current = defs[area] || defs.suas;

  const outer = {
    borderRadius: 28,
    border: "1px solid rgba(0,0,0,0.06)",
    background:
      "linear-gradient(180deg, rgba(255,255,255,0.75), rgba(255,255,255,0.60))",
    boxShadow: "0 20px 55px rgba(0,0,0,0.10)",
    padding: mobile ? 18 : 24,
  };

  const headerRow = {
    display: "flex",
    flexDirection: mobile ? "column" : "row",
    justifyContent: "space-between",
    alignItems: mobile ? "flex-start" : "flex-start",
    gap: 14,
    marginBottom: 16,
  };

  const layout = {
    display: "grid",
    gridTemplateColumns: mobile ? "1fr" : "320px 1fr",
    gap: 16,
    alignItems: "start",
  };

  const menuCard = (active) => ({
    width: "100%",
    textAlign: "left",
    borderRadius: 18,
    border: "1px solid rgba(0,0,0,0.06)",
    background: active ? "rgba(122,92,255,0.10)" : "rgba(255,255,255,0.65)",
    padding: 14,
    cursor: "pointer",
  });

  return (
    <section style={{ padding: mobile ? 14 : 22 }}>
      <div style={outer}>
        <div style={headerRow}>
          <div>
            <Pill>IDEAL — Inteligência Pública e de Mercado</Pill>
            <div style={{ fontSize: mobile ? 30 : 44, fontWeight: 990, lineHeight: 1.05, marginTop: 10, letterSpacing: -0.8,
  background: "linear-gradient(90deg, #A855F7 0%, #6366F1 55%, #22D3EE 100%)",
  WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent", color: "transparent" }}>
              Soluções Inovadoras para Gestão Pública
            </div>
            <div style={{ marginTop: 10, fontSize: 16, opacity: 0.85, maxWidth: 880 }}>
              Soluções integradas para prefeituras: SUAS, Saúde, Educação, Pesquisas, Projetos e Ouvidoria — com fluxo, SLA, evidências e indicadores para acelerar resultados.
            </div>
          </div>

          
        </div>

        <div style={layout}>
          {/* LEFT MENU */}
          <div style={{ display: "grid", gap: 12 }}>
            {order.map((k) => {
              const a = defs[k];
              const active = current.key === a.key;
              return (
                <button key={a.key} type="button" onClick={() => go(a.key)} style={menuCard(active)}>
                  <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
                    <div
                      style={{
                        width: 34,
                        height: 34,
                        borderRadius: 999,
                        border: "1px solid rgba(122,92,255,0.20)",
                        background: "rgba(122,92,255,0.08)",
                        display: "grid",
                        placeItems: "center",
                        fontSize: 16,
                        flex: "0 0 auto",
                      }}
                    >
                      {a.icon}
                    </div>
                    <div>
                      <div style={{ display: "flex", gap: 8, alignItems: "baseline" }}>
                        <div style={{ fontWeight: 980, fontSize: 16 }}>{a.menuTitle}</div>
                        <div style={{ fontSize: 12, opacity: 0.6, fontWeight: 900, textTransform: "uppercase" }}>
                          {a.pill}
                        </div>
                      </div>
                      <div style={{ marginTop: 3, fontSize: 13, opacity: 0.85 }}>{a.menuDesc}</div>
                    </div>
                  </div>
                </button>
              );
            })}
          </div>

          {/* RIGHT CONTENT */}
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 6 }}>
              <Pill>{current.pill}</Pill>
              <div style={{ fontSize: mobile ? 26 : 34, fontWeight: 980, letterSpacing: -0.6 }}>{current.title}</div>
            </div>
            <div style={{ fontSize: 15, opacity: 0.9, marginBottom: 14 }}>{current.tagline}</div>

            {/* top 3 cards */}
            <div
              style={{
                display: "grid",
                gridTemplateColumns: mobile ? "1fr" : "1fr 1fr 1fr",
                gap: 12,
              }}
            >
              <CardBox title="Por que funciona" icon="✅">
                <ItemList items={current.why} bullet="✅" />
              </CardBox>

              <CardBox title="O que entregamos" icon="📦">
                <ItemList items={current.delivers} bullet="📦" />
              </CardBox>

              <CardBox title="Indicadores" icon="📊">
                <ItemList items={current.indicators} bullet="📊" />
              </CardBox>
            </div>

            {/* bottom row */}
            <div
              style={{
                display: "grid",
                gridTemplateColumns: mobile ? "1fr" : "1.15fr 0.85fr",
                gap: 12,
                marginTop: 12,
              }}
            >
              <div
                style={{
                  border: "1px solid rgba(0,0,0,0.06)",
                  background: "rgba(255,255,255,0.70)",
                  borderRadius: 18,
                  padding: 14,
                }}
              >
                <div style={{ fontWeight: 980, marginBottom: 10 }}>Como colocamos de pé</div>
                <div style={{ display: "grid", gap: 10 }}>
                  {current.steps.map((st, idx) => (
                    <Step key={idx} n={idx + 1} title={st.title} desc={st.desc} />
                  ))}
                </div>
              </div>

              <div
                style={{
                  border: "1px solid rgba(0,0,0,0.06)",
                  background: "rgba(255,255,255,0.70)",
                  borderRadius: 18,
                  padding: 14,
                }}
              >
                <div style={{ fontWeight: 980, marginBottom: 10 }}>O que você leva para casa</div>
                <ItemList items={current.take} bullet="✅" />
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
