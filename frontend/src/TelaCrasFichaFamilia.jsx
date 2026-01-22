import { useEffect, useMemo, useState } from "react";

function fmt(iso) {
  if (!iso) return "—";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleString("pt-BR");
}

function dlCSV(filename, csvText) {
  const blob = new Blob([csvText], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

function esc(v) {
  const s = v == null ? "" : String(v);
  if (s.includes('"') || s.includes(",") || s.includes("\n")) return `"${s.replace(/"/g,'""')}"`;
  return s;
}

function exportPDFSimple(data, periodoStr) {
  const fam = data?.familia || {};
  const pend = data?.pendencias || [];
  const tl = data?.timeline || [];
  const htmlPend = pend.map((p) => `<tr><td>${esc(p.tipo)}</td><td>${esc(p.gravidade)}</td><td>${esc(p.detalhe)}</td></tr>`).join("");
  const htmlTl = tl.slice(0,80).map((e) => `<tr><td>${esc(e.quando)}</td><td>${esc(e.titulo)}</td><td>${esc(e.detalhe)}</td></tr>`).join("");

  const html = `
  <html><head><meta charset="utf-8"/>
  <title>Ficha da Família</title>
  <style>
    body{font-family:system-ui,-apple-system,Segoe UI,Roboto,Arial;padding:24px}
    h1{margin:0 0 6px 0}
    .muted{color:#555;margin:0 0 14px 0}
    table{border-collapse:collapse;width:100%}
    th,td{border-bottom:1px solid #e5e7eb;padding:8px;text-align:left;vertical-align:top}
    th{background:#f8fafc}
  </style>
  </head><body>
    <h1>Ficha da Família</h1>
    <p class="muted">Período: ${esc(periodoStr)} · Família #${esc(fam.id)} · NIS: ${esc(fam.nis_familia)} · Bairro: ${esc(fam.bairro)}</p>
    <h2>Pendências</h2>
    <table><thead><tr><th>Tipo</th><th>Gravidade</th><th>Detalhe</th></tr></thead><tbody>${htmlPend}</tbody></table>
    <h2 style="margin-top:18px;">Timeline</h2>
    <table><thead><tr><th>Quando</th><th>Evento</th><th>Obs</th></tr></thead><tbody>${htmlTl}</tbody></table>
  </body></html>`;
  const w = window.open("", "_blank");
  if (!w) return alert("Pop-up bloqueado. Permita pop-ups para exportar PDF.");
  w.document.open();
  w.document.write(html);
  w.document.close();
  setTimeout(() => { w.focus(); w.print(); }, 400);
}

export default function TelaCrasFichaFamilia({ apiBase, apiFetch, familiaId }) {
  const [erro, setErro] = useState("");
  const [loading, setLoading] = useState(false);

  const [familias, setFamilias] = useState([]);
  const [famSel, setFamSel] = useState(familiaId || null);
  const [data, setData] = useState(null);

  const periodo = useMemo(() => {
    const d = new Date();
    return { ano: d.getFullYear(), mes: (d.getMonth() + 1) };
  }, []);
  const periodoStr = `${periodo.ano}-${String(periodo.mes).padStart(2, "0")}`;

  async function loadFamilias() {
    try {
      const r = await apiFetch(`${apiBase}/cras/cadastros/familias`);
      if (!r.ok) { setErro(`Erro ao carregar famílias (${r.status})`); setFamilias([]); return; }
      const j = await r.json();
      setFamilias(Array.isArray(j) ? j : []);
    } catch (e) {
      console.error(e);
      setErro("Erro ao carregar famílias.");
      setFamilias([]);
    }
  }

  async function loadFicha() {
    if (!famSel) { setData(null); return; }
    setErro("");
    setLoading(true);
    try {
      const qs = new URLSearchParams();
      qs.set("ano", String(periodo.ano));
      qs.set("mes", String(periodo.mes));
      const r = await apiFetch(`${apiBase}/cras/ficha/familias/${Number(famSel)}?${qs.toString()}`);
      if (!r.ok) throw new Error(await r.text());
      setData(await r.json());
    } catch (e) {
      console.error(e);
      setErro("Erro ao carregar ficha da família.");
      setData(null);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { loadFamilias(); }, []); // eslint-disable-line
  useEffect(() => { if (familiaId) setFamSel(familiaId); }, [familiaId]);
  useEffect(() => { loadFicha(); }, [famSel]); // eslint-disable-line

  return (
    <div className="layout-1col">
      <div className="card" style={{ padding: 14, borderRadius: 18 }}>
        <div style={{ display: "flex", justifyContent: "space-between", gap: 12, flexWrap: "wrap", alignItems: "center" }}>
          <div>
            <div style={{ fontWeight: 900, fontSize: 18 }}>Ficha da Família</div>
            <div className="texto-suave">Período: <strong>{periodoStr}</strong></div>
          </div>

          <div style={{ minWidth: 520 }}>
            <div className="texto-suave">Selecionar família: <strong>{familias.length}</strong></div>
            <select className="input" value={famSel || ""} onChange={(e) => { const v = e.target.value; const id = v ? Number(v) : null; setFamSel(id); try { if (v) localStorage.setItem("cras_ficha_familia_id", v); } catch {} }}>
              <option value="">Selecione…</option>
              {familias.map((f) => (
                <option key={f.id} value={f.id}>Família #{f.id} · NIS: {f.nis_familia || "—"} · {f.bairro || "—"}</option>
              ))}
            </select>
          </div>

          <div style={{ display: "flex", gap: 10, flexWrap: "wrap", alignItems: "center" }}>
            <button className="btn btn-secundario" type="button" onClick={loadFicha}>Atualizar</button>
            <button className="btn btn-secundario btn-secundario-mini" type="button" disabled={!data} onClick={() => {
              const header = ["tipo","gravidade","detalhe"];
              const lines = [header.join(",")];
              (data.pendencias||[]).forEach((p) => lines.push([p.tipo,p.gravidade,p.detalhe].map(esc).join(",")));
              dlCSV(`ficha_familia_pendencias_${data.familia?.id || "familia"}_${periodoStr}.csv`, lines.join("\n"));
            }}>CSV pendências</button>
            <button className="btn btn-primario btn-primario-mini" type="button" disabled={!data} onClick={() => exportPDFSimple(data, periodoStr)}>PDF</button>
          </div>
        </div>

        {erro ? <div className="card" style={{ padding: 12, borderRadius: 14, marginTop: 10 }}><strong>{erro}</strong></div> : null}
        {loading ? <div className="texto-suave" style={{ marginTop: 10 }}>Carregando…</div> : null}
      </div>

      {data ? (
        <div className="card" style={{ padding: 14, borderRadius: 18, marginTop: 12 }}>
          <div style={{ fontWeight: 900 }}>Resumo</div>
          <div className="texto-suave" style={{ marginTop: 8 }}>
            Família #{data.familia?.id} · NIS: <strong>{data.familia?.nis_familia || "—"}</strong> · Bairro: <strong>{data.familia?.bairro || "—"}</strong> · Território: <strong>{data.familia?.territorio || "—"}</strong>
          </div>
          <div className="texto-suave">
            Membros: <strong>{(data.membros || []).length}</strong> · Pendências: <strong>{(data.pendencias || []).length}</strong> · Timeline: <strong>{(data.timeline || []).length}</strong>
          </div>

          <div className="texto-suave" style={{ marginTop: 10, fontWeight: 900 }}>Membros</div>
          <div style={{ display: "grid", gap: 8, marginTop: 8, maxHeight: 220, overflow: "auto" }}>
            {(data.membros || []).map((m, i) => (
              <div key={i} className="card" style={{ padding: 10, borderRadius: 14 }}>
                <div style={{ fontWeight: 900 }}>{m.pessoa?.nome || `Pessoa #${m.membro?.pessoa_id}`}</div>
                <div className="texto-suave">CPF: {m.pessoa?.cpf || "—"} · NIS: {m.pessoa?.nis || "—"}</div>
              </div>
            ))}
          </div>

          <div className="texto-suave" style={{ marginTop: 12, fontWeight: 900 }}>Pendências (top)</div>
          <div style={{ display: "grid", gap: 8, marginTop: 8, maxHeight: 220, overflow: "auto" }}>
            {(data.pendencias || []).slice(0, 12).map((p, i) => (
              <div key={i} className="card" style={{ padding: 10, borderRadius: 14 }}>
                <div style={{ fontWeight: 900 }}>{p.tipo} · {p.gravidade}</div>
                <div className="texto-suave">{p.detalhe}</div>
              </div>
            ))}
          </div>

          <div className="texto-suave" style={{ marginTop: 12, fontWeight: 900 }}>Timeline (top)</div>
          <div style={{ display: "grid", gap: 8, marginTop: 8, maxHeight: 220, overflow: "auto" }}>
            {(data.timeline || []).slice(0, 40).map((e, i) => (
              <div key={i} className="card" style={{ padding: 10, borderRadius: 14 }}>
                <div style={{ fontWeight: 900 }}>{e.titulo}</div>
                <div className="texto-suave">{fmt(e.quando)}</div>
                {e.detalhe ? <div className="texto-suave">Obs: {e.detalhe}</div> : null}
              </div>
            ))}
          </div>
        </div>
      ) : null}
    </div>
  );
}
