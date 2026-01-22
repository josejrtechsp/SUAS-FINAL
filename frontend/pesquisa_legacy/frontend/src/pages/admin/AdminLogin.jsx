import React from "react";

export default function AdminLogin() {
  return (
    <div
      style={{
        padding: "40px 20px",
        display: "flex",
        justifyContent: "center",
      }}
    >
      <div
        style={{
          border: "1px solid #ddd",
          borderRadius: 8,
          padding: 24,
          width: "100%",
          maxWidth: 380,
        }}
      >
        <h1 style={{ fontSize: 20, marginBottom: 16 }}>
          Login – Painel Ideal
        </h1>

        <div
          style={{
            display: "flex",
            flexDirection: "column",
            gap: 12,
            fontSize: 14,
          }}
        >
          <input placeholder="E-mail" style={{ padding: 8 }} />
          <input
            type="password"
            placeholder="Senha"
            style={{ padding: 8 }}
          />
          <button
            style={{
              marginTop: 8,
              padding: "8px 12px",
              border: "none",
              borderRadius: 4,
              background: "#050C36",
              color: "white",
              cursor: "pointer",
            }}
          >
            Entrar
          </button>
        </div>

        <p style={{ fontSize: 12, color: "#777", marginTop: 12 }}>
          Próximo passo: vamos integrar este login ao backend (FastAPI) para
          autenticação real e acesso ao painel de cadastro de pesquisas.
        </p>
      </div>
    </div>
  );
}