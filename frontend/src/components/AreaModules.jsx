import React, { useMemo, useState } from "react";

function Illus({ kind = "generic" }) {
  const common = { width: "100%", height: "100%", viewBox: "0 0 120 70", fill: "none" };
  const stroke = "rgba(255,255,255,0.78)";
  const stroke2 = "rgba(255,255,255,0.40)";

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

function Card({ title, desc, badge, active, onEnter, illusKind }) {
  return (
    <div className={"am-card" + (active ? "" : " am-cardDisabled")}>
      <div className="am-cardHead">
        <div className="am-illus">
          <Illus kind={illusKind} />
        </div>
        <div className={"am-badge " + (active ? "am-badgeOk" : "am-badgeSoon")}>{badge}</div>
      </div>

      <div className="am-cardTitle">{title}</div>
      <div className="am-cardDesc">{desc}</div>

      <div className="am-cardActions">
        {active ? (
          <button className="am-btn am-btnPrimary" type="button" onClick={onEnter}>Entrar</button>
        ) : (
          <button className="am-btn" type="button" disabled>Em breve</button>
        )}
      </div>
    </div>
  );
}

export default function AreaModules({ onSelect }) {
  const [area, setArea] = useState("suas");

  const data = useMemo(() => ({
    educacao: {
      label: "Educação",
      items: [
        { id: "vagas", title: "Vagas & Matrícula", desc: "Fila auditável e critérios por evidência", active: false, badge: "EM BREVE", illus: "edu" },
        { id: "evasao", title: "Frequência & Evasão", desc: "Alertas + tarefas automáticas", active: false, badge: "EM BREVE", illus: "edu" },
        { id: "pedagogico", title: "Intervenção pedagógica", desc: "Plano simples por meta e prazo", active: false, badge: "EM BREVE", illus: "docs" },
        { id: "inclusiva", title: "Educação inclusiva (AEE)", desc: "PEI/PDI + rede com LGPD", active: false, badge: "EM BREVE", illus: "edu" },
        { id: "transporte", title: "Transporte escolar", desc: "Rotas, ocorrências e conformidade", active: false, badge: "EM BREVE", illus: "map" },
        { id: "merenda", title: "Merenda", desc: "Cardápio → consumo → entrega → evidência", active: false, badge: "EM BREVE", illus: "docs" },
      ],
    },

    saude: {
      label: "Saúde",
      items: [
        { id: "aps", title: "APS em rede (UBS/ESF)", desc: "Pendências, linha de cuidado e SLA", active: false, badge: "EM BREVE", illus: "health" },
        { id: "regulacao", title: "Regulação (fila)", desc: "Prioridade com evidência e auditoria", active: false, badge: "EM BREVE", illus: "docs" },
        { id: "farmacia", title: "Farmácia", desc: "Ruptura, consumo e rastreabilidade", active: false, badge: "EM BREVE", illus: "health" },
        { id: "vigilancia", title: "Vigilância", desc: "Ação imediata + checklist operacional", active: false, badge: "EM BREVE", illus: "map" },
        { id: "mental", title: "Saúde mental", desc: "Gestão de caso e rede com LGPD", active: false, badge: "EM BREVE", illus: "health" },
        { id: "transporte_san", title: "Transporte sanitário", desc: "Agendamento, rotas e evidências", active: false, badge: "EM BREVE", illus: "map" },
      ],
    },

    suas: {
      label: "Assistência Social (SUAS)",
      items: [
        { id: "poprua", title: "Pop Rua", desc: "Atendimento e gestão de caso", active: true, badge: "ATIVO", illus: "suas" },
        { id: "cras", title: "CRAS", desc: "Proteção Social Básica", active: true, badge: "ATIVO", illus: "suas" },
        { id: "creas", title: "CREAS", desc: "Proteção Social Especial (PAEFI)", active: true, badge: "ATIVO", illus: "suas" },
        { id: "centropop", title: "Centro POP", desc: "Rotinas e serviços do Centro POP", active: false, badge: "EM BREVE", illus: "map" },
        { id: "terceiro_setor", title: "Terceiro Setor", desc: "OSCs, parcerias e prestação de contas", active: false, badge: "EM BREVE", illus: "docs" },
        { id: "gestao", title: "Gestão", desc: "Relatórios, coordenação e governança", active: false, badge: "EM BREVE", illus: "docs" },
      ],
    },
  }), []);

  const items = data[area].items;

  const enter = (id) => {
    if (typeof onSelect === "function") return onSelect(id);
    // fallback: vai para login/hub
    window.location.href = "/hub";
  };

  return (
    <div className="am-wrap">
      <div className="am-left">
        <div className="am-leftTitle">Áreas</div>

        <button className={"am-nav" + (area === "educacao" ? " am-navActive" : "")} onClick={() => setArea("educacao")} type="button">
          Educação
        </button>
        <button className={"am-nav" + (area === "saude" ? " am-navActive" : "")} onClick={() => setArea("saude")} type="button">
          Saúde
        </button>
        <button className={"am-nav" + (area === "suas" ? " am-navActive" : "")} onClick={() => setArea("suas")} type="button">
          Assistência Social (SUAS)
        </button>

        <div className="am-leftHint">
          Módulos em <strong>3 por linha</strong> (sem rolagem lateral).
        </div>
      </div>

      <div className="am-right">
        <div className="am-rightHead">
          <div className="am-rightTitle">{data[area].label}</div>
          <div className="am-rightSub">Selecione um módulo para entrar (ativos) ou visualizar o roadmap (em breve).</div>
        </div>

        <div className="am-grid">
          {items.map((m) => (
            <Card
              key={m.id}
              title={m.title}
              desc={m.desc}
              active={m.active}
              badge={m.badge}
              illusKind={m.illus}
              onEnter={() => enter(m.id)}
            />
          ))}
        </div>
      </div>
    </div>
  );
}
