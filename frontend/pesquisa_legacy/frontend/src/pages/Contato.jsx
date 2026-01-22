import React, { useState } from "react";

export default function Contato() {
  const [form, setForm] = useState({
    nome: "",
    email: "",
    telefone: "",
    municipio: "",
    tipo: "",
    mensagem: "",
  });

  const [status, setStatus] = useState<"idle" | "loading" | "ok" | "error">(
    "idle"
  );
  const [errorMsg, setErrorMsg] = useState("");

  const handleChange = (
    e: React.ChangeEvent<
      HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement
    >
  ) => {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setStatus("loading");
    setErrorMsg("");

    try {
      const resp = await fetch("http://localhost:8000/contact", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(form),
      });

      if (!resp.ok) {
        throw new Error("Erro ao enviar");
      }

      await resp.json();
      setStatus("ok");
      setForm({
        nome: "",
        email: "",
        telefone: "",
        municipio: "",
        tipo: "",
        mensagem: "",
      });
    } catch (err) {
      setStatus("error");
      setErrorMsg(
        "Não foi possível enviar sua mensagem. Tente novamente em alguns minutos."
      );
    }
  };

  const inputStyle: React.CSSProperties = {
    width: "100%",
    padding: "8px 10px",
    borderRadius: 8,
    border: "1px solid #d1d5db",
    fontSize: 14,
    outline: "none",
  };

  const labelStyle: React.CSSProperties = {
    fontSize: 13,
    fontWeight: 500,
    marginBottom: 4,
    color: "#111827",
  };

  return (
    <div
      style={{
        padding: "32px 40px",
        maxWidth: 900,
        margin: "0 auto",
      }}
    >
      <h1 style={{ fontSize: 26, marginBottom: 12 }}>Contato</h1>
      <p style={{ fontSize: 15, color: "#555", marginBottom: 16 }}>
        Utilize os canais abaixo para solicitar propostas, tirar dúvidas sobre
        pesquisas ou agendar uma reunião.
      </p>

      {/* Bloco com canais fixos */}
      <div
        style={{
          marginBottom: 24,
          fontSize: 15,
          padding: 16,
          borderRadius: 12,
          backgroundColor: "#f9fafb",
          border: "1px solid #e5e7eb",
        }}
      >
        <p style={{ margin: "0 0 6px" }}>
          <strong>E-mail:</strong> contato@idealdesenvolvimento.com.br
        </p>
        <p style={{ margin: "0 0 6px" }}>
          <strong>Telefone:</strong> (00) 0000-0000
        </p>
        <p style={{ margin: 0 }}>
          <strong>Cidade / UF:</strong> (preencher com seus dados reais depois)
        </p>
      </div>

      {/* Formulário de contato */}
      <div
        style={{
          borderRadius: 12,
          border: "1px solid #e5e7eb",
          backgroundColor: "#ffffff",
          boxShadow: "0 1px 3px rgba(15,23,42,0.06)",
          padding: 20,
        }}
      >
        <h2
          style={{
            fontSize: 18,
            marginTop: 0,
            marginBottom: 8,
            color: "#111827",
          }}
        >
          Envie uma mensagem para a Ideal
        </h2>
        <p
          style={{
            fontSize: 13,
            color: "#4b5563",
            marginTop: 0,
            marginBottom: 16,
          }}
        >
          Conte em poucas linhas qual é o desafio da sua prefeitura, consórcio,
          empresa ou campanha. Responderemos com uma proposta de estudo ou
          diagnóstico sob medida.
        </p>

        <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          <div>
            <label style={labelStyle} htmlFor="nome">
              Nome *
            </label>
            <input
              id="nome"
              name="nome"
              value={form.nome}
              onChange={handleChange}
              style={inputStyle}
              required
            />
          </div>

          <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
            <div style={{ flex: 1, minWidth: 220 }}>
              <label style={labelStyle} htmlFor="email">
                E-mail *
              </label>
              <input
                id="email"
                type="email"
                name="email"
                value={form.email}
                onChange={handleChange}
                style={inputStyle}
                required
              />
            </div>
            <div style={{ flex: 1, minWidth: 220 }}>
              <label style={labelStyle} htmlFor="telefone">
                Telefone / WhatsApp
              </label>
              <input
                id="telefone"
                name="telefone"
                value={form.telefone}
                onChange={handleChange}
                style={inputStyle}
              />
            </div>
          </div>

          <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
            <div style={{ flex: 1, minWidth: 220 }}>
              <label style={labelStyle} htmlFor="municipio">
                Município / Estado
              </label>
              <input
                id="municipio"
                name="municipio"
                value={form.municipio}
                onChange={handleChange}
                style={inputStyle}
              />
            </div>
            <div style={{ flex: 1, minWidth: 220 }}>
              <label style={labelStyle} htmlFor="tipo">
                Tipo de cliente
              </label>
              <select
                id="tipo"
                name="tipo"
                value={form.tipo}
                onChange={handleChange}
                style={inputStyle}
              >
                <option value="">Selecione</option>
                <option value="prefeitura">Prefeitura</option>
                <option value="consorcio">Consórcio</option>
                <option value="empresa">Empresa</option>
                <option value="campanha">Campanha eleitoral</option>
                <option value="outro">Outro</option>
              </select>
            </div>
          </div>

          <div>
            <label style={labelStyle} htmlFor="mensagem">
              Mensagem *
            </label>
            <textarea
              id="mensagem"
              name="mensagem"
              value={form.mensagem}
              onChange={handleChange}
              style={{
                ...inputStyle,
                minHeight: 120,
                resize: "vertical",
              }}
              required
            />
          </div>

          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 12,
              marginTop: 8,
            }}
          >
            <button
              type="submit"
              disabled={status === "loading"}
              style={{
                padding: "10px 18px",
                borderRadius: 999,
                border: "none",
                fontSize: 14,
                fontWeight: 600,
                cursor: status === "loading" ? "default" : "pointer",
                background:
                  "linear-gradient(90deg, #111827, #020617)",
                color: "#F9FAFB",
              }}
            >
              {status === "loading" ? "Enviando..." : "Falar com a Ideal"}
            </button>

            {status === "ok" && (
              <span
                style={{
                  fontSize: 13,
                  color: "#16a34a",
                }}
              >
                Mensagem enviada com sucesso. Em breve entraremos em contato.
              </span>
            )}

            {status === "error" && (
              <span
                style={{
                  fontSize: 13,
                  color: "#b91c1c",
                }}
              >
                {errorMsg}
              </span>
            )}
          </div>
        </form>
      </div>
    </div>
  );
}