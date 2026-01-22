import React, { useEffect, useMemo, useState } from "react";

async function tryJson(apiFetch, apiBase, paths) {
  let lastErr = null;
  for (const p of paths) {
    try {
      const res = await apiFetch(`${apiBase}${p}`);
      const j = await res.json().catch(() => null);
      if (!res.ok) throw new Error(j?.detail || `Falha (HTTP ${res.status})`);
      return j;
    } catch (e) {
      lastErr = e;
    }
  }
  throw lastErr || new Error("Falha ao carregar");
}

export default function TelaTerceiroSetorParcerias({ apiBase, apiFetch, municipioId }) {
  const [loading, setLoading] = useState(false);
  const [erro, setErro] = useState("");
  const [parcerias, setParcerias] = useState([]);
  const [q, setQ] = useState("");

  const storageKey = useMemo(() => `terceiro_setor_parcerias_cache_${municipioId || "all"}`, [municipioId]);

  async function carregar() {
    setLoading(true);
    setErro("");
    try {
      const qs = municipioId ? `?municipio_id=${encodeURIComponent(municipioId)}` : "";
      const data = await tryJson(apiFetch, apiBase, [
        `/terceiro-setor/parcerias${qs}`,
        `/terceiro_setor/parcerias${qs}`,
        `/parcerias${qs}`,
      ]);
      const arr = Array.isArray(data) ? data : (Array.isArray(data?.items) ? data.items : []);
      setParcerias(arr);
      try { localStorage.setItem(storageKey, JSON.stringify(arr)); } catch {}
    } catch (e) {
      // fallback: cache local
      try {
        const cached = JSON.parse(localStorage.getItem(storageKey) || "null");
        if (Array.isArray(cached)) setParcerias(cached);
      } catch {}
      setErro(e?.message || "Não foi possível carregar parcerias (integração em andamento)." );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    carregar();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [municipioId]);

  const filtradas = useMemo(() => {
    const term = q.trim().toLowerCase();
    if (!term) return parcerias;
    return (parcerias || []).filter((p) => {
      const txt = [p?.numero, p?.tipo, p?.osc_nome, p?.objeto, p?.status].filter(Boolean).join(" ").toLowerCase();
      return txt.includes(term);
    });
  }, [parcerias, q]);

  return (
    <div className="layout-1col">
      <div className="card card-wide">
        <div className="card-header-row">
          <div>
            <h2 style={{ margin: 0 }}>Parcerias</h2>
            <div className="card-subtitle">Termos/convênios, objeto, status e valores.</div>
          </div>
          <div style={{ display: "flex", gap: 10, alignItems: "center", flexWrap: "wrap" }}>
            <input
              className="input"
              placeholder="Buscar por OSC, número, objeto..."
              value={q}
              onChange={(e) => setQ(e.target.value)}
              style={{ width: 340, maxWidth: "70vw" }}
            />
            <button className="btn btn-secundario" type="button" onClick={carregar} disabled={loading}>
              Atualizar
            </button>
          </div>
        </div>

        {erro ? <div className="erro-global">{erro}</div> : null}

        <div style={{ marginTop: 12, overflowX: "auto" }}>
          <table className="tabela" style={{ minWidth: 860 }}>
            <thead>
              <tr>
                <th>Número</th>
                <th>Tipo</th>
                <th>OSC</th>
                <th>Objeto</th>
                <th>Status</th>
                <th>Valor</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr><td colSpan={6} className="texto-suave">Carregando...</td></tr>
              ) : (filtradas || []).length ? (
                filtradas.map((p) => (
                  <tr key={p.id ?? p.numero ?? Math.random()}>
                    <td><b>{p.numero || "—"}</b></td>
                    <td>{p.tipo || p.modalidade || "—"}</td>
                    <td>{p.osc_nome || p.osc?.nome || "—"}</td>
                    <td style={{ maxWidth: 420 }}>
                      <div style={{ whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }} title={p.objeto || ""}>
                        {p.objeto || "—"}
                      </div>
                    </td>
                    <td>{p.status || "—"}</td>
                    <td>{p.valor_total != null ? `R$ ${Number(p.valor_total).toLocaleString("pt-BR")}` : "—"}</td>
                  </tr>
                ))
              ) : (
                <tr><td colSpan={6} className="texto-suave">Nenhuma parceria encontrada.</td></tr>
              )}
            </tbody>
          </table>
        </div>

        <div className="texto-suave" style={{ marginTop: 12 }}>
          Observação: a tela já está pronta para integrar criação/edição e vínculos com metas e anexos. Assim que os endpoints forem expostos, ligamos os formulários.
        </div>
      </div>
    </div>
  );
}
