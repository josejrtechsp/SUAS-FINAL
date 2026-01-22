import { useEffect, useMemo, useState } from "react";

function statusLabel(st) {
  if (st === "pendente") return "Pendente";
  if (st === "agendado") return "Agendado";
  if (st === "finalizado") return "Finalizado";
  if (st === "nao_compareceu") return "Não compareceu";
  return st || "—";
}

function fmtDT(iso) {
  if (!iso) return "—";
  const d = new Date(iso);
  if (isNaN(d.getTime())) return iso;
  return d.toLocaleString("pt-BR");
}

function badge(st) {
  const base = {
    padding: "6px 12px",
    borderRadius: 999,
    fontWeight: 900,
    fontSize: 12,
    border: "1px solid rgba(2,6,23,.10)",
    background: "rgba(148,163,184,.10)",
    color: "rgba(2,6,23,.85)",
    whiteSpace: "nowrap",
  };
  if (st === "finalizado") return { ...base, background: "rgba(34,197,94,.12)", border: "1px solid rgba(34,197,94,.25)" };
  if (st === "agendado") return { ...base, background: "rgba(99,102,241,.12)", border: "1px solid rgba(99,102,241,.25)" };
  if (st === "nao_compareceu") return { ...base, background: "rgba(239,68,68,.12)", border: "1px solid rgba(239,68,68,.25)" };
  if (st === "pendente") return { ...base, background: "rgba(245,158,11,.12)", border: "1px solid rgba(245,158,11,.25)" };
  return base;
}

function sortCadunico(view, items) {
  const arr = Array.isArray(items) ? [...items] : [];

  if (view === "agendamentos") {
    // Ordena por data agendada (mais próxima primeiro)
    arr.sort((a, b) => {
      const ta = a?.data_agendada ? new Date(a.data_agendada).getTime() : Number.POSITIVE_INFINITY;
      const tb = b?.data_agendada ? new Date(b.data_agendada).getTime() : Number.POSITIVE_INFINITY;
      if (ta !== tb) return ta - tb;
      return Number(b?.id || 0) - Number(a?.id || 0);
    });
    return arr;
  }

  // Default: mais recentes primeiro
  arr.sort((a, b) => Number(b?.id || 0) - Number(a?.id || 0));
  return arr;
}

/**
 * TelaCrasCadUnico
 * Padrão produto: 1 subtela por vez (controlada pelo header).
 * Subtelas: precadastro | agendamentos | pendencias | historico
 */
export default function TelaCrasCadUnico({ apiBase, apiFetch, view = "precadastro", unidadeAtivaId, onSetView }) {
  const unidadeAtiva = useMemo(() => {
    if (unidadeAtivaId != null) return String(unidadeAtivaId || "");
    return localStorage.getItem("cras_unidade_ativa") || "";
  }, [unidadeAtivaId]);

  const activeView = String(view || "precadastro");

  const [msg, setMsg] = useState("");
  const [erro, setErro] = useState("");
  const [loading, setLoading] = useState(false);

  const [lista, setLista] = useState([]);

  // dados para criação (somente em Pré-cadastro)
  const [casos, setCasos] = useState([]);
  const [pessoas, setPessoas] = useState([]);
  const [familias, setFamilias] = useState([]);

  const [casoId, setCasoId] = useState("");
  const [pessoaId, setPessoaId] = useState("");
  const [familiaId, setFamiliaId] = useState("");
  const [obs, setObs] = useState("");

  // agendamento
  const [agendarId, setAgendarId] = useState(null);
  const [agendarDT, setAgendarDT] = useState("");

  const showCreate = activeView === "precadastro";
  const canEdit = activeView !== "historico";

  const pageTitle = useMemo(() => {
    if (activeView === "precadastro") return "CadÚnico — Pré-cadastro";
    if (activeView === "agendamentos") return "CadÚnico — Agendamentos";
    if (activeView === "pendencias") return "CadÚnico — Pendências";
    if (activeView === "historico") return "CadÚnico — Histórico";
    return "CadÚnico";
  }, [activeView]);

  const resumo = useMemo(() => {
    const r = { pendente: 0, agendado: 0, finalizado: 0, nao_compareceu: 0, total: 0 };
    (lista || []).forEach((x) => {
      r.total += 1;
      if (x.status in r) r[x.status] += 1;
    });
    return r;
  }, [lista]);

  async function loadCadastrosBase() {
    try {
      const [rc, rp, rf] = await Promise.all([
        apiFetch(`${apiBase}/cras/casos${unidadeAtiva ? `?unidade_id=${unidadeAtiva}` : ""}`),
        apiFetch(`${apiBase}/cras/cadastros/pessoas`),
        apiFetch(`${apiBase}/cras/cadastros/familias`),
      ]);
      if (rc.ok) setCasos(await rc.json());
      if (rp.ok) setPessoas(await rp.json());
      if (rf.ok) setFamilias(await rf.json());
    } catch {
      // silencioso
    }
  }

  async function fetchByStatus(st) {
    const qs = new URLSearchParams();
    if (unidadeAtiva) qs.set("unidade_id", unidadeAtiva);
    if (st) qs.set("status", st);
    const r = await apiFetch(`${apiBase}/cras/cadunico/precadastros?${qs.toString()}`);
    if (!r.ok) throw new Error(await r.text());
    const j = await r.json();
    return Array.isArray(j) ? j : [];
  }

  async function loadLista() {
    setErro("");
    setLoading(true);
    try {
      let items = [];

      if (activeView === "pendencias") {
        const [pend, nc] = await Promise.all([fetchByStatus("pendente"), fetchByStatus("nao_compareceu")]);
        items = [...pend, ...nc];
      } else if (activeView === "agendamentos") {
        items = await fetchByStatus("agendado");
      } else if (activeView === "historico") {
        items = await fetchByStatus("finalizado");
      } else {
        // precadastro
        items = await fetchByStatus("pendente");
      }

      setLista(sortCadunico(activeView, items));
    } catch (e) {
      console.error(e);
      setErro("Não foi possível carregar CadÚnico (pré-cadastros).\nVerifique unidade ativa e conexão.");
      setLista([]);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    // Apenas carrega base quando estiver em Pré-cadastro
    if (showCreate) loadCadastrosBase();
    // eslint-disable-next-line
  }, [showCreate, unidadeAtiva]);

  useEffect(() => {
    // Ao trocar subtela/unidade, recarrega lista
    loadLista();
    // fecha qualquer editor de agendamento
    setAgendarId(null);
    setAgendarDT("");
    // eslint-disable-next-line
  }, [activeView, unidadeAtiva]);

  async function criarPre() {
    setMsg("");
    if (!unidadeAtiva) return setMsg("Selecione a Unidade CRAS no cabeçalho.");
    if (!casoId && !pessoaId && !familiaId) return setMsg("Informe Caso ou Pessoa ou Família.");

    try {
      const r = await apiFetch(`${apiBase}/cras/cadunico/precadastros`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          unidade_id: Number(unidadeAtiva),
          caso_id: casoId ? Number(casoId) : null,
          pessoa_id: pessoaId ? Number(pessoaId) : null,
          familia_id: familiaId ? Number(familiaId) : null,
          observacoes: obs || null,
        }),
      });
      if (!r.ok) throw new Error(await r.text());
      setMsg("Pré-cadastro criado ✅");
      setCasoId("");
      setPessoaId("");
      setFamiliaId("");
      setObs("");

      // Mantém o usuário em Pré-cadastro e atualiza a lista
      if (typeof onSetView === "function") onSetView("precadastro");
      await loadLista();
    } catch (e) {
      console.error(e);
      setMsg("Erro ao criar pré-cadastro.");
    }
  }

  async function agendar(pcId) {
    setMsg("");
    if (!agendarDT) return setMsg("Selecione data/hora para agendar.");
    try {
      const r = await apiFetch(`${apiBase}/cras/cadunico/precadastros/${pcId}/agendar`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ data_agendada: agendarDT }),
      });
      if (!r.ok) throw new Error(await r.text());
      setMsg("Agendado ✅");
      setAgendarId(null);
      setAgendarDT("");
      await loadLista();
    } catch (e) {
      console.error(e);
      setMsg("Erro ao agendar.");
    }
  }

  async function finalizar(pcId) {
    setMsg("");
    try {
      const r = await apiFetch(`${apiBase}/cras/cadunico/precadastros/${pcId}/finalizar`, { method: "POST" });
      if (!r.ok) throw new Error(await r.text());
      setMsg("Finalizado ✅");
      await loadLista();
    } catch (e) {
      console.error(e);
      setMsg("Erro ao finalizar.");
    }
  }

  async function naoCompareceu(pcId) {
    setMsg("");
    try {
      const r = await apiFetch(`${apiBase}/cras/cadunico/precadastros/${pcId}/nao-compareceu`, { method: "POST" });
      if (!r.ok) throw new Error(await r.text());
      setMsg("Marcado como não compareceu ✅");
      await loadLista();
    } catch (e) {
      console.error(e);
      setMsg("Erro ao marcar não compareceu.");
    }
  }

  const listCard = (
    <div className="card" style={{ padding: 12, borderRadius: 18 }}>
      <div style={{ display: "flex", justifyContent: "space-between", gap: 10, flexWrap: "wrap", alignItems: "center" }}>
        <div style={{ fontWeight: 900 }}>{pageTitle}</div>
        <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
          <div className="texto-suave">Unidade ativa: <strong>{unidadeAtiva || "—"}</strong></div>
          <button className="btn btn-secundario" type="button" onClick={loadLista}>Atualizar</button>
        </div>
      </div>

      {loading ? <div className="texto-suave" style={{ marginTop: 10 }}>Carregando…</div> : null}

      <div className="texto-suave" style={{ marginTop: 8 }}>
        Total: <strong>{resumo.total}</strong>
        {activeView === "pendencias" ? (
          <> · Pendente: <strong>{resumo.pendente}</strong> · Não compareceu: <strong>{resumo.nao_compareceu}</strong></>
        ) : activeView === "agendamentos" ? (
          <> · Agendados: <strong>{resumo.agendado}</strong></>
        ) : activeView === "historico" ? (
          <> · Finalizados: <strong>{resumo.finalizado}</strong></>
        ) : (
          <> · Pendentes: <strong>{resumo.pendente}</strong></>
        )}
      </div>

      <div style={{ display: "grid", gap: 10, marginTop: 12 }}>
        {(lista || []).map((pc) => {
          const agLabel = pc.status === "agendado" ? "Reagendar" : "Agendar";
          return (
            <div key={pc.id} className="card" style={{ padding: 12, borderRadius: 16 }}>
              <div style={{ display: "flex", justifyContent: "space-between", gap: 12, flexWrap: "wrap" }}>
                <div>
                  <div style={{ fontWeight: 900 }}>#{pc.id} · {statusLabel(pc.status)}</div>
                  <div className="texto-suave" style={{ marginTop: 4 }}>
                    Caso: <strong>{pc.caso_id ?? "—"}</strong> · Pessoa: <strong>{pc.pessoa_id ?? "—"}</strong> · Família: <strong>{pc.familia_id ?? "—"}</strong>
                  </div>
                  <div className="texto-suave" style={{ marginTop: 4 }}>
                    Agendado: <strong>{fmtDT(pc.data_agendada)}</strong>
                  </div>
                  {pc.observacoes ? <div className="texto-suave" style={{ marginTop: 6 }}>Obs: {pc.observacoes}</div> : null}
                </div>

                <span style={badge(pc.status)}>{statusLabel(pc.status)}</span>
              </div>

              {canEdit ? (
                <div style={{ display: "flex", gap: 10, flexWrap: "wrap", marginTop: 10 }}>
                  <button
                    className="btn btn-secundario"
                    type="button"
                    onClick={() => { setAgendarId(pc.id); setAgendarDT(""); }}
                  >
                    {agLabel}
                  </button>
                  <button className="btn btn-secundario" type="button" onClick={() => finalizar(pc.id)}>Finalizar</button>
                  <button className="btn btn-secundario" type="button" onClick={() => naoCompareceu(pc.id)}>Não compareceu</button>
                </div>
              ) : null}

              {canEdit && agendarId === pc.id ? (
                <div className="card" style={{ padding: 10, borderRadius: 14, marginTop: 10, border: "1px solid rgba(2,6,23,.06)" }}>
                  <div style={{ fontWeight: 900, marginBottom: 8 }}>Agendar atendimento</div>
                  <div style={{ display: "grid", gridTemplateColumns: "1fr auto auto", gap: 10 }}>
                    <input
                      type="datetime-local"
                      className="input"
                      value={agendarDT}
                      onChange={(e) => setAgendarDT(e.target.value)}
                    />
                    <button className="btn btn-primario" type="button" onClick={() => agendar(pc.id)}>Salvar</button>
                    <button className="btn btn-secundario" type="button" onClick={() => { setAgendarId(null); setAgendarDT(""); }}>Cancelar</button>
                  </div>
                </div>
              ) : null}
            </div>
          );
        })}

        {!loading && (!lista || lista.length === 0) ? <div className="texto-suave">Nenhum registro.</div> : null}
      </div>
    </div>
  );

  return (
    <div className="layout-1col">
      {erro ? (
        <div className="card" style={{ padding: 12, borderRadius: 14 }}>
          <strong>{erro}</strong>
        </div>
      ) : null}
      {msg ? (
        <div className="card" style={{ padding: 12, borderRadius: 14 }}>
          <strong>{msg}</strong>
        </div>
      ) : null}

      {showCreate ? (
        <div style={{ display: "grid", gridTemplateColumns: "1fr 2fr", gap: 12 }}>
          <div className="card" style={{ padding: 12, borderRadius: 18 }}>
            <div style={{ fontWeight: 900, marginBottom: 10 }}>Criar pré-cadastro</div>
            <div className="texto-suave">Unidade ativa: <strong>{unidadeAtiva ? `CRAS ${unidadeAtiva}` : "—"}</strong></div>

            <div style={{ display: "grid", gap: 10, marginTop: 10 }}>
              <select className="input" value={casoId} onChange={(e) => setCasoId(e.target.value)}>
                <option value="">Vincular a um Caso (opcional)…</option>
                {(casos || []).map((c) => (
                  <option key={c.id} value={c.id}>Caso #{c.id} · {c.display?.nome || c.tipo_caso}</option>
                ))}
              </select>

              <select className="input" value={pessoaId} onChange={(e) => setPessoaId(e.target.value)}>
                <option value="">Vincular a uma Pessoa (opcional)…</option>
                {(pessoas || []).map((p) => (
                  <option key={p.id} value={p.id}>{p.nome_social ? `${p.nome_social} (${p.nome})` : p.nome}</option>
                ))}
              </select>

              <select className="input" value={familiaId} onChange={(e) => setFamiliaId(e.target.value)}>
                <option value="">Vincular a uma Família (opcional)…</option>
                {(familias || []).map((f) => (
                  <option key={f.id} value={f.id}>Família #{f.id} · NIS: {f.nis_familia || "—"}</option>
                ))}
              </select>

              <textarea className="input" rows={2} placeholder="Observações (opcional)" value={obs} onChange={(e) => setObs(e.target.value)} />

              <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
                <button className="btn btn-primario" type="button" onClick={criarPre}>Criar pré-cadastro</button>
                <button className="btn btn-secundario" type="button" onClick={loadLista}>Atualizar lista</button>
              </div>

              <div className="card" style={{ padding: 10, borderRadius: 14, border: "1px solid rgba(2,6,23,.06)" }}>
                <div style={{ fontWeight: 900 }}>Resumo desta lista</div>
                <div className="texto-suave" style={{ marginTop: 6 }}>
                  Total: <strong>{resumo.total}</strong> · Pendentes: <strong>{resumo.pendente}</strong>
                </div>
              </div>
            </div>
          </div>

          {listCard}
        </div>
      ) : (
        listCard
      )}
    </div>
  );
}

// CRAS_CADUNICO_SUBTABS_HELP_V1
