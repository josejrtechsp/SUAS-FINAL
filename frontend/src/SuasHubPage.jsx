import React, { useMemo, useState } from "react";
import "./SuasHub.css";

function Illus({ kind = "generic" }) {
  const common = { width: "100%", height: "100%", viewBox: "0 0 120 70", fill: "none" };
  const stroke = "rgba(255,255,255,0.75)";
  const stroke2 = "rgba(255,255,255,0.35)";

  if (kind === "suas") {
    return (
      <svg {...common}>
        <path d="M20 45c12-14 26-22 40-22s28 8 40 22" stroke={stroke} strokeWidth="4" strokeLinecap="round"/>
        <circle cx="40" cy="46" r="8" stroke={stroke} strokeWidth="4"/>
        <circle cx="80" cy="46" r="8" stroke={stroke} strokeWidth="4"/>
        <path d="M60 18v36" stroke={stroke2} strokeWidth="3" strokeLinecap="round"/>
      </svg>
    );
  }

  if (kind === "health") {
    return (
      <svg {...common}>
        <path d="M60 18v34" stroke={stroke} strokeWidth="6" strokeLinecap="round"/>
        <path d="M43 35h34" stroke={stroke} strokeWidth="6" strokeLinecap="round"/>
        <path d="M22 55c10-8 22-12 38-12s28 4 38 12" stroke={stroke2} strokeWidth="4" strokeLinecap="round"/>
      </svg>
    );
  }

  if (kind === "edu") {
    return (
      <svg {...common}>
        <path d="M20 30l40-14 40 14-40 14-40-14z" stroke={stroke} strokeWidth="4" strokeLinejoin="round"/>
        <path d="M30 38v14c10 8 20 10 30 10s20-2 30-10V38" stroke={stroke2} strokeWidth="4" strokeLinecap="round"/>
        <path d="M98 32v18" stroke={stroke2} strokeWidth="4" strokeLinecap="round"/>
      </svg>
    );
  }

  if (kind === "map") {
    return (
      <svg {...common}>
        <path d="M18 20l28-8 28 8 28-8v40l-28 8-28-8-28 8V20z" stroke={stroke} strokeWidth="3" strokeLinejoin="round"/>
        <path d="M46 12v40" stroke={stroke2} strokeWidth="3"/>
        <path d="M74 20v40" stroke={stroke2} strokeWidth="3"/>
        <circle cx="62" cy="38" r="6" stroke={stroke} strokeWidth="3"/>
      </svg>
    );
  }

  if (kind === "docs") {
    return (
      <svg {...common}>
        <path d="M34 12h34l14 14v32c0 4-3 6-6 6H34c-4 0-6-2-6-6V18c0-4 2-6 6-6z" stroke={stroke} strokeWidth="3"/>
        <path d="M68 12v16h16" stroke={stroke2} strokeWidth="3"/>
        <path d="M38 40h44" stroke={stroke2} strokeWidth="3" strokeLinecap="round"/>
        <path d="M38 50h34" stroke={stroke2} strokeWidth="3" strokeLinecap="round"/>
      </svg>
    );
  }

  return (
    <svg {...common}>
      <path d="M18 52c10-14 22-22 42-22s32 8 42 22" stroke={stroke} strokeWidth="4" strokeLinecap="round"/>
      <circle cx="40" cy="28" r="8" stroke={stroke2} strokeWidth="3"/>
      <circle cx="80" cy="28" r="8" stroke={stroke2} strokeWidth="3"/>
    </svg>
  );
}

function Card({ m, onSelect }) {
  const active = m.status === "ativo";
  return (
    <div className="suashub6-card">
      <div className="suashub6-cardHead">
        <div className="suashub6-cardIcon"><Illus kind={m.illus} /></div>
        <div className={"suashub6-pill " + (active ? "suashub6-pillOk" : "suashub6-pillSoon")}>{active ? "ATIVO" : "EM BREVE"}</div>
      </div>
      <div className="suashub6-cardBody">
        <div className="suashub6-cardTitle">{m.title}</div>
        <div className="suashub6-cardDesc">{m.desc}</div>
        <div className="suashub6-cardActions">
          {active ? (
            <button className="suashub6-cardBtn suashub6-cardBtnPrimary" type="button" onClick={() => onSelect?.(m.id)}>
              Entrar
            </button>
          ) : (
            <button className="suashub6-cardBtn" type="button" disabled>Em breve</button>
          )}
        </div>
      </div>
    </div>
  );
}

export default function SuasHubPage({ onBack, onSelect }) {
  const [area, setArea] = useState("suas");

  const areas = useMemo(() => ({
    educacao: {
      label: "Educação",
      icon: "🎓",
      desc: "Matrícula, risco de evasão, intervenção, inclusão, transporte e merenda — em fluxo.",
      modules: [
        { id: "vagas", title: "Vagas & Matrícula", desc: "Fila auditável e critérios", status: "breve", illus: "edu" },
        { id: "evasao", title: "Frequência & Evasão", desc: "Alertas + tarefas automáticas", status: "breve", illus: "edu" },
        { id: "pedagogico", title: "Intervenção pedagógica", desc: "Metas, responsáveis e prazo", status: "breve", illus: "docs" },
        { id: "inclusiva", title: "Educação inclusiva (AEE)", desc: "PEI/PDI + rede com LGPD", status: "breve", illus: "edu" },
        { id: "transporte_escolar", title: "Transporte escolar", desc: "Rotas, ocorrências e conformidade", status: "breve", illus: "map" },
        { id: "merenda", title: "Merenda", desc: "Cardápio → execução → evidência", status: "breve", illus: "docs" },
      ],
    },

    saude: {
      label: "Saúde",
      icon: "🩺",
      desc: "APS, regulação, farmácia e vigilância com SLA, evidências e gestão por gargalos.",
      modules: [
        { id: "aps", title: "APS em rede (UBS/ESF)", desc: "Pendências, linha de cuidado e SLA", status: "breve", illus: "health" },
        { id: "regulacao", title: "Regulação (fila)", desc: "Prioridade com evidência e auditoria", status: "breve", illus: "docs" },
        { id: "farmacia", title: "Farmácia", desc: "Ruptura, consumo e rastreabilidade", status: "breve", illus: "health" },
        { id: "vigilancia", title: "Vigilância", desc: "Ação imediata + checklist", status: "breve", illus: "map" },
        { id: "mental", title: "Saúde mental", desc: "Gestão de caso e rede", status: "breve", illus: "health" },
        { id: "transporte", title: "Transporte sanitário", desc: "Agendamento, rotas e evidências", status: "breve", illus: "map" },
      ],
    },

    suas: {
      label: "Assistência Social (SUAS)",
      icon: "🤝",
      desc: "PopRua, CRAS e CREAS com fluxo, SLA, evidências e rede.",
      modules: [
        { id: "poprua", title: "Pop Rua", desc: "Atendimento e gestão de caso", status: "ativo", illus: "suas" },
        { id: "cras", title: "CRAS", desc: "Proteção Social Básica", status: "ativo", illus: "suas" },
        { id: "creas", title: "CREAS", desc: "Proteção Social Especial (PAEFI)", status: "ativo", illus: "suas" },
        { id: "centropop", title: "Centro POP", desc: "Serviços e rotinas do Centro POP", status: "breve", illus: "map" },
        { id: "terceiro_setor", title: "Terceiro Setor", desc: "OSCs, parcerias (MROSC), metas e prestação de contas", status: "ativo", illus: "docs" },
        { id: "gestao", title: "Gestão", desc: "Dashboard do secretário (SLA, fila e rede)", status: "ativo", illus: "docs" },
      ],
    },
  }), []);

  const a = areas[area];

  return (
    <div className="suashub6-root">
      <aside className="suashub6-sidebar">
        <div className="suashub6-brand">
          <img className="suashub6-logo" src="/ideal-logo-alpha.png" alt="IDEAL" />
        </div>

        <div className="suashub6-sidebarTitle">Áreas</div>
        <div className="suashub6-nav">
          <button className={"suashub6-navBtn " + (area === "educacao" ? "suashub6-navBtnActive" : "")} onClick={() => setArea("educacao")} type="button">
            <div className="suashub6-navIcon">🎓</div>
            <div>
              <div>Educação</div>
              <div className="suashub6-navDesc">Matrícula, evasão, inclusão</div>
            </div>
          </button>

          <button className={"suashub6-navBtn " + (area === "saude" ? "suashub6-navBtnActive" : "")} onClick={() => setArea("saude")} type="button">
            <div className="suashub6-navIcon">🩺</div>
            <div>
              <div>Saúde</div>
              <div className="suashub6-navDesc">Fluxo, SLA e evidências</div>
            </div>
          </button>

          <button className={"suashub6-navBtn " + (area === "suas" ? "suashub6-navBtnActive" : "")} onClick={() => setArea("suas")} type="button">
            <div className="suashub6-navIcon">🤝</div>
            <div>
              <div>Assistência Social</div>
              <div className="suashub6-navDesc">PopRua, CRAS e CREAS</div>
            </div>
          </button>
        </div>

        <div className="suashub6-sidebarActions">
          <button className="suashub6-btn" type="button" onClick={() => onBack?.()}>← Voltar</button>
        </div>
      </aside>

      <main className="suashub6-main">
        <div className="suashub6-top">
          <div>
            <div className="suashub6-title">{a.label}</div>
            <div className="suashub6-sub">{a.desc}</div>
          </div>
        </div>

        <div className="suashub6-content">
          <div className="suashub6-grid">
            {a.modules.map((m) => (
              <Card key={m.id} m={m} onSelect={onSelect} />
            ))}
          </div>
        </div>
      </main>
    </div>
  );
}
