import React, { useEffect, useMemo, useState } from "react";

// RMA_METAS_PANEL_INDICADOR_V1
export default function RmaMetasPanel({ apiBase, apiFetch, isActive = true }) {
  const [mes, setMes] = useState(() => new Date().toISOString().slice(0, 7));
  const [unidade, setUnidade] = useState("");
  const [servico, setServico] = useState("CASOS");
  const [meta, setMeta] = useState("");
  const [actual, setActual] = useState(null);
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState("");

  const pct = useMemo(() => {
    const m = Number(meta || 0);
    const a = Number(actual || 0);
    if (!m) return 0;
    return Math.min(999, Math.round((a / m) * 100));
  }, [meta, actual]);

  const indicador = useMemo(() => {
    const m = Number(meta || 0);
    if (!m) return { label: "Sem meta", tone: "cinza" };
    if (pct >= 100) return { label: "Atingiu", tone: "verde" };
    if (pct >= 80) return { label: "Risco", tone: "amarelo" };
    return { label: "Abaixo", tone: "vermelho" };
  }, [meta, pct]);

  function badgeStyle(tone) {
    const base = {
      padding: "4px 10px",
      borderRadius: 999,
      fontWeight: 900,
      fontSize: 12,
      border: "1px solid rgba(2,6,23,.10)",
      background: "rgba(2,6,23,.05)",
      color: "rgba(2,6,23,.75)",
    };
    if (tone === "verde") return { ...base, background: "rgba(16,185,129,.18)", color: "rgba(6,95,70,1)" };
    if (tone === "amarelo") return { ...base, background: "rgba(245,158,11,.20)", color: "rgba(146,64,14,1)" };
    if (tone === "vermelho") return { ...base, background: "rgba(239,68,68,.18)", color: "rgba(153,27,27,1)" };
    return base;
  }

  async function loadMetaAndActual() {
    setMsg("");
    setLoading(true);
    try {
      const qs = new URLSearchParams();
      qs.set("mes", mes);
      if (unidade) qs.set("unidade_id", String(unidade));
      qs.set("servico", servico);

      // meta
      const r1 = await apiFetch(`${apiBase}/cras/rma/metas?${qs.toString()}`);
      if (!r1.ok) throw new Error(await r1.text());
      const metas = await r1.json();
      const m = Array.isArray(metas) && metas.length ? metas[0] : null;
      setMeta(m ? String(m.meta_total || 0) : "");

      // realizado (soma ações do serviço no mês)
      const r2 = await apiFetch(`${apiBase}/cras/rma/mes?${qs.toString()}`);
      if (!r2.ok) throw new Error(await r2.text());
      const j = await r2.json();
      const por = j?.por_servico || {};
      const acoes = por?.[servico] || {};
      const soma = Object.values(acoes).reduce((acc, v) => acc + Number(v || 0), 0);
      setActual(soma);
      setMsg("Carregado ✅");
    } catch (e) {
      console.error(e);
      setMsg("Falha ao carregar metas/realizado.");
      setActual(null);
    } finally {
      setLoading(false);
    }
  }

  async function salvarMeta() {
    setMsg("");
    setLoading(true);
    try {
      const payload = { mes, servico, unidade_id: unidade ? Number(unidade) : null, meta_total: meta ? Number(meta) : 0 };
      const r = await apiFetch(`${apiBase}/cras/rma/metas`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!r.ok) throw new Error(await r.text());
      setMsg("Meta salva ✅");
    } catch (e) {
      console.error(e);
      setMsg("Falha ao salvar meta.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (!isActive) return;
    if (!apiBase || typeof apiFetch !== "function") return;
    loadMetaAndActual();
    // eslint-disable-next-line
  }, [isActive]);

  if (!isActive) return null;

  return (
    <div className="card" style={{ padding: 12, borderRadius: 18, marginTop: 10 }}>
      <div style={{ display: "flex", justifyContent: "space-between", gap: 10, flexWrap: "wrap", alignItems: "center" }}>
        <div>
          <div style={{ fontWeight: 900, display: "flex", gap: 10, alignItems: "center", flexWrap: "wrap" }}>
            Metas do RMA <span style={badgeStyle(indicador.tone)}>{indicador.label}</span>
          </div>
          <div className="texto-suave">Indicador: atingiu (≥100%) · risco (80–99%) · abaixo (&lt;80%).</div>
        </div>

        <div style={{ display: "flex", gap: 8, flexWrap: "wrap", alignItems: "center" }}>
          <input className="input" type="month" value={mes} onChange={(e) => setMes(e.target.value)} style={{ minWidth: 140 }} />
          <input className="input" placeholder="Unidade (opcional)" value={unidade} onChange={(e) => setUnidade(e.target.value)} style={{ maxWidth: 160 }} />
          <select className="input" value={servico} onChange={(e) => setServico(e.target.value)} style={{ minWidth: 170 }}>
            <option value="CASOS">CASOS</option>
            <option value="PAIF">PAIF</option>
            <option value="CADUNICO">CADÚNICO</option>
            <option value="SCFV">SCFV</option>
            <option value="ENCAMINHAMENTO">ENCAMINHAMENTO</option>
            <option value="ENCAMINHAMENTO_SUAS">ENCAMINHAMENTO_SUAS</option>
            <option value="DOCUMENTO">DOCUMENTO</option>
            <option value="TAREFA">TAREFA</option>
          </select>
          <input className="input" placeholder="Meta (total no mês)" value={meta} onChange={(e) => setMeta(e.target.value)} style={{ maxWidth: 160 }} />
          <button className="btn btn-secundario" type="button" onClick={loadMetaAndActual} disabled={loading}>
            {loading ? "..." : "Atualizar"}
          </button>
          <button className="btn btn-primario" type="button" onClick={salvarMeta} disabled={loading}>
            Salvar
          </button>
        </div>
      </div>

      {msg ? <div className="texto-suave" style={{ marginTop: 8 }}><strong>{msg}</strong></div> : null}

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 10, marginTop: 10 }}>
        <div className="card" style={{ padding: 10, borderRadius: 16 }}>
          <div className="texto-suave">Realizado</div>
          <div style={{ fontWeight: 900, fontSize: 22 }}>{actual == null ? "—" : actual}</div>
        </div>
        <div className="card" style={{ padding: 10, borderRadius: 16 }}>
          <div className="texto-suave">Meta</div>
          <div style={{ fontWeight: 900, fontSize: 22 }}>{meta ? meta : "—"}</div>
        </div>
        <div className="card" style={{ padding: 10, borderRadius: 16 }}>
          <div className="texto-suave">Progresso</div>
          <div style={{ fontWeight: 900, fontSize: 22 }}>{meta ? `${pct}%` : "—"}</div>
        </div>
      </div>

      <div style={{ marginTop: 10 }}>
        <div style={{ height: 10, borderRadius: 999, background: "rgba(2,6,23,.08)" }}>
          <div style={{ height: 10, borderRadius: 999, width: `${meta ? Math.min(100, pct) : 0}%`, background: "rgba(99,102,241,.75)" }} />
        </div>
      </div>
    </div>
  );
}
