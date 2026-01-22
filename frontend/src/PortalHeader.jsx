import React from "react";
import { useNavigate } from "react-router-dom";
import "./Portal.css";

function safeKeydown(e, fn) {
  if (e.key === "Enter" || e.key === " ") {
    e.preventDefault();
    fn?.();
  }
}

function scrollToId(id) {
  const el = document.getElementById(id);
  if (!el) return;
  try {
    el.scrollIntoView({ behavior: "smooth", block: "start" });
  } catch (err) {
    try {
      el.scrollIntoView();
    } catch (_) {}
  }
}

export default function PortalHeader({
  onEntrar,
  backTo = "/",
  backLabel = "Início",
  showNav = false,
  navItems,
  activeNavId,
}) {
  const navigate = useNavigate();

  const items =
    navItems ||
    [
      { label: "SUAS", id: "sec-assistencia" },
      { label: "Saúde", id: "sec-saude" },
      { label: "Educação", id: "sec-educacao" },
    ];

  return (
    <header className="portalNewsTop">
      <div className="portalNewsTop-inner">
        <button
          type="button"
          className="portalNewsTop-brandBtn"
          onClick={() => navigate("/")}
          onKeyDown={(e) => safeKeydown(e, () => navigate("/"))}
          aria-label="Voltar para o início"
        >
          <div className="portalNewsBrand">
            {/* Marca (ícone) */}
            <img className="portalNewsBrand-mark" src="/ideal-icon.png" alt="" aria-hidden="true" />
            <div className="portalNewsBrand-text">
              <div className="portalNewsBrand-title">
                Plataforma Municipal <span className="portalNewsBrand-highlight">Integrada</span>
              </div>
              <div className="portalNewsBrand-sub">Portal de Atualizações</div>
            </div>
          </div>
        </button>

        {showNav && (
          <nav className="portalNewsTop-nav" aria-label="Seções do portal">
            {items.map((it) => (
              <button
                key={it.id}
                type="button"
                className={`portalNewsTop-chip ${activeNavId && String(activeNavId) === String(it.id) ? "portalNewsTop-chipActive" : ""}`}
                onClick={() => (typeof it?.onClick === "function" ? it.onClick() : scrollToId(it.id))}
                onKeyDown={(e) => safeKeydown(e, () => (typeof it?.onClick === "function" ? it.onClick() : scrollToId(it.id)))}
                aria-current={activeNavId && String(activeNavId) === String(it.id) ? "page" : undefined}
              >
                {it.label}
              </button>
            ))}
          </nav>
        )}

        <div className="portalNewsTop-actions">
          <button
            type="button"
            className="portal3-btn-secondary portalNewsTop-backBtn"
            onClick={() => navigate(backTo)}
            onKeyDown={(e) => safeKeydown(e, () => navigate(backTo))}
            aria-label={backLabel}
          >
            ← {backLabel}
          </button>

          <button
            type="button"
            className="portal3-btn-primary portalNewsTop-ctaBtn"
            onClick={() => onEntrar?.()}
            onKeyDown={(e) => safeKeydown(e, () => onEntrar?.())}
            aria-label="Acessar o painel"
          >
            Acessar o painel
          </button>
        </div>
      </div>
    </header>
  );
}
