import React, { useEffect, useState } from "react";

const inp = { width: "100%", padding: "10px 12px", borderRadius: 10, border: "1px solid rgba(2,6,23,.10)" };
const btnP = { padding: "10px 12px", borderRadius: 12, border: "1px solid rgba(2,6,23,.12)", background: "rgba(59,130,246,.12)", fontWeight: 900, cursor: "pointer" };
const btnG = { padding: "8px 10px", borderRadius: 10, border: "1px solid rgba(2,6,23,.12)", background: "#fff", fontWeight: 800, cursor: "pointer" };


export default function TelaTerceiroSetorPlanoMetas({ municipioId, apiJson }) {
  const [parcerias, setParcerias] = useState([]);
  const [parceriaId, setParceriaId] = useState("");
  const [plano, setPlano] = useState({ diagnostico: "", metodologia: "", publico_alvo: "", descricao_objeto: "" });
  const [metas, setMetas] = useState([]);
  const [erro, setErro] = useState("");

  const [metaForm, setMetaForm] = useState({
    codigo: "", titulo: "", unidade_medida: "oficinas",
    quantidade_alvo: "", indicador: "", criterio_aceite: "", meios_verificacao: "", prazo: ""
  });

  async function loadParcerias() {
    try {
      const p = await apiJson(`/terceiro-setor/parcerias?municipio_id=${encodeURIComponent(municipioId)}`);
      setParcerias(Array.isArray(p) ? p : []);
      if (!parceriaId && p?.[0]?.id) setParceriaId(String(p[0].id));
    } catch (e) { setErro(String(e?.message || e)); }
  }

  async function load(id) {
    if (!id) return;
    setErro("");
    try {
      const pl = await apiJson(`/terceiro-setor/parcerias/${id}/plano`).catch(() => null);
      if (pl && typeof pl === "object") {
        setPlano({
          diagnostico: pl.diagnostico || "",
          metodologia: pl.metodologia || "",
          publico_alvo: pl.publico_alvo || "",
          descricao_objeto: pl.descricao_objeto || "",
        });
      } else {
        setPlano({ diagnostico: "", metodologia: "", publico_alvo: "", descricao_objeto: "" });
      }
      const m = await apiJson(`/terceiro-setor/parcerias/${id}/metas`);
      setMetas(Array.isArray(m) ? m : []);
    } catch (e) { setErro(String(e?.message || e)); }
  }

  useEffect(() => { loadParcerias(); /* eslint-disable-next-line */ }, [municipioId]);
  useEffect(() => { if (parceriaId) load(parceriaId); /* eslint-disable-next-line */ }, [parceriaId]);

  async function salvarPlano() {
    try {
      await apiJson(`/terceiro-setor/parcerias/${parceriaId}/plano`, { method: "POST", body: JSON.stringify(plano) });
      await load(parceriaId);
      alert("Plano salvo.");
    } catch (e) { setErro(String(e?.message || e)); }
  }

  async function criarMeta() {
    setErro("");
    try {
      const payload = { ...metaForm, quantidade_alvo: metaForm.quantidade_alvo ? Number(metaForm.quantidade_alvo) : null, prazo: metaForm.prazo || null };
      await apiJson(`/terceiro-setor/parcerias/${parceriaId}/metas`, { method: "POST", body: JSON.stringify(payload) });
      setMetaForm({ codigo: "", titulo: "", unidade_medida: "oficinas", quantidade_alvo: "", indicador: "", criterio_aceite: "", meios_verificacao: "", prazo: "" });
      await load(parceriaId);
    } catch (e) { setErro(String(e?.message || e)); }
  }

  async function editarPrazo(metaId, atual) {
    const prazo = prompt("Prazo (YYYY-MM-DD):", atual || "");
    if (prazo == null) return;
    await apiJson(`/terceiro-setor/metas/${metaId}`, { method: "PATCH", body: JSON.stringify({ prazo: prazo || null }) });
    await load(parceriaId);
  }

  return (
    <div className="card" style={{ padding: 14, border: "1px solid rgba(2,6,23,.06)" }}>
      <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
        <div style={{ fontWeight: 900 }}>Plano & Metas</div>
        <select style={{...inp, width: 360}} value={parceriaId} onChange={e=>setParceriaId(e.target.value)}>
          {(parcerias || []).map(p => <option key={p.id} value={String(p.id)}>{p.numero || `Parceria #${p.id}`} · OSC #{p.osc_id}</option>)}
        </select>
        <button style={btnG} onClick={() => load(parceriaId)}>Recarregar</button>
        {erro ? <div style={{ marginLeft: "auto", color: "#b91c1c", fontWeight: 800 }}>{erro}</div> : <div style={{ marginLeft: "auto" }} />}
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, marginTop: 12 }}>
        <div style={{ border: "1px solid rgba(2,6,23,.08)", borderRadius: 14, padding: 12 }}>
          <div style={{ fontWeight: 900 }}>Plano</div>
          <div style={{ display: "grid", gap: 8, marginTop: 10 }}>
            <textarea style={{...inp, minHeight: 90}} placeholder="Diagnóstico" value={plano.diagnostico} onChange={e=>setPlano(p=>({...p,diagnostico:e.target.value}))}/>
            <textarea style={{...inp, minHeight: 70}} placeholder="Descrição do objeto" value={plano.descricao_objeto} onChange={e=>setPlano(p=>({...p,descricao_objeto:e.target.value}))}/>
            <textarea style={{...inp, minHeight: 90}} placeholder="Metodologia" value={plano.metodologia} onChange={e=>setPlano(p=>({...p,metodologia:e.target.value}))}/>
            <input style={inp} placeholder="Público-alvo" value={plano.publico_alvo} onChange={e=>setPlano(p=>({...p,publico_alvo:e.target.value}))}/>
            <button style={btnP} onClick={salvarPlano}>Salvar plano</button>
          </div>
        </div>

        <div style={{ border: "1px solid rgba(2,6,23,.08)", borderRadius: 14, padding: 12 }}>
          <div style={{ fontWeight: 900 }}>Nova Meta</div>
          <div style={{ display: "grid", gap: 8, marginTop: 10 }}>
            <input style={inp} placeholder="Código (M1)" value={metaForm.codigo} onChange={e=>setMetaForm(m=>({...m,codigo:e.target.value}))}/>
            <input style={inp} placeholder="Título" value={metaForm.titulo} onChange={e=>setMetaForm(m=>({...m,titulo:e.target.value}))}/>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
              <input style={inp} placeholder="Unidade (oficinas)" value={metaForm.unidade_medida} onChange={e=>setMetaForm(m=>({...m,unidade_medida:e.target.value}))}/>
              <input style={inp} placeholder="Quantidade alvo" value={metaForm.quantidade_alvo} onChange={e=>setMetaForm(m=>({...m,quantidade_alvo:e.target.value}))}/>
            </div>
            <input style={inp} placeholder="Indicador" value={metaForm.indicador} onChange={e=>setMetaForm(m=>({...m,indicador:e.target.value}))}/>
            <textarea style={{...inp, minHeight: 70}} placeholder="Critério de aceite" value={metaForm.criterio_aceite} onChange={e=>setMetaForm(m=>({...m,criterio_aceite:e.target.value}))}/>
            <textarea style={{...inp, minHeight: 70}} placeholder="Meios de verificação" value={metaForm.meios_verificacao} onChange={e=>setMetaForm(m=>({...m,meios_verificacao:e.target.value}))}/>
            <input style={inp} placeholder="Prazo (YYYY-MM-DD)" value={metaForm.prazo} onChange={e=>setMetaForm(m=>({...m,prazo:e.target.value}))}/>
            <button style={btnP} onClick={criarMeta}>Salvar meta</button>
          </div>
        </div>
      </div>

      <div style={{ marginTop: 14 }}>
        <div style={{ fontWeight: 900, marginBottom: 8 }}>Metas</div>
        <div style={{ display: "grid", gap: 10 }}>
          {metas.map(m => (
            <div key={m.id} style={{ border: "1px solid rgba(2,6,23,.08)", borderRadius: 14, padding: 12 }}>
              <div style={{ display: "flex", justifyContent: "space-between", gap: 10 }}>
                <div>
                  <div style={{ fontWeight: 900 }}>{(m.codigo ? m.codigo + " · " : "") + m.titulo}</div>
                  <div className="texto-suave" style={{ marginTop: 2 }}>
                    {m.unidade_medida} · alvo {m.quantidade_alvo ?? "—"} · prazo {m.prazo || "—"}
                  </div>
                </div>
                <button style={btnG} onClick={() => editarPrazo(m.id, m.prazo)}>Editar prazo</button>
              </div>
              <div className="texto-suave" style={{ marginTop: 8 }}>{m.indicador || "—"}</div>
            </div>
          ))}
          {!metas.length ? <div className="texto-suave">Nenhuma meta.</div> : null}
        </div>
      </div>
    </div>
  );
}
