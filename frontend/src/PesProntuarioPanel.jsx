import React, { useEffect, useMemo, useState } from "react";

// PES_PANEL_V1
export default function PesProntuarioPanel({ apiBase, apiFetch, pessoaId = null, familiaId = null, casoId = null, unidadeId = null }) {
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState("");
  const [formaAcesso, setFormaAcesso] = useState("");
  const [primeiroAt, setPrimeiroAt] = useState("");
  const [inPaif, setInPaif] = useState("");
  const [outPaif, setOutPaif] = useState("");
  const [obs, setObs] = useState("");

  const canLoad = useMemo(
    () => Boolean(apiBase && typeof apiFetch === "function" && (pessoaId || familiaId || casoId)),
    [apiBase, apiFetch, pessoaId, familiaId, casoId]
  );

  async function load() {
    if (!canLoad) return;
    setLoading(true); setMsg("");
    try {
      const qs = new URLSearchParams();
      if (pessoaId) qs.set("pessoa_id", String(pessoaId));
      if (familiaId) qs.set("familia_id", String(familiaId));
      if (casoId) qs.set("caso_id", String(casoId));
      const r = await apiFetch(`${apiBase}/cras/pes?${qs.toString()}`);
      if (!r.ok) throw new Error(await r.text());
      const j = await r.json();
      if (!j?.found) {
        setFormaAcesso(""); setPrimeiroAt(""); setInPaif(""); setOutPaif(""); setObs("");
        setMsg("Sem registro (preencha e salve).");
        return;
      }
      setFormaAcesso(j.forma_acesso || "");
      setPrimeiroAt(j.primeiro_atendimento_em || "");
      setInPaif(j.inserido_paif_em || "");
      setOutPaif(j.desligado_paif_em || "");
      setObs(j.observacoes_json || "");
      setMsg("Carregado ✅");
    } catch (e) { console.error(e); setMsg("Falha ao carregar PES."); }
    finally { setLoading(false); }
  }

  async function save() {
    if (!canLoad) return;
    setLoading(true); setMsg("");
    try {
      const payload = {
        pessoa_id: pessoaId || null,
        familia_id: familiaId || null,
        caso_id: casoId || null,
        unidade_id: unidadeId || null,
        forma_acesso: formaAcesso || null,
        primeiro_atendimento_em: primeiroAt || null,
        inserido_paif_em: inPaif || null,
        desligado_paif_em: outPaif || null,
        observacoes: obs || null,
      };
      const r = await apiFetch(`${apiBase}/cras/pes`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!r.ok) throw new Error(await r.text());
      setMsg("Salvo ✅");
    } catch (e) { console.error(e); setMsg("Falha ao salvar PES."); }
    finally { setLoading(false); }
  }

  useEffect(() => { if (open) load(); /* eslint-disable-next-line */ }, [open]);

  if (!canLoad) return null;

  return (
    <div className="card" style={{ padding: 12, borderRadius: 16, marginBottom: 10 }}>
      <div style={{ display: "flex", justifyContent: "space-between", gap: 10, flexWrap: "wrap", alignItems: "center" }}>
        <div>
          <div style={{ fontWeight: 900 }}>Prontuário (PES)</div>
          <div className="texto-suave">Campos estruturados (forma de acesso, inserção/desligamento PAIF) + trilha.</div>
        </div>
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
          <button className="btn btn-secundario" type="button" onClick={() => setOpen((v) => !v)}>
            {open ? "Fechar" : "Abrir"}
          </button>
          {open ? (
            <button className="btn btn-primario" type="button" onClick={save} disabled={loading}>
              {loading ? "..." : "Salvar"}
            </button>
          ) : null}
        </div>
      </div>

      {open ? (
        <div style={{ marginTop: 10, display: "grid", gap: 8 }}>
          {msg ? <div className="texto-suave"><strong>{msg}</strong></div> : null}

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
            <select className="input" value={formaAcesso} onChange={(e) => setFormaAcesso(e.target.value)}>
              <option value="">Forma de acesso…</option>
              <option value="espontanea">Espontânea</option>
              <option value="busca_ativa">Busca ativa</option>
              <option value="encaminhamento">Encaminhamento</option>
              <option value="demanda">Demanda</option>
              <option value="outro">Outro</option>
            </select>
            <input className="input" type="date" value={primeiroAt} onChange={(e) => setPrimeiroAt(e.target.value)} />
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
            <input className="input" type="date" value={inPaif} onChange={(e) => setInPaif(e.target.value)} />
            <input className="input" type="date" value={outPaif} onChange={(e) => setOutPaif(e.target.value)} />
          </div>

          <textarea className="input" rows={4} placeholder="Observações (JSON ou texto)" value={obs} onChange={(e) => setObs(e.target.value)} />
        </div>
      ) : null}
    </div>
  );
}
