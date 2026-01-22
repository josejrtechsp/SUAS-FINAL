import React, { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";

import "./Portal.css";
import PortalHeader from "./PortalHeader.jsx";

import { PORTAL_ATUALIZACOES } from "./content/portalAtualizacoesData.js";

/* -------------------- helpers -------------------- */
function formatDateBR(iso) {
  if (!iso) return "";
  const parts = String(iso).split("-");
  if (parts.length !== 3) return iso;
  const [y, m, d] = parts;
  if (!y || !m || !d) return iso;
  return `${d}/${m}/${y}`;
}

function areaShort(key) {
  if (key === "assistencia") return "SUAS";
  if (key === "saude") return "SUS";
  if (key === "educacao") return "EDU";
  return "ÁREA";
}

function coverForArea(key) {
  if (key === "assistencia") return "/portal-cover-suas.svg";
  if (key === "saude") return "/portal-cover-sus.svg";
  if (key === "educacao") return "/portal-cover-edu.svg";
  return "/portal-cover-sus.svg";
}

function tagForItem(item) {
  const t = (item?.tipo || "").trim();
  if (!t) return "ATUALIZAÇÃO";
  return t.toUpperCase();
}

function getAllSorted(items) {
  return (items || [])
    .slice()
    .sort((a, b) => String(b?.data || "").localeCompare(String(a?.data || "")));
}

function useWindowWidth() {
  const [w, setW] = useState(() => (typeof window === "undefined" ? 1200 : window.innerWidth));
  useEffect(() => {
    const on = () => setW(window.innerWidth);
    window.addEventListener("resize", on);
    return () => window.removeEventListener("resize", on);
  }, []);
  return w;
}

function useBlocoParam(defaultKey = "assistencia") {
  const read = () => {
    try {
      const u = new URL(window.location.href);
      return u.searchParams.get("bloco") || defaultKey;
    } catch {
      return defaultKey;
    }
  };
  const [bloco, setBloco] = useState(read);

  useEffect(() => {
    const onPop = () => setBloco(read());
    window.addEventListener("popstate", onPop);
    return () => window.removeEventListener("popstate", onPop);
  }, []);

  const go = (next) => {
    try {
      const u = new URL(window.location.href);
      u.searchParams.set("bloco", next);
      window.history.pushState({}, "", u.toString());
    } catch (_) {}
    setBloco(next);
    try {
      window.scrollTo({ top: 0, behavior: "smooth" });
    } catch (_) {
      window.scrollTo(0, 0);
    }
  };

  return { bloco, go };
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

function Chip({ children }) {
  return (
    <span
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 8,
        padding: "8px 10px",
        borderRadius: 999,
        border: "1px solid rgba(0,0,0,0.06)",
        background: "rgba(255,255,255,0.70)",
        fontSize: 13,
        fontWeight: 850,
      }}
    >
      {children}
    </span>
  );
}

function MiniRow({ u, onOpen }) {
  return (
    <button
      type="button"
      onClick={() => onOpen?.(u?.slug)}
      style={{
        width: "100%",
        textAlign: "left",
        border: "1px solid rgba(0,0,0,0.06)",
        background: "rgba(255,255,255,0.65)",
        borderRadius: 14,
        padding: 10,
        cursor: "pointer",
      }}
      aria-label={u?.titulo ? `Abrir: ${u.titulo}` : "Abrir"}
    >
      <div style={{ display: "flex", justifyContent: "space-between", gap: 10, fontSize: 12, opacity: 0.85 }}>
        <div style={{ fontWeight: 900 }}>{u?.area ? areaShort(u.area) : ""}{u?.area ? " · " : ""}{tagForItem(u)}</div>
        <div style={{ opacity: 0.7 }}>{formatDateBR(u?.data)}</div>
      </div>
      <div style={{ marginTop: 6, fontWeight: 980, fontSize: 14, lineHeight: 1.2 }}>{u?.titulo}</div>
      {u?.resumo ? <div style={{ marginTop: 4, fontSize: 13, opacity: 0.85, lineHeight: 1.35 }}>{u.resumo}</div> : null}
    </button>
  );
}

function HeadlineBtn({ item, active, index, onPick }) {
  const kicker = `${areaShort(item?.area)} · ${tagForItem(item)}`;
  return (
    <button
      type="button"
      onClick={() => onPick?.(item)}
      className={`portal3-hlBtn ${active ? "is-active" : ""}`}
      aria-label={item?.titulo ? `Selecionar: ${item.titulo}` : "Selecionar"}
    >
      <div className="portal3-hlIdx">{String(index + 1).padStart(2, "0")}</div>
      <div className="portal3-hlBody">
        <div className="portal3-hlKicker">{kicker}</div>
        <div className="portal3-hlTitle">{item?.titulo}</div>
      </div>
      <div className="portal3-hlDate">{formatDateBR(item?.data)}</div>
    </button>
  );
}

/* -------------------- page -------------------- */
export default function AtualizacoesPage({ onEntrar }) {
  const navigate = useNavigate();
  const w = useWindowWidth();
  const mobile = w < 980;
  const { bloco, go } = useBlocoParam("assistencia");

  const grouped = useMemo(() => {
    const base = { assistencia: [], saude: [], educacao: [] };
    (PORTAL_ATUALIZACOES || []).forEach((it) => {
      const k = (it?.area || "").trim();
      if (k && base[k]) base[k].push(it);
    });
    Object.keys(base).forEach((k) => {
      base[k] = getAllSorted(base[k]);
    });
    return base;
  }, []);

  const allSorted = useMemo(() => getAllSorted(PORTAL_ATUALIZACOES), []);

  const defs = useMemo(
    () => ({
      assistencia: {
        key: "assistencia",
        icon: "🤝",
        menuTitle: "SUAS",
        menuDesc: "Cofinanciamento, CNAS/FNAS, prazos e prestação de contas (texto claro).",
        pill: "SUAS",
        title: "Assistência Social (SUAS)",
        tagline: "Regras, repasses e resoluções — com impacto e checklist operacional.",
      },
      saude: {
        key: "saude",
        icon: "🩺",
        menuTitle: "Saúde",
        menuDesc: "Portarias, repasses e orientações do SUS — com evidência e execução.",
        pill: "SUS",
        title: "Saúde (SUS)",
        tagline: "Financiamento e orientações operacionais — em linguagem clara, com evidência e execução.",
      },
      educacao: {
        key: "educacao",
        icon: "🎓",
        menuTitle: "Educação",
        menuDesc: "FNDE/MEC: PDDE, repasses, regras, reprogramação e prestação de contas.",
        pill: "EDU",
        title: "Educação (MEC/FNDE)",
        tagline: "Regras e repasses — com o que mudou, risco e checklist do que fazer.",
      },
      ultimas: {
        key: "ultimas",
        icon: "🗞️",
        menuTitle: "Últimas",
        menuDesc: "Tudo que saiu nos últimos meses, em todos os blocos (SUAS/SUS/EDU).",
        pill: "Últimas",
        title: "Últimas atualizações",
        tagline: "Uma visão geral do que é mais relevante (tudo interno, em português claro).",
      },
    }),
    []
  );

  const order = ["assistencia", "saude", "educacao", "ultimas"];
  const current = defs[bloco] || defs.assistencia;

  const items = useMemo(() => {
    if (current.key === "ultimas") return allSorted;
    return grouped?.[current.key] || [];
  }, [allSorted, grouped, current.key]);

  // seleção (portal estilo UOL/G1): lista de manchetes à direita + explicação à esquerda
  const [selectedSlug, setSelectedSlug] = useState(() => items?.[0]?.slug || "");
  useEffect(() => {
    const next = items?.[0]?.slug || "";
    setSelectedSlug(next);
  }, [current.key]);

  const selected = useMemo(() => {
    if (!items?.length) return null;
    return items.find((x) => x?.slug === selectedSlug) || items[0];
  }, [items, selectedSlug]);

  const pick = (it) => {
    if (!it?.slug) return;
    setSelectedSlug(it.slug);
    try {
      const el = document.getElementById("portal-selected");
      if (el) el.scrollIntoView({ behavior: "smooth", block: "start" });
    } catch (_) {}
  };

  const openItem = (slug) => {
    if (!slug) return;
    navigate(`/atualizacoes/${encodeURIComponent(slug)}`);
  };

  const outer = {
    borderRadius: 28,
    border: "1px solid rgba(0,0,0,0.06)",
    background: "linear-gradient(180deg, rgba(255,255,255,0.75), rgba(255,255,255,0.60))",
    boxShadow: "0 20px 55px rgba(0,0,0,0.10)",
    padding: mobile ? 18 : 24,
  };

  const headerRow = {
    display: "flex",
    flexDirection: "column",
    justifyContent: "space-between",
    alignItems: "flex-start",
    gap: 10,
    marginBottom: 16,
  };

  const layout = {
    display: "grid",
    gridTemplateColumns: mobile ? "1fr" : "1.45fr 0.55fr",
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

  const heroTitleStyle = {
    fontSize: mobile ? 30 : 44,
    fontWeight: 990,
    lineHeight: 1.05,
    marginTop: 10,
    letterSpacing: -0.8,
    background: "linear-gradient(90deg, #A855F7 0%, #6366F1 55%, #22D3EE 100%)",
    WebkitBackgroundClip: "text",
    WebkitTextFillColor: "transparent",
    color: "transparent",
  };

  const checklist = [
    "O que mudou (sem juridiquês)",
    "Impacto prático e risco para o município",
    "Checklist: responsável · prazo (SLA) · evidência",
    "Fonte citada no final (para conferência)",
  ];

  return (
    <div className="portal3-root">
      <PortalHeader
        onEntrar={onEntrar}
        backTo="/"
        backLabel="Início"
        showNav
        activeNavId={current.key}
        navItems={[
          { label: "SUAS", id: "assistencia", onClick: () => go("assistencia") },
          { label: "Saúde", id: "saude", onClick: () => go("saude") },
          { label: "Educação", id: "educacao", onClick: () => go("educacao") },
          { label: "Últimas", id: "ultimas", onClick: () => go("ultimas") },
        ]}
      />

      <main className="portal3-main">
        <section className="portal3-section">
          <div style={outer}>
            <div style={headerRow}>
              <div>
                <Pill>IDEAL — Portal de Atualizações</Pill>
                <div style={heroTitleStyle}>Atualizações oficiais para a gestão municipal</div>
                <div style={{ marginTop: 10, fontSize: 16, opacity: 0.85, maxWidth: 920 }}>
                  Financiamento, regras e resoluções (Governo Federal) — em português claro, com <b>impacto</b> e <b>checklist</b> do que fazer.
                </div>
                <div style={{ marginTop: 12, display: "flex", flexWrap: "wrap", gap: 10 }}>
                  <Chip>✅ Texto claro</Chip>
                  <Chip>✅ O que mudou + impacto</Chip>
                  <Chip>✅ Checklist (SLA + evidência)</Chip>
                  <Chip>✅ Fonte citada no final</Chip>
                </div>
              </div>
            </div>

            <div style={layout}>

              {/* LEFT: explicação da notícia selecionada */}
              <div id="portal-selected">
                <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 6 }}>
                  <Pill>{current.pill}</Pill>
                  <div style={{ fontSize: mobile ? 26 : 34, fontWeight: 980, letterSpacing: -0.6 }}>{current.title}</div>
                </div>
                <div style={{ fontSize: 15, opacity: 0.9, marginBottom: 14 }}>{current.tagline}</div>

                {selected ? (
                  <div style={{ display: "grid", gap: 12 }}>
                    {/* header da notícia (modelo home: título forte + cards) */}
                    <div
                      style={{
                        border: "1px solid rgba(0,0,0,0.06)",
                        borderRadius: 18,
                        overflow: "hidden",
                        background: "rgba(255,255,255,0.70)",
                      }}
                    >
                      <div style={{ height: 112, position: "relative" }}>
                        <img
                          src={coverForArea(selected?.area || current.key)}
                          alt=""
                          aria-hidden="true"
                          style={{ width: "100%", height: "100%", objectFit: "cover", display: "block" }}
                        />
                        <div
                          style={{
                            position: "absolute",
                            left: 12,
                            top: 12,
                            padding: "6px 10px",
                            borderRadius: 999,
                            background: "rgba(15,23,42,0.72)",
                            color: "#fff",
                            fontSize: 12,
                            fontWeight: 900,
                          }}
                        >
                          {areaShort(selected.area)} · {tagForItem(selected)}
                        </div>
                        <div
                          style={{
                            position: "absolute",
                            right: 12,
                            top: 12,
                            padding: "6px 10px",
                            borderRadius: 999,
                            background: "rgba(255,255,255,0.85)",
                            color: "#111827",
                            fontSize: 12,
                            fontWeight: 900,
                            border: "1px solid rgba(0,0,0,0.08)",
                          }}
                        >
                          {formatDateBR(selected.data)}
                        </div>
                      </div>

                      <div style={{ padding: 14 }}>
                        <div style={{ fontWeight: 990, fontSize: mobile ? 18 : 22, lineHeight: 1.15 }}>
                          {selected.titulo}
                        </div>
                        {selected.subtitulo ? (
                          <div style={{ marginTop: 8, fontSize: 14, opacity: 0.86, lineHeight: 1.4 }}>
                            {selected.subtitulo}
                          </div>
                        ) : null}

                        {selected.resumo ? (
                          <div style={{ marginTop: 10, fontSize: 14, opacity: 0.86, lineHeight: 1.45 }}>
                            {selected.resumo}
                          </div>
                        ) : null}

                        <a
                          href={`/atualizacoes/${encodeURIComponent(selected.slug)}`}
                          onClick={(e) => {
                            e.preventDefault();
                            openItem(selected.slug);
                          }}
                          className="portal3-link"
                          style={{ marginTop: 10, display: "inline-flex" }}
                        >
                          Abrir atualização completa →
                        </a>
                      </div>
                    </div>

                    <div style={{ display: "grid", gridTemplateColumns: mobile ? "1fr" : "1fr 1fr", gap: 12 }}>
                      <CardBox title="Em 30 segundos" icon="⚡">
                        <ItemList items={selected.em30s || []} bullet="✅" />
                      </CardBox>

                      <CardBox title="Decisão rápida" icon="🧭">
                        <ItemList items={selected.decisaoRapida || []} bullet="✅" />
                      </CardBox>
                    </div>

                    <div style={{ display: "grid", gridTemplateColumns: mobile ? "1fr" : "1fr 1fr", gap: 12 }}>
                      <CardBox title="O que fazer (3 passos)" icon="🧩">
                        <div style={{ display: "grid", gap: 10 }}>
                          {(selected.passos || []).slice(0, 3).map((s, idx) => (
                            <Step key={idx} n={idx + 1} title={s?.t} desc={s?.d} />
                          ))}
                        </div>
                      </CardBox>

                      <CardBox title="Evidência mínima (3 provas)" icon="📌">
                        <div style={{ display: "grid", gap: 10 }}>
                          {(selected.evidenciaMinima || []).slice(0, 3).map((e, idx) => (
                            <div key={idx} style={{ lineHeight: 1.35 }}>
                              <div style={{ fontWeight: 980 }}>{e?.t}</div>
                              <div style={{ marginTop: 4, fontSize: 13, opacity: 0.86 }}>{e?.d}</div>
                            </div>
                          ))}
                        </div>
                      </CardBox>
                    </div>
                  </div>
                ) : (
                  <div style={{ fontSize: 13, opacity: 0.8 }}>
                    Nenhuma atualização cadastrada ainda.
                    <div style={{ marginTop: 6 }}>
                      Edite <b>src/content/portalAtualizacoesData.js</b> para adicionar conteúdo.
                    </div>
                  </div>
                )}
              </div>

              {/* RIGHT: lista de títulos (manchetes) */}
              <div>
                <CardBox title={current.key === "ultimas" ? "Últimas (geral)" : "Títulos do bloco"} icon="🗞️">
                  {items?.length ? (
                    <div className="portal3-hlList">
                      {items.slice(0, 18).map((u, idx) => (
                        <HeadlineBtn
                          key={u.id || u.slug}
                          item={u}
                          index={idx}
                          active={u?.slug === selected?.slug}
                          onPick={pick}
                        />
                      ))}
                    </div>
                  ) : (
                    <div style={{ fontSize: 13, opacity: 0.8 }}>Sem itens por enquanto.</div>
                  )}
                  {current.key !== "ultimas" ? (
                    <div style={{ marginTop: 10 }}>
                      <a
                        href="#"
                        className="portal3-link"
                        onClick={(e) => {
                          e.preventDefault();
                          go("ultimas");
                        }}
                      >
                        Ver tudo (Últimas) →
                      </a>
                    </div>
                  ) : null}
                </CardBox>

                <div style={{ fontSize: 12, opacity: 0.7, lineHeight: 1.5, marginTop: 10 }}>
                  Conteúdo interno (IDEAL). As fontes aparecem no final de cada atualização.
                </div>
              </div>
            </div>
          </div>
        </section>

        <div className="portal3-cta-strip">
          <div style={{ minWidth: 0 }}>
            <div className="portal3-cta-strip-text">Como a IDEAL escreve essas atualizações</div>
            <div style={{ marginTop: 6, fontSize: 12, color: "#374151", lineHeight: 1.6 }}>
              Nós lemos as publicações oficiais e transformamos em três coisas: <b>o que mudou</b>, <b>impacto prático</b> e <b>o que fazer agora</b>.
              <br />
              Isso não substitui o ato oficial — mas economiza tempo e reduz erro na rotina do município.
            </div>
            <div style={{ marginTop: 8, fontSize: 12, color: "#6b7280" }}>
              Atenção: sempre valide a aplicação formal no ato normativo e na orientação do órgão responsável.
            </div>
          </div>
          <button
            type="button"
            className="portal3-btn-primary"
            onClick={() => navigate("/")}
            aria-label="Voltar ao início"
          >
            Voltar ao Início
          </button>
        </div>
      </main>
    </div>
  );
}
