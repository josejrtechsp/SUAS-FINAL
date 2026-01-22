import React, { useMemo } from "react";

function Icon({ name }) {
  const common = { width: 18, height: 18, viewBox: "0 0 24 24", fill: "none", xmlns: "http://www.w3.org/2000/svg" };
  const stroke = { stroke: "currentColor", strokeWidth: 2, strokeLinecap: "round", strokeLinejoin: "round" };

  switch (name) {
    case "home":
      return (
        <svg {...common}>
          <path {...stroke} d="M3 10.5 12 3l9 7.5V21a1 1 0 0 1-1 1h-5v-7H9v7H4a1 1 0 0 1-1-1v-10.5Z" />
        </svg>
      );
    case "clipboard":
      return (
        <svg {...common}>
          <path {...stroke} d="M9 5h6" />
          <path {...stroke} d="M9 3h6a2 2 0 0 1 2 2v16H7V5a2 2 0 0 1 2-2Z" />
          <path {...stroke} d="M9 7h6" />
        </svg>
      );
    case "cases":
      return (
        <svg {...common}>
          <path {...stroke} d="M8 7V6a4 4 0 0 1 8 0v1" />
          <path {...stroke} d="M5 7h14a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V9a2 2 0 0 1 2-2Z" />
        </svg>
      );
    case "send":
      return (
        <svg {...common}>
          <path {...stroke} d="M22 2 11 13" />
          <path {...stroke} d="M22 2 15 22l-4-9-9-4 20-7Z" />
        </svg>
      );
    case "tasks":
      return (
        <svg {...common}>
          <path {...stroke} d="M9 11l3 3L22 4" />
          <path {...stroke} d="M2 12h6" />
          <path {...stroke} d="M2 6h10" />
          <path {...stroke} d="M2 18h10" />
        </svg>
      );
    case "id":
      return (
        <svg {...common}>
          <path {...stroke} d="M4 7h16v10H4V7Z" />
          <path {...stroke} d="M8 11h4" />
          <path {...stroke} d="M8 14h7" />
        </svg>
      );
    case "users":
      return (
        <svg {...common}>
          <path {...stroke} d="M17 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" />
          <path {...stroke} d="M9.5 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8Z" />
          <path {...stroke} d="M22 21v-2a3 3 0 0 0-2-2.83" />
          <path {...stroke} d="M16 3.17a4 4 0 0 1 0 7.66" />
        </svg>
      );
    case "grid":
      return (
        <svg {...common}>
          <path {...stroke} d="M10 3H3v7h7V3Z" />
          <path {...stroke} d="M21 3h-7v7h7V3Z" />
          <path {...stroke} d="M21 14h-7v7h7v-7Z" />
          <path {...stroke} d="M10 14H3v7h7v-7Z" />
        </svg>
      );
    case "calendar":
      return (
        <svg {...common}>
          <path {...stroke} d="M8 2v3" />
          <path {...stroke} d="M16 2v3" />
          <path {...stroke} d="M3 9h18" />
          <path {...stroke} d="M5 5h14a2 2 0 0 1 2 2v14H3V7a2 2 0 0 1 2-2Z" />
        </svg>
      );
    case "file":
      return (
        <svg {...common}>
          <path {...stroke} d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6Z" />
          <path {...stroke} d="M14 2v6h6" />
        </svg>
      );
    case "bolt":
      return (
        <svg {...common}>
          <path {...stroke} d="M13 2 3 14h7l-1 8 10-12h-7l1-8Z" />
        </svg>
      );
    case "doc":
      return (
        <svg {...common}>
          <path {...stroke} d="M7 3h7l5 5v13a1 1 0 0 1-1 1H7a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1Z" />
          <path {...stroke} d="M14 3v6h6" />
          <path {...stroke} d="M9 13h6" />
          <path {...stroke} d="M9 17h6" />
        </svg>
      );
    case "chart":
      return (
        <svg {...common}>
          <path {...stroke} d="M3 3v18h18" />
          <path {...stroke} d="M7 15v3" />
          <path {...stroke} d="M12 11v7" />
          <path {...stroke} d="M17 7v11" />
        </svg>
      );
    default:
      return (
        <svg {...common}>
          <circle {...stroke} cx="12" cy="12" r="9" />
        </svg>
      );
  }
}

export default function CrasSidebarNav({
  groups = [],
  activeKey = "",
  onChange = () => {},
  collapsed = false,
  onToggleCollapsed = () => {},
  query = "",
  setQuery = () => {},
  municipioNome = "Município",
  unidadeNome = "CRAS",
}) {
  const flat = useMemo(() => {
    const items = [];
    (groups || []).forEach((g) => (g.items || []).forEach((it) => items.push({ ...it, group: g.title })));
    return items;
  }, [groups]);

  const activeLabel = useMemo(() => {
    const found = flat.find((x) => x.key === activeKey);
    return found?.label || "—";
  }, [flat, activeKey]);

  const q = (query || "").trim().toLowerCase();

  const filteredGroups = useMemo(() => {
    if (!q) return groups;
    const out = [];
    for (const g of (groups || [])) {
      const items = (g.items || []).filter((it) => (it.label || "").toLowerCase().includes(q));
      if (items.length) out.push({ ...g, items });
    }
    return out;
  }, [groups, q]);

  return (
    <aside className={"cras-sidebar-v2" + (collapsed ? " is-collapsed" : "")}>
      <div className="cras-sidebar-v2-head">
        <div className="cras-sidebar-v2-title">
          <div className="cras-sidebar-v2-muni">CRAS</div>
          <div className="cras-sidebar-v2-sub">{activeLabel}</div>
        </div>

        <button type="button" className="cras-sidebar-v2-toggle" onClick={onToggleCollapsed} aria-label="Recolher/expandir menu">
          {collapsed ? "›" : "‹"}
        </button>
      </div>

      {!collapsed ? (
        <input
          className="cras-sidebar-v2-search"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Buscar aba…"
        />
      ) : null}

      <nav className="cras-sidebar-v2-nav" aria-label="Navegação CRAS">
        {(filteredGroups || []).map((g) => (
          <div key={g.title} className="cras-sidebar-v2-group">
            {!collapsed ? <div className="cras-sidebar-v2-group-title">{g.title}</div> : null}
            {(g.items || []).map((it) => {
              const isActive = it.key === activeKey;
              return (
                <button
                  key={it.key}
                  type="button"
                  className={"cras-sidebar-v2-item" + (isActive ? " is-active" : "")}
                  onClick={() => onChange(it.key)}
                  title={collapsed ? `${g.title} · ${it.label}` : undefined}
                  aria-current={isActive ? "page" : undefined}
                >
                  <span className="cras-sidebar-v2-icon"><Icon name={it.icon} /></span>
                  {!collapsed ? <span className="cras-sidebar-v2-label">{it.label}</span> : null}
                  {it.badge ? <span className="cras-sidebar-v2-badge">{it.badge}</span> : null}
                </button>
              );
            })}
          </div>
        ))}
      </nav>

      {!collapsed ? (
        <div className="cras-sidebar-v2-foot">
          <div className="cras-sidebar-v2-foot-strong">{unidadeNome}</div>
          <div className="cras-sidebar-v2-foot-soft" style={{marginTop:6}}>{municipioNome}</div>
          <div className="cras-sidebar-v2-foot-soft">Dica: use a busca para localizar uma aba rapidamente.</div>
        </div>
      ) : null}
    </aside>
  );
}
