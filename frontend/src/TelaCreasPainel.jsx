import React, { useEffect, useMemo, useState } from "react";
import { getCreasCases, seedCreasIfEmpty,
  setCreasSelectedCaseId, getCreasWorkflow } from "./domain/creasStore.js";
import { isGestor, isTecnico, scopeCases } from "./domain/acl.js";
import { getSuasOverdueForModulo } from "./domain/suasEncaminhamentosStore.js";
import { buildCreasCaseQueue } from "./domain/creasQueue.js";
import { buildCreasGestaoMetrics, toCsv } from "./domain/creasMetrics.js";

function daysSince(iso) {
  if (!iso) return null;
  const ms = Date.now() - new Date(iso).getTime();
  return Math.max(0, Math.floor(ms / (1000 * 60 * 60 * 24)));
}

// escopo por perfil (técnico: meus + sem responsável)

export default function TelaCreasPainel({ usuarioLogado, onNavigate }) {
  const [cases, setCases] = useState(() => seedCreasIfEmpty());
  const [filter, setFilter] = useState("minha_fila"); // minha_fila | pendencias | risco_alto | sem_movimento | novos | encerramentos

  function openQueue(queue) {
    onNavigate?.({ tab: "pendencias", queue: queue || {} });
  }
 // minha_fila | pendencias | risco_alto | sem_movimento | novos | encerramentos

  useEffect(() => {
    const onStorage = () => setCases(getCreasCases());
    window.addEventListener("storage", onStorage);
    return () => window.removeEventListener("storage", onStorage);
  }, []);

  const scopedCases = useMemo(() => scopeCases(cases, usuarioLogado), [cases, usuarioLogado]);
  const gestor = useMemo(() => isGestor(usuarioLogado), [usuarioLogado]);
  const workflow = useMemo(() => getCreasWorkflow(), [usuarioLogado]);
  const gestaoMetrics = useMemo(() => (gestor ? buildCreasGestaoMetrics({ cases: scopedCases, workflow }) : null), [gestor, scopedCases, workflow]);

  const tecnico = useMemo(() => isTecnico(usuarioLogado), [usuarioLogado]);

  // ✅ Atrasados SUAS (entre equipamentos) — prazo vencido
  const suasOverdue = useMemo(() => getSuasOverdueForModulo("CREAS"), [cases]);
  const suasIn = useMemo(() => (suasOverdue || []).filter((x) => String(x?.destino_modulo || "").toUpperCase() === "CREAS"), [suasOverdue]);
  const suasOut = useMemo(() => (suasOverdue || []).filter((x) => String(x?.origem_modulo || "").toUpperCase() === "CREAS"), [suasOverdue]);

  const kpis = useMemo(() => {
    const ativos = (scopedCases || []).filter((c) => c.status === "ativo");
    const riscoAlto = ativos.filter((c) => c.risco === "alto");
    const semMov = ativos.filter((c) => {
      const d = daysSince(c.ultimo_registro_em || c.criado_em) || 0;
      const limite = c.risco === "alto" ? 7 : 14;
      return d >= limite;
    });
    const pend = ativos.filter((c) => {
      if (!c.proximo_passo_em) return false;
      return new Date(c.proximo_passo_em) <= new Date();
    });
    const encerr = ativos.filter((c) => String(c?.encerramento_status || "").toLowerCase() === "solicitado");

    return {
      ativos: ativos.length,
      riscoAlto: riscoAlto.length,
      pendencias: pend.length,
      semMovimento: semMov.length,
      encerramentos: encerr.length,
    };
  }, [scopedCases]);

  const filaTop = useMemo(() => {
    const ativos = (scopedCases || []).filter((c) => c.status === "ativo");
    return buildCreasCaseQueue(ativos, { gestor }).slice(0, 5);
  }, [scopedCases, gestor]);


  const lista = useMemo(() => {
    const ativos = (scopedCases || []).filter((c) => c.status === "ativo");
    if (filter === "encerramentos") {
      return ativos.filter((c) => String(c?.encerramento_status || "").toLowerCase() === "solicitado");
    }
    if (filter === "risco_alto") return ativos.filter((c) => c.risco === "alto");
    if (filter === "sem_movimento")
      return ativos.filter((c) => {
        const d = daysSince(c.ultimo_registro_em || c.criado_em) || 0;
        const limite = c.risco === "alto" ? 7 : 14;
        return d >= limite;
      });
    if (filter === "novos") {
      return ativos.slice().sort((a, b) => new Date(b.criado_em) - new Date(a.criado_em));
    }
    if (filter === "pendencias") {
      return ativos.filter((c) => c.proximo_passo_em && new Date(c.proximo_passo_em) <= new Date());
    }
    return ativos;
  }, [scopedCases, filter]);

  function downloadCsv(filename, csvText) {
    try {
      const blob = new Blob([csvText], { type: "text/csv;charset=utf-8;" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch {}
  }

  const chip = (key, label) => (
    <button type="button" className={"app-tab" + (filter === key ? " app-tab-active" : "")} onClick={() => setFilter(key)}>
      {label}
    </button>
  );

  return (
    <div className="layout-1col">
      <div className="card">
        <div className="card-header-row">
          <div>
            <div style={{ fontSize: 18, fontWeight: 950 }}>Minha fila (CREAS)</div>
            <div className="texto-suave">Clique no caso para abrir. Use os chips para filtrar.</div>
          </div>

          <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
            <button className="btn btn-primario" type="button" onClick={() => onNavigate?.({ tab: "novo" })}>
              + Novo caso
            </button>
            <button className="btn btn-secundario" type="button" onClick={() => onNavigate?.({ tab: "casos" })}>
              Abrir casos
            </button>
          </div>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(4, minmax(0, 1fr))", gap: 12 }}>
          <div className="card" style={{ padding: 14, boxShadow: "none", border: "1px solid rgba(2,6,23,.06)" }}>
            <div className="texto-suave">Ativos</div>
            <div style={{ fontSize: 28, fontWeight: 950 }}>{kpis.ativos}</div>
          </div>
          <div className="card" style={{ padding: 14, boxShadow: "none", border: "1px solid rgba(2,6,23,.06)" }}>
            <div className="texto-suave">Risco alto</div>
            <div style={{ fontSize: 28, fontWeight: 950 }}>{kpis.riscoAlto}</div>
          </div>
          <div className="card" style={{ padding: 14, boxShadow: "none", border: "1px solid rgba(2,6,23,.06)" }}>
            <div className="texto-suave">Pendências</div>
            <div style={{ fontSize: 28, fontWeight: 950 }}>{kpis.pendencias}</div>
          </div>
          <div className="card" style={{ padding: 14, boxShadow: "none", border: "1px solid rgba(2,6,23,.06)" }}>
            <div className="texto-suave">Sem movimento</div>
            <div style={{ fontSize: 28, fontWeight: 950 }}>{kpis.semMovimento}</div>
          </div>
        </div>

        {gestor && kpis.encerramentos > 0 ? (
          <div
            className="card"
            style={{
              marginTop: 12,
              padding: 14,
              boxShadow: "none",
              border: "1px solid rgba(59,130,246,.25)",
              background: "rgba(59,130,246,.06)",
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", gap: 12, flexWrap: "wrap", alignItems: "center" }}>
              <div>
                <div style={{ fontWeight: 950 }}>⏳ Encerramentos pendentes</div>
                <div className="texto-suave">Casos com encerramento solicitado aguardando sua aprovação.</div>
              </div>
              <div style={{ display: "flex", gap: 10, flexWrap: "wrap", alignItems: "center" }}>
                <div className="texto-suave" style={{ fontWeight: 950 }}>
                  Total: <b>{kpis.encerramentos}</b>
                </div>
                <button className="btn btn-primario" type="button" onClick={() => setFilter("encerramentos")}>
                  Ver para aprovar
                </button>
                <button className="btn btn-secundario" type="button" onClick={() => onNavigate?.({ tab: "pendencias" })}>
                  Abrir Pendências
                </button>
              </div>
            </div>
          </div>
        ) : null}

        {(gestor || tecnico) && (suasOverdue || []).length ? (
          <div
            className="card"
            style={{
              marginTop: 12,
              padding: 14,
              boxShadow: "none",
              border: "1px solid rgba(239, 68, 68, .25)",
              background: "rgba(239, 68, 68, 0.06)",
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", gap: 12, flexWrap: "wrap", alignItems: "center" }}>
              <div>
                <div style={{ fontWeight: 950 }}>⚠️ Atrasados (SUAS)</div>
                <div className="texto-suave">Encaminhamentos internos com prazo vencido (CRAS/CREAS/PopRua).</div>
                <div className="texto-suave" style={{ marginTop: 6 }}>
                  Recebidos: <b>{suasIn.length}</b> · Enviados: <b>{suasOut.length}</b>
                </div>
              </div>

              <div style={{ display: "flex", gap: 10, flexWrap: "wrap", alignItems: "center" }}>
                {suasIn.length ? (
                  <button
                    className="btn btn-primario"
                    type="button"
                    onClick={() => {
                      try {
                        localStorage.setItem("suas_nav_modulo", "CREAS");
                        localStorage.setItem("suas_nav_view", "inbox");
                        if (suasIn[0]?.id) localStorage.setItem("suas_nav_selected_id", String(suasIn[0].id));
                      } catch {}
                      onNavigate?.({ tab: "rede" });
                    }}
                  >
                    Abrir Recebidos
                  </button>
                ) : null}

                {suasOut.length ? (
                  <button
                    className="btn btn-primario"
                    type="button"
                    onClick={() => {
                      try {
                        localStorage.setItem("suas_nav_modulo", "CREAS");
                        localStorage.setItem("suas_nav_view", "outbox");
                        if (suasOut[0]?.id) localStorage.setItem("suas_nav_selected_id", String(suasOut[0].id));
                      } catch {}
                      onNavigate?.({ tab: "rede" });
                    }}
                  >
                    Abrir Enviados
                  </button>
                ) : null}

                <button className="btn btn-secundario" type="button" onClick={() => onNavigate?.({ tab: "pendencias" })}>
                  Ver Pendências
                </button>
              </div>
            </div>
          </div>
        ) : null}
      </div>

      {filaTop.length ? (
        <div
          className="card"
          style={{
            marginTop: 12,
            padding: 14,
            boxShadow: "none",
            border: "1px solid rgba(99,102,241,.22)",
            background: "rgba(99,102,241,.06)",
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", gap: 12, flexWrap: "wrap", alignItems: "center" }}>
            <div>
              <div style={{ fontWeight: 950 }}>⭐ Top prioridades (fila inteligente)</div>
              <div className="texto-suave">Os 5 itens mais prioritários do dia (score automático).</div>
            </div>
            <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
              <button className="btn btn-primario" type="button" onClick={() => onNavigate?.({ tab: "pendencias" })}>
                Abrir fila inteligente
              </button>
            </div>
          </div>

          <div style={{ display: "grid", gap: 8, marginTop: 10 }}>
            {filaTop.map((it) => (
              <button
                key={String(it.casoId)}
                type="button"
                className="card"
                style={{
                  textAlign: "left",
                  padding: 12,
                  boxShadow: "none",
                  border: "1px solid rgba(2,6,23,.06)",
                  background: "rgba(255,255,255,.92)",
                }}
                onClick={() => {
                  try {
                    setCreasSelectedCaseId(String(it.casoId));
                  } catch {}
                  onNavigate?.({ tab: "casos" });
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", gap: 10, flexWrap: "wrap", alignItems: "center" }}>
                  <div>
                    <div style={{ fontWeight: 950 }}>{it.title}</div>
                    <div className="texto-suave">{it.subtitle}</div>
                  </div>
                  <div className="texto-suave" style={{ fontWeight: 950 }}>Score: {Math.round(it.score || 0)}</div>
                </div>
              </button>
            ))}
          </div>
        </div>
      ) : null}


      <div className="card">
        <div className="app-tabs" style={{ padding: 0, marginBottom: 10 }}>
          {chip("minha_fila", "Minha fila")}
          {chip("pendencias", "Pendências")}
          {chip("risco_alto", "Risco alto")}
          {chip("sem_movimento", "Sem movimento")}
          {chip("novos", "Novos")}
          {gestor && kpis.encerramentos > 0 ? chip("encerramentos", `Encerramentos (${kpis.encerramentos})`) : null}
        </div>

        {lista.length ? (
          <div style={{ display: "grid", gap: 10 }}>
            {lista.map((c) => {
              const dias = daysSince(c.ultimo_registro_em || c.criado_em);
              const resp = c?.responsavel_nome || null;
              const semResp = !c?.responsavel_id;

              const encSt = String(c?.encerramento_status || "").toLowerCase();
              const encTag = encSt === "solicitado" ? " · Encerramento solicitado" : "";

              return (
                <button
                  key={c.id}
                  type="button"
                  className="btn"
                  style={{ textAlign: "left", justifyContent: "space-between", display: "flex" }}
                  onClick={() => {
                    try {
                      setCreasSelectedCaseId(String(c.id));
                    } catch {}
                    onNavigate?.({ tab: "casos" });
                  }}
                >
                  <div>
                    <div style={{ fontWeight: 950 }}>{c.nome}</div>
                    <div className="texto-suave">
                      Risco <b>{c.risco}</b> · Último registro há <b>{dias ?? 0}d</b> · Próximo passo: <b>{c.proximo_passo || "—"}</b>
                      {semResp ? " · Sem responsável" : resp ? ` · Resp.: ${resp}` : ""}
                      {encTag}
                    </div>
                  </div>
                  <div style={{ fontWeight: 900, opacity: 0.75 }}>Abrir →</div>
                </button>
              );
            })}
          </div>
        ) : (
          <div className="texto-suave">Sem casos para este filtro.</div>
        )}
      </div>
      {gestaoMetrics ? (
        <div className="card">
          <div className="card-header-row">
            <div>
              <div style={{ fontSize: 16, fontWeight: 950 }}>Painel da coordenação</div>
              <div className="texto-suave">
                Indicadores por etapa e por técnico (transparente, sem IA). Escopo: Município/Unidade selecionados no topo.
              </div>
            </div>

            <div style={{ display: "flex", gap: 10, flexWrap: "wrap", justifyContent: "flex-end" }}>
              <button
                className="btn btn-secundario"
                type="button"
                onClick={() => {
                  const rows = (gestaoMetrics?.ranking || []).map((r) => ({
                    tecnico: r.nome,
                    total: r.total,
                    risco_alto: r.alto,
                    prox_vencido: r.prox_venc,
                    sem_movimento: r.sem_mov,
                    score: r.score,
                  }));
                  downloadCsv("creas_ranking_tecnicos.csv", toCsv(rows, ["tecnico", "total", "risco_alto", "prox_vencido", "sem_movimento", "score"]));
                }}
              >
                Exportar ranking (CSV)
              </button>

              <button
                className="btn btn-secundario"
                type="button"
                onClick={() => {
                  const rows = (gestaoMetrics?.etapas || []).map((e) => ({
                    etapa_codigo: e.codigo,
                    etapa_nome: e.nome,
                    total: e.total,
                    sla_dias: e.sla_dias ?? "",
                    vencidos: e.vencidos,
                    pct_vencidos: e.pct_vencidos,
                    media_dias_na_etapa: e.media_dias ?? "",
                  }));
                  downloadCsv(
                    "creas_etapas_gargalos.csv",
                    toCsv(rows, [
                      "etapa_codigo",
                      "etapa_nome",
                      "total",
                      "sla_dias",
                      "vencidos",
                      "pct_vencidos",
                      "media_dias_na_etapa",
                    ])
                  );
                }}
              >
                Exportar etapas (CSV)
              </button>
            </div>
          </div>

          <div style={{ display: "grid", gap: 12 }}>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: 12 }}>
              <div className="card" style={{ padding: 12, boxShadow: "none", border: "1px solid rgba(2,6,23,.06)", cursor: "pointer" }} onClick={() => openQueue({ filtro: "casos" })}>
                <div className="texto-suave">Casos ativos</div>
                <div style={{ fontSize: 28, fontWeight: 950 }}>{gestaoMetrics.totals.ativos}</div>
              </div>

              <div className="card" style={{ padding: 12, boxShadow: "none", border: "1px solid rgba(2,6,23,.06)", cursor: "pointer" }} onClick={() => openQueue({ filtro: "casos", drill: { risco: "alto" } })}>
                <div className="texto-suave">Risco alto</div>
                <div style={{ fontSize: 28, fontWeight: 950 }}>{gestaoMetrics.byRisco.alto}</div>
              </div>

              <div className="card" style={{ padding: 12, boxShadow: "none", border: "1px solid rgba(2,6,23,.06)", cursor: "pointer" }} onClick={() => openQueue({ filtro: "prox" })}>
                <div className="texto-suave">Próximo passo vencido</div>
                <div style={{ fontSize: 28, fontWeight: 950 }}>{gestaoMetrics.totals.prox_vencidos}</div>
              </div>

              <div className="card" style={{ padding: 12, boxShadow: "none", border: "1px solid rgba(2,6,23,.06)" }}>
                <div className="texto-suave">Sem movimento (≥ {gestaoMetrics.semMovDias} dias)</div>
                <div style={{ fontSize: 28, fontWeight: 950 }}>{gestaoMetrics.totals.sem_movimento}</div>
              </div>
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(360px, 1fr))", gap: 12, alignItems: "start" }}>
              <div className="card" style={{ padding: 12, boxShadow: "none", border: "1px solid rgba(2,6,23,.06)" }}>
                <div style={{ fontWeight: 950, marginBottom: 8 }}>Gargalos do workflow</div>
                {gestaoMetrics.gargalos?.length ? (
                  <div style={{ display: "grid", gap: 8 }}>
                    {gestaoMetrics.gargalos.map((g) => (
                      <div key={g.codigo} style={{ display: "flex", justifyContent: "space-between", gap: 12, cursor: "pointer" }} onClick={() => openQueue({ filtro: "sla", drill: { etapa: g.codigo } })}>
                        <div>
                          <div style={{ fontWeight: 900 }}>{g.nome}</div>
                          <div className="texto-suave">
                            Total: <b>{g.total}</b> · SLA: <b>{g.sla_dias ?? "—"}d</b> · Média: <b>{g.media_dias ?? "—"}d</b>
                          </div>
                        </div>
                        <div style={{ fontWeight: 950 }}>{g.pct_vencidos}%</div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="texto-suave">Sem gargalos detectados (ou SLA não configurado).</div>
                )}
              </div>

              <div className="card" style={{ padding: 12, boxShadow: "none", border: "1px solid rgba(2,6,23,.06)" }}>
                <div style={{ fontWeight: 950, marginBottom: 8 }}>Ranking por técnico</div>

                <div style={{ overflowX: "auto" }}>
                  <table style={{ width: "100%", borderCollapse: "collapse" }}>
                    <thead>
                      <tr style={{ textAlign: "left" }}>
                        <th style={{ padding: "8px 6px", borderBottom: "1px solid rgba(2,6,23,.08)" }}>Técnico</th>
                        <th style={{ padding: "8px 6px", borderBottom: "1px solid rgba(2,6,23,.08)" }}>Total</th>
                        <th style={{ padding: "8px 6px", borderBottom: "1px solid rgba(2,6,23,.08)" }}>Risco alto</th>
                        <th style={{ padding: "8px 6px", borderBottom: "1px solid rgba(2,6,23,.08)" }}>Vencidos</th>
                        <th style={{ padding: "8px 6px", borderBottom: "1px solid rgba(2,6,23,.08)" }}>Sem mov.</th>
                        <th style={{ padding: "8px 6px", borderBottom: "1px solid rgba(2,6,23,.08)" }}>Score</th>
                      </tr>
                    </thead>
                    <tbody>
                      {(gestaoMetrics.ranking || []).slice(0, 10).map((r) => (
                        <tr key={r.nome} style={{ cursor: "pointer" }} onClick={() => openQueue({ filtro: "casos", drill: { tecnico: r.nome } })}>
                          <td style={{ padding: "8px 6px", borderBottom: "1px solid rgba(2,6,23,.06)", fontWeight: 900 }}>{r.nome}</td>
                          <td style={{ padding: "8px 6px", borderBottom: "1px solid rgba(2,6,23,.06)" }}>{r.total}</td>
                          <td style={{ padding: "8px 6px", borderBottom: "1px solid rgba(2,6,23,.06)" }}>{r.alto}</td>
                          <td style={{ padding: "8px 6px", borderBottom: "1px solid rgba(2,6,23,.06)" }}>{r.prox_venc}</td>
                          <td style={{ padding: "8px 6px", borderBottom: "1px solid rgba(2,6,23,.06)" }}>{r.sem_mov}</td>
                          <td style={{ padding: "8px 6px", borderBottom: "1px solid rgba(2,6,23,.06)", fontWeight: 950 }}>{r.score}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                <div className="texto-suave" style={{ marginTop: 8 }}>
                  Score = Total + (Risco alto×2) + (Sem movimento×2) + (Próximo passo vencido×3).
                </div>
              </div>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
