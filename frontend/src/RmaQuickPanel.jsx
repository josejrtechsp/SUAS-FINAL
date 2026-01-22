import React, { useMemo, useState } from "react";

export default function RmaQuickPanel({ apiBase, apiFetch }) {
  const [mes, setMes] = useState(() => new Date().toISOString().slice(0, 7)); // YYYY-MM
  const [unidade, setUnidade] = useState("");
  const [loading, setLoading] = useState(false);
  const [resumo, setResumo] = useState(null);
  const [erro, setErro] = useState("");

  const rows = useMemo(() => {
    const por = resumo?.por_servico || {};
    const out = [];
    Object.keys(por).forEach((serv) => {
      const acoes = por[serv] || {};
      Object.keys(acoes).forEach((acao) => out.push({ servico: serv, acao, qtd: acoes[acao] }));
    });
    out.sort((a, b) => (a.servico + a.acao).localeCompare(b.servico + b.acao));
    return out;
  }, [resumo]);

  async function carregarResumo() {
    setErro(""); setLoading(true);
    try {
      if (!apiBase || typeof apiFetch !== "function") throw new Error("apiBase/apiFetch ausente");
      if (!mes || mes.length < 7) throw new Error("mês inválido");
      const qs = new URLSearchParams();
      qs.set("mes", mes);
      if (unidade) qs.set("unidade_id", String(unidade));
      const r = await apiFetch(`${apiBase}/cras/rma/mes?${qs.toString()}`);
      if (!r.ok) throw new Error(await r.text());
      setResumo(await r.json());
    } catch (e) {
      console.error(e);
      setResumo(null);
      setErro("Não foi possível carregar o resumo do RMA.");
    } finally { setLoading(false); }
  }

  async function baixarCsv() {
    setErro(""); setLoading(true);
    try {
      if (!apiBase || typeof apiFetch !== "function") throw new Error("apiBase/apiFetch ausente");
      if (!mes || mes.length < 7) throw new Error("mês inválido");
      const qs = new URLSearchParams();
      qs.set("mes", mes);
      if (unidade) qs.set("unidade_id", String(unidade));
      const r = await apiFetch(`${apiBase}/cras/rma/export.csv?${qs.toString()}`);
      if (!r.ok) throw new Error(await r.text());
      const blob = await r.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `rma_${mes}${unidade ? `_unidade_${unidade}` : ""}.csv`;
      document.body.appendChild(a); a.click(); a.remove(); URL.revokeObjectURL(url);
    } catch (e) {
      console.error(e);
      setErro("Não foi possível baixar o CSV do RMA.");
    } finally { setLoading(false); }
  }

  return (
    <div className="card" style={{ padding: 12, borderRadius: 18, marginTop: 10 }}>
      <div style={{ display: "flex", justifyContent: "space-between", gap: 10, flexWrap: "wrap", alignItems: "center" }}>
        <div>
          <div style={{ fontWeight: 900 }}>RMA do mês</div>
          <div className="texto-suave">Resumo + export (1 clique). Coleta automática durante a operação.</div>
        </div>
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap", alignItems: "center" }}>
          <input className="input" type="month" value={mes} onChange={(e) => setMes(e.target.value)} style={{ minWidth: 140 }} />
          <input className="input" placeholder="Unidade (opcional)" value={unidade} onChange={(e) => setUnidade(e.target.value)} style={{ maxWidth: 160 }} />
          <button className="btn btn-secundario" type="button" onClick={carregarResumo} disabled={loading}>
            {loading ? "Carregando..." : "Carregar"}
          </button>
          <button className="btn btn-primario" type="button" onClick={baixarCsv} disabled={loading}>
            Baixar CSV
          </button>
        </div>
      </div>

      {erro ? <div className="texto-suave" style={{ marginTop: 8 }}><strong>{erro}</strong></div> : null}

      {resumo ? (
        <div style={{ marginTop: 12 }}>
          <div className="texto-suave">Total de eventos no mês: <strong>{resumo.total_eventos}</strong></div>
          <div style={{ marginTop: 10, overflowX: "auto" }}>
            <table className="table" style={{ width: "100%" }}>
              <thead><tr><th>Serviço</th><th>Ação</th><th>Qtd</th></tr></thead>
              <tbody>
                {rows.map((r, idx) => (
                  <tr key={idx}><td>{r.servico}</td><td>{r.acao}</td><td><strong>{r.qtd}</strong></td></tr>
                ))}
                {!rows.length ? <tr><td colSpan={3} className="texto-suave">Sem dados para o filtro atual.</td></tr> : null}
              </tbody>
            </table>
          </div>
        </div>
      ) : null}
    </div>
  );
}

// RMA_PANEL_V1
