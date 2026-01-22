import React, { useEffect, useMemo, useState } from "react";

function fmtDateBR(d) {
  if (!d) return "—";
  try {
    const dt = typeof d === "string" ? new Date(d) : d;
    if (Number.isNaN(dt.getTime())) return String(d);
    return dt.toLocaleDateString();
  } catch {
    return String(d);
  }
}

function toDateInput(v) {
  if (!v) return "";
  try {
    const dt = typeof v === "string" ? new Date(v) : v;
    if (Number.isNaN(dt.getTime())) return "";
    const y = dt.getFullYear();
    const m = String(dt.getMonth() + 1).padStart(2, "0");
    const d = String(dt.getDate()).padStart(2, "0");
    return `${y}-${m}-${d}`;
  } catch {
    return "";
  }
}

function Pill({ children, tone = "info" }) {
  const map = {
    info: { border: "rgba(122,92,255,0.18)", bg: "rgba(122,92,255,0.10)", fg: "rgba(92,74,220,1)" },
    warn: { border: "rgba(245,158,11,0.22)", bg: "rgba(245,158,11,0.14)", fg: "rgba(146,64,14,1)" },
    ok: { border: "rgba(16,185,129,0.22)", bg: "rgba(16,185,129,0.12)", fg: "rgba(4,120,87,1)" },
    bad: { border: "rgba(239,68,68,0.22)", bg: "rgba(239,68,68,0.12)", fg: "rgba(127,29,29,1)" },
  };
  const c = map[tone] || map.info;
  return (
    <span
      style={{
        padding: "6px 10px",
        borderRadius: 999,
        border: `1px solid ${c.border}`,
        background: c.bg,
        fontWeight: 900,
        color: c.fg,
        whiteSpace: "nowrap",
      }}
    >
      {children}
    </span>
  );
}

function Modal({ open, title, onClose, children }) {
  if (!open) return null;
  return (
    <div
      role="dialog"
      aria-modal="true"
      onMouseDown={(e) => {
        if (e.target === e.currentTarget) onClose?.();
      }}
      style={{
        position: "fixed",
        inset: 0,
        background: "rgba(2,6,23,0.45)",
        display: "grid",
        placeItems: "center",
        padding: 16,
        zIndex: 9999,
      }}
    >
      <div
        className="card"
        style={{
          width: "min(980px, 100%)",
          maxHeight: "85vh",
          overflow: "auto",
          borderRadius: 18,
          padding: 14,
        }}
      >
        <div style={{ display: "flex", justifyContent: "space-between", gap: 10, alignItems: "center" }}>
          <div style={{ fontWeight: 950, fontSize: 16 }}>{title}</div>
          <button className="btn btn-secundario btn-secundario-mini" type="button" onClick={onClose}>
            Fechar
          </button>
        </div>
        <div style={{ marginTop: 12 }}>{children}</div>
      </div>
    </div>
  );
}

export default function CrasPiaCard({ apiBase, apiFetch, caso, onChanged }) {
  const casoId = Number(caso?.id || 0) || null;

  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [erro, setErro] = useState("");
  const [plano, setPlano] = useState(null);
  const [acoes, setAcoes] = useState([]);
  const [usuarios, setUsuarios] = useState([]);

  // edição do plano
  const [editPlano, setEditPlano] = useState({ resumo_diagnostico: "", objetivos: "", status: "ativo", data_revisao: "" });

  // nova ação
  const [acaoNova, setAcaoNova] = useState({ descricao: "", prazo: "", responsavel_usuario_id: "", status: "pendente" });
  const [msg, setMsg] = useState("");

  const stats = useMemo(() => {
    const total = Array.isArray(acoes) ? acoes.length : 0;
    const concluidas = (acoes || []).filter((a) => String(a.status || "") === "concluida").length;
    const pendentes = total - concluidas;
    return { total, concluidas, pendentes };
  }, [acoes]);

  const statusTone = useMemo(() => {
    if (!plano) return "warn";
    if (String(plano.status || "") === "finalizado") return "ok";
    if (stats.pendentes > 0) return "info";
    return "ok";
  }, [plano, stats.pendentes]);

  async function loadPia() {
    if (!casoId) return;
    setErro("");
    setLoading(true);
    try {
      const r = await apiFetch(`${apiBase}/cras/casos/${casoId}/pia/plano`);
      if (!r.ok) throw new Error(await r.text());
      const j = await r.json();
      setPlano(j?.plano || null);
      setAcoes(Array.isArray(j?.acoes) ? j.acoes : []);

      const p = j?.plano || null;
      setEditPlano({
        resumo_diagnostico: p?.resumo_diagnostico || "",
        objetivos: p?.objetivos || "",
        status: p?.status || "ativo",
        data_revisao: p?.data_revisao ? toDateInput(p.data_revisao) : "",
      });
    } catch (e) {
      console.error(e);
      setErro("Não foi possível carregar o PIA.");
      setPlano(null);
      setAcoes([]);
    } finally {
      setLoading(false);
    }
  }

  async function loadUsuarios() {
    try {
      const municipioId = localStorage.getItem("cras_municipio_ativo") || "";
      const qs = new URLSearchParams();
      if (municipioId) qs.set("municipio_id", municipioId);
      const r = await apiFetch(`${apiBase}/usuarios?${qs.toString()}`);
      if (!r.ok) return setUsuarios([]);
      const j = await r.json();
      setUsuarios(Array.isArray(j) ? j : []);
    } catch {
      setUsuarios([]);
    }
  }

  useEffect(() => {
    // quando troca o caso selecionado
    setPlano(null);
    setAcoes([]);
    setErro("");
    setMsg("");
    if (open) {
      loadPia();
      loadUsuarios();
    }
    // eslint-disable-next-line
  }, [casoId]);

  useEffect(() => {
    if (open) {
      loadPia();
      loadUsuarios();
    }
    // eslint-disable-next-line
  }, [open]);

  async function salvarPlano() {
    if (!casoId) return;
    setMsg("");
    try {
      const payload = {
        resumo_diagnostico: editPlano.resumo_diagnostico,
        objetivos: editPlano.objetivos,
        status: editPlano.status,
        data_revisao: editPlano.data_revisao || null,
      };
      const r = await apiFetch(`${apiBase}/cras/casos/${casoId}/pia/plano`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!r.ok) throw new Error(await r.text());
      setMsg("Plano salvo ✅");
      await loadPia();
      onChanged?.();
    } catch (e) {
      console.error(e);
      setMsg("Erro ao salvar plano.");
    }
  }

  async function criarAcao() {
    if (!casoId) return;
    setMsg("");
    const desc = (acaoNova.descricao || "").trim();
    if (!desc) return setMsg("Descrição da ação é obrigatória.");

    try {
      const payload = {
        descricao: desc,
        prazo: acaoNova.prazo || null,
        status: acaoNova.status || "pendente",
        responsavel_usuario_id: acaoNova.responsavel_usuario_id ? Number(acaoNova.responsavel_usuario_id) : null,
      };
      const r = await apiFetch(`${apiBase}/cras/casos/${casoId}/pia/acoes`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!r.ok) throw new Error(await r.text());
      setAcaoNova({ descricao: "", prazo: "", responsavel_usuario_id: "", status: "pendente" });
      setMsg("Ação criada ✅");
      await loadPia();
      onChanged?.();
    } catch (e) {
      console.error(e);
      setMsg("Erro ao criar ação.");
    }
  }

  async function atualizarAcao(acaoId, payload) {
    setMsg("");
    try {
      const r = await apiFetch(`${apiBase}/cras/pia/acoes/${acaoId}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!r.ok) throw new Error(await r.text());
      setMsg("Ação atualizada ✅");
      await loadPia();
      onChanged?.();
    } catch (e) {
      console.error(e);
      setMsg("Erro ao atualizar ação.");
    }
  }

  async function concluirAcao(acaoId) {
    setMsg("");
    const evidencias = window.prompt("Evidências/resultado (opcional):") || "";
    try {
      const r = await apiFetch(`${apiBase}/cras/pia/acoes/${acaoId}/concluir`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ evidencias_texto: evidencias }),
      });
      if (!r.ok) throw new Error(await r.text());
      setMsg("Ação concluída ✅");
      await loadPia();
      onChanged?.();
    } catch (e) {
      console.error(e);
      setMsg("Erro ao concluir ação.");
    }
  }

  const statusLabel = plano ? (plano.status === "finalizado" ? "Finalizado" : "Ativo") : "Sem plano";
  const prazoLabel = plano?.data_revisao ? fmtDateBR(plano.data_revisao) : "—";
  const resumoLabel = plano?.resumo_diagnostico ? String(plano.resumo_diagnostico).slice(0, 160) : "Sem diagnóstico resumido.";

  return (
    <>
      <div
        style={{
          borderRadius: 22,
          padding: 16,
          background: "rgba(255,255,255,0.70)",
          border: "1px solid rgba(0,0,0,0.06)",
          boxShadow: "0 18px 60px rgba(0,0,0,0.12)",
          backdropFilter: "blur(10px)",
          WebkitBackdropFilter: "blur(10px)",
          marginTop: 12,
        }}
      >
        <div style={{ display: "flex", justifyContent: "space-between", gap: 12, alignItems: "center", flexWrap: "wrap" }}>
          <div style={{ fontWeight: 900 }}>PIA / Plano do caso</div>
          <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
            <Pill tone={statusTone}>{statusLabel}</Pill>
            <button className="btn btn-secundario btn-secundario-mini" type="button" onClick={() => setOpen(true)}>
              Abrir
            </button>
          </div>
        </div>

        <div style={{ marginTop: 10, opacity: 0.85, display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
          <div>
            <div style={{ fontWeight: 800, marginBottom: 6 }}>Próxima revisão:</div>
            <div>{prazoLabel}</div>
          </div>
          <div>
            <div style={{ fontWeight: 800, marginBottom: 6 }}>Ações:</div>
            <div>
              <strong>{stats.pendentes}</strong> pendentes · <strong>{stats.concluidas}</strong> concluídas
            </div>
          </div>
        </div>

        <div style={{ marginTop: 10, opacity: 0.85 }}>
          <div style={{ fontWeight: 800, marginBottom: 6 }}>Resumo:</div>
          <div>{resumoLabel}</div>
        </div>
      </div>

      <Modal
        open={open}
        title={casoId ? `PIA — Caso #${casoId}` : "PIA"}
        onClose={() => setOpen(false)}
      >
        {erro ? (
          <div className="card" style={{ padding: 12, borderRadius: 14 }}>
            <strong>{erro}</strong>
          </div>
        ) : null}
        {loading ? <div className="texto-suave">Carregando…</div> : null}

        {msg ? (
          <div className="card" style={{ padding: 10, borderRadius: 14, marginTop: 10 }}>
            <strong>{msg}</strong>
          </div>
        ) : null}

        <div className="card" style={{ padding: 12, borderRadius: 16, marginTop: 10 }}>
          <div style={{ fontWeight: 950, marginBottom: 10 }}>Plano</div>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
            <div>
              <div className="texto-suave" style={{ fontWeight: 900, marginBottom: 6 }}>Status</div>
              <select className="input" value={editPlano.status} onChange={(e) => setEditPlano((s) => ({ ...s, status: e.target.value }))}>
                <option value="ativo">Ativo</option>
                <option value="finalizado">Finalizado</option>
              </select>
            </div>
            <div>
              <div className="texto-suave" style={{ fontWeight: 900, marginBottom: 6 }}>Próxima revisão</div>
              <input className="input" type="date" value={editPlano.data_revisao} onChange={(e) => setEditPlano((s) => ({ ...s, data_revisao: e.target.value }))} />
            </div>
          </div>

          <div style={{ display: "grid", gap: 10, marginTop: 12 }}>
            <div>
              <div className="texto-suave" style={{ fontWeight: 900, marginBottom: 6 }}>Resumo do diagnóstico</div>
              <textarea className="input" rows={3} value={editPlano.resumo_diagnostico} onChange={(e) => setEditPlano((s) => ({ ...s, resumo_diagnostico: e.target.value }))} />
            </div>
            <div>
              <div className="texto-suave" style={{ fontWeight: 900, marginBottom: 6 }}>Objetivos</div>
              <textarea className="input" rows={3} value={editPlano.objetivos} onChange={(e) => setEditPlano((s) => ({ ...s, objetivos: e.target.value }))} />
            </div>
          </div>

          <div style={{ display: "flex", gap: 10, flexWrap: "wrap", marginTop: 10 }}>
            <button className="btn btn-primario" type="button" onClick={salvarPlano}>Salvar plano</button>
            <button className="btn btn-secundario" type="button" onClick={loadPia}>Recarregar</button>
          </div>
        </div>

        <div className="card" style={{ padding: 12, borderRadius: 16, marginTop: 12 }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 10, flexWrap: "wrap" }}>
            <div style={{ fontWeight: 950 }}>Ações do PIA</div>
            <Pill tone={stats.pendentes ? "warn" : "ok"}>{stats.pendentes} pendentes</Pill>
          </div>

          <div style={{ marginTop: 10, overflow: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse" }}>
              <thead>
                <tr>
                  {["Descrição", "Prazo", "Responsável", "Status", "Ações"].map((h) => (
                    <th key={h} style={{ textAlign: "left", padding: 8, borderBottom: "1px solid rgba(2,6,23,.10)" }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {(acoes || []).map((a) => (
                  <AcaoRow
                    key={a.id}
                    acao={a}
                    usuarios={usuarios}
                    onSave={(payload) => atualizarAcao(a.id, payload)}
                    onConcluir={() => concluirAcao(a.id)}
                  />
                ))}
                {!(acoes || []).length ? (
                  <tr>
                    <td colSpan={5} className="texto-suave" style={{ padding: 10 }}>Sem ações registradas.</td>
                  </tr>
                ) : null}
              </tbody>
            </table>
          </div>

          <div className="card" style={{ padding: 12, borderRadius: 14, marginTop: 12, border: "1px solid rgba(2,6,23,.06)" }}>
            <div style={{ fontWeight: 900, marginBottom: 10 }}>Nova ação</div>
            <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr 1fr 1fr", gap: 10 }}>
              <input className="input" placeholder="Descrição" value={acaoNova.descricao} onChange={(e) => setAcaoNova((s) => ({ ...s, descricao: e.target.value }))} />
              <input className="input" type="date" value={acaoNova.prazo} onChange={(e) => setAcaoNova((s) => ({ ...s, prazo: e.target.value }))} />
              <select className="input" value={acaoNova.responsavel_usuario_id} onChange={(e) => setAcaoNova((s) => ({ ...s, responsavel_usuario_id: e.target.value }))}>
                <option value="">Responsável…</option>
                {(usuarios || []).map((u) => (
                  <option key={u.id} value={u.id}>{u.nome}</option>
                ))}
              </select>
              <select className="input" value={acaoNova.status} onChange={(e) => setAcaoNova((s) => ({ ...s, status: e.target.value }))}>
                <option value="pendente">Pendente</option>
                <option value="em_andamento">Em andamento</option>
                <option value="concluida">Concluída</option>
              </select>
            </div>
            <div style={{ marginTop: 10 }}>
              <button className="btn btn-primario" type="button" onClick={criarAcao}>Adicionar</button>
            </div>
          </div>
        </div>
      </Modal>
    </>
  );
}

function AcaoRow({ acao, usuarios, onSave, onConcluir }) {
  const [edit, setEdit] = useState(false);
  const [draft, setDraft] = useState(() => ({
    descricao: acao.descricao || "",
    prazo: acao.prazo ? toDateInput(acao.prazo) : "",
    responsavel_usuario_id: acao.responsavel_usuario_id || "",
    status: acao.status || "pendente",
    evidencias_texto: acao.evidencias_texto || "",
  }));

  useEffect(() => {
    setDraft({
      descricao: acao.descricao || "",
      prazo: acao.prazo ? toDateInput(acao.prazo) : "",
      responsavel_usuario_id: acao.responsavel_usuario_id || "",
      status: acao.status || "pendente",
      evidencias_texto: acao.evidencias_texto || "",
    });
  }, [acao?.id]);

  const responsavelNome = useMemo(() => {
    const id = Number(acao.responsavel_usuario_id || 0);
    const u = (usuarios || []).find((x) => Number(x.id) === id);
    return u?.nome || (id ? `#${id}` : "—");
  }, [acao.responsavel_usuario_id, usuarios]);

  return (
    <tr>
      <td style={{ padding: 8, borderBottom: "1px solid rgba(2,6,23,.06)", minWidth: 260 }}>
        {!edit ? (
          <>
            <strong>{acao.descricao}</strong>
            {acao.evidencias_texto ? <div className="texto-suave" style={{ marginTop: 4 }}>Evidências: {String(acao.evidencias_texto).slice(0, 120)}</div> : null}
          </>
        ) : (
          <div style={{ display: "grid", gap: 8 }}>
            <input className="input" value={draft.descricao} onChange={(e) => setDraft((s) => ({ ...s, descricao: e.target.value }))} />
            <textarea className="input" rows={2} placeholder="Evidências (opcional)" value={draft.evidencias_texto} onChange={(e) => setDraft((s) => ({ ...s, evidencias_texto: e.target.value }))} />
          </div>
        )}
      </td>

      <td style={{ padding: 8, borderBottom: "1px solid rgba(2,6,23,.06)", whiteSpace: "nowrap" }}>
        {!edit ? (acao.prazo ? fmtDateBR(acao.prazo) : "—") : (
          <input className="input" type="date" value={draft.prazo} onChange={(e) => setDraft((s) => ({ ...s, prazo: e.target.value }))} />
        )}
      </td>

      <td style={{ padding: 8, borderBottom: "1px solid rgba(2,6,23,.06)", whiteSpace: "nowrap" }}>
        {!edit ? responsavelNome : (
          <select className="input" value={draft.responsavel_usuario_id} onChange={(e) => setDraft((s) => ({ ...s, responsavel_usuario_id: e.target.value }))}>
            <option value="">—</option>
            {(usuarios || []).map((u) => (
              <option key={u.id} value={u.id}>{u.nome}</option>
            ))}
          </select>
        )}
      </td>

      <td style={{ padding: 8, borderBottom: "1px solid rgba(2,6,23,.06)", whiteSpace: "nowrap" }}>
        {!edit ? (
          <span style={{ fontWeight: 900 }}>{String(acao.status || "").toUpperCase()}</span>
        ) : (
          <select className="input" value={draft.status} onChange={(e) => setDraft((s) => ({ ...s, status: e.target.value }))}>
            <option value="pendente">Pendente</option>
            <option value="em_andamento">Em andamento</option>
            <option value="concluida">Concluída</option>
          </select>
        )}
      </td>

      <td style={{ padding: 8, borderBottom: "1px solid rgba(2,6,23,.06)" }}>
        {!edit ? (
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            <button className="btn btn-secundario btn-secundario-mini" type="button" onClick={() => setEdit(true)}>
              Editar
            </button>
            {String(acao.status || "") !== "concluida" ? (
              <button className="btn btn-primario btn-primario-mini" type="button" onClick={onConcluir}>
                Concluir
              </button>
            ) : null}
          </div>
        ) : (
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            <button
              className="btn btn-primario btn-primario-mini"
              type="button"
              onClick={() => {
                onSave?.({
                  descricao: draft.descricao,
                  prazo: draft.prazo || null,
                  status: draft.status,
                  responsavel_usuario_id: draft.responsavel_usuario_id ? Number(draft.responsavel_usuario_id) : null,
                  evidencias_texto: draft.evidencias_texto,
                });
                setEdit(false);
              }}
            >
              Salvar
            </button>
            <button className="btn btn-secundario btn-secundario-mini" type="button" onClick={() => setEdit(false)}>
              Cancelar
            </button>
          </div>
        )}
      </td>
    </tr>
  );
}
