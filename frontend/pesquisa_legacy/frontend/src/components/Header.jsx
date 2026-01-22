import React from "react";

const azul = "#0F153A";
const dourado = "#BB8800";

export default function Header() {
  return (
    <header style={{ width: "100%", backgroundColor: azul }}>
      {/* Faixa dourada superior */}
      <div
        style={{
          width: "100%",
          height: 6,
          backgroundColor: dourado,
        }}
      />

      {/* Container central */}
      <div
        style={{
          maxWidth: 1200,
          margin: "0 auto",
          padding: "14px 20px",
          display: "flex",
          alignItems: "center",
          justifyContent: "center", // >>> CENTRALIZA TUDO <<<
          gap: 18,
          color: "white",
          textAlign: "center",
        }}
      >
        {/* Logo */}
        <img
          src="/ideal-logo.png"
          alt="Ideal Desenvolvimento Estratégico"
          style={{
            height: 48,
            width: "auto",
            objectFit: "contain",
          }}
        />

        {/* Textos */}
        <div>
          <div
            style={{
              fontSize: 22,
              fontWeight: 700,
              marginBottom: 2,
              whiteSpace: "nowrap",
            }}
          >
            Ideal Desenvolvimento Estratégico
          </div>

          <div
            style={{
              fontSize: 13,
              opacity: 0.9,
            }}
          >
            Pesquisas eleitorais e de opinião
          </div>
        </div>
      </div>

      {/* Faixa dourada inferior */}
      <div
        style={{
          width: "100%",
          height: 4,
          backgroundColor: dourado,
        }}
      />
    </header>
  );
}