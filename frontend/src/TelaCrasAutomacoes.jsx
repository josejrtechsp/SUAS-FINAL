import React, { useEffect, useMemo, useState } from "react";

function fmtDateTime(v) {
  if (!v) return "—";
  try {
    const d = typeof v === "string" ? new Date(v) : v;
    if (Number.isNaN(d.getTime())) return String(v);
    return d.toLocaleString();
  } catch {
    return String(v);
  }
}

function Button({ children, onClick, disabled, kind = "primary", style }) {
  const base = {
    padding: "10px 12px",
    borderRadius: 12,
    border: "1px solid rgba(2,6,23,.12)",
    cursor: disabled ? "not-allowed" : "pointer",
    opacity: disabled ? 0.6 : 1,
    fontWeight: 800,
    fontSize: 13,
    userSelect: "none",
  };

  const kinds = {
    primary: { background: "rgba(2,6,23,.92)", color: "white" },
    soft: { background: "rgba(2,6,23,.04)", color: "rgba(2,6,23,.92)" },
    danger: { background: "rgba(220,38,38,.1)", color: "rgba(220,38,38,.95)", border: "1px solid rgba(220,38,38,.25)" },
  };

  return (
    <button
      type="button"
      onClick={disabled ? undefined : onClick}
      disabled={disabled}
      style={{ ...base, ...(kinds[kind] || kinds.primary), ...style }}
    >
      {children}
    </button>
  );
}

function Chip({ children, tone = "muted" }) {
  const map = {
    ok: { background: "rgba(16,185,129,.12)", color: "rgba(6,95,70,1)", border: "1px solid rgba(16,185,129,.25)" },
    warn: { background: "rgba(245,158,11,.12)", color: "rgba(146,64,14,1)", border: "1px solid rgba(245,158,11,.25)" },
    muted: { background: "rgba(2,6,23,.06)", color: "rgba(2,6,23,.75)", border: "1px solid rgba(2,6,23,.10)" },
  };
  const s = map[tone] || map.muted;
  return (
    <span style={{ display: "inline-flex", alignItems: "center", gap: 6, padding: "5px 10px", borderRadius: 999, fontSize: 12, fontWeight: 800, ...s }}>
      {children}
    </span>
  );
}

function Modal({ open, title, onClose, children, footer }) {
  if (!open) return null;
  return (
    <div
      role="dialog"
      aria-modal="true"
      onMouseDown={(e) => {
        if (e.target === e.currentTarget) onClose?.();
      }}
      style={{ position: "fixed", inset: 0, background: "rgba(2,6,23,.55)", zIndex: 50, display: "flex", alignItems: "center", justifyContent: "center", padding: 14 }}
    >
      <div style={{ width: "min(920px, 96vw)", maxHeight: "90vh", overflow: "auto", background: "white", borderRadius: 16, border: "1px solid rgba(2,6,23,.12)", boxShadow: "0 20px 60px rgba(0,0,0,.25)" }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: 14, borderBottom: "1px solid rgba(2,6,23,.08)" }}>
          <div style={{ fontWeight: 950, fontSize: 14 }}>{title}</div>
          <Button kind="soft" onClick={onClose}>Fechar</Button>
        </div>
        <div style={{ padding: 14 }}>{children}</div>
        {footer ? <div style={{ padding: 14, borderTop: "1px solid rgba(2,6,23,.08)", display: "flex", justifyContent: "flex-end", gap: 10 }}>{footer}</div> : null}
      </div>
    </div>
  );
}

function Row({ label, children, hint }) {
  return (
    <div style={{ display: "grid", gridTemplateColumns: "220px 1fr", gap: 10, alignItems: "start", padding: "10px 0", borderBottom: "1px dashed rgba(2,6,23,.10)" }}>
      <div>
        <div style={{ fontSize: 12, fontWeight: 900, color: "rgba(2,6,23,.75)" }}>{label}</div>
        {hint ? <div style={{ marginTop: 4, fontSize: 12, color: "rgba(2,6,23,.55)" }}>{hint}</div> : null}
      </div>
      <div>{children}</div>
    </div>
  );
}

function Input({ value, onChange, type = "text", placeholder, style }) {
  return (
    <input
      value={value ?? ""}
      onChange={(e) => onChange?.(e.target.value)}
      type={type}
      placeholder={placeholder}
      style={{ width: "100%", padding: "10px 12px", borderRadius: 12, border: "1px solid rgba(2,6,23,.12)", outline: "none", fontSize: 13, ...style }}
    />
  );
}

function Select({ value, onChange, options, style }) {
  return (
    <select
      value={value ?? ""}
      onChange={(e) => onChange?.(e.target.value)}
      style={{ width: "100%", padding: "10px 12px", borderRadius: 12, border: "1px solid rgba(2,6,23,.12)", outline: "none", fontSize: 13, background: "white", ...style }}
    >
      {options.map((o) => (
        <option key={String(o.value)} value={o.value}>
          {o.label}
        </option>
      ))}
    </select>
  );
}

export default function TelaCrasAutomacoes({ apiBase, apiFetch, municipioId, unidadeId, usuarioLogado, onChanged, view = "ativas", onSetView = () => {} }) {
  const mun = useMemo(() => {
    const v = municipioId || usuarioLogado?.municipio_id;
    const n = Number(v);
    return Number.isFinite(n) && n > 0 ? n : 0;
  }, [municipioId, usuarioLogado]);

  const uni = useMemo(() => {
    const n = Number(unidadeId);
    return Number.isFinite(n) && n > 0 ? n : 0;
  }, [unidadeId]);


  const viewKey = String(view || "ativas").toLowerCase();
  const canEdit = useMemo(() => {
    const p = String(usuarioLogado?.perfil || "").toLowerCase();
    return ["admin", "gestor", "coordenador", "coord", "supervisor"].includes(p);
  }, [usuarioLogado]);

  const [includeInativas, setIncludeInativas] = useState(true);
  const [seedParaUnidade, setSeedParaUnidade] = useState(false);

  const [loading, setLoading] = useState(false);
  const [regras, setRegras] = useState([]);
  const [erro, setErro] = useState("");
  const [ok, setOk] = useState("");

  const [execucao, setExecucao] = useState(null);

  const [editRule, setEditRule] = useState(null);
  const [editAtivo, setEditAtivo] = useState(true);
  const [editFreq, setEditFreq] = useState("1440");
  const [editTitulo, setEditTitulo] = useState("");
  const [editDesc, setEditDesc] = useState("");
  const [editDiasSemMov, setEditDiasSemMov] = useState("");
  const [editPrazoDias, setEditPrazoDias] = useState("");
  const [editPrioridade, setEditPrioridade] = useState("");
  const [modoAvancado, setModoAvancado] = useState(false);
  const [editJson, setEditJson] = useState("");

  const prioridades = useMemo(
    () => [
      { value: "alta", label: "Alta" },
      { value: "media", label: "Média" },
      { value: "baixa", label: "Baixa" },
    ],
    []
  );

  function clearFlash() {
    setErro("");
    setOk("");
  }

  async function loadRegras() {
    if (!mun) return setRegras([]);
    try {
      setLoading(true);
      clearFlash();
      const qs = new URLSearchParams();
      qs.set("municipio_id", String(mun));
      if (uni) qs.set("unidade_id", String(uni));
      qs.set("include_inativas", includeInativas ? "true" : "false");

      const r = await apiFetch(`${apiBase}/cras/automacoes/regras?${qs.toString()}`);
      const j = await r.json().catch(() => null);
      if (!r.ok) throw new Error(j?.detail || `Falha (HTTP ${r.status})`);
      setRegras(Array.isArray(j) ? j : []);
    } catch (e) {
      setErro(String(e?.message || e));
      setRegras([]);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadRegras();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [mun, uni, includeInativas]);

  async function seed() {
    if (!canEdit) return;
    if (!mun) return setErro("Selecione um município no topo.");
    try {
      setLoading(true);
      clearFlash();
      const qs = new URLSearchParams();
      qs.set("municipio_id", String(mun));
      if (seedParaUnidade && uni) qs.set("unidade_id", String(uni));
      const r = await apiFetch(`${apiBase}/cras/automacoes/seed?${qs.toString()}`, { method: "POST" });
      const j = await r.json().catch(() => null);
      if (!r.ok) throw new Error(j?.detail || `Falha (HTTP ${r.status})`);
      setOk(`Regras padrão carregadas (${(j?.regras || []).length}).`);
      await loadRegras();
    } catch (e) {
      setErro(String(e?.message || e));
    } finally {
      setLoading(false);
    }
  }

  async function executar({ dryRun = true, devidas = false } = {}) {
    if (!mun) return setErro("Selecione um município no topo.");
    try {
      setLoading(true);
      clearFlash();
      const qs = new URLSearchParams();
      qs.set("municipio_id", String(mun));
      if (uni) qs.set("unidade_id", String(uni));
      if (!devidas) qs.set("dry_run", dryRun ? "true" : "false");

      const path = devidas ? "/cras/automacoes/executar-devidas" : "/cras/automacoes/executar";
      const r = await apiFetch(`${apiBase}${path}?${qs.toString()}`, { method: "POST" });
      const j = await r.json().catch(() => null);
      if (!r.ok) throw new Error(j?.detail || `Falha (HTTP ${r.status})`);
      setExecucao(j);
      if (!dryRun && !devidas) {
        onChanged?.(); // atualiza badge de tarefas
        setOk("Execução concluída. Tarefas podem ter sido criadas.");
      } else if (devidas) {
        onChanged?.();
        setOk("Execução (devidas) concluída.");
      } else {
        setOk("Simulação concluída (dry-run).");
      }
    } catch (e) {
      setErro(String(e?.message || e));
    } finally {
      setLoading(false);
    }
  }

  async function atualizarRegra(regraId, payload) {
    if (!canEdit) return;
    try {
      setLoading(true);
      clearFlash();
      const r = await apiFetch(`${apiBase}/cras/automacoes/regras/${regraId}`, {
        method: "POST",
        body: JSON.stringify(payload || {}),
      });
      const j = await r.json().catch(() => null);
      if (!r.ok) throw new Error(j?.detail || `Falha (HTTP ${r.status})`);
      setRegras((prev) =>
        prev.map((x) => (x.id === regraId ? { ...x, ...j, parametros: j.parametros ?? x.parametros } : x))
      );
      setOk("Regra atualizada.");
    } catch (e) {
      setErro(String(e?.message || e));
    } finally {
      setLoading(false);
    }
  }

  function abrirEdicao(r) {
    setEditRule(r);
    setModoAvancado(false);
    setEditAtivo(!!r.ativo);
    setEditFreq(String(r.frequencia_minutos ?? 1440));
    setEditTitulo(r.titulo || "");
    setEditDesc(r.descricao || "");
    const p = r.parametros || {};
    setEditDiasSemMov(p.dias_sem_mov != null ? String(p.dias_sem_mov) : "");
    setEditPrazoDias(p.prazo_dias != null ? String(p.prazo_dias) : "");
    setEditPrioridade(p.prioridade != null ? String(p.prioridade) : "");
    setEditJson(JSON.stringify(p || {}, null, 2));
  }

  function closeEdicao() {
    setEditRule(null);
  }

  async function salvarEdicao() {
    if (!editRule) return;
    const base = (editRule.parametros && typeof editRule.parametros === "object") ? { ...editRule.parametros } : {};
    let params = { ...base };

    if (modoAvancado) {
      try {
        const parsed = JSON.parse(editJson || "{}");
        if (parsed && typeof parsed === "object") params = { ...params, ...parsed };
      } catch {
        return setErro("JSON inválido em parâmetros (modo avançado).");
      }
    }

    if (editDiasSemMov !== "") params.dias_sem_mov = Number(editDiasSemMov);
    if (editPrazoDias !== "") params.prazo_dias = Number(editPrazoDias);
    if (editPrioridade) params.prioridade = String(editPrioridade);

    const freq = Number(editFreq);
    const payload = {
      ativo: !!editAtivo,
      frequencia_minutos: Number.isFinite(freq) ? freq : 1440,
      titulo: editTitulo,
      descricao: editDesc,
      parametros: params,
    };

    await atualizarRegra(editRule.id, payload);
    closeEdicao();
  }

  const freqOptions = useMemo(
    () => [
      { value: 60, label: "A cada 1 hora" },
      { value: 180, label: "A cada 3 horas" },
      { value: 360, label: "A cada 6 horas" },
      { value: 720, label: "A cada 12 horas" },
      { value: 1440, label: "1x por dia" },
      { value: 2880, label: "A cada 2 dias" },
      { value: 10080, label: "1x por semana" },
    ],
    []
  );

  
  // --- GESTAO_VIEW_SWITCH_V1 ---
  if (viewKey === "criar") {
    return (
      <div className="layout-1col">
        <div className="card" style={{ padding: 12, borderRadius: 18 }}>
          <div style={{ fontWeight: 950, fontSize: 18 }}>Criar automação</div>
          <div className="texto-suave" style={{ marginTop: 6 }}>
            Crie ou ajuste regras que geram alertas e tarefas automaticamente (SLA). Para iniciar rápido, use “Criar/atualizar regras padrão”
            e depois ajuste conforme sua rotina.
          </div>
          <div style={{ display: "flex", gap: 10, flexWrap: "wrap", marginTop: 12 }}>
            <button className="btn btn-primario" type="button" onClick={() => onSetView("ativas")}>
              Ver regras ativas
            </button>
          </div>
        </div>
        <div className="card" style={{ padding: 12, borderRadius: 18 }}>
          <div style={{ fontWeight: 900 }}>Dica</div>
          <div className="texto-suave" style={{ marginTop: 6 }}>
            Fluxo recomendado: (1) carregar regras padrão, (2) simular (dry-run), (3) executar e acompanhar histórico.
          </div>
        </div>
      </div>
    );
  }

  if (viewKey === "historico") {
    return (
      <div className="layout-1col">
        <div className="card" style={{ padding: 12, borderRadius: 18 }}>
          <div style={{ fontWeight: 950, fontSize: 18 }}>Histórico</div>
          <div className="texto-suave" style={{ marginTop: 6 }}>
            Aqui você acompanha execuções e resultados. Use “Simular” e “Executar” na aba de Regras ativas para gerar uma execução e
            depois volte aqui para auditar.
          </div>
          <div style={{ display: "flex", gap: 10, flexWrap: "wrap", marginTop: 12 }}>
            <button className="btn btn-primario" type="button" onClick={() => onSetView("ativas")}>
              Ir para Regras ativas
            </button>
          </div>
        </div>

        {execucao ? (
          <div className="card" style={{ padding: 12, borderRadius: 18 }}>
            <div style={{ fontWeight: 900, marginBottom: 8 }}>Última execução (resumo)</div>
            <pre style={{ margin: 0, whiteSpace: "pre-wrap", fontSize: 12, lineHeight: 1.35 }}>
{JSON.stringify(execucao, null, 2)}
            </pre>
          </div>
        ) : (
          <div className="card" style={{ padding: 12, borderRadius: 18 }}>
            <div className="texto-suave">Ainda não há execução carregada nesta sessão.</div>
          </div>
        )}
      </div>
    );
  }

  if (viewKey === "relatorios") {
    return (
      <div className="layout-1col">
        <div className="card" style={{ padding: 12, borderRadius: 18 }}>
          <div style={{ fontWeight: 950, fontSize: 18 }}>Relatórios</div>
          <div className="texto-suave" style={{ marginTop: 6 }}>
            Consolide o impacto das automações: quantas tarefas/alertas foram gerados, quantas vencidas reduziram e quais rotinas precisaram de ajuste.
          </div>
          <div className="texto-suave" style={{ marginTop: 10 }}>
            Regras carregadas nesta unidade: <strong>{(regras || []).length}</strong>
          </div>
          <div style={{ display: "flex", gap: 10, flexWrap: "wrap", marginTop: 12 }}>
            <button className="btn btn-primario" type="button" onClick={() => onSetView("ativas")}>
              Ver regras ativas
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div style={{ display: "grid", gap: 12 }}>
      <div
        style={{
          padding: 12,
          borderRadius: 16,
          border: "1px solid rgba(2,6,23,.10)",
          background: "rgba(2,6,23,.02)",
          display: "flex",
          flexWrap: "wrap",
          alignItems: "center",
          justifyContent: "space-between",
          gap: 10,
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap" }}>
          <Chip tone="muted">Município: {mun || "—"}</Chip>
          <Chip tone="muted">Unidade: {uni || "—"}</Chip>
          {!canEdit ? <Chip tone="warn">Somente leitura</Chip> : <Chip tone="ok">Gestor</Chip>}
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap" }}>
          <label style={{ display: "inline-flex", alignItems: "center", gap: 8, fontSize: 13, fontWeight: 800, color: "rgba(2,6,23,.75)" }}>
            <input type="checkbox" checked={includeInativas} onChange={(e) => setIncludeInativas(e.target.checked)} />
            Incluir inativas
          </label>

          <label style={{ display: "inline-flex", alignItems: "center", gap: 8, fontSize: 13, fontWeight: 800, color: "rgba(2,6,23,.75)" }}>
            <input type="checkbox" checked={seedParaUnidade} onChange={(e) => setSeedParaUnidade(e.target.checked)} />
            Seed para esta unidade
          </label>

          <Button kind="soft" onClick={loadRegras} disabled={loading || !mun}>
            Recarregar
          </Button>
          <Button kind="soft" onClick={() => executar({ dryRun: true })} disabled={loading || !mun}>
            Simular (dry-run)
          </Button>
          <Button onClick={() => executar({ dryRun: false })} disabled={loading || !mun}>
            Executar agora
          </Button>
          <Button kind="soft" onClick={() => executar({ devidas: true })} disabled={loading || !mun}>
            Executar devidas
          </Button>
          <Button kind="soft" onClick={seed} disabled={loading || !mun || !canEdit}>
            Criar/atualizar regras padrão
          </Button>
        </div>
      </div>

      {erro ? (
        <div style={{ padding: 12, borderRadius: 14, border: "1px solid rgba(220,38,38,.25)", background: "rgba(220,38,38,.06)", color: "rgba(185,28,28,1)", fontWeight: 800 }}>
          {erro}
        </div>
      ) : null}

      {ok ? (
        <div style={{ padding: 12, borderRadius: 14, border: "1px solid rgba(16,185,129,.25)", background: "rgba(16,185,129,.06)", color: "rgba(5,150,105,1)", fontWeight: 800 }}>
          {ok}
        </div>
      ) : null}

      {execucao ? (
        <div style={{ padding: 12, borderRadius: 16, border: "1px solid rgba(2,6,23,.10)", background: "white" }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 10, flexWrap: "wrap" }}>
            <div style={{ fontWeight: 950 }}>Resultado da execução</div>
            <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
              <Chip tone="muted">Dry-run: {execucao.dry_run ? "sim" : "não"}</Chip>
              <Chip tone="muted">Regras: {execucao.total_regras ?? "—"}</Chip>
            </div>
          </div>

          <div style={{ marginTop: 10, display: "grid", gap: 8 }}>
            {(execucao.resultados || []).map((r) => (
              <div key={`${r.regra_id}-${r.execucao_id}`} style={{ padding: 10, borderRadius: 14, border: "1px solid rgba(2,6,23,.08)", background: "rgba(2,6,23,.02)" }}>
                <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 10, flexWrap: "wrap" }}>
                  <div style={{ fontWeight: 900 }}>{r.titulo || r.chave}</div>
                  <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                    <Chip tone={r.status === "ok" ? "ok" : "warn"}>{r.status || "—"}</Chip>
                    <Chip tone="muted">created: {r.resumo?.created ?? 0}</Chip>
                    <Chip tone="muted">skipped: {r.resumo?.skipped ?? 0}</Chip>
                  </div>
                </div>
                {r.resumo?.erro ? <div style={{ marginTop: 6, color: "rgba(185,28,28,1)", fontWeight: 800 }}>{r.resumo.erro}</div> : null}
              </div>
            ))}
          </div>
        </div>
      ) : null}

      <div style={{ display: "grid", gap: 12 }}>
        {loading && regras.length === 0 ? (
          <div style={{ padding: 14, color: "rgba(2,6,23,.65)", fontWeight: 800 }}>Carregando…</div>
        ) : null}

        {!loading && regras.length === 0 ? (
          <div style={{ padding: 14, border: "1px dashed rgba(2,6,23,.20)", borderRadius: 14, background: "rgba(2,6,23,.02)" }}>
            <div style={{ fontWeight: 950 }}>Nenhuma regra encontrada</div>
            <div style={{ marginTop: 6, color: "rgba(2,6,23,.65)" }}>
              Clique em <b>Criar/atualizar regras padrão</b> para carregar as regras iniciais.
            </div>
          </div>
        ) : null}

        {regras.map((r) => (
          <div key={r.id} style={{ padding: 14, borderRadius: 16, border: "1px solid rgba(2,6,23,.10)", background: "white" }}>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 10, flexWrap: "wrap" }}>
              <div style={{ display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap" }}>
                <div style={{ fontWeight: 950, fontSize: 14 }}>{r.titulo}</div>
                {r.ativo ? <Chip tone="ok">Ativa</Chip> : <Chip tone="warn">Inativa</Chip>}
                <Chip tone="muted">{r.chave}</Chip>
              </div>

              <div style={{ display: "flex", gap: 10, alignItems: "center", flexWrap: "wrap" }}>
                <div style={{ fontSize: 12, color: "rgba(2,6,23,.60)", fontWeight: 800 }}>
                  Última execução: {fmtDateTime(r.ultima_execucao_em)}
                </div>
                <Button kind="soft" onClick={() => abrirEdicao(r)} disabled={loading || !canEdit}>
                  Configurar
                </Button>
                <Button
                  kind="soft"
                  onClick={() => atualizarRegra(r.id, { ativo: !r.ativo })}
                  disabled={loading || !canEdit}
                >
                  {r.ativo ? "Desativar" : "Ativar"}
                </Button>
              </div>
            </div>

            {r.descricao ? <div style={{ marginTop: 6, color: "rgba(2,6,23,.70)" }}>{r.descricao}</div> : null}

            <div style={{ marginTop: 10, display: "grid", gridTemplateColumns: "1fr 280px", gap: 12, alignItems: "start" }}>
              <div style={{ borderRadius: 14, border: "1px solid rgba(2,6,23,.08)", background: "rgba(2,6,23,.02)", padding: 12 }}>
                <div style={{ fontWeight: 900, marginBottom: 8 }}>Parâmetros</div>
                <div style={{ display: "grid", gap: 6 }}>
                  {Object.keys(r.parametros || {}).length === 0 ? (
                    <div style={{ color: "rgba(2,6,23,.6)", fontWeight: 800 }}>—</div>
                  ) : (
                    Object.entries(r.parametros || {}).map(([k, v]) => (
                      <div key={k} style={{ display: "flex", justifyContent: "space-between", gap: 10 }}>
                        <div style={{ fontSize: 12, fontWeight: 900, color: "rgba(2,6,23,.75)" }}>{k}</div>
                        <div style={{ fontSize: 12, fontWeight: 800, color: "rgba(2,6,23,.70)" }}>{String(v)}</div>
                      </div>
                    ))
                  )}
                </div>
              </div>

              <div style={{ borderRadius: 14, border: "1px solid rgba(2,6,23,.08)", background: "rgba(2,6,23,.02)", padding: 12 }}>
                <div style={{ fontWeight: 900, marginBottom: 8 }}>Execução</div>
                <div style={{ display: "grid", gap: 10 }}>
                  <div>
                    <div style={{ fontSize: 12, fontWeight: 900, color: "rgba(2,6,23,.75)", marginBottom: 6 }}>Frequência</div>
                    <Select
                      value={String(r.frequencia_minutos ?? 1440)}
                      onChange={(v) => atualizarRegra(r.id, { frequencia_minutos: Number(v) })}
                      options={freqOptions.map((o) => ({ value: String(o.value), label: o.label }))}
                      style={{ fontWeight: 800 }}
                    />
                  </div>

                  <Button kind="soft" onClick={() => executar({ dryRun: true })} disabled={loading || !mun}>
                    Simular
                  </Button>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      <Modal
        open={!!editRule}
        title={editRule ? `Configurar regra — ${editRule.titulo}` : "Configurar regra"}
        onClose={closeEdicao}
        footer={
          <>
            <Button kind="soft" onClick={closeEdicao}>Cancelar</Button>
            <Button onClick={salvarEdicao} disabled={!canEdit}>Salvar</Button>
          </>
        }
      >
        {editRule ? (
          <div style={{ display: "grid", gap: 10 }}>
            <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
              <Chip tone="muted">{editRule.chave}</Chip>
              {editAtivo ? <Chip tone="ok">Ativa</Chip> : <Chip tone="warn">Inativa</Chip>}
            </div>

            <Row label="Ativa">
              <label style={{ display: "inline-flex", alignItems: "center", gap: 10, fontWeight: 900 }}>
                <input type="checkbox" checked={editAtivo} onChange={(e) => setEditAtivo(e.target.checked)} />
                Ativar regra
              </label>
            </Row>

            <Row label="Frequência" hint="Com que frequência o sistema deve checar e criar tarefas.">
              <Select
                value={editFreq}
                onChange={setEditFreq}
                options={freqOptions.map((o) => ({ value: String(o.value), label: o.label }))}
              />
            </Row>

            <Row label="Título">
              <Input value={editTitulo} onChange={setEditTitulo} />
            </Row>

            <Row label="Descrição">
              <Input value={editDesc} onChange={setEditDesc} />
            </Row>

            <Row label="Dias sem movimentação" hint="Aparece apenas em regras de caso sem atualização.">
              <Input value={editDiasSemMov} onChange={setEditDiasSemMov} type="number" placeholder="Ex.: 7" />
            </Row>

            <Row label="Prazo da tarefa" hint="Quantos dias para vencer a tarefa criada automaticamente.">
              <Input value={editPrazoDias} onChange={setEditPrazoDias} type="number" placeholder="Ex.: 2" />
            </Row>

            <Row label="Prioridade">
              <Select value={editPrioridade || "alta"} onChange={setEditPrioridade} options={prioridades} />
            </Row>

            <div style={{ marginTop: 10, display: "flex", alignItems: "center", justifyContent: "space-between", gap: 10, flexWrap: "wrap" }}>
              <div style={{ fontWeight: 950 }}>Modo avançado</div>
              <label style={{ display: "inline-flex", alignItems: "center", gap: 10, fontWeight: 900 }}>
                <input type="checkbox" checked={modoAvancado} onChange={(e) => setModoAvancado(e.target.checked)} />
                Editar JSON dos parâmetros
              </label>
            </div>

            {modoAvancado ? (
              <textarea
                value={editJson}
                onChange={(e) => setEditJson(e.target.value)}
                spellCheck={false}
                style={{
                  width: "100%",
                  minHeight: 180,
                  padding: 12,
                  borderRadius: 12,
                  border: "1px solid rgba(2,6,23,.12)",
                  fontFamily: "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace",
                  fontSize: 12,
                }}
              />
            ) : null}
          </div>
        ) : null}
      </Modal>
    </div>
  );
}
