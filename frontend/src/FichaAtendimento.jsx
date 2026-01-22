import { useState } from "react";
import "./App.css";

const API_BASE = "http://localhost:8000";

function FichaAtendimento({ pessoa, caso, onVoltar, onAtendimentoSalvo }) {
  const [form, setForm] = useState({
    tipo_atendimento: "",
    equipamento: "",
    resultado: "",
    descricao: "",
    // datetime-local usa só até minutos
    data_atendimento: new Date().toISOString().slice(0, 16),
  });

  const [salvando, setSalvando] = useState(false);
  const [erro, setErro] = useState("");
  const [okMsg, setOkMsg] = useState("");

  function handleChange(campo, valor) {
    setForm((prev) => ({
      ...prev,
      [campo]: valor,
    }));
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setErro("");
    setOkMsg("");

    if (!form.tipo_atendimento || !form.equipamento || !form.resultado) {
      setErro("Preencha Tipo de atendimento, Equipamento/Local e Resultado.");
      return;
    }

    let dataAtendimentoISO;
    try {
      dataAtendimentoISO = new Date(form.data_atendimento).toISOString();
    } catch {
      dataAtendimentoISO = new Date().toISOString();
    }

    const body = {
      tipo_atendimento: form.tipo_atendimento,
      equipamento: form.equipamento,
      resultado: form.resultado,
      descricao: form.descricao || "",
      data_atendimento: dataAtendimentoISO,
    };

    try {
      setSalvando(true);
      const res = await fetch(
        `${API_BASE}/pessoas/${caso.pessoa_id}/atendimentos`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body),
        }
      );

      if (!res.ok) {
        let msg = "Erro ao registrar atendimento.";
        try {
          const errJson = await res.json();
          if (errJson.detail) msg = errJson.detail;
        } catch (_) {}
        throw new Error(msg);
      }

      await res.json(); // não precisamos do retorno completo agora

      // avisa o App para recarregar os atendimentos
      if (onAtendimentoSalvo) {
        await onAtendimentoSalvo();
      }

      setOkMsg("Atendimento registrado com sucesso.");
      setForm((prev) => ({
        ...prev,
        tipo_atendimento: "",
        equipamento: "",
        resultado: "",
        descricao: "",
        data_atendimento: new Date().toISOString().slice(0, 16),
      }));
    } catch (e) {
      console.error(e);
      setErro(e.message || "Erro ao registrar atendimento.");
    } finally {
      setSalvando(false);
    }
  }

  const nomePessoa =
    pessoa?.nome_social ||
    pessoa?.nome_civil ||
    `Pessoa #${caso.pessoa_id}`;

  const cpf = pessoa?.cpf || "Não informado";
  const genero = pessoa?.genero || "Não informado";
  const municipioOrigem = pessoa?.municipio_origem_id
    ? `Município origem ID ${pessoa.municipio_origem_id}`
    : "Não informado";
  const tempoRua = pessoa?.tempo_rua || "Não informado";
  const localReferencia = pessoa?.local_referencia || "Não informado";

  return (
    <>
      {/* Cabeçalho da ficha */}
      <div className="card">
        <div className="card-header-row">
          <button
            type="button"
            className="btn btn-secundario"
            onClick={onVoltar}
          >
            ← Voltar para casos
          </button>
          <div>
            <h2>Ficha de atendimento</h2>
            <p className="card-subtitle">
              Caso #{caso.id} · Pessoa #{caso.pessoa_id} — {nomePessoa}
            </p>
          </div>
        </div>
      </div>

      {/* Dados da pessoa */}
      <div className="card">
        <h3>Dados da pessoa</h3>
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
            gap: "0.75rem",
            marginTop: "0.75rem",
          }}
        >
          <div className="info-box">
            <div className="info-label">Nome</div>
            <div className="info-value">{nomePessoa}</div>
          </div>
          <div className="info-box">
            <div className="info-label">CPF</div>
            <div className="info-value">{cpf}</div>
          </div>
          <div className="info-box">
            <div className="info-label">Gênero</div>
            <div className="info-value">{genero}</div>
          </div>
          <div className="info-box">
            <div className="info-label">Município de origem</div>
            <div className="info-value">{municipioOrigem}</div>
          </div>
          <div className="info-box">
            <div className="info-label">Tempo de rua</div>
            <div className="info-value">{tempoRua}</div>
          </div>
          <div className="info-box">
            <div className="info-label">Local de referência</div>
            <div className="info-value">{localReferencia}</div>
          </div>
        </div>
      </div>

      {/* Dados do atendimento */}
      <div className="card">
        <h3>Dados do atendimento</h3>

        <form onSubmit={handleSubmit} className="form-caso">
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))",
              gap: "0.75rem",
              marginTop: "0.75rem",
            }}
          >
            <label className="form-label">
              Tipo de atendimento *
              <input
                className="input"
                type="text"
                placeholder="Ex.: Abordagem na rua, Atendimento CRAS..."
                value={form.tipo_atendimento}
                onChange={(e) =>
                  handleChange("tipo_atendimento", e.target.value)
                }
              />
            </label>

            <label className="form-label">
              Equipamento / Local *
              <input
                className="input"
                type="text"
                placeholder="Ex.: Rua - Praça Central, CRAS Centro..."
                value={form.equipamento}
                onChange={(e) =>
                  handleChange("equipamento", e.target.value)
                }
              />
            </label>

            <label className="form-label">
              Resultado *
              <input
                className="input"
                type="text"
                placeholder="Ex.: Encaminhamento para CRAS, Acompanhamento..."
                value={form.resultado}
                onChange={(e) => handleChange("resultado", e.target.value)}
              />
            </label>

            <label className="form-label">
              Data e hora do atendimento
              <input
                className="input"
                type="datetime-local"
                value={form.data_atendimento}
                onChange={(e) =>
                  handleChange("data_atendimento", e.target.value)
                }
              />
            </label>
          </div>

          <label className="form-label" style={{ marginTop: "0.75rem" }}>
            Descrição / relato (opcional)
            <textarea
              className="input"
              rows={3}
              placeholder="Resumo do que foi realizado, orientações, reações da pessoa, etc."
              value={form.descricao}
              onChange={(e) => handleChange("descricao", e.target.value)}
            />
          </label>

          {erro && <p className="erro" style={{ marginTop: 8 }}>{erro}</p>}
          {okMsg && (
            <p className="sucesso" style={{ marginTop: 8 }}>
              {okMsg}
            </p>
          )}

          <div style={{ marginTop: "1rem" }}>
            <button
              type="submit"
              className="btn btn-primario"
              disabled={salvando}
            >
              {salvando ? "Salvando..." : "Salvar atendimento"}
            </button>
          </div>
        </form>
      </div>
    </>
  );
}

export default FichaAtendimento;