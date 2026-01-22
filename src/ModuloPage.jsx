import React, { useEffect, useMemo, useRef, useState } from "react";
import { useParams } from "react-router-dom";
import "./Portal.css";

const MODULES = {
  
  poprua: {
    key: "poprua",
    accent: "#06b6d4",
    accent2: "#4f46e5",
    kicker: "Módulo SUAS",
    title: "Pop Rua (abordagem, busca ativa e rede)",
    subtitle:
      "Gestão de caso e operação de rua com rastreabilidade por etapa e controle de exposição (LGPD).",
    kpis: [
      { label: "Abordagens (mês)", value: "—", hint: "por equipe/território" },
      { label: "Casos ativos", value: "—", hint: "por etapa" },
      { label: "Tempo de resposta", value: "—", hint: "média" },
    ],
    blocks: {
      resolve: [
        "Registro rápido na rua + histórico completo do caso.",
        "Linha do tempo por etapas com evidências e responsáveis.",
        "Encaminhamentos com status e devolutiva (rede).",
        "Gestão enxerga gargalos, recorrência e tempos de resposta.",
      ],
      flow: [
        { t: "Abordagem rápida", d: "Registro mínimo necessário e próximo passo." },
        { t: "Atendimento completo", d: "Escuta, orientações e plano inicial." },
        { t: "Encaminhamentos", d: "Destino + status + devolutiva." },
        { t: "Acompanhamento", d: "Pendências, prazos e validações." },
        { t: "Desfecho", d: "Encerramento com histórico e evidências." },
      ],
      features: [
        { icon: "⚡", t: "Registro ágil", d: "Abordagem 1 minuto + atendimento completo." },
        { icon: "🚇", t: "Linha do metrô", d: "Etapas clicáveis e histórico imutável." },
        { icon: "🛡️", t: "LGPD por perfil", d: "Exposição mínima e auditoria." },
        { icon: "📌", t: "Rede com devolutiva", d: "Encaminhamento → status → retorno." },
        { icon: "📊", t: "Indicadores", d: "Recorrência, tempo de resposta e desfechos." },
        { icon: "✅", t: "Protocolos", d: "Checklists e rotinas do Guia SUAS." },
      ],
      indicators: [
        "Abordagens/atendimentos por período e território",
        "Recorrência e tempo de resposta",
        "Desfechos por etapa e status",
      ],
      guia: [
        "Pop Rua: protocolos e rotinas",
        "LGPD na prática: mínimo necessário",
        "Fluxo por etapas e devolutivas",
        "Evidências e relatórios",
      ],
      faq: [
        { q: "É módulo SUS?", a: "Não. É fluxo intersetorial com exposição mínima de dados, sem prontuário clínico." },
        { q: "Funciona na rua?", a: "Sim: registro rápido e histórico por etapas. Offline pode ser evolução." },
        { q: "Como prova trabalho?", a: "Histórico imutável por etapa + auditoria e anexos." },
      ],
    },
  },
cras: {
    key: "cras",
    accent: "#4f46e5",
    accent2: "#7c3aed",
    kicker: "Módulo SUAS",
    title: "CRAS (PAIF / SCFV / encaminhamentos)",
    subtitle:
      "Do acolhimento à continuidade do acompanhamento: padronização do registro, fluxo por etapas e LGPD por perfil — com evidência para gestão.",
    kpis: [
      { label: "Triagens do mês", value: "—", hint: "por unidade/equipe" },
      { label: "Famílias acompanhadas", value: "—", hint: "PAIF / rede" },
      { label: "Encaminhamentos sem devolutiva", value: "—", hint: "alertas" },
    ],
    blocks: {
      resolve: [
        "Padroniza CRAS (evita “cada um registra de um jeito”) e reduz retrabalho.",
        "Mantém histórico contínuo do caso/família com plano e pendências.",
        "Organiza encaminhamentos e devolutivas com responsabilidade por etapa.",
        "Gera evidências para relatórios e prestação de contas com rastreabilidade.",
      ],
      flow: [
        { t: "Recepção e triagem", d: "Registro inicial guiado + demanda principal." },
        { t: "Cadastro/atualização", d: "Dados essenciais e validações (mínimo necessário)."},
        { t: "Avaliação e encaminhamento", d: "Orientações, encaminhamento e devolutiva esperada."},
        { t: "Plano (PAIF)", d: "Objetivos, ações, prazos e responsáveis."},
        { t: "Execução e registros", d: "Atividades/ações e acompanhamento com histórico recuperável."},
        { t: "Monitoramento", d: "Alertas de estagnação, pendências e fechamento/continuidade."},
      ],
      features: [
        { icon: "🧭", t: "Fluxo por etapas", d: "Etapas claras com validação e histórico contínuo." },
        { icon: "🛡️", t: "LGPD por perfil", d: "Acesso mínimo necessário e mascaramento quando aplicável." },
        { icon: "📌", t: "Encaminhamentos com devolutiva", d: "Status e responsabilidades para não perder o caso na rede." },
        { icon: "✅", t: "Checklist e rotinas", d: "Modelos prontos (Guia SUAS) para reduzir improviso." },
        { icon: "📊", t: "Indicadores e relatórios", d: "Evidências para gestão, auditoria e prestação de contas." },
        { icon: "🧾", t: "Rastreabilidade", d: "Quem fez, quando e o que mudou — segurança institucional." },
      ],
      indicators: [
        "Atendimentos por unidade/equipe/período",
        "Famílias acompanhadas, tempo de resposta e pendências",
        "Encaminhamentos por destino e devolutivas pendentes",
        "Evolução mensal e gargalos por etapa",
      ],
      guia: [
        "Tipificação e rotinas do CRAS (PAIF/SCFV)",
        "RMA: como registrar para gerar evidência",
        "LGPD na prática: perfis e campos sensíveis",
        "Fluxo recomendado: etapas e devolutivas",
      ],
      faq: [
        { q: "Isso substitui o Prontuário SUAS?", a: "O portal e o sistema organizam fluxo e governança. A estratégia pode ser operar como camada de padronização/gestão e evidências, conforme desenho do município." },
        { q: "Como evita retrabalho?", a: "Registro guiado, histórico contínuo, etapas claras e encaminhamentos com devolutiva — reduz repetição e perda de informação." },
        { q: "Como funciona LGPD?", a: "Acesso por perfil + auditoria. Informações sensíveis podem ser tratadas com mínimo necessário e mascaramento, conforme política do município." },
      ],
    },
  },

  creas: {
    key: "creas",
    accent: "#2563eb",
    accent2: "#4f46e5",
    kicker: "Módulo SUAS",
    title: "CREAS (PAEFI / violações / medidas)",
    subtitle:
      "Casos complexos com prazos, contexto preservado e rastreabilidade. LGPD aplicada por perfil e evidências para auditoria e prestação de contas.",
    kpis: [
      { label: "Casos ativos", value: "—", hint: "por etapa" },
      { label: "Pendências críticas", value: "—", hint: "prazo/alerta" },
      { label: "Tempo médio por etapa", value: "—", hint: "gargalos" },
    ],
    blocks: {
      resolve: [
        "Evita perda de contexto em casos complexos (histórico por etapa).",
        "Organiza prazos, pendências e responsáveis (alertas).",
        "Dá segurança institucional com LGPD e trilha de auditoria.",
        "Gera evidências para relatórios, prestação de contas e controle interno.",
      ],
      flow: [
        { t: "Entrada/Notificação", d: "Abertura do caso e classificação inicial." },
        { t: "Avaliação e risco", d: "Registro estruturado, dados sensíveis sob controle." },
        { t: "Plano de acompanhamento", d: "Objetivos, ações e prazos com responsáveis." },
        { t: "Execução e registros", d: "Evidências, anexos e movimentações por etapa." },
        { t: "Articulação de rede", d: "Encaminhamentos e devolutivas com status." },
        { t: "Monitoramento e encerramento", d: "Fechamento com justificativa e histórico completo." },
      ],
      features: [
        { icon: "⏱️", t: "Prazos e alertas", d: "Pendências e estagnação visíveis para coordenação." },
        { icon: "🧾", t: "Histórico por etapa", d: "Mudança gera registro (evidência), não “sobrescreve”." },
        { icon: "🛡️", t: "Dados sensíveis", d: "Acesso por perfil e política de exposição." },
        { icon: "📎", t: "Anexos e evidências", d: "Documentos/fotos com rastreabilidade." },
        { icon: "📌", t: "Rede com devolutiva", d: "Encaminhamento → recebido → atendido → devolutiva." },
        { icon: "📊", t: "Indicadores", d: "Tempo por etapa, gargalos e produtividade por equipe." },
      ],
      indicators: [
        "Casos por etapa/status e tempo médio em cada etapa",
        "Pendências em aberto e reincidência",
        "Produtividade por equipe/unidade",
        "Encaminhamentos sem devolutiva e prazos estourados",
      ],
      guia: [
        "Protocolos e fluxos do CREAS/PAEFI",
        "LGPD: campos sensíveis e auditoria",
        "Modelos de registro estruturado",
        "Relatórios e evidências para prestação de contas",
      ],
      faq: [
        { q: "Como a gestão enxerga gargalos?", a: "O sistema consolida tempo por etapa, pendências e alertas de estagnação, por unidade/equipe." },
        { q: "Dá para registrar anexos com segurança?", a: "Sim — com rastreabilidade e política de acesso por perfil. O que é sensível pode ser restrito." },
        { q: "E o controle social?", a: "Relatórios e evidências podem ser exibidos com mascaramento/anonimização quando necessário." },
      ],
    },
  },

  terceiro_setor: {
    key: "terceiro_setor",
    accent: "#7c3aed",
    accent2: "#ec4899",
    kicker: "Módulo SUAS",
    title: "Terceiro Setor (OSCs, parcerias e prestação de contas)",
    subtitle:
      "Organize execução, documentos e evidências por parceria — com transparência, trilha de auditoria e controle de acesso.",
    kpis: [
      { label: "Parcerias ativas", value: "—", hint: "por OSC" },
      { label: "Pendências documentais", value: "—", hint: "checklist" },
      { label: "Prestação de contas", value: "—", hint: "por período" },
    ],
    blocks: {
      resolve: [
        "Centraliza documentos e evidências por parceria (sem dispersão).",
        "Facilita análise e acompanhamento pela gestão com checklist e pendências.",
        "Apoia transparência e controle social com informação objetiva.",
        "Evita exposição indevida: acesso por perfil e auditoria.",
      ],
      flow: [
        { t: "Cadastro da OSC e parceria", d: "Informações essenciais e definição de escopo." },
        { t: "Plano de trabalho e metas", d: "Metas, atividades e calendário por período." },
        { t: "Execução (registros)", d: "Atividades e entregas registradas com evidências." },
        { t: "Documentos e comprovações", d: "Upload, organização e trilha por parceria." },
        { t: "Prestação de contas", d: "Checklist, pendências e versões por período." },
        { t: "Avaliação e renovação", d: "Resumo, indicadores e histórico para decisão." },
      ],
      features: [
        { icon: "📁", t: "Documentos por parceria", d: "Tudo organizado por OSC/período/objeto." },
        { icon: "✅", t: "Checklist de pendências", d: "A gestão enxerga o que falta em 1 clique." },
        { icon: "🔎", t: "Trilha de evidências", d: "Quem enviou/validou/quando — rastreabilidade." },
        { icon: "🛡️", t: "Acesso por perfil (LGPD)", d: "Acesso orientado à necessidade e auditoria." },
        { icon: "📊", t: "Relatórios", d: "Execução por parceria e consolidados para prestação de contas." },
        { icon: "🏛️", t: "Base para controle social", d: "Relatórios e evidências para CMAS, com governança." },
      ],
      indicators: [
        "Pendências documentais por parceria",
        "Execução por período (atividades/entregas registradas)",
        "Prestação de contas: status e conformidade",
        "Trilha de auditoria (acessos/exports)",
      ],
      guia: [
        "Modelos e checklist de prestação de contas",
        "Boas práticas de governança e transparência",
        "LGPD: o que pode/como expor com segurança",
        "Relatórios para gestão e CMAS",
      ],
      faq: [
        { q: "A OSC acessa o sistema?", a: "Pode — com perfil específico (restrito) para registrar execução e anexar documentos, conforme desenho do município." },
        { q: "Como evitar bagunça documental?", a: "Estrutura por parceria/período + checklist + evidências e trilha de auditoria." },
        { q: "Conselho consegue acompanhar?", a: "Sim — com visão orientada a relatórios/evidências e controle de exposição (LGPD)." },
      ],
    },
  },
};

function useScrollSpy(ids) {
  const [active, setActive] = useState(ids[0] || "visao");
  useEffect(() => {
    const els = ids.map((id) => document.getElementById(id)).filter(Boolean);
    if (!els.length) return;

    const io = new IntersectionObserver(
      (entries) => {
        const visible = entries.filter((e) => e.isIntersecting).sort((a, b) => b.intersectionRatio - a.intersectionRatio)[0];
        if (visible?.target?.id) setActive(visible.target.id);
      },
      { rootMargin: "-20% 0px -70% 0px", threshold: [0.08, 0.16, 0.24] }
    );

    els.forEach((el) => io.observe(el));
    return () => io.disconnect();
  }, [ids.join("|")]);
  return active;
}

function Section({ id, title, subtitle, children }) {
  return (
    <section className="mod2-section" id={id}>
      <div className="mod2-head">
        <h2 className="mod2-h2">{title}</h2>
        {subtitle ? <p className="mod2-sub">{subtitle}</p> : null}
      </div>
      {children}
    </section>
  );
}

function Card({ icon, title, text }) {
  return (
    <div className="mod2-card">
      <div className="mod2-ico">{icon}</div>
      <div className="mod2-ct">{title}</div>
      <div className="mod2-cd">{text}</div>
    </div>
  );
}

function Accordion({ items }) {
  const [open, setOpen] = useState(0);
  return (
    <div className="mod2-acc">
      {items.map((it, idx) => (
        <button
          key={idx}
          type="button"
          className={"mod2-accItem" + (open == idx ? " is-open" : "")}
          onClick={() => setOpen(open == idx ? -1 : idx)}
        >
          <div className="mod2-accQ">{it.q}</div>
          <div className="mod2-accA">{it.a}</div>
        </button>
      ))}
    </div>
  );
}

export default function ModuloPage({ onEntrar }) {
  const { id } = useParams();
  const key = (id || "").toLowerCase();
  const mod = MODULES[key];

  const ids = ["visao", "fluxo", "funcionalidades", "indicadores", "guia", "faq"];
  const active = useScrollSpy(ids);

  useEffect(() => {
    if (mod?.title) document.title = `${mod.title} — Portal SUAS`;
  }, [mod?.title]);

  if (!mod) {
    return (
      <div className="portal3-root">
        <header className="portal3-topbar">
          <div className="portal3-topbar-inner">
            <div className="portal3-brandWrap">
  <img className="portal3-logo" src="/ideal-logo.png" alt="IDEAL"  loading="lazy" decoding="async" />
  <div className="portal3-brand">
    <div className="portal3-brand-tag">IDEAL · INTELIGÊNCIA PÚBLICA E DE MERCADO</div>
    <div className="portal3-brand-title">Plataforma Municipal <span className="portal3-brand-highlight">Integrada</span></div>
    <div className="portal3-brand-sub">GovTech • Pesquisa • Diagnóstico • Monitoramento • Execução</div>
  </div>
</div>

<div className="portal3-actions">
              <button type="button" className="portal3-btn-secondary" onClick={() => (window.location.href = "/#modulos")}>
                ← Portal
              </button>
              <button type="button" className="portal3-btn-primary" onClick={() => onEntrar?.()}>
                Acessar o painel
              </button>
            </div>
          </div>
        </header>

        <main className="portal3-main">
          <section className="portal3-section">
            <div className="portal3-empty">Módulo inválido: “{id}”.</div>
          </section>
        </main>
      </div>
    );
  }

  return (
    <div className="mod2-root" style={{ "--accent": mod.accent, "--accent2": mod.accent2 }}>
      <header className="mod2-top">
        <div className="mod2-topInner">
          <div className="mod2-brand">
            <div className="mod2-tag">{mod.kicker} · Inteligencia Social</div>
            <div className="mod2-title">{mod.title}</div>
            <div className="mod2-subtitle">{mod.subtitle}</div>
          </div>

          <div className="mod2-actions">
            <button type="button" className="portal3-btn-secondary" onClick={() => (window.location.href = "/#modulos")}>
              ← Portal
            </button>
            <button type="button" className="portal3-btn-primary" onClick={() => onEntrar?.()}>
              Acessar o painel
            </button>
          </div>
        </div>
      </header>

      <div className="mod2-hero">
        <div className="mod2-heroInner">
          <div className="mod2-kpis">
            {mod.kpis.map((k, i) => (
              <div key={i} className="mod2-kpi">
                <div className="mod2-kpiLabel">{k.label}</div>
                <div className="mod2-kpiValue">{k.value}</div>
                <div className="mod2-kpiHint">{k.hint}</div>
              </div>
            ))}
          </div>

          <div className="mod2-ctaRow">
            <button type="button" className="portal3-btn-primary portal3-btn-big" onClick={() => onEntrar?.()}>
              Ver no painel (login)
            </button>
            <a className="mod2-link" href="#fluxo">Fluxo do serviço ↓</a>
            <a className="mod2-link" href="#indicadores">Indicadores ↓</a>
          </div>

          <div className="mod2-nav">
            {ids.map((sid) => (
              <a key={sid} className={"mod2-navItem" + (active === sid ? " is-active" : "")} href={`#${sid}`}>
                {sid === "visao" ? "Visão" :
                 sid === "fluxo" ? "Fluxo" :
                 sid === "funcionalidades" ? "Funcionalidades" :
                 sid === "indicadores" ? "Indicadores" :
                 sid === "guia" ? "Guia SUAS" : "FAQ"}
              </a>
            ))}
          </div>
        </div>
      </div>

      <main className="mod2-main">
        <Section id="visao" title="O que esse módulo resolve?" subtitle="Objetivo: padrão, continuidade e evidências — com proteção de dados.">
          <div className="mod2-split">
            <div className="mod2-panel">
              <ul className="mod2-bullets">
                {mod.blocks.resolve.map((t, i) => <li key={i}>{t}</li>)}
              </ul>
            </div>
            <div className="mod2-panel mod2-panelSoft">
              <div className="mod2-panelTitle">Padrão de governança</div>
              <div className="mod2-panelText">
                Acesso por perfil, trilha de auditoria e fluxo por etapas. O gestor enxerga gargalos e a ponta trabalha com clareza do “próximo passo”.
              </div>
              <button type="button" className="portal3-btn-secondary" onClick={() => (window.location.href = "/#guia")}>
                Abrir Guia SUAS (portal)
              </button>
            </div>
          </div>
        </Section>

        <Section id="fluxo" title="Fluxo do serviço" subtitle="Etapas claras, responsáveis e validação — o caso não se perde.">
          <div className="mod2-timeline">
            {mod.blocks.flow.map((s, i) => (
              <div key={i} className="mod2-step">
                <div className="mod2-stepN">{i + 1}</div>
                <div className="mod2-stepBody">
                  <div className="mod2-stepT">{s.t}</div>
                  <div className="mod2-stepD">{s.d}</div>
                </div>
              </div>
            ))}
          </div>
        </Section>

        <Section id="funcionalidades" title="Como o sistema ajuda" subtitle="Funcionalidades práticas para ganhar rotina (sem improviso).">
          <div className="mod2-grid">
            {mod.blocks.features.map((f, i) => (
              <Card key={i} icon={f.icon} title={f.t} text={f.d} />
            ))}
          </div>
        </Section>

        <Section id="indicadores" title="Indicadores e evidências" subtitle="Gestão e coordenação com dados que sustentam decisão e prestação de contas.">
          <div className="mod2-grid">
            {mod.blocks.indicators.map((t, i) => (
              <Card key={i} icon="📊" title={t} text="Painéis e exportações com controle de exposição (LGPD), quando necessário." />
            ))}
          </div>

          <div className="mod2-cta">
            <div className="mod2-ctaText">
              Quer ver isso no seu município? Comece por este módulo e evolua para o SUAS completo.
            </div>
            <button type="button" className="portal3-btn-primary" onClick={() => onEntrar?.()}>
              Acessar o painel
            </button>
          </div>
        </Section>

        <Section id="guia" title="Guia SUAS recomendado" subtitle="Tópicos do portal que orientam a equipe (modelo pronto + linguagem simples).">
          <div className="mod2-grid">
            {mod.blocks.guia.map((t, i) => (
              <Card key={i} icon="📚" title={t} text="No portal, com referências oficiais e modelos operacionais." />
            ))}
          </div>
        </Section>

        <Section id="faq" title="Perguntas frequentes" subtitle="Respostas diretas para implantação e governança.">
          <Accordion items={mod.blocks.faq} />
        </Section>

        <footer className="mod2-footer">
          <div><strong>Portal SUAS</strong> • Inteligencia Social</div>
          <div className="mod2-footerMuted">Página do módulo: /modulos/{mod.key}</div>
        </footer>
      </main>
    </div>
  );
}
