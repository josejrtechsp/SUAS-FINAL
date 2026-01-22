import React from "react";
import { Link } from "react-router-dom";

const azulIdeal = "#050C36";
const douradoIdeal = "#B28316";

export default function Home() {
  return (
    <div
      style={{
        maxWidth: 1150,
        margin: "0 auto",
        padding: "30px 20px",
        fontFamily: "system-ui",
      }}
    >
      {/* CHAMADA PRINCIPAL */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "1.4fr 1fr",
          gap: 20,
          marginBottom: 40,
          alignItems: "center",
        }}
      >
        {/* Texto */}
        <div>
          <h1
            style={{
              fontSize: 32,
              lineHeight: 1.25,
              fontWeight: 700,
              color: azulIdeal,
              marginBottom: 12,
            }}
          >
            Brasil volta a mostrar estabilidade em índices de avaliação do governo
          </h1>

          <p
            style={{
              fontSize: 16,
              color: "#444",
              lineHeight: 1.5,
            }}
          >
            Nova pesquisa nacional da Ideal Desenvolvimento Estratégico mostra leve redução
            nas avaliações negativas e manutenção da percepção econômica da população.
          </p>

          <Link to="/pesquisas">
            <button
              style={{
                marginTop: 20,
                padding: "10px 20px",
                backgroundColor: azulIdeal,
                color: "white",
                border: "none",
                borderRadius: 6,
                fontSize: 15,
                cursor: "pointer",
              }}
            >
              Ver pesquisas
            </button>
          </Link>
        </div>

        {/* Imagem direita */}
        <img
          src="/home-foto.jpg"
          alt="Pesquisa eleitoral"
          style={{
            width: "100%",
            height: "auto",
            borderRadius: 8,
            objectFit: "cover",
          }}
        />
      </div>

      {/* SUBCHAMADAS — estilo Datafolha */}
      <div style={{ marginTop: 20 }}>
        <h2
          style={{
            fontSize: 22,
            color: azulIdeal,
            marginBottom: 18,
            fontWeight: 700,
          }}
        >
          Destaques das pesquisas
        </h2>

        <div style={{ display: "grid", gap: 24 }}>
          {/* 1 */}
          <div>
            <h3 style={{ fontSize: 18, lineHeight: 1.3 }}>
              Avaliação do governo se mantém estável em novo levantamento
            </h3>
            <p style={{ fontSize: 14, color: "#555", marginTop: 4 }}>
              Pesquisa mostra pequenas oscilações, mas sem mudança estrutural no cenário nacional.
            </p>
          </div>

          {/* 2 */}
          <div>
            <h3 style={{ fontSize: 18, lineHeight: 1.3 }}>
              Intenção de voto registra movimentações sutis entre pré-candidatos
            </h3>
            <p style={{ fontSize: 14, color: "#555", marginTop: 4 }}>
              Cenários testados mostram estabilidade e variações dentro da margem de erro.
            </p>
          </div>

          {/* 3 */}
          <div>
            <h3 style={{ fontSize: 18, lineHeight: 1.3 }}>
              Percepção econômica segue dividida entre melhora e piora
            </h3>
            <p style={{ fontSize: 14, color: "#555", marginTop: 4 }}>
              Opinião pública segue cautelosa diante do cenário econômico atual.
            </p>
          </div>

          {/* 4 */}
          <div>
            <h3 style={{ fontSize: 18, lineHeight: 1.3 }}>
              Pessimismo sobe sobre economia e aprovação cai
            </h3>
            <p style={{ fontSize: 14, color: "#555", marginTop: 4 }}>
              Avaliação negativa das condições econômicas aumenta e impacta percepção sobre o governo.
            </p>
          </div>

          {/* 5 */}
          <div>
            <h3 style={{ fontSize: 18, lineHeight: 1.3 }}>
              Lula oscila para cima em cenários do 1º turno
            </h3>
            <p style={{ fontSize: 14, color: "#555", marginTop: 4 }}>
              Presidente apresenta leve alta nas intenções de voto em simulações de disputa presidencial.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}