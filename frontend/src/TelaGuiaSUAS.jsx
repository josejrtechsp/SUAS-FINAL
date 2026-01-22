import { useMemo, useState } from "react";
import "./GuiaSUAS.css";

import {
  GUIA_SUAS_CATEGORIAS,
  GUIA_SUAS_START_5MIN,
  GUIA_SUAS_TEMAS,
  GUIA_SUAS_BLOCOS,
} from "./content/guiaSuasContent";

function normalize(text) {
  return (text || "")
    .toString()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .trim();
}

async function copyToClipboard(text) {
  try {
    if (navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(text);
      return true;
    }
  } catch (e) {
    // fallback abaixo
  }
  try {
    const ta = document.createElement("textarea");
    ta.value = text;
    ta.setAttribute("readonly", "");
    ta.style.position = "absolute";
    ta.style.left = "-9999px";
    document.body.appendChild(ta);
    ta.select();
    document.execCommand("copy");
    document.body.removeChild(ta);
    return true;
  } catch (e) {
    return false;
  }
}

function buildTemaTexto(tema) {
  const s = tema?.sections || {};
  const lines = [];
  lines.push(`${tema?.title || "Tema"}`);
  lines.push(`Categoria: ${tema?.categoria || "-"}`);
  if (tema?.bloco) lines.push(`Bloco: ${tema.bloco}`);
  lines.push("");
  if (s.oque) {
    lines.push("O que é (30s)");
    lines.push(s.oque);
    lines.push("");
  }
  if (s.quando) {
    lines.push("Quando usar");
    lines.push(s.quando);
    lines.push("");
  }
  if (Array.isArray(s.como) && s.como.length) {
    lines.push("Como fazer (passo a passo)");
    s.como.forEach((item, idx) => lines.push(`${idx + 1}. ${item}`));
    lines.push("");
  }
  if (Array.isArray(s.erros) && s.erros.length) {
    lines.push("Erros comuns");
    s.erros.forEach((item) => lines.push(`- ${item}`));
    lines.push("");
  }
  if (Array.isArray(s.checklist) && s.checklist.length) {
    lines.push("Checklist");
    s.checklist.forEach((item) => lines.push(`- ${item}`));
    lines.push("");
  }
  if (s.texto) {
    lines.push("Texto pronto (copiar e colar)");
    lines.push(s.texto);
    lines.push("");
  }
  return lines.join("\n");
}

export default function TelaGuiaSUAS() {
  const [mode, setMode] = useState("categoria"); // categoria | biblioteca | start | tema
  const [cat, setCat] = useState("financiamento");
  const [temaId, setTemaId] = useState(null);
  const [tab, setTab] = useState("oque");
  const [q, setQ] = useState("");

  const [libCat, setLibCat] = useState("todas");
  const [libBlock, setLibBlock] = useState("todos");

  const temaById = useMemo(() => {
    const m = new Map();
    GUIA_SUAS_TEMAS.forEach((t) => m.set(t.id, t));
    return m;
  }, []);

  const tema = temaId ? temaById.get(temaId) : null;

  const categorias = useMemo(() => {
    // adiciona biblioteca como "pseudo categoria" no menu lateral
    return [
      ...GUIA_SUAS_CATEGORIAS,
      { key: "biblioteca", label: "Biblioteca", icon: "📚", desc: "Todos os temas em uma lista, com filtros." },
    ];
  }, []);

  const searchResults = useMemo(() => {
    const nq = normalize(q);
    if (!nq) return [];
    const hits = GUIA_SUAS_TEMAS.filter((t) => {
      const hay = [
        t.title,
        t.categoria,
        t.bloco,
        ...(t.keywords || []),
        t.sections?.oque,
        t.sections?.quando,
        (t.sections?.como || []).join(" "),
        (t.sections?.erros || []).join(" "),
        (t.sections?.checklist || []).join(" "),
        t.sections?.texto,
      ]
        .filter(Boolean)
        .join(" ");
      return normalize(hay).includes(nq);
    });
    return hits.slice(0, 60);
  }, [q]);

  const blocks = useMemo(() => {
    return (GUIA_SUAS_BLOCOS && GUIA_SUAS_BLOCOS[cat]) || [];
  }, [cat]);

  const temasDoBloco = useMemo(() => {
    const index = new Map();
    GUIA_SUAS_TEMAS.forEach((t) => index.set(t.id, t));
    return (bloco) => (bloco?.temaIds || []).map((id) => index.get(id)).filter(Boolean);
  }, []);

  const biblioteca = useMemo(() => {
    let items = GUIA_SUAS_TEMAS.slice();
    if (libCat !== "todas") items = items.filter((t) => t.categoria === libCat);
    if (libBlock !== "todos") items = items.filter((t) => t.bloco === libBlock);
    const nq = normalize(q);
    if (nq) {
      items = items.filter((t) => normalize([t.title, ...(t.keywords || [])].join(" ")).includes(nq));
    }
    return items.slice(0, 400);
  }, [libCat, libBlock, q]);

  const onOpenTema = (id) => {
    setTemaId(id);
    setMode("tema");
    setTab("oque");
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const onOpenCategoria = (key) => {
    if (key === "biblioteca") {
      setMode("biblioteca");
      setTemaId(null);
      return;
    }
    setCat(key);
    setMode("categoria");
    setTemaId(null);
  };

  const renderStart = () => (
    <div className="guia-card">
      <div className="guia-card-h">
        <div>
          <div className="guia-card-title">Começar por aqui (5 min)</div>
          <div className="muted">Um resumo rápido para quem chegou agora.</div>
        </div>
        <div className="guia-card-actions">
          <button
            type="button"
            className="btn btn-secundario btn-secundario-mini"
            onClick={() => onOpenCategoria("financiamento")}
          >
            Ir para Financiamento
          </button>
        </div>
      </div>

      <div className="guia-start-grid">
        {(GUIA_SUAS_START_5MIN?.cards || []).map((c, idx) => (
          <div className="guia-start-card" key={idx}>
            <div className="guia-start-title">{c.title}</div>
            <div className="guia-start-text">{c.text}</div>
          </div>
        ))}
      </div>
    </div>
  );

  const renderCategoria = () => (
    <>
      <div className="guia-breadcrumb">
        <span className="link" onClick={() => setMode("categoria")}>
          Guia SUAS
        </span>
        <span className="muted">›</span>
        <span className="muted">
          {GUIA_SUAS_CATEGORIAS.find((c) => c.key === cat)?.label || cat}
        </span>
      </div>

      <div className="guia-blocks">
        {blocks.map((b) => (
          <div className="guia-block" key={b.key}>
            <div className="guia-block-title">{b.title}</div>
            <div className="guia-block-desc">{b.desc}</div>

            <div className="guia-block-list">
              {temasDoBloco(b).map((t) => (
                <button
                  key={t.id}
                  type="button"
                  className="guia-topic"
                  onClick={() => onOpenTema(t.id)}
                  title={t.title}
                >
                  <div className="guia-topic-title">{t.title}</div>
                  <div className="guia-topic-cta">Abrir</div>
                </button>
              ))}
            </div>
          </div>
        ))}
      </div>
    </>
  );

  const renderBiblioteca = () => (
    <>
      <div className="guia-breadcrumb">
        <span className="link" onClick={() => setMode("categoria")}>
          Guia SUAS
        </span>
        <span className="muted">›</span>
        <span className="muted">Biblioteca</span>
      </div>

      <div className="guia-card">
        <div className="guia-card-h">
          <div>
            <div className="guia-card-title">Biblioteca</div>
            <div className="muted">Todos os temas, com filtros.</div>
          </div>
          <div className="guia-card-actions">
            <select className="input guia-select" value={libCat} onChange={(e) => setLibCat(e.target.value)}>
              <option value="todas">Todas as categorias</option>
              {GUIA_SUAS_CATEGORIAS.map((c) => (
                <option key={c.key} value={c.key}>
                  {c.label}
                </option>
              ))}
            </select>
            <select className="input guia-select" value={libBlock} onChange={(e) => setLibBlock(e.target.value)}>
              <option value="todos">Todos os blocos</option>
              <option value="entender">Entender o recurso</option>
              <option value="posso_gastar">Posso gastar com isso?</option>
              <option value="prestacao">Prestação de contas</option>
              <option value="organizacao">Organização</option>
              <option value="registro">Registro e indicadores</option>
              <option value="equipe">Equipe</option>
              <option value="equipamentos">Equipamentos</option>
              <option value="modelos">Modelos</option>
              <option value="faq">Perguntas rápidas</option>
              <option value="glossario">Glossário</option>
            </select>
          </div>
        </div>

        <div className="guia-lib-list">
          {!biblioteca.length ? (
            <div className="muted">Nenhum tema encontrado.</div>
          ) : (
            biblioteca.map((t) => (
              <button
                key={t.id}
                type="button"
                className="guia-lib-item"
                onClick={() => onOpenTema(t.id)}
              >
                <div className="guia-lib-title">{t.title}</div>
                <div className="guia-lib-meta">
                  <span className="muted">{t.categoria}</span>
                  <span className="muted">•</span>
                  <span className="muted">{t.bloco}</span>
                </div>
              </button>
            ))
          )}
        </div>
      </div>
    </>
  );

  const renderTema = () => {
    if (!tema) return null;

    const catLabel =
      GUIA_SUAS_CATEGORIAS.find((c) => c.key === tema.categoria)?.label || tema.categoria;

    const s = tema.sections || {};
    const tabs = [
      { key: "oque", label: "O que é" },
      { key: "quando", label: "Quando usar" },
      { key: "como", label: "Como fazer" },
      { key: "erros", label: "Erros comuns" },
      { key: "checklist", label: "Checklist" },
      { key: "texto", label: "Texto pronto" },
    ];

    const copyAll = async () => {
      await copyToClipboard(buildTemaTexto(tema));
    };

    const renderTab = () => {
      if (tab === "oque") return <div className="guia-theme-text">{s.oque || "—"}</div>;
      if (tab === "quando") return <div className="guia-theme-text">{s.quando || "—"}</div>;
      if (tab === "como")
        return (
          <ol className="guia-list">
            {(s.como || []).map((x, i) => (
              <li key={i}>{x}</li>
            ))}
          </ol>
        );
      if (tab === "erros")
        return (
          <ul className="guia-list">
            {(s.erros || []).map((x, i) => (
              <li key={i}>{x}</li>
            ))}
          </ul>
        );
      if (tab === "checklist")
        return (
          <ul className="guia-list">
            {(s.checklist || []).map((x, i) => (
              <li key={i}>{x}</li>
            ))}
          </ul>
        );
      return (
        <div>
          <div className="guia-theme-text">{s.texto || "—"}</div>
          <div style={{ marginTop: 10 }}>
            <button
              type="button"
              className="btn btn-secundario btn-secundario-mini"
              onClick={() => copyToClipboard(s.texto || "")}
            >
              Copiar texto pronto
            </button>
          </div>
        </div>
      );
    };

    return (
      <>
        <div className="guia-breadcrumb">
          <span className="link" onClick={() => onOpenCategoria(tema.categoria)}>
            {catLabel}
          </span>
          <span className="muted">›</span>
          <span className="muted">{tema.title}</span>
        </div>

        <div className="guia-theme">
          <div className="guia-theme-head">
            <div>
              <div className="guia-theme-title">{tema.title}</div>
              <div className="guia-theme-meta">
                <span className="chip">{catLabel}</span>
                <span className="chip">{tema.bloco}</span>
              </div>
            </div>

            <div className="guia-theme-actions">
              <button
                type="button"
                className="btn btn-secundario btn-secundario-mini"
                onClick={copyAll}
              >
                Copiar tudo
              </button>
              <button
                type="button"
                className="btn btn-secundario btn-secundario-mini"
                onClick={() => setMode("categoria")}
              >
                Voltar
              </button>
            </div>
          </div>

          <div className="guia-theme-body">
            <div className="guia-chips">
              {tabs.map((t) => (
                <button
                  key={t.key}
                  type="button"
                  className={"chip " + (tab === t.key ? "chip-ativo" : "")}
                  onClick={() => setTab(t.key)}
                >
                  {t.label}
                </button>
              ))}
            </div>

            {renderTab()}
          </div>
        </div>
      </>
    );
  };

  const sideCats = (
    <div className="guia-cat-list">
      {categorias.map((c) => (
        <button
          key={c.key}
          type="button"
          className={"guia-cat " + ((mode === "biblioteca" && c.key === "biblioteca") || (mode !== "biblioteca" && c.key === cat) ? "active" : "")}
          onClick={() => onOpenCategoria(c.key)}
        >
          <div className="guia-cat-icon">{c.icon}</div>
          <div className="guia-cat-body">
            <div className="guia-cat-title">{c.label}</div>
            <div className="guia-cat-desc">{c.desc}</div>
          </div>
        </button>
      ))}
    </div>
  );

  return (
    <section className="card card-wide guia-suas">
      <div className="guia-topbar">
        <div>
          <div className="guia-title">Guia SUAS — Gestão e Financiamento na prática</div>
          <div className="guia-subtitle">
            Conteúdos práticos para equipe e gestão: financiamento, organização e equipamentos do SUAS.
          </div>
        </div>

        <div className="guia-topbar-right">
          <button
            type="button"
            className="btn btn-secundario btn-secundario-mini"
            onClick={() => {
              setMode("start");
              setTemaId(null);
              window.scrollTo({ top: 0, behavior: "smooth" });
            }}
          >
            Começar por aqui (5 min)
          </button>
        </div>
      </div>

      <div className="guia-layout">
        <aside className="guia-sidebar">
          <div className="guia-sidebar-inner">
            <div className="guia-search-wrap">
              <input
                className="input guia-search"
                value={q}
                onChange={(e) => setQ(e.target.value)}
                placeholder="Pesquisar (ex.: benefício eventual, CRAS, capacitação...)"
              />
              <button
                type="button"
                className="btn btn-secundario btn-secundario-mini"
                onClick={() => setQ("")}
                title="Limpar busca"
              >
                Limpar
              </button>
            </div>

            {q && (
              <div className="guia-search-panel">
                <div className="guia-search-title">Resultados ({searchResults.length})</div>
                {searchResults.slice(0, 8).map((t) => (
                  <button
                    key={t.id}
                    type="button"
                    className="guia-search-item"
                    onClick={() => onOpenTema(t.id)}
                  >
                    <div className="guia-search-item-title">{t.title}</div>
                    <div className="muted">{t.categoria} • {t.bloco}</div>
                  </button>
                ))}
                {searchResults.length > 8 && (
                  <button
                    type="button"
                    className="guia-search-more"
                    onClick={() => setMode("biblioteca")}
                  >
                    Ver mais na Biblioteca
                  </button>
                )}
              </div>
            )}

            {sideCats}
          </div>
        </aside>

        <main className="guia-main">
          {mode === "start" && renderStart()}
          {mode === "biblioteca" && renderBiblioteca()}
          {mode === "tema" && renderTema()}
          {mode === "categoria" && renderCategoria()}
        </main>
      </div>
    </section>
  );
}
