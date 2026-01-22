import React, { useEffect, useMemo, useState } from "react";

function onlyDigits(s) {
  return String(s || "").replace(/\D+/g, "");
}

function isValidCnpj(cnpj) {
  const d = onlyDigits(cnpj);
  return d.length === 14;
}

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

export default function TelaTerceiroSetorOscs({ apiBase, apiFetch, municipioId }) {
  const [loading, setLoading] = useState(false);
  const [erro, setErro] = useState("");
  const [oscs, setOscs] = useState([]);
  const [q, setQ] = useState("");

  const [formOpen, setFormOpen] = useState(false);
  const [form, setForm] = useState({
    nome: "",
    razao_social: "",
    cnpj: "",
    area_atuacao: "",
    contato: "",
    email: "",
    telefone: "",
    endereco: "",
  });

  const storageKey = useMemo(() => `terceiro_setor_oscs_cache_${municipioId || "all"}`, [municipioId]);

  async function carregar() {
    setLoading(true);
    setErro("");
    try {
      const qs = municipioId ? `?municipio_id=${encodeURIComponent(municipioId)}` : "";
      const data = await tryJson(apiFetch, apiBase, [
        `/terceiro-setor/oscs${qs}`,
        `/terceiro_setor/oscs${qs}`,
        `/oscs${qs}`,
      ]);
      const arr = Array.isArray(data) ? data : (Array.isArray(data?.items) ? data.items : []);
      setOscs(arr);
      try { localStorage.setItem(storageKey, JSON.stringify(arr)); } catch {}
    } catch (e) {
      // fallback: cache local
      try {
        const cached = JSON.parse(localStorage.getItem(storageKey) || "null");
        if (Array.isArray(cached)) setOscs(cached);
      } catch {}
      setErro(e?.message || "Não foi possível carregar OSCs (integração em andamento)."
      );
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
    if (!term) return oscs;
    return (oscs || []).filter((o) => {
      const txt = [o?.nome, o?.razao_social, o?.cnpj, o?.area_atuacao, o?.email].filter(Boolean).join(" ").toLowerCase();
      return txt.includes(term);
    });
  }, [oscs, q]);

  function resetForm() {
    setForm({ nome: "", razao_social: "", cnpj: "", area_atuacao: "", contato: "", email: "", telefone: "", endereco: "" });
  }

  async function salvar() {
    const payload = {
      ...form,
      municipio_id: municipioId ? Number(municipioId) : null,
      cnpj: onlyDigits(form.cnpj),
    };

    if (!payload.nome && !payload.razao_social) {
      setErro("Informe pelo menos o nome (ou razão social) da OSC.");
      return;
    }
    if (payload.cnpj && !isValidCnpj(payload.cnpj)) {
      setErro("CNPJ inválido (precisa ter 14 dígitos).");
      return;
    }

    setErro("");
    setLoading(true);
    try {
      // tenta salvar no back-end; se não existir, mantém no cache local
      const res = await apiFetch(`${apiBase}/terceiro-setor/oscs`, {
        method: "POST",
        body: JSON.stringify(payload),
      });
      const j = await res.json().catch(() => null);
      if (!res.ok) throw new Error(j?.detail || `Falha (HTTP ${res.status})`);

      // Se o back retornar o item, adiciona; senão recarrega.
      if (j && typeof j === "object") {
        setOscs((prev) => {
          const next = [j, ...(prev || [])];
          try { localStorage.setItem(storageKey, JSON.stringify(next)); } catch {}
          return next;
        });
      } else {
        await carregar();
      }

      resetForm();
      setFormOpen(false);
    } catch (e) {
      // fallback local
      const localItem = {
        id: `local_${Date.now()}`,
        ...payload,
        nome: payload.nome || payload.razao_social,
      };
      setOscs((prev) => {
        const next = [localItem, ...(prev || [])];
        try { localStorage.setItem(storageKey, JSON.stringify(next)); } catch {}
        return next;
      });
      resetForm();
      setFormOpen(false);
      setErro("Back-end de OSCs ainda não está ativo — salvei localmente (cache do navegador) para não travar seu fluxo.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="layout-1col">
      <div className="card card-wide">
        <div className="card-header-row">
          <div>
            <h2 style={{ margin: 0 }}>OSCs</h2>
            <div className="card-subtitle">Cadastro de organizações (OSC) e dados para parcerias (MROSC).</div>
          </div>
          <div style={{ display: "flex", gap: 10, alignItems: "center", flexWrap: "wrap" }}>
            <input
              className="input"
              placeholder="Buscar por nome, CNPJ, área..."
              value={q}
              onChange={(e) => setQ(e.target.value)}
              style={{ width: 320, maxWidth: "70vw" }}
            />
            <button className="btn btn-secundario" type="button" onClick={carregar} disabled={loading}>
              Atualizar
            </button>
            <button className="btn btn-primario" type="button" onClick={() => setFormOpen((v) => !v)}>
              {formOpen ? "Fechar" : "Nova OSC"}
            </button>
          </div>
        </div>

        {erro ? <div className="erro-global">{erro}</div> : null}

        {formOpen ? (
          <div className="card" style={{ padding: 14, marginTop: 12, background: "rgba(255,255,255,0.75)" }}>
            <div className="card-header-row">
              <h3 style={{ margin: 0 }}>Cadastrar OSC</h3>
              <div className="texto-suave">Campos mínimos: Nome/Razão Social.</div>
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "repeat(2, minmax(0, 1fr))", gap: 12 }}>
              <div>
                <label className="form-label">Nome fantasia</label>
                <input className="input" value={form.nome} onChange={(e) => setForm((f) => ({ ...f, nome: e.target.value }))} />
              </div>
              <div>
                <label className="form-label">Razão social</label>
                <input className="input" value={form.razao_social} onChange={(e) => setForm((f) => ({ ...f, razao_social: e.target.value }))} />
              </div>

              <div>
                <label className="form-label">CNPJ</label>
                <input className="input" value={form.cnpj} onChange={(e) => setForm((f) => ({ ...f, cnpj: e.target.value }))} placeholder="00.000.000/0000-00" />
              </div>
              <div>
                <label className="form-label">Área de atuação</label>
                <input className="input" value={form.area_atuacao} onChange={(e) => setForm((f) => ({ ...f, area_atuacao: e.target.value }))} placeholder="Ex.: acolhimento, SCFV, crianças..." />
              </div>

              <div>
                <label className="form-label">Contato</label>
                <input className="input" value={form.contato} onChange={(e) => setForm((f) => ({ ...f, contato: e.target.value }))} />
              </div>
              <div>
                <label className="form-label">E-mail</label>
                <input className="input" value={form.email} onChange={(e) => setForm((f) => ({ ...f, email: e.target.value }))} />
              </div>

              <div>
                <label className="form-label">Telefone</label>
                <input className="input" value={form.telefone} onChange={(e) => setForm((f) => ({ ...f, telefone: e.target.value }))} />
              </div>
              <div>
                <label className="form-label">Endereço</label>
                <input className="input" value={form.endereco} onChange={(e) => setForm((f) => ({ ...f, endereco: e.target.value }))} />
              </div>
            </div>

            <div className="card-footer-right">
              <button className="btn btn-secundario" type="button" onClick={() => { resetForm(); setFormOpen(false); }} disabled={loading}>
                Cancelar
              </button>
              <button className="btn btn-primario" type="button" onClick={salvar} disabled={loading}>
                Salvar
              </button>
            </div>
          </div>
        ) : null}

        <div style={{ marginTop: 12, overflowX: "auto" }}>
          <table className="tabela" style={{ minWidth: 860 }}>
            <thead>
              <tr>
                <th>OSC</th>
                <th>CNPJ</th>
                <th>Área</th>
                <th>Contato</th>
                <th>Telefone</th>
                <th>E-mail</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr><td colSpan={6} className="texto-suave">Carregando...</td></tr>
              ) : (filtradas || []).length ? (
                filtradas.map((o) => (
                  <tr key={o.id ?? o.cnpj ?? o.nome ?? Math.random()}>
                    <td><b>{o.nome || o.razao_social || "—"}</b><div className="texto-suave">{o.razao_social && o.nome && o.razao_social !== o.nome ? o.razao_social : ""}</div></td>
                    <td>{o.cnpj ? String(o.cnpj) : "—"}</td>
                    <td>{o.area_atuacao || "—"}</td>
                    <td>{o.contato || "—"}</td>
                    <td>{o.telefone || "—"}</td>
                    <td>{o.email || "—"}</td>
                  </tr>
                ))
              ) : (
                <tr><td colSpan={6} className="texto-suave">Nenhuma OSC encontrada.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
