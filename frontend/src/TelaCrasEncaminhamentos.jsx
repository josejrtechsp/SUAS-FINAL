import { useEffect, useMemo, useState } from "react";
import EncaminhamentosSuas from "./components/EncaminhamentosSuas.jsx";
import { rmaCollect } from "./domain/rmaCollector.js";


const STATUS_ORDER = ["enviado","recebido","agendado","atendido","devolutiva","concluido"];
const STATUS_LABEL = {
  enviado: "ENVIADO",
  recebido: "RECEBIDO",
  agendado: "AGENDADO",
  atendido: "ATENDIDO",
  devolutiva: "DEVOLUTIVA",
  concluido: "CONCLUÍDO",
  cancelado: "CANCELADO",
};

function StatusPill({ status }) {
  const s = (status || "enviado").toLowerCase();
  const label = STATUS_LABEL[s] || String(s).toUpperCase();
  return <span className={`cras-pill cras-pill--${s}`}>{label}</span>;
}

function FlowMini({ status }) {
  const s = (status || "enviado").toLowerCase();
  const idx = STATUS_ORDER.indexOf(s);

  const steps = [
    { key: "enviado", label: "Enviado" },
    { key: "recebido", label: "Recebido" },
    { key: "agendado", label: "Agendado" },
    { key: "atendido", label: "Atendido" },
    { key: "devolutiva", label: "Devolutiva" },
    { key: "concluido", label: "Concluído" },
  ];

  // cancelado: marca tudo como "parado"
  if (s === "cancelado") {
    return (
      <div className="cras-flow-mini">
        {steps.map((st, i) => (
          <div key={st.key} className="cras-flow-step" title={st.label}>
            <div className="cras-flow-dot is-cancel" />
            {i < steps.length - 1 ? <div className="cras-flow-line is-cancel" /> : null}
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="cras-flow-mini">
      {steps.map((st, i) => {
        const stepIdx = STATUS_ORDER.indexOf(st.key);
        const done = idx >= 0 && stepIdx >= 0 && idx > stepIdx;
        const current = idx >= 0 && stepIdx === idx;
        return (
          <div key={st.key} className="cras-flow-step" title={st.label}>
            <div className={"cras-flow-dot" + (done ? " is-done" : "") + (current ? " is-current" : "")} />
            {i < steps.length - 1 ? (
              <div className={"cras-flow-line" + (idx > stepIdx ? " is-done" : "")} />
            ) : null}
          </div>
        );
      })}
    </div>
  );
}

export default function TelaCrasEncaminhamentos({ apiBase, apiFetch, usuarioLogado, focus, onNavigate }) {
  const [unidades, setUnidades] = useState([]);
  const [unidadeId, setUnidadeId] = useState(localStorage.getItem("cras_unidade_ativa") || "");
  const [pessoas, setPessoas] = useState([]);

  const [destinosMeta, setDestinosMeta] = useState([]);
  const [destinoFiltro, setDestinoFiltro] = useState("");

  const [lista, setLista] = useState([]);
  const [semDevolutiva, setSemDevolutiva] = useState([]);

  // Deep-link (Gestão → abrir encaminhamento): destaca e rola até o ID
  const [focusEncId, setFocusEncId] = useState(() => localStorage.getItem("cras_open_enc_id") || "");

  const [msg, setMsg] = useState("");
  const municipioAtivo = localStorage.getItem("cras_municipio_ativo") || "";

  const [form, setForm] = useState({
    pessoa_id: "",
    destino_tipo: "saude",
    destino_nome: "",
    motivo: "",
    observacao_operacional: "",
    prazo_devolutiva_dias: 7,
  });

  const mapaUn = useMemo(() => {
    const m = new Map();
    unidades.forEach((u) => m.set(u.id, u.nome));
    return m;
  }, [unidades]);

  async function loadBasics() {
    const qU = new URLSearchParams();
    if (municipioAtivo) qU.set("municipio_id", municipioAtivo);
    const u = await apiFetch(`${apiBase}/cras/unidades?${qU.toString()}`);
    if (u.ok) {
      const data = await u.json();
      setUnidades(data);
      if (!unidadeId && data.length) setUnidadeId(String(data[0].id));
    }

    const p = await apiFetch(`${apiBase}/pessoas/`);
    if (p.ok) setPessoas(await p.json());

    const d = await apiFetch(`${apiBase}/cras/encaminhamentos/destinos`);
    if (d.ok) {
      const j = await d.json();
      setDestinosMeta(j.destinos || []);
    }
  }

  async function loadList() {
    if (!unidadeId) return;

    const q = new URLSearchParams();
    if (municipioAtivo) q.set("municipio_id", municipioAtivo);
    q.set("unidade_id", unidadeId);
    if (destinoFiltro) q.set("destino_tipo", destinoFiltro);

    const r = await apiFetch(`${apiBase}/cras/encaminhamentos?${q.toString()}`);
    if (r.ok) setLista(await r.json());

    const s = await apiFetch(`${apiBase}/cras/encaminhamentos/sem-devolutiva?${q.toString()}`);
    if (s.ok) setSemDevolutiva(await s.json());
  }

  useEffect(() => { loadBasics(); /* eslint-disable-next-line */ }, []);
  useEffect(() => { loadList(); /* eslint-disable-next-line */ }, [unidadeId, destinoFiltro]);

  useEffect(() => {
    if (!focusEncId) return;
    setTimeout(() => {
      const el = document.getElementById(`cras_enc_${focusEncId}`);
      if (el && typeof el.scrollIntoView === "function") {
        el.scrollIntoView({ behavior: "smooth", block: "center" });
      }
    }, 260);
    try { localStorage.removeItem("cras_open_enc_id"); } catch {}
    const t = setTimeout(() => setFocusEncId(""), 5000);
    return () => clearTimeout(t);
  }, [focusEncId, lista, semDevolutiva]);

  useEffect(() => {
    if (focus === "sem") {
      setTimeout(() => {
        const el = document.getElementById("sem-devolutiva-panel");
        if (el) el.scrollIntoView({ behavior: "smooth", block: "start" });
      }, 80);
    }
  }, [focus]);

  async function criar() {
    setMsg("");
    if (!unidadeId) return setMsg("Selecione uma unidade.");
    if (!form.destino_nome.trim()) return setMsg("Informe o destino (nome).");
    if (!form.motivo.trim()) return setMsg("Informe o motivo.");

    const payload = {
      municipio_id: municipioAtivo ? Number(municipioAtivo) : undefined,
      unidade_id: Number(unidadeId),
      pessoa_id: form.pessoa_id ? Number(form.pessoa_id) : null,
      destino_tipo: form.destino_tipo,
      destino_nome: form.destino_nome.trim(),
      motivo: form.motivo.trim(),
      observacao_operacional: form.observacao_operacional?.trim() || null,
      prazo_devolutiva_dias: Number(form.prazo_devolutiva_dias || 7),
    };

    const r = await apiFetch(`${apiBase}/cras/encaminhamentos`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!r.ok) return setMsg("Erro ao criar encaminhamento.");

    setForm({ ...form, destino_nome: "", motivo: "", observacao_operacional: "" });
    setMsg("Encaminhamento criado ✅");
    // RMA_COLLECT_V1 ENC_CRIAR
    try {
      await rmaCollect({
        apiBase,
        apiFetch,
        servico: "ENCAMINHAMENTO",
        acao: "criar",
        unidade_id: (typeof unidadeId !== "undefined" && unidadeId) ? Number(unidadeId) : null,
        pessoa_id: payload?.pessoa_id ?? null,
        alvo_tipo: "encaminhamento",
        meta: { destino_tipo: payload?.destino_tipo, destino_nome: payload?.destino_nome, prazo_dias: payload?.prazo_devolutiva_dias },
      });
    } catch {}
    await loadList();
  }

  async function avancar(enc) {
    const idx = STATUS_ORDER.indexOf(enc.status);
    const next = idx >= 0 && idx < STATUS_ORDER.length - 1 ? STATUS_ORDER[idx + 1] : null;
    if (!next) return;

    const r = await apiFetch(`${apiBase}/cras/encaminhamentos/${enc.id}/status`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status: next, detalhe: "" }),
    });
    if (!r.ok) return setMsg("Não foi possível avançar (ordem do fluxo).");
    await loadList();
  }

  async function registrarDevolutiva(enc) {
    const detalhe = prompt("Digite a devolutiva (resumo):") || "";
    if (!detalhe.trim()) return;

    const r = await apiFetch(`${apiBase}/cras/encaminhamentos/${enc.id}/status`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status: "devolutiva", detalhe }),
    });
    if (!r.ok) return setMsg("Erro ao registrar devolutiva.");
    await loadList();
    // RMA_COLLECT_V1 ENC_DEVOLUTIVA
    try {
      await rmaCollect({
        apiBase,
        apiFetch,
        servico: "ENCAMINHAMENTO",
        acao: "devolutiva",
        unidade_id: (typeof unidadeId !== "undefined" && unidadeId) ? Number(unidadeId) : null,
        alvo_tipo: "encaminhamento",
        alvo_id: enc?.id ?? null,
        meta: { detalhe },
      });
    } catch {}
  }

  async function cobrar(enc) {
    const detalhe = prompt("Texto curto da cobrança:") || "";
    if (!detalhe.trim()) return;

    const q = new URLSearchParams();
    if (municipioAtivo) q.set("municipio_id", municipioAtivo);

    const r = await apiFetch(`${apiBase}/cras/encaminhamentos/${enc.id}/cobrar?${q.toString()}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ detalhe }),
    });
    if (!r.ok) return setMsg("Erro ao registrar cobrança.");
    setMsg("Cobrança registrada ✅");
    // RMA_COLLECT_V1 ENC_COBRAR
    try {
      await rmaCollect({
        apiBase,
        apiFetch,
        servico: "ENCAMINHAMENTO",
        acao: "cobrar",
        unidade_id: (typeof unidadeId !== "undefined" && unidadeId) ? Number(unidadeId) : null,
        alvo_tipo: "encaminhamento",
        alvo_id: enc?.id ?? null,
        meta: { detalhe },
      });
    } catch {}
    await loadList();
  }

  async function cancelar(enc) {
    const q = new URLSearchParams();
    if (municipioAtivo) q.set("municipio_id", municipioAtivo);

    const r = await apiFetch(`${apiBase}/cras/encaminhamentos/${enc.id}/status?${q.toString()}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status: "cancelado", detalhe: "Cancelado" }),
    });
    if (!r.ok) return setMsg("Erro ao cancelar.");
    await loadList();
  }



  const pessoasOptionsSuas = useMemo(() => {
    return (pessoas || [])
      .map((p) => ({
        id: Number(p?.id),
        nome: p?.nome_social || p?.nome_civil || p?.nome || `Pessoa #${p?.id}`,
      }))
      .filter((x) => x.id && !Number.isNaN(x.id));
  }, [pessoas]);

  // Encaminhamentos SUAS (internos): ao RECEBER, podemos criar um caso CRAS automaticamente.
  async function createCrasCaseFromSuasEncaminhamento(item) {
    try {
      const pid = Number(item?.pessoa_id);
      if (!pid || Number.isNaN(pid)) return null;

      const unidadeAtiva = unidadeId || localStorage.getItem('cras_unidade_ativa') || '';
      const unid = Number(unidadeAtiva);
      if (!unid || Number.isNaN(unid)) {
        alert('Selecione a Unidade CRAS ativa no topo antes de receber.');
        return null;
      }

      const obs = `(Encaminhamento SUAS) Origem: ${String(item?.origem_modulo || '-')}` +
        ` · Motivo: ${String(item?.motivo || '-')}`;

      const body = {
        unidade_id: unid,
        tipo_caso: 'individuo',
        pessoa_id: pid,
        familia_id: null,
        observacoes_iniciais: obs,
        prioridade: 'media',
      };

      const r = await apiFetch(`${apiBase}/cras/casos`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });

      if (!r.ok) {
        const txt = await r.text().catch(() => '');
        throw new Error(txt || `Erro ao criar caso CRAS (${r.status})`);
      }

      const data = await r.json().catch(() => ({}));
      const novoId = Number(data?.id ?? data?.caso_id ?? data?.casoId);
      if (!novoId || Number.isNaN(novoId)) return null;
      return novoId;
    } catch (e) {
      console.error(e);
      alert(e?.message || 'Não foi possível criar o caso CRAS automaticamente.');
      return null;
    }
  }

  function abrirCasoCras(item) {
    if (!item?.destino_caso_id) return;
    try {
      localStorage.setItem('cras_selected_case', String(item.destino_caso_id));
      // backup: se o app estiver em outra aba, isso ajuda na reabertura.
      localStorage.setItem('cras_active_tab', 'casos');
    } catch {}
    onNavigate?.({ tab: 'casos' });
  }


  const unidadeNome = unidadeId ? (mapaUn.get(Number(unidadeId)) || `Unidade ${unidadeId}`) : "—";

  return (
    <div className="layout-1col">

      {msg ? <div className="card" style={{ padding: 12, borderRadius: 14 }}><strong>{msg}</strong></div> : null}

      <EncaminhamentosSuas
        apiBase={apiBase}
        apiFetch={apiFetch}
        modulo="CRAS"
        usuarioLogado={usuarioLogado}
        allowCreate={true}
        pessoasOptions={pessoasOptionsSuas}
        onAcceptCreateCaso={(item) => createCrasCaseFromSuasEncaminhamento(item)}
        onOpenDestinoCaso={(item) => abrirCasoCras(item)}
        title="Encaminhamentos SUAS"
        subtitle="CRAS ⇄ CREAS ⇄ PopRua, com recebimento e contrarreferência."
      />

      <div className="card" style={{ padding: 12, borderRadius: 18 }}>
        <div style={{ display: "flex", gap: 10, flexWrap: "wrap", alignItems: "end" }}>
          <div style={{ flex: "1 1 260px" }}>
            <label className="label">Unidade CRAS</label>
            <select className="input" value={unidadeId} onChange={(e) => setUnidadeId(e.target.value)}>
              <option value="">Selecione…</option>
              {unidades.map((u) => <option key={u.id} value={u.id}>{u.nome}</option>)}
            </select>
          </div>

          <div style={{ flex: "1 1 220px" }}>
            <label className="label">Destino</label>
            <select className="input" value={destinoFiltro} onChange={(e) => setDestinoFiltro(e.target.value)}>
              <option value="">Todos</option>
              {destinosMeta.map((d) => <option key={d.codigo} value={d.codigo}>{d.nome}</option>)}
            </select>
          </div>

          <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
            <button className="btn btn-secundario" type="button" onClick={loadList}>Atualizar</button>

            <div className="card" style={{ padding: "10px 12px", borderRadius: 14, border: "1px solid rgba(245,158,11,.28)", background: "rgba(255,247,237,.72)" }}>
              <div className="texto-suave" style={{ fontWeight: 900 }}>Sem devolutiva</div>
              <div style={{ fontSize: 18, fontWeight: 950 }}>{semDevolutiva.length}</div>
            </div>
          </div>
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
        <div className="card" style={{ padding: 12, borderRadius: 18 }}>
          <h3 style={{ margin: 0 }}>Novo encaminhamento</h3>
          <p className="texto-suave" style={{ marginTop: 6 }}>
            Defina um prazo por item para cobrança automática (“sem devolutiva”).
          </p>

          <div style={{ display: "grid", gap: 8 }}>
            <div>
              <label className="label">Pessoa (opcional)</label>
              <select className="input" value={form.pessoa_id} onChange={(e) => setForm({ ...form, pessoa_id: e.target.value })}>
                <option value="">Selecione…</option>
                {pessoas.map((p) => (
                  <option key={p.id} value={p.id}>#{p.id} — {p.nome_social || p.nome_civil || "Pessoa"}</option>
                ))}
              </select>
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
              <div>
                <label className="label">Destino (tipo)</label>
                <select className="input" value={form.destino_tipo} onChange={(e) => setForm({ ...form, destino_tipo: e.target.value })}>
                  {destinosMeta.map((d) => <option key={d.codigo} value={d.codigo}>{d.nome}</option>)}
                </select>
              </div>

              <div>
                <label className="label">Prazo devolutiva (dias)</label>
                <input className="input" value={form.prazo_devolutiva_dias} onChange={(e) => setForm({ ...form, prazo_devolutiva_dias: e.target.value })} />
              </div>
            </div>

            <div>
              <label className="label">Destino (nome)</label>
              <input className="input" value={form.destino_nome} onChange={(e) => setForm({ ...form, destino_nome: e.target.value })} placeholder="Ex.: UBS Centro, Escola X, CREAS..." />
            </div>

            <div>
              <label className="label">Motivo</label>
              <input className="input" value={form.motivo} onChange={(e) => setForm({ ...form, motivo: e.target.value })} placeholder="Ex.: avaliação, atualização, acompanhamento..." />
            </div>

            <div>
              <label className="label">Observação (operacional)</label>
              <textarea className="input" rows={4} value={form.observacao_operacional} onChange={(e) => setForm({ ...form, observacao_operacional: e.target.value })} />
            </div>

            <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
              <button className="btn btn-primario" type="button" onClick={criar}>Criar encaminhamento</button>
              <button className="btn btn-secundario" type="button" onClick={() => setForm({ ...form, destino_nome: "", motivo: "", observacao_operacional: "" })}>
                Limpar
              </button>
            </div>
          </div>
        </div>

        <div id="sem-devolutiva-panel" className="card" style={{ padding: 12, borderRadius: 18 }}>
          <h3 style={{ margin: 0 }}>Sem devolutiva (atrasados)</h3>
          <p className="texto-suave" style={{ marginTop: 6 }}>Atraso calculado pelo prazo do próprio encaminhamento.</p>

          <div style={{ display: "grid", gap: 8, marginTop: 8 }}>
            {semDevolutiva.length ? semDevolutiva.map((e) => (
              <div
                id={`cras_enc_${e.id}`}
                key={e.id}
                className="card"
                style={{
                  padding: 10,
                  borderRadius: 14,
                  border: String(e.id) === String(focusEncId) ? "2px solid rgba(59,130,246,.40)" : "1px solid rgba(229,231,235,0.9)",
                  background: String(e.id) === String(focusEncId) ? "rgba(239,246,255,.70)" : undefined,
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", gap: 10, flexWrap: "wrap", alignItems: "center" }}>
                  <div><b>#{e.id}</b> · {e.destino_nome}</div>
                  <StatusPill status={e.status} />
                </div>

                <div style={{ marginTop: 6 }}>
                  <FlowMini status={e.status} />
                </div>

                <div className="texto-suave" style={{ marginTop: 6 }}>
                  Tipo: {e.destino_tipo} · Pessoa: {e.pessoa_id ? `#${e.pessoa_id}` : "—"} · aberto: <b>{e.dias_aberto}</b>d · prazo: <b>{e.prazo_usado}</b>d
                </div>

                <div style={{ display: "flex", gap: 8, marginTop: 8, flexWrap: "wrap" }}>
                  <button className="btn btn-primario" type="button" onClick={() => registrarDevolutiva(e)}>Registrar devolutiva</button>
                  <button className="btn btn-secundario" type="button" onClick={() => cobrar(e)}>Cobrar</button>
                  <button className="btn btn-secundario" type="button" onClick={() => avancar(e)}>Avançar</button>
                </div>
              </div>
            )) : (
              <div className="texto-suave">Nenhum item atrasado.</div>
            )}
          </div>
        </div>
      </div>

      <div className="card" style={{ padding: 12, borderRadius: 18 }}>
        <h3 style={{ margin: 0 }}>Todos os encaminhamentos</h3>
        <p className="texto-suave" style={{ marginTop: 6 }}>
          Unidade: <b>{unidadeNome}</b> {destinoFiltro ? <>· Filtro: <b>{destinoFiltro}</b></> : null}
        </p>

        <div style={{ display: "grid", gap: 8, marginTop: 8 }}>
          {lista.length ? lista.map((e) => (
            <div
              id={`cras_enc_${e.id}`}
              key={e.id}
              className="card"
              style={{
                padding: 10,
                borderRadius: 14,
                border: String(e.id) === String(focusEncId) ? "2px solid rgba(59,130,246,.40)" : "1px solid rgba(229,231,235,0.9)",
                background: String(e.id) === String(focusEncId) ? "rgba(239,246,255,.70)" : undefined,
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", gap: 10, flexWrap: "wrap", alignItems: "center" }}>
                <div><b>#{e.id}</b> · {e.destino_nome}</div>
                <StatusPill status={e.status} />
              </div>

              <div style={{ marginTop: 6 }}>
                <FlowMini status={e.status} />
              </div>

              <div className="texto-suave" style={{ marginTop: 6 }}>
                Tipo: {e.destino_tipo} · Pessoa: {e.pessoa_id ? `#${e.pessoa_id}` : "—"} · Prazo: <b>{e.prazo_devolutiva_dias || 7}d</b>
              </div>

              <div style={{ display: "flex", gap: 8, marginTop: 8, flexWrap: "wrap" }}>
                <button className="btn btn-secundario" type="button" onClick={() => avancar(e)}>Avançar</button>
                <button className="btn btn-secundario" type="button" onClick={() => registrarDevolutiva(e)}>Devolutiva</button>
                <button className="btn btn-secundario" type="button" onClick={() => cobrar(e)}>Cobrar</button>
                <button className="btn btn-secundario" type="button" onClick={() => cancelar(e)}>Cancelar</button>
              </div>
            </div>
          )) : (
            <div className="texto-suave">Nenhum encaminhamento nesta unidade.</div>
          )}
        </div>
      </div>
    </div>
  );
}
