import React from "react";

export default function TabHint({ module = "CREAS", title = "", subtitle = "", bullets = [] }) {
  return (
    <div className="card" style={{ width: "100%", padding: 14 }}>
      <div className="texto-suave" style={{ margin: 0, fontWeight: 900 }}>
        Você está em
      </div>
      <div style={{ fontWeight: 950, fontSize: 18, marginTop: 2 }}>
        {module} — {title}
      </div>
      {subtitle ? <div className="texto-suave" style={{ marginTop: 6 }}>{subtitle}</div> : null}
      {bullets && bullets.length ? (
        <div style={{ marginTop: 10, display: "flex", flexWrap: "wrap", gap: 8 }}>
          {bullets.map((b, idx) => (
            <span key={idx} className="chip" style={{ fontWeight: 800 }}>
              {b}
            </span>
          ))}
        </div>
      ) : null}
    </div>
  );
}
