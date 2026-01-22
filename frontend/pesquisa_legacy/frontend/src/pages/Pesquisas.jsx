import React, { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { pesquisasFake } from "../data/pesquisasFake";

const azulIdeal = "#050C36";
const douradoIdeal = "#B28316";

export default function Pesquisas() {
  const navigate = useNavigate();

  const [filtroTexto, setFiltroTexto] = useState("");
  const [filtroTipo, setFiltroTipo] = useState("todos");
  const [filtroAno, setFiltroAno] = useState("todos");

  // anos disponíveis a partir dos dados
  const anosDisponiveis = useMemo(() => {
    const anos = Array.from(
      new Set(pesquisasFake.map((p) => p.ano).filter(Boolean))
    );
    anos.sort((a, b) => b - a);
    return anos;
  }, []);

  // aplica filtros
  const pesquisasFiltradas = useMemo(() => {
    return pesquisasFake.filter((p) => {
      const texto = filtroTexto.toLowerCase().trim();

      if (texto) {
        const base = (
          p.titulo +
          " " +
          (p.local || "") +
          " " +
          (p.tipo || "") +
          " " +
          (p.cargo || "") +
          " " +
          (p.tags || []).join(" ")
        ).toLowerCase();
        if (!base.includes(texto)) return false;
      }

      if (filtroTipo !== "todos" && p.tipo !== filtroTipo) return false;

      if (filtroAno !== "todos" && String(p.ano) !== String(filtroAno))
        return false;

      return true;
    });
  }, [filtroTexto, filtroTipo, filtroAno]);

  function irParaDetalhe(id) {
    navigate(`/pesquisas/${id}`);
  }

  return (
    <div
      style={{
        maxWidth: 1150,
        margin: "0 auto",
        padding: "30px 20px",
        fontFamily: "system-ui",
      }}
    >
      <h1
        style={{
          fontSize: 26,
          fontWeight: 700,
          color: azulIdeal,
          marginBottom: 8,
        }}
      >
        Pesquisas Ideal
      </h1>

      <p
        style={{
          fontSize: 15,
          color: "#555",
          maxWidth: 780,
          marginBottom: 20,
        }}
      >
        Consulta às principais pesquisas realizadas pela Ideal Desenvolvimento
        Estratégico. Em breve, esta página será integrada ao painel
        administrativo para exibir pesquisas em tempo real, com gráficos,
        fichas técnicas completas e relatórios em PDF.
      </p>

      {/* FILTROS */}
      <div
        style={{
          display: "flex",
          flexWrap: "wrap",
          gap: 12,
          padding: 12,
          borderRadius: 8,
          border: "1px solid #e0e0e0",
          backgroundColor: "#f8fafc",
          marginBottom: 20,
        }}
      >
        <input
          placeholder="Buscar por título, local, palavra-chave..."
          value={filtroTexto}
          onChange={(e) => setFiltroTexto(e.target.value)}
          style={{
            flex: "2 1 260px",
            padding: 8,
            borderRadius: 4,
            border: "1px solid #cbd5e1",
            fontSize: 14,
          }}
        />

        <select
          value={filtroTipo}
          onChange={(e) => setFiltroTipo(e.target.value)}
          style={{
            flex: "1 1 170px",
            padding: 8,
            borderRadius: 4,
            border: "1px solid #cbd5e1",
            fontSize: 14,
          }}
        >
          <option value="todos">Todos os tipos</option>
          <option value="Eleitoral">Eleitoral</option>
          <option value="Avaliação de governo">Avaliação de governo</option>
          <option value="Opinião pública">Opinião pública</option>
        </select>

        <select
          value={filtroAno}
          onChange={(e) => setFiltroAno(e.target.value)}
          style={{
            flex: "0 0 130px",
            padding: 8,
            borderRadius: 4,
            border: "1px solid #cbd5e1",
            fontSize: 14,
          }}
        >
          <option value="todos">Todos os anos</option>
          {anosDisponiveis.map((ano) => (
            <option key={ano} value={ano}>
              {ano}
            </option>
          ))}
        </select>
      </div>

      {/* LISTA / GRID DE CARDS */}
      {pesquisasFiltradas.length === 0 ? (
        <p style={{ fontSize: 14, color: "#777" }}>
          Nenhuma pesquisa encontrada com os filtros atuais.
        </p>
      ) : (
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))",
            gap: 16,
          }}
        >
          {pesquisasFiltradas.map((p) => (
            <div
              key={p.id}
              style={{
                border: "1px solid #e2e8f0",
                borderRadius: 8,
                backgroundColor: "white",
                padding: 14,
                display: "flex",
                flexDirection: "column",
                justifyContent: "space-between",
                minHeight: 180,
              }}
            >
              <div>
                <div
                  style={{
                    fontSize: 11,
                    textTransform: "uppercase",
                    fontWeight: 700,
                    color: douradoIdeal,
                    marginBottom: 4,
                  }}
                >
                  {p.tipo}
                  {p.cargo ? ` · ${p.cargo}` : ""}
                </div>

                <h2
                  style={{
                    fontSize: 17,
                    fontWeight: 600,
                    color: azulIdeal,
                    marginBottom: 6,
                    lineHeight: 1.3,
                  }}
                >
                  {p.titulo}
                </h2>

                <div
                  style={{
                    fontSize: 13,
                    color: "#64748b",
                    marginBottom: 6,
                  }}
                >
                  {p.local} · {p.dataColeta} · Amostra {p.amostra} · Margem{" "}
                  {p.margemErro}
                </div>

                <p
                  style={{
                    fontSize: 13,
                    color: "#475569",
                    marginBottom: 6,
                  }}
                >
                  {p.descricaoCurta}
                </p>

                {p.tags && (
                  <div style={{ marginTop: 4, fontSize: 12 }}>
                    {p.tags.map((tag) => (
                      <span
                        key={tag}
                        style={{
                          display: "inline-block",
                          padding: "2px 6px",
                          borderRadius: 999,
                          border: "1px solid #e2e8f0",
                          marginRight: 4,
                          marginTop: 4,
                        }}
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                )}
              </div>

              <div style={{ marginTop: 10, display: "flex", gap: 8 }}>
                <button
                  onClick={() => irParaDetalhe(p.id)}
                  style={{
                    padding: "6px 10px",
                    borderRadius: 4,
                    border: "none",
                    backgroundColor: azulIdeal,
                    color: "white",
                    fontSize: 13,
                    cursor: "pointer",
                  }}
                >
                  Ver detalhes
                </button>

                <button
                  style={{
                    padding: "6px 10px",
                    borderRadius: 4,
                    border: `1px solid ${azulIdeal}`,
                    backgroundColor: "white",
                    color: azulIdeal,
                    fontSize: 13,
                    cursor: "pointer",
                  }}
                  onClick={() => {
                    if (p.pdfUrl && p.pdfUrl !== "#") {
                      window.open(p.pdfUrl, "_blank", "noopener,noreferrer");
                    } else {
                      alert(
                        "Nesta versão de demonstração o PDF ainda não está cadastrado."
                      );
                    }
                  }}
                >
                  Baixar PDF
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      <div style={{ marginTop: 24, fontSize: 12, color: "#777" }}>
        <em>
          Em breve: filtros por estado, município, cargo, cenário, linha do
          tempo e integração direta com o banco de dados da Ideal.
        </em>
      </div>
    </div>
  );
}