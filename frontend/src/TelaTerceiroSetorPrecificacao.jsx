import React, { useEffect, useState } from "react";

const inp = { width: "100%", padding: "10px 12px", borderRadius: 10, border: "1px solid rgba(2,6,23,.10)" };
const btnP = { padding: "10px 12px", borderRadius: 12, border: "1px solid rgba(2,6,23,.12)", background: "rgba(59,130,246,.12)", fontWeight: 900, cursor: "pointer" };
const btnG = { padding: "8px 10px", borderRadius: 10, border: "1px solid rgba(2,6,23,.12)", background: "#fff", fontWeight: 800, cursor: "pointer" };


export default function TelaTerceiroSetorPrecificacao({ municipioId, apiJson }) {
  const [parcerias, setParcerias] = useState([]);
  const [parceriaId, setParceriaId] = useState("");
  const [metas, setMetas] = useState([]);
  const [erro, setErro] = useState("");

  async function loadParcerias() {
    try {
      const p = await apiJson(`/terceiro-setor/parcerias?municipio_id=${encodeURIComponent(municipioId)}`);
      setParcerias(Array.isArray(p) ? p : []);
      if (!parceriaId && p?.[0]?.id) setParceriaId(String(p[0].id));
    } catch (e) { setErro(String(e?.message || e)); }
  }

  async function loadMetas(id) {
    if (!id) return;
    try {
      const m = await apiJson(`/terceiro-setor/parcerias/${id}/metas`);
      setMetas(Array.isArray(m) ? m : []);
    } catch (e) { setErro(String(e?.message || e)); }
  }

  useEffect(() => { loadParcerias(); /* eslint-disable-next-line */ }, [municipioId]);
  useEffect(() => { if (parceriaId) loadMetas(parceriaId); /* eslint-disable-next-line */ }, [parceriaId]);

  async function definir(metaId) {
    const q = prompt("Quantidade:", "48"); if (q == null) return;
    const cu = prompt("Custo unitário:", "520"); if (cu == null) return;
    const mem = prompt("Memória de cálculo (opcional):", "") ?? "";
    try {
      await apiJson(`/terceiro-setor/metas/${metaId}/precificacao`, {
        method: "POST",
        body: JSON.stringify({ quantidade: Number(q), custo_unitario: Number(cu), memoria_calculo: mem || null })
      });
      await loadMetas(parceriaId);
      alert("Precificação salva.");
    } catch (e) { alert(String(e?.message || e)); }
  }

  return (
    <div className="card" style={{ padding: 14, border: "1px solid rgba(2,6,23,.06)" }}>
      <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
        <div style={{ fontWeight: 900 }}>Precificação</div>
        <select style={{...inp, width: 360}} value={parceriaId} onChange={e=>setParceriaId(e.target.value)}>
          {(parcerias || []).map(p => <option key={p.id} value={String(p.id)}>{p.numero || `Parceria #${p.id}`} · OSC #{p.osc_id}</option>)}
        </select>
        <button style={btnG} onClick={() => loadMetas(parceriaId)}>Recarregar</button>
        {erro ? <div style={{ marginLeft: "auto", color: "#b91c1c", fontWeight: 800 }}>{erro}</div> : <div style={{ marginLeft: "auto" }} />}
      </div>

      <div style={{ marginTop: 12, display: "grid", gap: 10 }}>
        {metas.map(m => (
          <div key={m.id} style={{ border: "1px solid rgba(2,6,23,.08)", borderRadius: 14, padding: 12 }}>
            <div style={{ display: "flex", justifyContent: "space-between", gap: 10 }}>
              <div>
                <div style={{ fontWeight: 900 }}>{(m.codigo ? m.codigo + " · " : "") + m.titulo}</div>
                <div className="texto-suave" style={{ marginTop: 2 }}>{m.unidade_medida} · alvo {m.quantidade_alvo ?? "—"}</div>
              </div>
              <button style={btnP} onClick={() => definir(m.id)}>Definir custo</button>
            </div>
          </div>
        ))}
        {!metas.length ? <div className="texto-suave">Nenhuma meta.</div> : null}
      </div>
    </div>
  );
}
