import React from "react";

export default function Footer() {
  return (
    <footer
      style={{
        width: "100%",
        padding: "25px 0",
        borderTop: "1px solid #e5e7eb",
        marginTop: 20,
        textAlign: "center",
        fontSize: 14,
        color: "#444",
        backgroundColor: "#f9fafb",
      }}
    >
      <div style={{ fontWeight: 600 }}>
        Ideal Desenvolvimento Estratégico
      </div>

      <div style={{ marginTop: 4 }}>
        Pesquisas eleitorais, de opinião pública e inteligência para gestão.
      </div>

      <div style={{ marginTop: 8, color: "#777" }}>
        © {new Date().getFullYear()} Ideal Desenvolvimento Estratégico — Versão
        demonstrativa do site.
      </div>
    </footer>
  );
}