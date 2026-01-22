import React, { useEffect, useMemo, useState } from "react";
import "./App.css";
import { API_BASE } from "./config";

export default function TelaEncaminhamentoIntermunicipal({
  apiBase = API_BASE,
  apiFetch,
  usuarioLogado,
  municipios = [],
  pessoas = [],
  casos = [],
  municipioAtivoNome,
  onVoltar,
}) {
  const [erro, setErro] = useState("");
  const [loading, setLoading] = useState(false);

  const [pessoaId, setPessoaId] = useState("");
  const [casoId, setCasoId] = useState("");
  const [destinoId, setDestinoId] = useState("");
  const [motivo, setMotivo] = useState("");
  const [observacoes, setObservacoes] = useState("");
  const [consentimento, setConsentimento] = useState(false);

  async function fetchComAuth(url, options = {}) {
    if (typeof apiFetch === "function") return apiFetch(url, options);

    const token =
      localStorage.getItem("poprua_token") ||
      localStorage.getItem("access_token") ||
      "";

    return fetch(url, {
      ...options,
      headers: {
        ...(options.headers || {}),
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
    });
  }

  const municipiosOrdenados = useMemo(() => {
    const arr = Array.isArray(municipios) ? [...municipios] : [];
    arr.sort((a, b) =>
      (a?.nome || a?.nome_municipio || "").localeCompare(a?.nome || a?.nome_municipio || "") ||
      0
    );
    return arr;
  }, [municipios]);

  const pessoasOrdenadas = useMemo(() => {
    const arr = Array.isArray(pessoas) ? [...pessoas] : [];
    arr.sort((a, b) =>
      (a?.nome_social || a?.nome_civil || "").localeCompare(b?.nome_social || b?.nome_civil || "")
    );
    return arr;
  }, [pessoas]);

  const casosDaPessoa = useMemo(() => {
    if (!pessoaId) return [];
    const pid = Number(pessoaId);
    return (casos || []).filter((c) => Number(c.pessoa_id) === pid);
  }, [casos, pessoaId]);

  useEffect(() => {
    setCasoId("");
  }, [pessoaId]);

  async function criar(e) {
    e.preventDefault();
    setErro("");

    if (!pessoaId) return setErro("Selecione a pessoa.");
    if (!destinoId) return setErro("Selecione o município destino.");
    if (!motivo.trim()) return setErro("Informe o motivo.");
    if (!consentimento) return setErro("Marque o consentimento da pessoa (obrigatório).");

    try {
      setLoading(true);

      const body = {
        pessoa_id: Number(pessoaId),
        caso_id: casoId ? Number(casoId) : null,
        municipio_destino_id: Number(destinoId),
        motivo: motivo.trim(),
        observacoes: observacoes.trim() || null,
        consentimento_registrado: true,
      };

      const res = await fetchComAuth(`${apiBase}/encaminhamentos/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });

      if (!res.ok) {
        const txt = await res.text().catch(() => "");
        throw new Error(`Falha ao criar (HTTP ${res.status}). ${txt}`);
      }

      await res.json();
      alert("Encaminhamento criado com sucesso!");
      onVoltar?.();
    } catch (e2) {
      setErro(e2.message || "Erro ao criar encaminhamento.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="layout-1col">
      <section className="card card-wide">
        <div className="card-header-row">
          <div>
            <h2 style={{ margin: 0 }}>Novo encaminhamento</h2>
            <p className="card-subtitle" style={{ marginTop: 6 }}>
              Origem: <strong>{municipioAtivoNome || "—"}</strong>
              {usuarioLogado?.nome ? (
                <>
                  {" "}
                  · Usuário: <strong>{usuarioLogado.nome}</strong>
                </>
              ) : null}
            </p>
          </div>

          <div style={{ display: "flex", gap: 8 }}>
            <button type="button" className="btn btn-secundario" onClick={() => onVoltar?.()}>
              Voltar
            </button>
          </div>
        </div>

        <form onSubmit={criar} className="form-caso">
          <div className="grid-2cols">
            <label className="form-label">
              Pessoa *
              <select className="input" value={pessoaId} onChange={(e) => setPessoaId(e.target.value)}>
                <option value="">Selecione...</option>
                {pessoasOrdenadas.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.nome_social || p.nome_civil}
                  </option>
                ))}
              </select>
            </label>

            <label className="form-label">
              Caso (opcional)
              <select
                className="input"
                value={casoId}
                onChange={(e) => setCasoId(e.target.value)}
                disabled={!pessoaId}
              >
                <option value="">
                  {pessoaId ? "Selecione..." : "Selecione a pessoa primeiro"}
                </option>
                {casosDaPessoa.map((c) => (
                  <option key={c.id} value={c.id}>
                    Etapa {c.etapa_atual || "—"} ({c.status || "—"})
                  </option>
                ))}
              </select>
            </label>

            <label className="form-label">
              Município destino *
              <select className="input" value={destinoId} onChange={(e) => setDestinoId(e.target.value)}>
                <option value="">Selecione...</option>
                {municipiosOrdenados.map((m) => (
                  <option key={m.id} value={m.id}>
                    {m.nome || m.nome_municipio}
                  </option>
                ))}
              </select>
            </label>

            <label className="form-label">
              Motivo *
              <input
                className="input"
                value={motivo}
                onChange={(e) => setMotivo(e.target.value)}
                placeholder="Ex.: retorno familiar, tratamento, trabalho..."
              />
            </label>
          </div>

          <label className="form-label" style={{ marginTop: 10 }}>
            Observações (opcional)
            <textarea
              className="input"
              rows={3}
              value={observacoes}
              onChange={(e) => setObservacoes(e.target.value)}
              placeholder="Informações essenciais para o destino (acolhimento, saúde, necessidades)."
            />
          </label>

          <label className="form-label" style={{ marginTop: 10, display: "flex", gap: 10, alignItems: "center" }}>
            <input
              type="checkbox"
              checked={consentimento}
              onChange={(e) => setConsentimento(e.target.checked)}
              style={{ width: 18, height: 18 }}
            />
            <span>
              A pessoa <strong>solicitou/consentiu</strong> com o deslocamento (obrigatório)
            </span>
          </label>

          {erro && <p className="erro-global">{erro}</p>}

          <div className="card-footer-right">
            <button type="submit" className="btn btn-primario" disabled={loading}>
              {loading ? "Salvando..." : "Criar encaminhamento"}
            </button>
          </div>
        </form>
      </section>
    </div>
  );
}