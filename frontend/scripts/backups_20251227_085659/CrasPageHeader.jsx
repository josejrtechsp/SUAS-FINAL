import React from "react";

/**
 * Cabeçalho padrão CRAS (modelo do print) — compacto e full width.
 * Compatível com props antigas: tips, badge, rightText
 * e novas: bullets, rightTag, rightMetaLabel/rightMetaValue
 */
export default function CrasPageHeader({
  kicker = "MÓDULO SUAS · INTELIGÊNCIA SOCIAL",
  title,
  subtitle,
  bullets,
  tips,
  rightTag,
  badge,
  rightMetaLabel = "Usuário",
  rightMetaValue = "—",
  rightText,
}) {
  const lista = (bullets && bullets.length ? bullets : tips) || [];
  const tag = rightTag || badge || "CRAS";

  return (
    <div
      className="card"
      style={{
        width: "100%",
        maxWidth: "100%",
        padding: 14,
        borderRadius: 18,
        border: "1px solid rgba(2,6,23,.08)",
        background:
          "radial-gradient(1200px 420px at 25% 0%, rgba(99,102,241,.12), rgba(255,255,255,.70))",
        boxShadow: "0 10px 30px rgba(2,6,23,.07)",
      }}
    >
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "1fr 280px",
          gap: 14,
          alignItems: "start",
        }}
      >
        <div>
          <div
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: 8,
              padding: "5px 10px",
              borderRadius: 999,
              border: "1px solid rgba(99,102,241,.25)",
              background: "rgba(99,102,241,.08)",
              color: "rgb(79,70,229)",
              fontWeight: 900,
              letterSpacing: ".10em",
              textTransform: "uppercase",
              fontSize: 11,
            }}
          >
            {kicker}
          </div>

          <div style={{ marginTop: 6, fontSize: 30, fontWeight: 950, color: "rgb(2,6,23)", lineHeight: 1.08 }}>
            {title}
          </div>

          {subtitle ? (
            <div style={{ marginTop: 6, fontSize: 16, color: "rgba(2,6,23,.65)", lineHeight: 1.35 }}>
              {subtitle}
            </div>
          ) : null}

          {lista.length ? (
            <div style={{ marginTop: 10 }}>
              {lista.map((t, idx) => (
                <div key={idx} style={{ display: "flex", gap: 10, alignItems: "flex-start", marginTop: 6, fontSize: 16 }}>
                  <span aria-hidden style={{ lineHeight: "20px" }}>✅</span>
                  <div style={{ color: "rgba(2,6,23,.85)" }}>{t}</div>
                </div>
              ))}
            </div>
          ) : null}
        </div>

        <div>
          <div
            style={{
              height: 24,
              borderRadius: 999,
              background: "rgba(14,165,233,.12)",
              border: "1px solid rgba(14,165,233,.18)",
              display: "flex",
              alignItems: "center",
              padding: "0 10px",
            }}
          >
            <span style={{ fontSize: 12, fontWeight: 900, color: "rgb(3,105,161)" }}>{tag}</span>
          </div>

          <div style={{ marginTop: 6, color: "rgba(2,6,23,.65)", fontSize: 13 }}>
            {rightText ? (
              rightText
            ) : (
              <>
                {rightMetaLabel}: <strong style={{ color: "rgba(2,6,23,.9)" }}>{rightMetaValue}</strong>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
