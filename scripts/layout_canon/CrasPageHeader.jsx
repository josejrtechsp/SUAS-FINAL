import React from "react";

export default function CrasPageHeader({
  moduleTag = "MÓDULO SUAS · INTELIGÊNCIA SOCIAL",
  moduleChip = "CRAS",
  userLabel = "Usuário:",
  userName = "—",
  title = "Título",
  subtitle = "",
  bullets = [],
}) {
  return (
    <div
      style={{
        // IMPORTANT: app-main é flex-wrap; sem isso, o header encolhe e não ocupa a largura total.
        width: "100%",
        flex: "0 0 100%",
        borderRadius: 22,
        padding: 18,
        background: "rgba(255,255,255,0.70)",
        border: "1px solid rgba(0,0,0,0.06)",
        boxShadow: "0 18px 60px rgba(0,0,0,0.12)",
        backdropFilter: "blur(10px)",
        WebkitBackdropFilter: "blur(10px)",
        marginBottom: 18,
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", gap: 16 }}>
        {/* LEFT */}
        <div style={{ flex: 1, minWidth: 0 }}>
          <div
            style={{
              display: "inline-flex",
              alignItems: "center",
              padding: "6px 10px",
              borderRadius: 999,
              border: "1px solid rgba(122, 92, 255, 0.25)",
              background: "rgba(122, 92, 255, 0.10)",
              fontSize: 12,
              fontWeight: 800,
              letterSpacing: 1,
              textTransform: "uppercase",
              color: "rgba(92, 74, 220, 1)",
              marginBottom: 10,
            }}
          >
            {moduleTag}
          </div>

          <div style={{ fontSize: 34, fontWeight: 900, lineHeight: 1.1 }}>
            {title}
          </div>

          {subtitle ? (
            <div style={{ marginTop: 6, fontSize: 16, opacity: 0.8 }}>
              {subtitle}
            </div>
          ) : null}

          {bullets?.length ? (
            <div style={{ marginTop: 12 }}>
              {bullets.map((b, i) => (
                <div key={i} style={{ display: "flex", gap: 10, marginTop: 6 }}>
                  <span aria-hidden="true">✅</span>
                  <div style={{ opacity: 0.88 }}>{b}</div>
                </div>
              ))}
            </div>
          ) : null}
        </div>

        {/* RIGHT */}
        <div style={{ width: 280, maxWidth: "40%" }}>
          <div
            style={{
              display: "inline-flex",
              alignItems: "center",
              justifyContent: "center",
              width: "100%",
              padding: "6px 10px",
              borderRadius: 999,
              border: "1px solid rgba(0,0,0,0.06)",
              background: "rgba(100,180,255,0.18)",
              fontWeight: 900,
              letterSpacing: 0.5,
              marginBottom: 10,
              color: "rgba(0,90,170,1)",
            }}
          >
            {moduleChip}
          </div>

          <div style={{ opacity: 0.75, fontWeight: 700 }}>{userLabel} <span style={{ opacity: 1, fontWeight: 900 }}>{userName}</span></div>
        </div>
      </div>
    </div>
  );
}
