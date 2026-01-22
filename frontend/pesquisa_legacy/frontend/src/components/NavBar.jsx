import React from "react";
import { Link } from "react-router-dom";

const azul = "#050C36";

export default function NavBar() {
  return (
    <nav
      style={{
        width: "100%",
        backgroundColor: "#ffffff",
        borderBottom: "1px solid #e5e7eb",
      }}
    >
      <div
        style={{
          maxWidth: 1150,
          margin: "0 auto",
          padding: "12px 20px",
          display: "flex",
          justifyContent: "center",
          gap: 40,
        }}
      >
        <Link style={link} to="/">Início</Link>
        <Link style={link} to="/pesquisas">Pesquisas</Link>
        <Link style={link} to="/metodologia">Metodologia</Link>
        <Link style={link} to="/sobre">Sobre a Ideal</Link>
        <Link style={link} to="/contato">Contato</Link>
      </div>
    </nav>
  );
}

const link = {
  fontSize: 15,
  color: azul,
  textDecoration: "none",
  fontWeight: 500,
};