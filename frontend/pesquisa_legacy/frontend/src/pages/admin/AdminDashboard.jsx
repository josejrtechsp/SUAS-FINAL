import React from "react";

export default function AdminDashboard() {
  return (
    <div style={{ padding: "32px 40px" }}>
      <h1 style={{ fontSize: 24, marginBottom: 16 }}>
        Painel administrativo – Ideal
      </h1>
      <p style={{ fontSize: 15, color: "#555", marginBottom: 16 }}>
        Aqui ficará o cadastro de pesquisas, notícias e relatórios. Nesta
        primeira versão, estamos só estruturando o frontend.
      </p>

      <ul style={{ fontSize: 14, color: "#555" }}>
        <li>Cadastro de nova pesquisa</li>
        <li>Lista de pesquisas existentes</li>
        <li>Cadastro de notícias / releases</li>
        <li>Configurações básicas</li>
      </ul>
    </div>
  );
}