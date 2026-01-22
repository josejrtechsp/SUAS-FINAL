import React, { useEffect, useMemo, useState } from "react";

const GRADIENT = "linear-gradient(90deg, #A855F7 0%, #6366F1 55%, #22D3EE 100%)";

function useWindowWidth() {
  const [w, setW] = useState(() => (typeof window === "undefined" ? 1200 : window.innerWidth));
  useEffect(() => {
    const on = () => setW(window.innerWidth);
    window.addEventListener("resize", on);
    return () => window.removeEventListener("resize", on);
  }, []);
  return w;
}

function getQuery(name) {
  try {
    return new URL(window.location.href).searchParams.get(name);
  } catch {
    return null;
  }
}

function slugFromURL() {
  const q = (getQuery("artigo") || "").trim();
  if (q) return q.toLowerCase();
  try {
    const last = (window.location.pathname || "").split("/").filter(Boolean).pop();
    if (last && last.length > 2) return last.toLowerCase();
  } catch {}
  return "no-estrutural";
}

function Chip({ children }) {
  return (
    <span
      style={{
        display: "inline-flex",
        alignItems: "center",
        padding: "6px 10px",
        borderRadius: 999,
        border: "1px solid rgba(122,92,255,0.18)",
        background: "rgba(122,92,255,0.10)",
        color: "rgba(90,70,210,1)",
        fontWeight: 900,
        fontSize: 12,
        letterSpacing: 0.5,
        textTransform: "uppercase",
      }}
    >
      {children}
    </span>
  );
}

function Btn({ primary = false, children, onClick }) {
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
  const p = {
    border: "1px solid rgba(122,92,255,0.25)",
    background: "rgba(122,92,255,0.95)",
    color: "white",
  };
  return (
    <button type="button" onClick={onClick} style={{ ...base, ...(primary ? p : {}) }}>
      {children}
    </button>
  );
}

function Card({ title, children }) {
  return (
    <div
      style={{
        borderRadius: 22,
        padding: 16,
        border: "1px solid rgba(0,0,0,0.06)",
        background: "rgba(255,255,255,0.70)",
        boxShadow: "0 14px 36px rgba(0,0,0,0.08)",
      }}
    >
      {title ? <div style={{ fontWeight: 980, marginBottom: 10 }}>{title}</div> : null}
      {children}
    </div>
  );
}

function Callout({ title, children }) {
  return (
    <div
      style={{
        borderRadius: 18,
        padding: 14,
        border: "1px solid rgba(122,92,255,0.18)",
        background: "linear-gradient(135deg, rgba(122,92,255,0.10), rgba(255,255,255,0.60))",
      }}
    >
      {title ? <div style={{ fontWeight: 980, marginBottom: 6 }}>{title}</div> : null}
      {children}
    </div>
  );
}

function TocButton({ id, children }) {
  return (
    <button
      type="button"
      onClick={() => document.getElementById(id)?.scrollIntoView({ behavior: "smooth", block: "start" })}
      style={{
        width: "100%",
        textAlign: "left",
        border: "1px solid rgba(0,0,0,0.06)",
        background: "rgba(255,255,255,0.62)",
        borderRadius: 14,
        padding: "10px 12px",
        cursor: "pointer",
        fontWeight: 850,
        fontSize: 13,
        opacity: 0.92,
      }}
    >
      {children}
    </button>
  );
}

function BulletList({ items }) {
  return (
    <div style={{ display: "grid", gap: 8, marginTop: 10, fontSize: 15, lineHeight: 1.7, opacity: 0.92 }}>
      {items.map((t, i) => (
        <div key={i} style={{ display: "flex", gap: 10, alignItems: "flex-start" }}>
          <span style={{ marginTop: 2 }}>✅</span>
          <span>{t}</span>
        </div>
      ))}
    </div>
  );
}

// Lista em formato de texto corrido (sem tópicos), como o usuário pediu.
function InlineList({ items, sep = "; " }) {
  const txt = (Array.isArray(items) ? items : [])
    .map((t) => String(t || "").trim())
    .filter(Boolean)
    .map((t) =>
      t
        .replace(/^[-•\s]+/, "")
        .replace(/^[a-e]\)\s*/i, "")
        .replace(/\s*;\s*$/, "")
        .replace(/\s*\.\s*$/, "")
    )
    .join(sep);

  if (!txt) return null;
  return (
    <p style={{ marginTop: 10, fontSize: 15, lineHeight: 1.75, opacity: 0.92 }}>
      {txt.endsWith(".") ? txt : `${txt}.`}
    </p>
  );
}

function AlphaList({ items }) {
  return (
    <div style={{ marginTop: 10, paddingLeft: 18, fontSize: 15, lineHeight: 1.7, opacity: 0.92 }}>
      {items.map((t, i) => (
        <div key={i} style={{ marginTop: 6 }}>
          <b>{String.fromCharCode(97 + i)})</b> {t}
        </div>
      ))}
    </div>
  );
}

export default function ArtigoPage() {
  const w = useWindowWidth();
  const mobile = w < 980;

  const slug = slugFromURL();

  const artigo = useMemo(() => {
    if (slug === "no-estrutural") {
      return {
        categoria: "Artigo",
        titulo: "O Nó Estrutural da Gestão nas Prefeituras",
        subtitulo: "Por que bons projetos travam — e como destravar com estrutura, dados e governança.",
        leitura: "5–6 min",
        autor: "José Antônio da Silva Júnior",
        credenciais: "Doutor em Ciências Sociais · Secretário Executivo do CONCEN · CEO da IDEAL Desenvolvimento Estratégico",
        // Texto corrido (sem tópicos)
        resumo:
          "O problema central não é só recurso: é a estrutura (processos, sistemas e governança) que não sustenta o ciclo completo da política pública. Sem rotina, indicadores e dados integrados, a gestão vira reativa e perde continuidade. O caminho é prático: fluxos claros, responsáveis, integração mínima de dados e capacitação contínua orientada ao cotidiano.",
        etapas: [
          "Planejar com base em diagnóstico e dados",
          "Executar com continuidade",
          "Monitorar com indicadores confiáveis",
          "Avaliar com método",
          "Ajustar as ações com base em evidências",
        ],
        secoes: [
          {
            id: "no",
            h2: "O Nó Estrutural",
            blocks: [
              "A administração pública municipal, sobretudo em cidades pequenas e médias, enfrenta desafios que vão além de recurso: a estrutura institucional — processos, sistemas, regras e cultura — frequentemente não sustenta o ciclo completo da política pública.",
              "Quando o dia a dia é manual, fragmentado e sem governança, até projetos promissores travam no meio do caminho.",
            ],
          },
          {
            id: "ciclo",
            h2: "O ciclo mínimo que precisa funcionar",
            blocks: [
              "Política pública vira resultado quando o ciclo vira rotina — com responsável, prazo, evidência e indicadores. Planejar com base em diagnóstico e dados; executar com continuidade; monitorar com indicadores confiáveis; avaliar com método; ajustar as ações com base nas evidências.",
              "Sem esse ciclo, a gestão fica reativa: apaga incêndios, perde memória institucional e repete erros.",
            ],
          },
          {
            id: "gargalos",
            h2: "Os gargalos que mais travam a prefeitura",
            blocks: [
              "Na prática, o nó estrutural aparece em processos fragmentados e manuais; sistemas isolados (sem integração); ausência de governança entre secretarias; perda de memória institucional a cada troca de governo; cultura de urgência (sem estratégia) e prioridades difusas.",
              "O efeito é instabilidade, improviso e decisões reativas — o que derruba continuidade e desempenho.",
            ],
          },
          {
            id: "pessoas",
            h2: "Pessoas e continuidade: sem método, a gestão vira reativa",
            blocks: [
              "Com equipes pequenas, a prefeitura até entrega o básico, mas não consegue fazer o trabalho estruturante (planejar, medir, avaliar e melhorar).",
              "Mesmo onde há equipe, sem capacitação contínua e com rotatividade alta, o município não acumula rotina, indicadores e memória institucional.",
              "Isso impede atividades essenciais como desenhar políticas e projetos com começo–meio–fim, monitorar indicadores regularmente, padronizar rotinas e reduzir retrabalho, e implementar inovação administrativa sem depender de “heróis”.",
              "Isso não é falta de esforço do servidor: é excesso de demanda sem estrutura.",
            ],
          },
          {
            id: "dados",
            h2: "Dados e planejamento que saem do papel",
            blocks: [
              "Planejar sem dados é governar no escuro. Sem bases integradas e indicadores regulares, decisões dependem de percepção, intuição ou pressão.",
              "Quando o PPA vira apenas formalidade, orçamento e execução se desconectam — e cada secretaria corre para apagar incêndios.",
              "Esse cenário costuma vir acompanhado de cadastros e sistemas que não conversam entre si, indicadores inexistentes ou irregulares, metas e prazos sem acompanhamento e planejamento desconectado da prática.",
            ],
            callout: "“Planejar sem dados é como governar no escuro.”",
          },
          {
            id: "checklist",
            h2: "O que fazer agora (checklist)",
            blocks: [
              "Um caminho realista para as próximas 8–12 semanas é: mapear e padronizar fluxos críticos (entrada → decisão → execução → evidência); definir responsáveis e SLAs por etapa; integrar cadastros mínimos (pessoas, unidades, serviços) para reduzir duplicidade; criar indicadores simples e acompanhar mensalmente; implantar capacitação curta e contínua; instituir governança intersetorial; e aproximar universidade/terceiro setor quando fizer sentido.",
              "Com rotina e dados, até cidades pequenas ganham escala, continuidade e resultado — com melhor uso do recurso público.",
            ],
          },
          {
            id: "conclusao",
            h2: "Conclusão",
            blocks: [
              "Modernizar a gestão municipal é, antes de tudo, fortalecer capacidade institucional: processos, pessoas, dados e governança.",
              "Com isso, boas políticas deixam de depender de improviso e passam a virar entrega real para a população.",
            ],
          },
        ],
        assinatura: [
          "José Antônio da Silva Júnior",
          "Doutor em Ciências Sociais",
          "Secretário Executivo do CONCEN",
          "CEO da Ideal Desenvolvimento Estratégico",
        ],
      };
    }

    if (slug === "diagnostico-execucao") {
      return {
        categoria: "Artigo",
        titulo: "Do diagnóstico à execução: governança de dados e software para entregar resultado na gestão municipal",
        subtitulo: "Por que a entrega trava — e como transformar plano em rotina com dados confiáveis, fluxo e monitoramento.",
        leitura: "7–8 min",
        autor: "José Antônio da Silva Júnior",
        credenciais: "Doutor em Ciências Sociais · Secretário Executivo do CONCEN · CEO da IDEAL Desenvolvimento Estratégico",
        resumo:
          "A política pública costuma travar não só por recurso, mas pela falta de uma ponte operacional entre planejamento e execução. Governança de dados cria consistência e confiança na informação; software de execução organiza fluxo, prazos, responsabilidades e monitoramento. Resultado: o município sai do “planeja e corre atrás” e entra no “executa, monitora e melhora”.",
        etapas: [
          "Planejar com base em diagnóstico e dados",
          "Executar com continuidade",
          "Monitorar com indicadores confiáveis",
          "Avaliar com método",
          "Ajustar as ações com base em evidências",
        ],
        secoes: [
          {
            id: "ponte",
            h2: "A ponte entre planejar e executar",
            blocks: [
              "Todo prefeito já viveu isso: o município faz diagnóstico, define prioridades, publica plano, anuncia metas — e, mesmo assim, a entrega não acontece no ritmo esperado. A política pública “existe”, mas a execução se perde no caminho.",
              "Na prática, o problema raramente é só dinheiro. O que mais trava é a ponte entre planejar e executar: informações espalhadas, processos sem padrão, pouca clareza de responsabilidades, falta de acompanhamento e decisões sem base consistente.",
              "É aqui que entram dois pilares que mudam a gestão: governança de dados e software de execução e monitoramento.",
            ],
          },
          {
            id: "vida-real",
            h2: "O que impede a entrega (na vida real)",
            blocks: [
              "Quando não existe um sistema que organize a execução, o município cai em quatro problemas recorrentes: dados desencontrados (cada área com sua planilha e seu número), processos sem fluxo (ninguém sabe o próximo passo e quem responde), acompanhamento fraco (o atraso aparece tarde) e pouca visão de resultado (muito esforço, pouco impacto medido).",
            ],
          },
          {
            id: "governanca",
            h2: "Governança de dados: decidir com informação confiável",
            blocks: [
              "Governança de dados é criar regras simples para que o município trabalhe com dados padronizados, confiáveis, acessíveis, seguros (com controle de acesso e LGPD) e úteis para decisão.",
              "Quando isso existe, o gestor responde com rapidez perguntas que definem resultado: onde está o gargalo do serviço, qual território concentra mais demanda, o que está atrasado e por quê, e o que precisa de prioridade agora.",
            ],
          },
          {
            id: "software",
            h2: "Software de execução: transformar plano em rotina",
            blocks: [
              "Um bom software não é “mais um sistema”. Ele organiza o trabalho para a política pública sair do papel.",
              "Ele transforma o processo em passo a passo claro: etapas, responsáveis e evidências do que foi feito. Isso reduz retrabalho e evita “perder o caso” no caminho.",
              "Também coloca prazos por etapa (SLA), alerta atrasos e mostra onde travou — apontando gargalos por equipe, serviço e território. A gestão para de correr atrás de crise e passa a corrigir no caminho.",
              "Por fim, dá visibilidade do que depende de quem na rede: pendências entre áreas, encaminhamentos e pontos de destrave entre secretarias e serviços.",
            ],
          },
          {
            id: "monitoramento",
            h2: "Monitoramento: governar pelo que entrega",
            blocks: [
              "Sem acompanhamento, meta vira discurso. Com software, monitoramento vira rotina: indicadores simples por serviço e território, painel de atrasos e prioridades, relatórios consistentes para gestão, conselhos e controle, e histórico do que foi feito (memória institucional).",
              "Resultado: prefeito e secretários passam a gerir com dados — não com impressão.",
            ],
          },
          {
            id: "importa",
            h2: "Por que isso importa para prefeito e gestor municipal",
            blocks: [
              "Na prática, governança de dados + software de execução entregam mais serviço com o mesmo recurso (menos desperdício e retrabalho), mais rapidez no atendimento (prazos e alertas), priorização de verdade com base em dados, mais transparência e prestação de contas, e continuidade mesmo com troca de equipe.",
            ],
          },
          {
            id: "ideal",
            h2: "Como a IDEAL atua: do diagnóstico à entrega",
            blocks: [
              "A IDEAL conecta quatro pontos que normalmente ficam soltos: diagnóstico orientado a decisão, planejamento com foco em execução, governança de dados (padrão, qualidade e segurança) e software para executar, monitorar e medir resultado.",
              "O objetivo é direto: transformar plano em rotina e rotina em resultado mensurável.",
            ],
          },
          {
            id: "metodo",
            h2: "Resultado não é sorte. É método.",
            blocks: [
              "Gestão pública que entrega não depende de herói. Depende de processo claro, dados confiáveis e ferramenta para acompanhar a execução.",
              "A IDEAL ajuda o município a sair do “planeja e corre atrás” e entrar no “executa, monitora e melhora”.",
            ],
          },
        ],
        assinatura: [
          "José Antônio da Silva Júnior",
          "Doutor em Ciências Sociais",
          "Secretário Executivo do CONCEN",
          "CEO da Ideal Desenvolvimento Estratégico",
        ],
      };
    }

    return null;
  }, [slug]);

  useEffect(() => {
    if (artigo?.titulo) document.title = `${artigo.titulo} · IDEAL`;
  }, [artigo]);

  if (!artigo) {
    return (
      <div style={{ padding: 24 }}>
        <Card title="Artigo não encontrado">
          Verifique o link. Ex.: <code>?artigo=no-estrutural</code>
        </Card>
      </div>
    );
  }

  const page = {
    padding: mobile ? 14 : 22,
    background: "linear-gradient(180deg, rgba(122,92,255,0.10), rgba(255,255,255,0.00) 70%)",
  };

  const shell = {
    maxWidth: 1040,
    margin: "0 auto",
  };

  const topbar = {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    gap: 12,
    padding: "12px 14px",
    borderRadius: 18,
    border: "1px solid rgba(0,0,0,0.06)",
    background: "rgba(255,255,255,0.72)",
    boxShadow: "0 14px 34px rgba(0,0,0,0.08)",
  };

  const layout = {
    display: "grid",
    gridTemplateColumns: "1fr",
    gap: 14,
    alignItems: "start",
    marginTop: 14,
  };

  return (
    <div style={page}>
      <style>{`
        @media print {
          .no-print { display: none !important; }
          body { background: white !important; }
        }
      `}</style>

      <div style={shell}>
        {/* TOP BAR */}
        <div style={topbar}>
          <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
            <img
              src="/ideal-icon.png"
              alt="IDEAL"
              style={{ width: 56, height: 56, borderRadius: 18, objectFit: "contain" }}
              onError={(e) => (e.currentTarget.style.display = "none")}
            />
            <div>
              <div style={{ fontWeight: 900, fontSize: 13, opacity: 0.75, letterSpacing: 0.6 }}>
                IDEAL · INTELIGÊNCIA PÚBLICA E DE MERCADO
              </div>
              <div style={{ fontWeight: 980, fontSize: 18 }}>Biblioteca & Artigos</div>
            </div>
          </div>

          <div className="no-print" style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
            <Btn onClick={() => (window.history.length > 1 ? window.history.back() : (window.location.href = "/"))}>
              ← Voltar
            </Btn>
            <Btn primary onClick={() => window.print()}>
              Imprimir / PDF
            </Btn>
          </div>
        </div>

        <div style={layout}>
          {/* MAIN */}
          <div>
            <Card>
              <Chip>{artigo.categoria}</Chip>

              <div
                style={{
                  marginTop: 12,
                  fontSize: mobile ? 34 : 52,
                  fontWeight: 990,
                  lineHeight: 1.02,
                  letterSpacing: -1,
                  background: GRADIENT,
                  WebkitBackgroundClip: "text",
                  WebkitTextFillColor: "transparent",
                  color: "transparent",
                }}
              >
                {artigo.titulo}
              </div>

              <div style={{ marginTop: 10, fontSize: 16, opacity: 0.86, fontWeight: 750 }}>
                {artigo.subtitulo}
              </div>

              <div style={{ marginTop: 10, display: "flex", gap: 10, flexWrap: "wrap", fontSize: 12, opacity: 0.8 }}>
                <span><b>Leitura:</b> {artigo.leitura}</span>
                <span>·</span>
                <span><b>Autor:</b> {artigo.autor}</span>
              </div>
            </Card>

            {artigo.resumo ? (
              <div style={{ marginTop: 12 }}>
                <Callout title="Em 30 segundos">
	                  {Array.isArray(artigo.resumo) ? (
	                    <InlineList items={artigo.resumo} sep="; " />
	                  ) : (
	                    <p style={{ marginTop: 10, fontSize: 15, lineHeight: 1.75, opacity: 0.92 }}>{artigo.resumo}</p>
	                  )}
                </Callout>
              </div>
            ) : null}

            <div style={{ marginTop: 12 }}>
              <Callout title="O ciclo mínimo da política pública">
	                {Array.isArray(artigo.etapas) ? (
	                  <InlineList items={artigo.etapas} sep="; " />
	                ) : (
	                  <p style={{ marginTop: 10, fontSize: 15, lineHeight: 1.75, opacity: 0.92 }}>{artigo.etapas}</p>
	                )}
              </Callout>
            </div>

            
  {/* BODY */}
  <div style={{ marginTop: 12, display: "grid", gap: 12 }}>
    <Card>
      {artigo.secoes.map((sec, sidx) => (
        <div
          key={sec.id}
          style={{
            paddingTop: sidx === 0 ? 0 : 18,
            marginTop: sidx === 0 ? 0 : 18,
            borderTop: sidx === 0 ? "none" : "1px solid rgba(0,0,0,0.06)",
          }}
        >
          <div id={sec.id} style={{ fontWeight: 990, fontSize: 22, letterSpacing: -0.4 }}>
            {sec.h2}
          </div>

          {sec.blocks?.map((p, idx) => (
            <p key={idx} style={{ marginTop: 10, fontSize: 15, lineHeight: 1.75, opacity: 0.92 }}>
              {p}
            </p>
          ))}

	          {sec.alpha ? <InlineList items={sec.alpha} sep="; " /> : null}
	          {sec.bullets ? <InlineList items={sec.bullets} sep="; " /> : null}

          {sec.after ? (
            <p style={{ marginTop: 10, fontSize: 15, lineHeight: 1.75, opacity: 0.92 }}>
              {sec.after}
            </p>
          ) : null}

          {sec.callout ? (
            <div style={{ marginTop: 12 }}>
              <Callout title="Frase-chave">
                <div style={{ fontSize: 15, lineHeight: 1.6, opacity: 0.95 }}>{sec.callout}</div>
              </Callout>
            </div>
          ) : null}
        </div>
      ))}
    </Card>

    <Card title="Assinatura">
      <div style={{ display: "grid", gap: 6, fontSize: 15, lineHeight: 1.7, opacity: 0.92 }}>
        {artigo.assinatura.map((t, i) => (
          <div key={i} style={{ fontWeight: i === 0 ? 990 : 700 }}>
            {t}
          </div>
        ))}
      </div>
    </Card>

    <Card title="Contato / demonstração">
      <div style={{ display: "grid", gap: 10, fontSize: 14, opacity: 0.92 }}>
        <div>Quer aplicar isso no seu município?</div>
        <div className="no-print" style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
          <Btn primary onClick={() => (window.location.href = "#contato")}>Agendar demonstração</Btn>
          <Btn onClick={() => (window.location.href = "/")}>Voltar ao site</Btn>
        </div>
      </div>
    </Card>
  </div>
</div>
        </div>
      </div>
    </div>
  );
}
