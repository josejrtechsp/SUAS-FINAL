import React, { useEffect, useState } from "react";

/**
 * CRAS · Tab Context Header (legado)
 * Obs.: o CRAS UI v2 usa CrasPageHeader; este componente fica aqui
 * para compatibilidade/uso futuro.
 */
export default function CrasTabContextHeader({ activeTab, tabMeta, onGo }) {
  const meta = (tabMeta && activeTab && tabMeta[activeTab]) || (tabMeta && tabMeta.default) || {};
  const title = meta.title || "";
  const subtitle = meta.subtitle || "";
  const chips = meta.chips || meta.bullets || [];
  const actions = meta.actions || [];

  // CRAS_ENC_HEADER_MODES_V1 (legado)
  const isEnc = String(title || "").toLowerCase().includes("encaminh");
  const [encView, setEncView] = useState(() => {
    try {
      return localStorage.getItem("cras_enc_view") || "suas";
    } catch (e) {
      return "suas";
    }
  });

  useEffect(() => {
    if (!isEnc) return;
    try {
      localStorage.setItem("cras_enc_view", encView);
    } catch (e) {}
    const apply = () => {
      const el = document.querySelector(".cras-enc-split");
      if (el) el.setAttribute("data-enc-view", encView);
    };
    apply();
    setTimeout(apply, 0);
    setTimeout(apply, 120);
  }, [encView, isEnc]);

  return (
    <div className="cras-context-wrap">
      <div className="cras-context-inner">
        <div className="cras-context-left">
          <div className="cras-context-kicker">Você está em</div>
          <div className="cras-context-title">{title}</div>
          {subtitle ? <div className="cras-context-subtitle">{subtitle}</div> : null}

          {chips?.length ? (
            <div className="cras-context-chips" aria-label="Resumo da aba">
              {chips.slice(0, 4).map((c, idx) => (
                <span key={idx} className="cras-context-chip">
                  {c}
                </span>
              ))}
            </div>
          ) : null}
        </div>

        <div className="cras-context-right" aria-label="Atalhos">
          {(actions || []).slice(0, 2).map((a, idx) => (
            <button
              key={idx}
              type="button"
              className={
                "btn " +
                (a.kind === "secondary" ? "btn-secundario btn-secundario-mini" : "btn-primario btn-primario-mini")
              }
              onClick={() => onGo?.(a.tab)}
            >
              {a.label}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
