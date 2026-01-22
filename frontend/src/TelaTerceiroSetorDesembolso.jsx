import React, { useEffect, useState } from "react";

const inp = { width: "100%", padding: "10px 12px", borderRadius: 10, border: "1px solid rgba(2,6,23,.10)" };
const btnP = { padding: "10px 12px", borderRadius: 12, border: "1px solid rgba(2,6,23,.12)", background: "rgba(59,130,246,.12)", fontWeight: 900, cursor: "pointer" };
const btnG = { padding: "8px 10px", borderRadius: 10, border: "1px solid rgba(2,6,23,.12)", background: "#fff", fontWeight: 800, cursor: "pointer" };


export default function TelaTerceiroSetorDesembolso({ municipioId, apiJson }) {
  const [parcerias, setParcerias] = useState([]);
  const [parceriaId, setParceriaId] = useState("");
  const [parcelas, setParcelas] = useState([]);
  const [erro, setErro] = useState("");

  const [form, setForm] = useState({ numero: "", valor: "", data_prevista: "", condicao: "" });

  async function loadParcerias() {
    try {
      const p = await apiJson(`/terceiro-setor/parcerias?municipio_id=${encodeURIComponent(municipioId)}`);
      setParcerias(Array.isArray(p) ? p : []);
      if (!parceriaId && p?.[0]?.id) setParceriaId(String(p[0].id));
    } catch (e) { setErro(String(e?.message || e)); }
  }

  async function loadParcelas(id) {
    if (!id) return;
    try {
      const j = await apiJson(`/terceiro-setor/parcerias/${id}/desembolso`);
      setParcelas(Array.isArray(j) ? j : []);
    } catch (e) { setErro(String(e?.message || e)); }
  }

  useEffect(() => { loadParcerias(); /* eslint-disable-next-line */ }, [municipioId]);
  useEffect(() => { if (parceriaId) loadParcelas(parceriaId); /* eslint-disable-next-line */ }, [parceriaId]);

  async function criar() {
    try {
      await apiJson(`/terceiro-setor/parcerias/${parceriaId}/desembolso`, {
        method: "POST",
        body: JSON.stringify({
          numero: Number(form.numero),
          valor: Number(form.valor),
          data_prevista: form.data_prevista || null,
          condicao: form.condicao || null,
        })
      });
      setForm({ numero: "", valor: "", data_prevista: "", condicao: "" });
      await loadParcelas(parceriaId);
    } catch (e) { setErro(String(e?.message || e)); }
  }

  return (
    <div className="card" style={{ padding: 14, border: "1px solid rgba(2,6,23,.06)" }}>
      <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
        <div style={{ fontWeight: 900 }}>Desembolso</div>
        <select style={{...inp, width: 360}} value={parceriaId} onChange={e=>setParceriaId(e.target.value)}>
          {(parcerias || []).map(p => <option key={p.id} value={String(p.id)}>{p.numero || `Parceria #${p.id}`} · OSC #{p.osc_id}</option>)}
        </select>
        <button style={btnG} onClick={() => loadParcelas(parceriaId)}>Recarregar</button>
        {erro ? <div style={{ marginLeft: "auto", color: "#b91c1c", fontWeight: 800 }}>{erro}</div> : <div style={{ marginLeft: "auto" }} />}
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "420px 1fr", gap: 12, marginTop: 12 }}>
        <div style={{ border: "1px solid rgba(2,6,23,.08)", borderRadius: 14, padding: 12 }}>
          <div style={{ fontWeight: 900, marginBottom: 8 }}>Nova parcela</div>
          <div style={{ display: "grid", gap: 8 }}>
            <input style={inp} placeholder="Número" value={form.numero} onChange={e=>setForm(f=>({...f,numero:e.target.value}))}/>
            <input style={inp} placeholder="Valor" value={form.valor} onChange={e=>setForm(f=>({...f,valor:e.target.value}))}/>
            <input style={inp} placeholder="Data prevista (YYYY-MM-DD)" value={form.data_prevista} onChange={e=>setForm(f=>({...f,data_prevista:e.target.value}))}/>
            <textarea style={{...inp, minHeight: 90}} placeholder="Condição" value={form.condicao} onChange={e=>setForm(f=>({...f,condicao:e.target.value}))}/>
            <button style={btnP} onClick={criar}>Salvar parcela</button>
          </div>
        </div>

        <div style={{ border: "1px solid rgba(2,6,23,.08)", borderRadius: 14, padding: 12 }}>
          <div style={{ fontWeight: 900 }}>Parcelas</div>
          <div style={{ marginTop: 10, display: "grid", gap: 10 }}>
            {parcelas.map(p => (
              <div key={p.id} style={{ border: "1px solid rgba(2,6,23,.08)", borderRadius: 14, padding: 12 }}>
                <div style={{ fontWeight: 900 }}>Parcela {p.numero}</div>
                <div className="texto-suave" style={{ marginTop: 2 }}>{p.valor} · {p.data_prevista || "sem data"}</div>
                {p.condicao ? <div className="texto-suave" style={{ marginTop: 8 }}>{p.condicao}</div> : null}
              </div>
            ))}
            {!parcelas.length ? <div className="texto-suave">Nenhuma parcela.</div> : null}
          </div>
        </div>
      </div>
    </div>
  );
}
