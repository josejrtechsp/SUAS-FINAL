import { useEffect, useMemo, useState } from "react";

function ymNow() {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`;
}

// SCFV_SUBTABS_HELP_V1

function toCSVResumo(rows) {
  const header = [
    "nome","cpf","nis",
    "total_encontros","presencas","faltas_explicitas","nao_registrado","faltas_total",
    "taxa_presenca","faltas_seguidas_atual","faltas_seguidas_max","evasao_alerta","presenca_alerta"
  ];
  const esc = (v) => {
    const s = v == null ? "" : String(v);
    if (s.includes('"') || s.includes(",") || s.includes("\n")) return `"${s.replace(/"/g,'""')}"`;
    return s;
  };
  const lines = [header.join(",")];
  for (const r of rows) lines.push(header.map((k) => esc(r[k])).join(","));
  return lines.join("\n");
}

function toCSVDetalhado(rel) {
  const datas = rel.datas_encontros || [];
  const header = ["nome","cpf","nis", ...datas];
  const esc = (v) => {
    const s = v == null ? "" : String(v);
    if (s.includes('"') || s.includes(",") || s.includes("\n")) return `"${s.replace(/"/g,'""')}"`;
    return s;
  };
  const lines = [header.join(",")];
  for (const r of rel.rows) {
    const m = r.matrix || {};
    const row = [r.nome, r.cpf || "", r.nis || "", ...datas.map((d) => m[d] || "")];
    lines.push(row.map(esc).join(","));
  }
  return lines.join("\n");
}

export default function TelaCrasScfv({
  apiBase,
  apiFetch,
  onNavigate,
  focus,
  onFocusConsumed,
  view = "chamada",
  onSetView = () => {},
}) {
  const unidadeAtiva = localStorage.getItem("cras_unidade_ativa") || "";

  const viewKey = String(view || "chamada").toLowerCase();

  const [msg, setMsg] = useState("");
  const [erro, setErro] = useState("");

  const [turmas, setTurmas] = useState([]);
  const [turmaSel, setTurmaSel] = useState(null);

  const [pessoas, setPessoas] = useState([]);
  const [participantes, setParticipantes] = useState([]);

  // criar turma
  const [nome, setNome] = useState("");
  const [publico, setPublico] = useState("");
  const [faixa, setFaixa] = useState("");
  const [dias, setDias] = useState("");
  const [horario, setHorario] = useState("");
  const [vagas, setVagas] = useState("");
  const [local, setLocal] = useState("");

  // inscrever
  const [pessoaId, setPessoaId] = useState("");

  // chamada
  const [dataChamada, setDataChamada] = useState(() => {
    const d = new Date();
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
  });
  const [chamada, setChamada] = useState([]);
  const [draftPresenca, setDraftPresenca] = useState({});
  const [loadingChamada, setLoadingChamada] = useState(false);

  // relatório
  const [mesRel, setMesRel] = useState(ymNow());
  const [limiteEvasao, setLimiteEvasao] = useState(3);
  const [presencaMin, setPresencaMin] = useState(75);
  const [relLoading, setRelLoading] = useState(false);
  const [rel, setRel] = useState(null);

  // painel gestor (unidade) — evasão/baixa presença/sem registro
  const [kpi, setKpi] = useState(null);
  const [kpiLoading, setKpiLoading] = useState(false);

  const [pendingAutoRel, setPendingAutoRel] = useState(false);
  const relRef = useMemo(() => ({ current: null }), []);

  const turmasOrdenadas = useMemo(() => {
    const arr = Array.isArray(turmas) ? [...turmas] : [];
    arr.sort((a, b) => Number(b?.id || 0) - Number(a?.id || 0));
    return arr;
  }, [turmas]);

  const alertas = useMemo(() => {
    const rows = rel?.rows || [];
    return rows.filter((r) => r.evasao_alerta || r.presenca_alerta);
  }, [rel]);

  async function loadTurmas() {
    setErro("");
    try {
      const qs = new URLSearchParams();
      if (unidadeAtiva) qs.set("unidade_id", unidadeAtiva);
      const r = await apiFetch(`${apiBase}/cras/scfv/turmas?${qs.toString()}`);
      if (!r.ok) throw new Error(await r.text());
      const j = await r.json();
      const arr = Array.isArray(j) ? j : [];
      setTurmas(arr);
      if (!turmaSel && arr.length) setTurmaSel(arr[0]);
    } catch (e) {
      console.error(e);
      setErro("Não foi possível carregar turmas SCFV.");
    }
  }

  async function loadPessoas() {
    try {
      const r = await apiFetch(`${apiBase}/cras/cadastros/pessoas`);
      if (r.ok) setPessoas(await r.json());
    } catch {}
  }

  async function loadParticipantes(turmaId) {
    if (!turmaId) return setParticipantes([]);
    try {
      const r = await apiFetch(`${apiBase}/cras/scfv/turmas/${turmaId}/participantes`);
      setParticipantes(r.ok ? await r.json() : []);
    } catch {
      setParticipantes([]);
    }
  }

  async function loadChamada() {
    if (!turmaSel?.id || !dataChamada) return setChamada([]);
    setLoadingChamada(true);
    try {
      const qs = new URLSearchParams();
      qs.set("turma_id", String(turmaSel.id));
      qs.set("data", dataChamada);
      const r = await apiFetch(`${apiBase}/cras/scfv/presencas?${qs.toString()}`);
      if (!r.ok) throw new Error(await r.text());
      const data = await r.json();
      setChamada(data);

      const draft = {};
      (Array.isArray(data) ? data : []).forEach((c) => {
        draft[c.participante_id] = { presente_bool: c.presente_bool, observacao: c.observacao || "" };
      });
      setDraftPresenca(draft);
    } catch (e) {
      console.error(e);
      setChamada([]);
    } finally {
      setLoadingChamada(false);
    }
  }


  async function loadKpiEvasaoUnidade() {
    if (!unidadeAtiva || !mesRel) {
      setKpi(null);
      return;
    }
    const parts = String(mesRel || '').split('-');
    const y = Number(parts[0] || 0);
    const m = Number(parts[1] || 0);
    if (!y || !m) {
      setKpi(null);
      return;
    }

    setKpiLoading(true);
    try {
      const qs = new URLSearchParams();
      qs.set('unidade_id', String(unidadeAtiva));
      qs.set('ano', String(y));
      qs.set('mes', String(m));
      qs.set('limite_evasao', String(Number(limiteEvasao || 3)));
      qs.set('limite_presenca_min', String((Number(presencaMin || 75) / 100).toFixed(2)));
      qs.set('usar_calendario_turma', 'true');
      qs.set('considerar_nao_registrado_como_falta', 'true');
      const r = await apiFetch(`${apiBase}/cras/scfv/kpis/evasao?${qs.toString()}`);
      if (!r.ok) throw new Error(await r.text());
      setKpi(await r.json());
    } catch (e) {
      console.error(e);
      setKpi(null);
    } finally {
      setKpiLoading(false);
    }
  }

  function abrirTurmaDoKpi(turmaId, autoGerar = false) {
    if (!turmaId) return;
    const found = (turmas || []).find((x) => Number(x.id) === Number(turmaId));
    if (found) {
      setTurmaSel(found);
      if (autoGerar) setPendingAutoRel(true);
    }
  }

  // Atualiza o painel gestor do mês (unidade)
  useEffect(() => {
    if (viewKey !== "alertas") return;
    loadKpiEvasaoUnidade();
    // eslint-disable-next-line
  }, [viewKey, unidadeAtiva, mesRel, limiteEvasao, presencaMin, turmas.length]);

  useEffect(() => {
    loadTurmas();
    loadPessoas();
    // eslint-disable-next-line
  }, []);

  useEffect(() => {
    if (turmaSel?.id) {
      loadParticipantes(turmaSel.id);
      loadChamada();
      setRel(null);
    }
    // eslint-disable-next-line
  }, [turmaSel?.id]);

  useEffect(() => {
    if (turmaSel?.id) loadChamada();
    // eslint-disable-next-line
  }, [dataChamada]);

  // foco vindo do KPI da Home
  useEffect(() => {
    if (!focus) return;

    // quando vem da Home, abra a visão mais apropriada
    try {
      if (typeof onSetView === "function") {
        if (focus.scrollRel) onSetView("exportar");
        else onSetView("alertas");
      }
    } catch {}
    if (focus.mes) setMesRel(focus.mes);
    if (focus.limite) setLimiteEvasao(focus.limite);
    if (focus.presMin) setPresencaMin(focus.presMin);
    if (focus.scrollRel) {
      // marca para rolar após gerar
      setTimeout(() => {
        try { document.getElementById('scfv_relatorio_anchor')?.scrollIntoView({ behavior: 'smooth', block: 'start' }); } catch {}
      }, 300);
    }
    if (focus.turmaId && Array.isArray(turmas) && turmas.length) {
      const found = turmas.find((x) => Number(x.id) === Number(focus.turmaId));
      if (found) setTurmaSel(found);
    }
    setPendingAutoRel(true);
    // eslint-disable-next-line
  }, [focus, turmas.length]);

  useEffect(() => {
    if (!pendingAutoRel) return;
    if (!turmaSel?.id) return;
    gerarRelatorio().finally(() => {
      setPendingAutoRel(false);
      if (typeof onFocusConsumed === "function") onFocusConsumed();
    });
    // eslint-disable-next-line
  }, [pendingAutoRel, turmaSel?.id]);

  async function criarTurma() {
    setMsg("");
    if (!unidadeAtiva) return setMsg("Selecione a Unidade CRAS no cabeçalho.");
    if (!nome.trim()) return setMsg("Nome da turma é obrigatório.");

    try {
      const r = await apiFetch(`${apiBase}/cras/scfv/turmas`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          unidade_id: Number(unidadeAtiva),
          nome: nome.trim(),
          publico: publico || null,
          faixa_etaria: faixa || null,
          dias: dias || null,
          horario: horario || null,
          vagas: vagas ? Number(vagas) : null,
          local: local || null,
        }),
      });
      if (!r.ok) throw new Error(await r.text());
      const created = await r.json();
      setMsg("Turma criada ✅");
      setNome(""); setPublico(""); setFaixa(""); setDias(""); setHorario(""); setVagas(""); setLocal("");
      await loadTurmas();
      if (created?.id) setTurmaSel(created);
    } catch (e) {
      console.error(e);
      setMsg("Erro ao criar turma.");
    }
  }

  async function inscrever() {
    setMsg("");
    if (!turmaSel?.id) return setMsg("Selecione uma turma.");
    if (!pessoaId) return setMsg("Selecione uma pessoa.");

    try {
      const r = await apiFetch(`${apiBase}/cras/scfv/turmas/${turmaSel.id}/inscrever`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ pessoa_id: Number(pessoaId) }),
      });
      if (!r.ok) throw new Error(await r.text());
      setMsg("Inscrito ✅");
      setPessoaId("");
      await loadParticipantes(turmaSel.id);
      await loadChamada();
    } catch (e) {
      console.error(e);
      setMsg("Erro ao inscrever (capacidade/duplicidade).");
    }
  }

  function marcarTodos(presente_bool) {
    const next = { ...draftPresenca };
    (chamada || []).forEach((c) => {
      next[c.participante_id] = { presente_bool, observacao: next[c.participante_id]?.observacao || c.observacao || "" };
    });
    setDraftPresenca(next);
    setMsg(presente_bool ? "Todos marcados como PRESENTE (rascunho) ✅" : "Todos marcados como AUSENTE (rascunho) ✅");
  }

  async function salvarLote() {
    if (!turmaSel?.id || !dataChamada) return;
    const itens = (chamada || []).map((c) => {
      const d = draftPresenca[c.participante_id] || {};
      if (d.presente_bool == null) return null;
      return { participante_id: c.participante_id, data: dataChamada, presente_bool: !!d.presente_bool, observacao: d.observacao || null };
    }).filter(Boolean);

    if (!itens.length) return setMsg("Nada para salvar no lote.");

    setMsg("Salvando lote…");
    try {
      await Promise.all(itens.map((payload) =>
        apiFetch(`${apiBase}/cras/scfv/presencas`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) })
      ));
      setMsg("Lote salvo ✅");
      await loadChamada();
    } catch (e) {
      console.error(e);
      setMsg("Erro ao salvar lote.");
    }
  }

  async function gerarRelatorio() {
    setMsg("");
    if (!turmaSel?.id) return setMsg("Selecione uma turma.");
    if (!mesRel) return setMsg("Selecione um mês.");
    const [y, m] = mesRel.split("-");
    if (!y || !m) return setMsg("Mês inválido.");

    setRelLoading(true);
    try {
      const qs = new URLSearchParams();
      qs.set("turma_id", String(turmaSel.id));
      qs.set("ano", String(Number(y)));
      qs.set("mes", String(Number(m)));
      qs.set("limite_evasao", String(Number(limiteEvasao || 3)));
      qs.set("limite_presenca_min", String((Number(presencaMin || 75) / 100).toFixed(2)));
      const r = await apiFetch(`${apiBase}/cras/scfv/relatorio/mensal?${qs.toString()}`);
      if (!r.ok) throw new Error(await r.text());
      setRel(await r.json());
    } catch (e) {
      console.error(e);
      setMsg("Erro ao gerar relatório.");
      setRel(null);
    } finally {
      setRelLoading(false);
    }
  }

  function exportarCSVResumo() {
    if (!rel?.rows?.length) return setMsg("Gere um relatório antes de exportar.");
    const csv = toCSVResumo(rel.rows);
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    const ym = `${rel.ano}-${String(rel.mes).padStart(2, "0")}`;
    a.download = `scfv_relatorio_${ym}_turma_${rel.turma_id}.csv`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  }

  function exportarCSVDetalhado() {
    if (!rel?.rows?.length) return setMsg("Gere um relatório antes de exportar.");
    const csv = toCSVDetalhado(rel);
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    const ym = `${rel.ano}-${String(rel.mes).padStart(2, "0")}`;
    a.download = `scfv_detalhado_${ym}_turma_${rel.turma_id}.csv`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  }

  const setTurmaById = (id) => {
    const found = (turmas || []).find((x) => String(x.id) === String(id));
    if (found) setTurmaSel(found);
  };

  const TurmaPicker = ({ showManage = true } = {}) => (
    <div className="card" style={{ padding: 12, borderRadius: 18 }}>
      <div style={{ display: "flex", justifyContent: "space-between", gap: 10, flexWrap: "wrap", alignItems: "center" }}>
        <div>
          <div style={{ fontWeight: 900 }}>Turma</div>
          <div className="texto-suave">Unidade ativa: <strong>{unidadeAtiva ? `CRAS ${unidadeAtiva}` : "—"}</strong></div>
        </div>
        <div style={{ display: "flex", gap: 10, flexWrap: "wrap", alignItems: "center" }}>
          <select className="input" value={turmaSel?.id || ""} onChange={(e) => setTurmaById(e.target.value)} style={{ minWidth: 260 }}>
            <option value="">Selecione uma turma…</option>
            {turmasOrdenadas.map((t) => (
              <option key={t.id} value={t.id}>#{t.id} · {t.nome}</option>
            ))}
          </select>
          <button className="btn btn-secundario" type="button" onClick={loadTurmas}>Atualizar turmas</button>
          {showManage ? (
            <button className="btn btn-secundario" type="button" onClick={() => onSetView("turmas")}>Gerenciar turmas</button>
          ) : null}
        </div>
      </div>
    </div>
  );

  const NeedTurma = () => (
    <div className="card" style={{ padding: 12, borderRadius: 18 }}>
      <div style={{ fontWeight: 900 }}>Selecione uma turma</div>
      <div className="texto-suave" style={{ marginTop: 6 }}>
        Para continuar, selecione uma turma no topo ou vá em <strong>Turmas</strong> para criar/inscrever participantes.
      </div>
      <div style={{ display: "flex", gap: 10, flexWrap: "wrap", marginTop: 10 }}>
        <button className="btn btn-primario" type="button" onClick={() => onSetView("turmas")}>Ir para Turmas</button>
      </div>
    </div>
  );

  const TurmasView = () => (
    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
      <div className="card" style={{ padding: 12, borderRadius: 18 }}>
        <div style={{ display: "flex", justifyContent: "space-between", gap: 10, flexWrap: "wrap", alignItems: "center" }}>
          <div>
            <div style={{ fontWeight: 900 }}>SCFV — Turmas</div>
            <div className="texto-suave">Crie turmas e mantenha a lista organizada por unidade.</div>
          </div>
          <button className="btn btn-secundario" type="button" onClick={() => onSetView("chamada")}>Ir para Chamada</button>
        </div>

        <div className="card" style={{ padding: 10, borderRadius: 14, marginTop: 12, border: "1px solid rgba(2,6,23,.06)" }}>
          <div style={{ fontWeight: 900, marginBottom: 8 }}>Criar turma</div>
          <div style={{ display: "grid", gap: 8 }}>
            <input className="input" placeholder="Nome da turma" value={nome} onChange={(e) => setNome(e.target.value)} />
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
              <select className="input" value={publico} onChange={(e) => setPublico(e.target.value)}>
                <option value="">Público (opcional)…</option>
                <option value="crianca">Criança</option>
                <option value="adolescente">Adolescente</option>
                <option value="adulto">Adulto</option>
                <option value="idoso">Idoso</option>
                <option value="mulher">Mulheres</option>
                <option value="pcd">PCD</option>
                <option value="outros">Outros</option>
              </select>
              <input className="input" placeholder="Faixa etária (opcional)" value={faixa} onChange={(e) => setFaixa(e.target.value)} />
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
              <input className="input" placeholder="Dias (ex: Seg/Qua)" value={dias} onChange={(e) => setDias(e.target.value)} />
              <input className="input" placeholder="Horário (ex: 14:00-16:00)" value={horario} onChange={(e) => setHorario(e.target.value)} />
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
              <input className="input" placeholder="Vagas (opcional)" value={vagas} onChange={(e) => setVagas(e.target.value)} />
              <input className="input" placeholder="Local (opcional)" value={local} onChange={(e) => setLocal(e.target.value)} />
            </div>
            <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
              <button className="btn btn-primario" type="button" onClick={criarTurma}>Criar</button>
              <button className="btn btn-secundario" type="button" onClick={loadTurmas}>Atualizar</button>
            </div>
          </div>
        </div>

        <div style={{ display: "grid", gap: 8, marginTop: 12, maxHeight: 420, overflow: "auto" }}>
          {turmasOrdenadas.map((t) => (
            <button
              key={t.id}
              type="button"
              className="card"
              onClick={() => setTurmaSel(t)}
              style={{
                textAlign: "left",
                padding: 12,
                borderRadius: 16,
                cursor: "pointer",
                border: turmaSel?.id === t.id ? "2px solid rgba(99,102,241,.55)" : "1px solid rgba(2,6,23,.08)",
              }}
            >
              <div style={{ fontWeight: 900 }}>#{t.id} · {t.nome}</div>
              <div className="texto-suave" style={{ marginTop: 6 }}>
                {t.publico ? `Público: ${t.publico} · ` : ""}
                {t.faixa_etaria ? `Faixa: ${t.faixa_etaria} · ` : ""}
                {t.dias || "—"} · {t.horario || "—"}
              </div>
              <div className="texto-suave">
                {t.vagas != null ? `Vagas: ${t.vagas}` : "Vagas: —"}
                {t.local ? ` · Local: ${t.local}` : ""}
              </div>
            </button>
          ))}
          {!turmasOrdenadas.length ? <div className="texto-suave">Nenhuma turma cadastrada.</div> : null}
        </div>
      </div>

      <div className="card" style={{ padding: 12, borderRadius: 18 }}>
        <div style={{ fontWeight: 900 }}>Participantes</div>
        <div className="texto-suave" style={{ marginTop: 6 }}>Inscreva pessoas para aparecerem na chamada.</div>

        {!turmaSel ? (
          <div className="texto-suave" style={{ marginTop: 10 }}>Selecione uma turma à esquerda.</div>
        ) : (
          <>
            <div className="texto-suave" style={{ marginTop: 8 }}>Turma: <strong>{turmaSel.nome}</strong></div>

            <div className="card" style={{ padding: 10, borderRadius: 14, marginTop: 12, border: "1px solid rgba(2,6,23,.06)" }}>
              <div style={{ fontWeight: 900, marginBottom: 8 }}>Inscrever participante</div>
              <div style={{ display: "flex", gap: 10, flexWrap: "wrap", alignItems: "center" }}>
                <select className="input" value={pessoaId} onChange={(e) => setPessoaId(e.target.value)} style={{ minWidth: 280 }}>
                  <option value="">Selecione a pessoa…</option>
                  {pessoas.map((p) => (
                    <option key={p.id} value={p.id}>{p.nome_social ? `${p.nome_social} (${p.nome})` : p.nome}</option>
                  ))}
                </select>
                <button className="btn btn-primario" type="button" onClick={inscrever}>Inscrever</button>
                <button className="btn btn-secundario" type="button" onClick={() => loadParticipantes(turmaSel.id)}>Atualizar</button>
              </div>
            </div>

            <div style={{ display: "grid", gap: 8, marginTop: 12, maxHeight: 420, overflow: "auto" }}>
              {participantes.map((pt) => (
                <div key={pt.id} className="card" style={{ padding: 10, borderRadius: 14 }}>
                  <div style={{ fontWeight: 900 }}>{pt.pessoa?.nome || `Pessoa #${pt.pessoa_id}`}</div>
                  <div className="texto-suave">CPF: {pt.pessoa?.cpf || "—"} · NIS: {pt.pessoa?.nis || "—"}</div>
                </div>
              ))}
              {!participantes.length ? <div className="texto-suave">Sem participantes.</div> : null}
            </div>
          </>
        )}
      </div>
    </div>
  );

  const ChamadaView = () => (
    <div style={{ display: "grid", gap: 12 }}>
      <TurmaPicker />
      {!turmaSel ? <NeedTurma /> : (
        <div className="card" style={{ padding: 12, borderRadius: 18 }}>
          <div style={{ display: "flex", justifyContent: "space-between", gap: 10, flexWrap: "wrap", alignItems: "center" }}>
            <div>
              <div style={{ fontWeight: 900 }}>Chamada</div>
              <div className="texto-suave">Marque presença por turma e data. Salve em lote.</div>
            </div>
            <div style={{ display: "flex", gap: 10, alignItems: "center", flexWrap: "wrap" }}>
              <input type="date" className="input" value={dataChamada} onChange={(e) => setDataChamada(e.target.value)} />
              <button className="btn btn-secundario" type="button" onClick={loadChamada}>Atualizar</button>
            </div>
          </div>

          <div style={{ display: "flex", gap: 10, flexWrap: "wrap", marginTop: 12 }}>
            <button className="btn btn-secundario" type="button" onClick={() => marcarTodos(true)}>Marcar todos presentes</button>
            <button className="btn btn-secundario" type="button" onClick={() => marcarTodos(false)}>Marcar todos ausentes</button>
            <button className="btn btn-primario" type="button" onClick={salvarLote}>Salvar lote</button>
          </div>

          {loadingChamada ? <div className="texto-suave" style={{ marginTop: 10 }}>Carregando…</div> : null}

          <div style={{ display: "grid", gap: 8, marginTop: 12, maxHeight: 520, overflow: "auto" }}>
            {chamada.map((c) => {
              const nomePessoa = c.pessoa?.nome || `Pessoa #${c.pessoa_id}`;
              const d = draftPresenca[c.participante_id] || {};
              const current = d.presente_bool == null ? "" : (d.presente_bool ? "sim" : "nao");
              return (
                <div key={c.participante_id} className="card" style={{ padding: 10, borderRadius: 14 }}>
                  <div style={{ fontWeight: 900 }}>{nomePessoa}</div>
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr auto", gap: 10, marginTop: 10 }}>
                    <select
                      className="input"
                      value={current}
                      onChange={(e) => {
                        const v = e.target.value;
                        const next = { ...draftPresenca };
                        next[c.participante_id] = {
                          presente_bool: v === "" ? null : (v === "sim"),
                          observacao: next[c.participante_id]?.observacao || "",
                        };
                        setDraftPresenca(next);
                      }}
                    >
                      <option value="">Marcar…</option>
                      <option value="sim">Presente</option>
                      <option value="nao">Ausente</option>
                    </select>

                    <input
                      className="input"
                      value={(draftPresenca[c.participante_id]?.observacao ?? "")}
                      placeholder="Obs (opcional)"
                      onChange={(e) => {
                        const obs = e.target.value;
                        const next = { ...draftPresenca };
                        next[c.participante_id] = {
                          presente_bool: next[c.participante_id]?.presente_bool ?? null,
                          observacao: obs,
                        };
                        setDraftPresenca(next);
                      }}
                    />

                    <button className="btn btn-secundario" type="button" onClick={loadChamada}>Recarregar</button>
                  </div>
                </div>
              );
            })}
            {!chamada.length ? <div className="texto-suave">Sem chamada (sem participantes ativos ou sem registros).</div> : null}
          </div>
        </div>
      )}
    </div>
  );

  const AlertasView = () => (
    <div style={{ display: "grid", gap: 12 }}>
      <div className="card" style={{ padding: 12, borderRadius: 18 }}>
        <div style={{ display: "flex", justifyContent: "space-between", gap: 10, flexWrap: "wrap", alignItems: "center" }}>
          <div>
            <div style={{ fontWeight: 900 }}>Painel de alertas (Unidade)</div>
            <div className="texto-suave">Evasão, baixa presença e dias sem registro no mês.</div>
          </div>
          <button className="btn btn-secundario" type="button" onClick={loadKpiEvasaoUnidade}>Atualizar painel</button>
        </div>

        <div style={{ display: "flex", gap: 10, flexWrap: "wrap", marginTop: 12, alignItems: "center" }}>
          <label className="texto-suave">Mês:</label>
          <input type="month" className="input" value={mesRel} onChange={(e) => setMesRel(e.target.value)} />
          <label className="texto-suave">Faltas seguidas:</label>
          <input type="number" className="input" value={limiteEvasao} min={1} max={60} onChange={(e) => setLimiteEvasao(e.target.value)} style={{ width: 110 }} />
          <label className="texto-suave">Presença mínima (%):</label>
          <input type="number" className="input" value={presencaMin} min={0} max={100} onChange={(e) => setPresencaMin(e.target.value)} style={{ width: 110 }} />
        </div>

        {!unidadeAtiva ? <div className="texto-suave" style={{ marginTop: 10 }}>Selecione a Unidade CRAS no cabeçalho para ver os alertas.</div> : null}
        {kpiLoading ? <div className="texto-suave" style={{ marginTop: 10 }}>Carregando…</div> : null}

        {kpi ? (
          <>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(4, minmax(0, 1fr))", gap: 10, marginTop: 12 }}>
              <div className="card" style={{ padding: 10, borderRadius: 14 }}>
                <div className="texto-suave" style={{ fontWeight: 900 }}>Evasão</div>
                <div style={{ fontSize: 20, fontWeight: 950 }}>{kpi.total_alertas_evasao ?? 0}</div>
              </div>
              <div className="card" style={{ padding: 10, borderRadius: 14 }}>
                <div className="texto-suave" style={{ fontWeight: 900 }}>Baixa presença</div>
                <div style={{ fontSize: 20, fontWeight: 950 }}>{kpi.total_alertas_baixa_presenca ?? 0}</div>
              </div>
              <div className="card" style={{ padding: 10, borderRadius: 14 }}>
                <div className="texto-suave" style={{ fontWeight: 900 }}>Dias sem registro</div>
                <div style={{ fontSize: 20, fontWeight: 950 }}>{kpi.dias_sem_registro_total ?? 0}</div>
              </div>
              <div className="card" style={{ padding: 10, borderRadius: 14 }}>
                <div className="texto-suave" style={{ fontWeight: 900 }}>Turmas com alerta</div>
                <div style={{ fontSize: 20, fontWeight: 950 }}>{kpi.turmas_com_alerta ?? 0}</div>
              </div>
            </div>

            <div style={{ marginTop: 12, fontWeight: 900 }}>Top turmas (mês)</div>
            <div className="texto-suave">Clique para abrir a turma e (se quiser) gerar o relatório do mês.</div>
            <div style={{ marginTop: 8, overflow: "auto" }}>
              <table style={{ width: "100%", borderCollapse: "collapse" }}>
                <thead>
                  <tr>
                    {["Turma", "Evasão", "Baixa", "Sem registro", "Encontros", "Ação"].map((h) => (
                      <th key={h} style={{ textAlign: "left", padding: 8, borderBottom: "1px solid rgba(2,6,23,.10)" }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {(kpi.top_turmas || []).map((t) => (
                    <tr key={t.turma_id}>
                      <td style={{ padding: 8, borderBottom: "1px solid rgba(2,6,23,.06)" }}><strong>#{t.turma_id}</strong> · {t.turma_nome}</td>
                      <td style={{ padding: 8, borderBottom: "1px solid rgba(2,6,23,.06)" }}>{t.alertas_evasao ?? 0}</td>
                      <td style={{ padding: 8, borderBottom: "1px solid rgba(2,6,23,.06)" }}>{t.alertas_baixa_presenca ?? 0}</td>
                      <td style={{ padding: 8, borderBottom: "1px solid rgba(2,6,23,.06)" }}>{t.dias_sem_registro ?? 0}</td>
                      <td style={{ padding: 8, borderBottom: "1px solid rgba(2,6,23,.06)" }}>{t.total_encontros ?? 0}</td>
                      <td style={{ padding: 8, borderBottom: "1px solid rgba(2,6,23,.06)" }}>
                        <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
                          <button className="btn btn-secundario btn-secundario-mini" type="button" onClick={() => abrirTurmaDoKpi(t.turma_id, false)}>Abrir</button>
                          <button className="btn btn-primario btn-primario-mini" type="button" onClick={() => abrirTurmaDoKpi(t.turma_id, true)}>Abrir + relatório</button>
                        </div>
                      </td>
                    </tr>
                  ))}
                  {!(kpi.top_turmas || []).length ? (
                    <tr><td colSpan={6} className="texto-suave" style={{ padding: 10 }}>Sem alertas neste mês.</td></tr>
                  ) : null}
                </tbody>
              </table>
            </div>
          </>
        ) : null}
      </div>

      <TurmaPicker />

      {!turmaSel ? <NeedTurma /> : (
        <div className="card" style={{ padding: 12, borderRadius: 18 }}>
          <div style={{ display: "flex", justifyContent: "space-between", gap: 10, flexWrap: "wrap", alignItems: "center" }}>
            <div>
              <div style={{ fontWeight: 900 }}>Alertas da turma (mês)</div>
              <div className="texto-suave">Gere o resumo do mês para listar evasão e baixa presença.</div>
            </div>
            <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
              <button className="btn btn-primario" type="button" onClick={gerarRelatorio} disabled={relLoading}>
                {relLoading ? "Gerando…" : "Gerar resumo"}
              </button>
              <button className="btn btn-secundario" type="button" onClick={() => onSetView("exportar")}>Ver relatório completo</button>
            </div>
          </div>

          {rel ? (
            <>
              <div className="texto-suave" style={{ marginTop: 10 }}>
                Encontros: <strong>{rel.total_encontros}</strong> · sem registro: <strong style={{ color: rel.total_sem_registro > 0 ? "rgba(220,38,38,.95)" : "inherit" }}>{rel.total_sem_registro}</strong> · Participantes: <strong>{rel.total_participantes}</strong> · Alertas: <strong>{alertas.length}</strong>
              </div>

              {alertas.length ? (
                <div style={{ display: "grid", gap: 8, marginTop: 12 }}>
                  {alertas.map((a) => {
                    const parts = [];
                    if (a.evasao_alerta) parts.push(`EVASÃO (${a.faltas_seguidas_max} seg.)`);
                    if (a.presenca_alerta) parts.push(`BAIXA PRESENÇA (${Math.round((a.taxa_presenca || 0) * 100)}%)`);
                    return (
                      <div key={a.participante_id} className="card" style={{ padding: 10, borderRadius: 14, border: "1px solid rgba(245,158,11,.22)", background: "rgba(245,158,11,.06)" }}>
                        <div style={{ fontWeight: 900 }}>{a.nome}</div>
                        <div className="texto-suave">{parts.join(" + ")}</div>
                      </div>
                    );
                  })}
                </div>
              ) : (
                <div className="texto-suave" style={{ marginTop: 10 }}>Sem alertas no mês para esta turma.</div>
              )}
            </>
          ) : (
            <div className="texto-suave" style={{ marginTop: 10 }}>Clique em “Gerar resumo” para listar alertas do mês.</div>
          )}
        </div>
      )}
    </div>
  );

  const ExportarView = () => (
    <div style={{ display: "grid", gap: 12 }}>
      <TurmaPicker />
      {!turmaSel ? <NeedTurma /> : (
        <div className="card" style={{ padding: 12, borderRadius: 18 }}>
          <div id="scfv_relatorio_anchor" style={{ display: "flex", justifyContent: "space-between", gap: 10, flexWrap: "wrap", alignItems: "center" }}>
            <div>
              <div style={{ fontWeight: 900 }}>Relatório mensal de frequência</div>
              <div className="texto-suave">Gere o mês, revise alertas e exporte CSV.</div>
            </div>
            <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
              <button className="btn btn-secundario" type="button" onClick={exportarCSVResumo}>Exportar CSV</button>
              <button className="btn btn-secundario" type="button" onClick={exportarCSVDetalhado}>CSV (datas)</button>
            </div>
          </div>

          <div style={{ display: "flex", gap: 10, flexWrap: "wrap", marginTop: 12, alignItems: "center" }}>
            <label className="texto-suave">Mês:</label>
            <input type="month" className="input" value={mesRel} onChange={(e) => setMesRel(e.target.value)} />
            <label className="texto-suave">Faltas seguidas:</label>
            <input type="number" className="input" value={limiteEvasao} min={1} max={60} onChange={(e) => setLimiteEvasao(e.target.value)} style={{ width: 110 }} />
            <label className="texto-suave">Presença mínima (%):</label>
            <input type="number" className="input" value={presencaMin} min={0} max={100} onChange={(e) => setPresencaMin(e.target.value)} style={{ width: 110 }} />
            <button className="btn btn-primario" type="button" onClick={gerarRelatorio} disabled={relLoading}>
              {relLoading ? "Gerando…" : "Gerar"}
            </button>
          </div>

          {rel ? (
            <>
              <div className="texto-suave" style={{ marginTop: 10 }}>
                Encontros no mês: <strong>{rel.total_encontros}</strong> · com registro: <strong>{rel.total_com_registro}</strong> · sem registro: <strong style={{ color: rel.total_sem_registro > 0 ? "rgba(220,38,38,.95)" : "inherit" }}>{rel.total_sem_registro}</strong> · Participantes: <strong>{rel.total_participantes}</strong> · Alertas: <strong>{alertas.length}</strong>
                <button
                  className="btn btn-secundario btn-secundario-mini"
                  type="button"
                  style={{ marginLeft: 10 }}
                  onClick={() => {
                    if (rel?.datas_sem_registro?.length) {
                      alert(`Datas sem registro:\n\n${rel.datas_sem_registro.join("\n")}`);
                    } else {
                      setMsg("Sem datas sem registro.");
                    }
                  }}
                >
                  Ver datas sem registro
                </button>
              </div>

              {alertas.length ? (
                <div className="card" style={{ padding: 10, borderRadius: 14, marginTop: 10, border: "1px solid rgba(245,158,11,.22)", background: "rgba(245,158,11,.06)" }}>
                  <div style={{ fontWeight: 900 }}>Alertas</div>
                  <div className="texto-suave" style={{ marginTop: 6 }}>
                    {alertas
                      .map((a) => {
                        const parts = [];
                        if (a.evasao_alerta) parts.push(`EVASÃO (${a.faltas_seguidas_max} seg.)`);
                        if (a.presenca_alerta) parts.push(`BAIXA PRESENÇA (${Math.round((a.taxa_presenca || 0) * 100)}%)`);
                        return `${a.nome}: ${parts.join(" + ")}`;
                      })
                      .join(" · ")}
                  </div>
                </div>
              ) : null}

              <div style={{ marginTop: 12, overflow: "auto" }}>
                <table style={{ width: "100%", borderCollapse: "collapse" }}>
                  <thead>
                    <tr>
                      {["Nome", "Pres.", "Faltas", "Não reg.", "Total", "% Pres.", "Máx seg.", "Alerta"].map((h) => (
                        <th key={h} style={{ textAlign: "left", padding: "8px 6px", borderBottom: "1px solid rgba(2,6,23,.08)" }}>{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {rel.rows.map((r) => (
                      <tr key={r.participante_id} style={{ background: (r.evasao_alerta || r.presenca_alerta) ? "rgba(245,158,11,.08)" : "transparent" }}>
                        <td style={{ padding: "8px 6px", borderBottom: "1px solid rgba(2,6,23,.06)" }}>
                          <strong>{r.nome}</strong>
                          <div className="texto-suave">CPF: {r.cpf || "—"} · NIS: {r.nis || "—"}</div>
                        </td>
                        <td style={{ padding: "8px 6px", borderBottom: "1px solid rgba(2,6,23,.06)" }}>{r.presencas}</td>
                        <td style={{ padding: "8px 6px", borderBottom: "1px solid rgba(2,6,23,.06)" }}>{r.faltas_total}</td>
                        <td style={{ padding: "8px 6px", borderBottom: "1px solid rgba(2,6,23,.06)" }}>{r.nao_registrado}</td>
                        <td style={{ padding: "8px 6px", borderBottom: "1px solid rgba(2,6,23,.06)" }}>{r.total_encontros}</td>
                        <td style={{ padding: "8px 6px", borderBottom: "1px solid rgba(2,6,23,.06)" }}>
                          {r.taxa_presenca == null ? "—" : `${Math.round(r.taxa_presenca * 100)}%`}
                        </td>
                        <td style={{ padding: "8px 6px", borderBottom: "1px solid rgba(2,6,23,.06)" }}>{r.faltas_seguidas_max}</td>
                        <td style={{ padding: "8px 6px", borderBottom: "1px solid rgba(2,6,23,.06)" }}>
                          {r.evasao_alerta ? "EVASÃO" : (r.presenca_alerta ? "BAIXA PRES." : "—")}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          ) : (
            <div className="texto-suave" style={{ marginTop: 10 }}>Clique em “Gerar” para montar o relatório do mês.</div>
          )}
        </div>
      )}
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

      {viewKey === "turmas" ? <TurmasView /> : null}
      {viewKey === "chamada" ? <ChamadaView /> : null}
      {viewKey === "alertas" ? <AlertasView /> : null}
      {viewKey === "exportar" ? <ExportarView /> : null}

      {!(["turmas", "chamada", "alertas", "exportar"].includes(viewKey)) ? <ChamadaView /> : null}
    </div>
  );
}
