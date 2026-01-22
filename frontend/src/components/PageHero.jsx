import React from "react";

/**
 * PageHero (Padrão SUAS)
 * Compatível com chamadas antigas (chip/right/children) e novas (kicker/tips/badge/rightText/actions).
 * Objetivo: padronizar o "retângulo explicativo" (como CRAS/CREAS/Gestão) sem quebrar telas.
 */
export default function PageHero({
  // base
  title = "",
  subtitle = "",
  chip = "",
  right = null,
  children = null,

  // aliases / padrão SUAS
  kicker = "",
  tips = [],
  bullets = [],
  badge = "",
  rightText = null,
  actions = null,

  // opcional (se algum módulo quiser mostrar usuário)
  userLabel = "Usuário:",
  userName = "",
}) {
  const chipText = (kicker || chip || "").trim();
  const lista = Array.isArray(bullets) && bullets.length ? bullets : (Array.isArray(tips) ? tips : []);
  const rightNode = rightText ?? right;

  const chipStyle = {
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
  };

  const badgeStyle = {
    display: "inline-flex",
    alignItems: "center",
    justifyContent: "center",
    padding: "10px 16px",
    borderRadius: 999,
    border: "1px solid rgba(2,6,23,.08)",
    background: "rgba(122, 92, 255, 0.10)",
    fontWeight: 900,
    letterSpacing: 0.5,
    color: "rgba(30, 41, 59, 1)",
    minWidth: 140,
    textTransform: "uppercase",
  };

  const userStyle = {
    width: "100%",
    padding: "10px 14px",
    borderRadius: 16,
    border: "1px solid rgba(2,6,23,.08)",
    background: "rgba(255,255,255,0.75)",
    boxShadow: "0 10px 30px rgba(0,0,0,0.06)",
    fontSize: 14,
    color: "rgba(30, 41, 59, 0.92)",
    textAlign: "left",
  };

  return (
    <div
      style={{
        // IMPORTANT: app-main é flex-wrap; sem isso, o header encolhe e não ocupa a largura total.
        width: "100%",
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
      <div style={{ display: "flex", justifyContent: "space-between", gap: 16, flexWrap: "wrap" }}>
        {/* LEFT */}
        <div style={{ flex: 1, minWidth: 0 }}>
          {chipText ? <div style={chipStyle}>{chipText}</div> : null}

          <div
            style={{
              fontSize: 44,
              fontWeight: 900,
              letterSpacing: -1,
              lineHeight: 1.02,
              color: "rgba(15, 23, 42, 1)",
              marginBottom: 8,
              wordBreak: "break-word",
            }}
          >
            {title}
          </div>

          {subtitle ? (
            <div
              style={{
                fontSize: 16,
                color: "rgba(15, 23, 42, 0.72)",
                lineHeight: 1.35,
              }}
            >
              {subtitle}
            </div>
          ) : null}

          {lista && lista.length ? (
            <div style={{ marginTop: 12, display: "grid", gap: 8 }}>
              {lista.map((b, idx) => (
                <div key={idx} style={{ display: "flex", gap: 10, alignItems: "flex-start" }}>
                  <div style={{ width: 22, height: 22, display: "flex", alignItems: "center", justifyContent: "center" }}>
                    <span style={{ fontSize: 18 }}>✅</span>
                  </div>
                  <div style={{ fontSize: 15, color: "rgba(15, 23, 42, 0.78)", lineHeight: 1.35 }}>{b}</div>
                </div>
              ))}
            </div>
          ) : null}

          {children}
        </div>

        {/* RIGHT */}
        {(badge || rightNode || actions || userName) ? (
          <div style={{ minWidth: 240, display: "flex", flexDirection: "column", alignItems: "flex-end", gap: 10 }}>
            {badge ? <div style={badgeStyle}>{badge}</div> : null}

            {(userName || rightNode) ? (
              <div style={userStyle}>
                {userName ? (
                  <div style={{ marginBottom: rightNode ? 8 : 0 }}>
                    <span style={{ opacity: 0.75 }}>{userLabel} </span>
                    <strong>{userName}</strong>
                  </div>
                ) : null}
                {rightNode}
              </div>
            ) : null}

            {actions ? (
              <div style={{ display: "flex", gap: 8, flexWrap: "wrap", justifyContent: "flex-end" }}>
                {actions}
              </div>
            ) : null}
          </div>
        ) : null}
      </div>
    </div>
  );
}
