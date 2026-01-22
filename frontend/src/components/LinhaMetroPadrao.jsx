import React from "react";

/**
 * LinhaMetroPadrao
 * - steps: [{ key, title, subtitle? }]
 * - currentKey: string (etapa atual)
 * - nextLabel: string (ex.: "Próximo passo: Agendar retorno (10/01)")
 */
export default function LinhaMetroPadrao({
  title = "Fluxo do caso",
  steps = [],
  currentKey = null,
  nextLabel = "",
}) {
  const idx = steps.findIndex((s) => s.key === currentKey);
  const currentIndex = idx >= 0 ? idx : 0;

  return (
    <div
      style={{
        borderRadius: 22,
        padding: 16,
        background: "rgba(255,255,255,0.70)",
        border: "1px solid rgba(0,0,0,0.06)",
        boxShadow: "0 18px 60px rgba(0,0,0,0.12)",
        backdropFilter: "blur(10px)",
        WebkitBackdropFilter: "blur(10px)",
      }}
    >
      <div style={{ fontWeight: 900, marginBottom: 10 }}>{title}</div>

      {nextLabel ? (
        <div
          style={{
            borderRadius: 14,
            padding: "10px 12px",
            background: "rgba(122,92,255,0.10)",
            border: "1px solid rgba(122,92,255,0.18)",
            marginBottom: 12,
            fontWeight: 800,
            color: "rgba(92,74,220,1)",
          }}
        >
          {nextLabel}
        </div>
      ) : null}

      <div style={{ display: "grid", gap: 10 }}>
        {steps.map((s, i) => {
          const isDone = i < currentIndex;
          const isCurrent = i === currentIndex;

          return (
            <div key={s.key} style={{ display: "grid", gridTemplateColumns: "24px 1fr", gap: 12 }}>
              {/* DOT + LINE */}
              <div style={{ display: "flex", flexDirection: "column", alignItems: "center" }}>
                <div
                  style={{
                    width: 14,
                    height: 14,
                    borderRadius: 999,
                    border: "2px solid rgba(122,92,255,0.45)",
                    background: isCurrent
                      ? "rgba(122,92,255,0.95)"
                      : isDone
                      ? "rgba(122,92,255,0.55)"
                      : "rgba(255,255,255,0.9)",
                    boxShadow: isCurrent ? "0 10px 24px rgba(122,92,255,0.25)" : "none",
                    marginTop: 3,
                  }}
                />
                {i < steps.length - 1 ? (
                  <div
                    style={{
                      width: 2,
                      flex: 1,
                      background: isDone ? "rgba(122,92,255,0.35)" : "rgba(0,0,0,0.10)",
                      marginTop: 6,
                      borderRadius: 999,
                      minHeight: 18,
                    }}
                  />
                ) : null}
              </div>

              {/* CONTENT */}
              <div
                style={{
                  borderRadius: 16,
                  padding: "10px 12px",
                  border: isCurrent ? "1px solid rgba(122,92,255,0.25)" : "1px solid rgba(0,0,0,0.06)",
                  background: isCurrent ? "rgba(122,92,255,0.08)" : "rgba(255,255,255,0.55)",
                }}
              >
                <div style={{ fontWeight: 900, opacity: isDone ? 0.8 : 1 }}>
                  {s.title}
                </div>
                {s.subtitle ? (
                  <div style={{ fontSize: 12, opacity: 0.7, marginTop: 2 }}>
                    {s.subtitle}
                  </div>
                ) : null}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
