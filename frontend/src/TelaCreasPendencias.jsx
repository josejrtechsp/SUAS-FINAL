import React, { useEffect, useMemo, useState } from "react";
import { getCreasCases, seedCreasIfEmpty, setCreasSelectedCaseId } from "./domain/creasStore.js";
import { isGestor, isTecnico, scopeCases } from "./domain/acl.js";
import { getSuasOverdueForModulo, inferSuasActionForModulo } from "./domain/suasEncaminhamentosStore.js";
import { buildCreasCaseQueue } from "./domain/creasQueue.js";

function daysOverdueDateStr(dateStr) {
  if (!dateStr) return 0;
  const t = new Date(String(dateStr) + "T23:59:59").getTime();
  if (!Number.isFinite(t)) return 0;
  const diff = Date.now() - t;
  return diff <= 0 ? 0 : Math.floor(diff / (1000 * 60 * 60 * 24));
}

function labelSuasAction(action) {
  if (action === "receber") return "SUAS: Receber encaminhamento";
  if (action === "devolutiva") return "SUAS: Enviar devolutiva";
  if (action === "cobrar") return "SUAS: Cobrar retorno";
  if (action === "concluir") return "SUAS: Concluir";
  return "SUAS: Acompanhar";
}

function baseScoreSuas(action) {
  if (action === "receber") return 90;
  if (action === "devolutiva") return 82;
  if (action === "cobrar") return 74;
  if (action === "concluir") return 66;
  return 70;
}

function chip(key, label, active, onClick) {
  return (
    <button type="button" className={"app-tab" + (active ? " app-tab-active" : "")} onClick={onClick}>
      {label}
    </button>
  );
}

export default function TelaCreasPendencias({ usuarioLogado, onNavigate, queueNav }) {
  const [cases, setCases] = useState(() => seedCreasIfEmpty());
  const [filtro, setFiltro] = useState("tudo");
  const [q, setQ] = useState("");
  const [drillEtapa, setDrillEtapa] = useState(null);
  const [drillTecnico, setDrillTecnico] = useState(null);
  const [drillRisco, setDrillRisco] = useState(null);
  const [drillOnlySla, setDrillOnlySla] = useState(false);
  const [lastNavToken, setLastNavToken] = useState(0);

  useEffect(() => {
    const onStorage = () => setCases(getCreasCases());
    window.addEventListener("storage", onStorage);
    return () => window.removeEventListener("storage", onStorage);
  }, []);

  // Navegação "drill-down" (vinda do Painel): aplica filtro/etapa/técnico/risco e abre a fila já filtrada.
  useEffect(() => {
    const t = queueNav?.token || 0;
    if (!t || t === lastNavToken) return;

    try {
      if (queueNav?.filtro) setFiltro(String(queueNav.filtro));
      if (queueNav?.q != null) setQ(String(queueNav.q || ""));
      const d = queueNav?.drill || {};
      if (d?.etapa != null) setDrillEtapa(d.etapa ? String(d.etapa) : null);
      if (d?.tecnico != null) setDrillTecnico(d.tecnico ? String(d.tecnico) : null);
      if (d?.risco != null) setDrillRisco(d.risco ? String(d.risco).toLowerCase() : null);
      if (typeof d?.onlySla === "boolean") setDrillOnlySla(Boolean(d.onlySla));
    } catch {}

    setLastNavToken(t);
    // garante que o usuário veja o topo da fila
    try { window.scrollTo({ top: 0, behavior: "smooth" }); } catch {}
  }, [queueNav, lastNavToken]);


  const scopedCases = useMemo(() => scopeCases(cases, usuarioLogado), [cases, usuarioLogado]);
  const gestor = useMemo(() => isGestor(usuarioLogado), [usuarioLogado]);

  // 1) Casos (fila inteligente)
  const filaCasos = useMemo(() => buildCreasCaseQueue(scopedCases, { gestor }), [scopedCases, gestor]);

  // 2) Pendências SUAS (unificadas na fila)
  const filaSuas = useMemo(() => {
    const podeVerSuas = isGestor(usuarioLogado) || isTecnico(usuarioLogado);
    if (!podeVerSuas) return [];

    const overdue = getSuasOverdueForModulo("CREAS");
    const out = [];

    for (const it of overdue || []) {
      const action = inferSuasActionForModulo(it, "CREAS");
      const isInbox = String(it?.destino_modulo || "").toUpperCase() === "CREAS";
      const view = isInbox ? "inbox" : "outbox";
      const pessoa = it?.pessoa_id ? `Pessoa #${it.pessoa_id}` : "Pessoa";
      const motivo = it?.motivo || it?.assunto || "Encaminhamento";
      const atraso = it?.prazo_retorno ? daysOverdueDateStr(it.prazo_retorno) : 0;

      const base = baseScoreSuas(action);
      const score = base + Math.min(40, atraso * 4);

      const flags = { suas: true };
      if (action === "receber") flags.suas_receber = true;
      if (action === "devolutiva") flags.suas_devolutiva = true;
      if (action === "cobrar") flags.suas_cobrar = true;

      out.push({
        kind: "suas",
        score,
        title: labelSuasAction(action),
        subtitle: `${pessoa} · ${isInbox ? "Recebidos" : "Enviados"} · ${motivo}${it?.prazo_retorno ? ` (prazo ${it.prazo_retorno})` : ""}`,
        tags: ["SUAS", isInbox ? "INBOX" : "OUTBOX", atraso ? `+${atraso}d` : ""].filter(Boolean),
        flags,
        reasons: [
          {
            label: "Prazo vencido",
            detail: atraso ? `Atraso: +${atraso} dia(s)` : "Vencido/hoje",
            weight: score,
          },
        ],
        suasId: it?.id,
        suasView: view,
      });
    }

    return out;
  }, [usuarioLogado, cases]);

  // 3) Fila unificada
  const fila = useMemo(() => {
    const all = [...(filaSuas || []), ...(filaCasos || [])];
    all.sort((a, b) => (b?.score || 0) - (a?.score || 0));
    return all;
  }, [filaSuas, filaCasos]);

  const filtrada = useMemo(() => {
    const s = String(q || "").trim().toLowerCase();

    return (fila || []).filter((it) => {
      // texto
      if (s) {
        const txt = `${it?.title || ""} ${it?.subtitle || ""}`.toLowerCase();
        if (!txt.includes(s)) return false;
      }

      // filtros
      if (filtro === "casos") return it.kind === "case";
      if (filtro === "suas") return it.kind === "suas";
      if (filtro === "alta") return (it?.score || 0) >= 80;

      // drill-down (painel): etapa/técnico/risco/SLA
      if (it.kind === "suas" && (drillEtapa || drillTecnico || drillRisco || drillOnlySla)) return false;
      if (it.kind === "case") {
        if (drillOnlySla && !(it?.flags || {}).sla_etapa) return false;
        if (drillEtapa && String(it?.etapaCodigo || "") !== String(drillEtapa)) return false;
        if (drillTecnico) {
          const rn = String(it?.responsavelNome || "");
          if (!rn || rn.toLowerCase() !== String(drillTecnico).toLowerCase()) return false;
        }
        if (drillRisco) {
          const rr = String(it?.risco || "");
          if (rr.toLowerCase() !== String(drillRisco).toLowerCase()) return false;
        }
      }


      if (it.kind === "case") {
        const f = it?.flags || {};
        if (filtro === "sla") return Boolean(f.sla_etapa);
        if (filtro === "prox") return Boolean(f.proximo_passo);
        if (filtro === "rede") return Boolean(f.rede);
        if (filtro === "sem_resp") return Boolean(f.sem_responsavel);
        if (filtro === "encerr") return Boolean(f.encerramento);
        if (filtro === "sem_mov") return Boolean(f.sem_movimento);
      }

      if (it.kind === "suas") {
        const f = it?.flags || {};
        if (filtro === "suas_receber") return Boolean(f.suas_receber);
        if (filtro === "suas_devolutiva") return Boolean(f.suas_devolutiva);
      }

      return filtro === "tudo";
    });
  }, [fila, filtro, q]);

  function openItem(it) {
    if (!it) return;

    // SUAS
    if (it.kind === "suas") {
      try {
        localStorage.setItem("suas_nav_modulo", "CREAS");
        localStorage.setItem("suas_nav_view", it.suasView || "inbox");
        if (it.suasId != null) localStorage.setItem("suas_nav_selected_id", String(it.suasId));
      } catch {}
      onNavigate?.({ tab: "rede" });
      return;
    }

    // Caso CREAS
    try {
      setCreasSelectedCaseId(String(it.casoId));
    } catch {}
    onNavigate?.({ tab: "casos" });
  }

  return (
    <div className="layout-1col">
      <div className="card">
        <div className="card-header-row">
          <div>
            <div style={{ fontWeight: 950, fontSize: 18 }}>Fila inteligente (CREAS)</div>
            <div className="texto-suave">Prioridade automática por risco, SLA, atrasos e pendências (casos + SUAS).</div>
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

        <div style={{ display: "flex", gap: 10, alignItems: "center", flexWrap: "wrap" }}>
          <div className="app-tabs" style={{ padding: 0, margin: 0 }}>
            {chip("tudo", "Tudo", filtro === "tudo", () => setFiltro("tudo"))}
            {chip("alta", "Alta prioridade", filtro === "alta", () => setFiltro("alta"))}
            {chip("casos", "Casos", filtro === "casos", () => setFiltro("casos"))}
            {chip("sla", "SLA vencido", filtro === "sla", () => setFiltro("sla"))}
            {chip("prox", "Próximo passo", filtro === "prox", () => setFiltro("prox"))}
            {chip("rede", "Rede", filtro === "rede", () => setFiltro("rede"))}
            {chip("sem_resp", "Sem responsável", filtro === "sem_resp", () => setFiltro("sem_resp"))}
            {gestor ? chip("encerr", "Encerramentos", filtro === "encerr", () => setFiltro("encerr")) : null}
            {chip("suas", "SUAS", filtro === "suas", () => setFiltro("suas"))}
          </div>

          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Buscar na fila..."
            style={{
              marginLeft: "auto",
              minWidth: 220,
              padding: "10px 12px",
              borderRadius: 12,
              border: "1px solid rgba(2,6,23,.10)",
              outline: "none",
            }}
          />

        {(drillEtapa || drillTecnico || drillRisco || drillOnlySla) ? (
          <div style={{ marginTop: 10, display: "flex", gap: 8, flexWrap: "wrap", alignItems: "center" }}>
            <div className="texto-suave" style={{ fontWeight: 800 }}>Filtros aplicados:</div>

            {drillEtapa ? (
              <span className="chip chip-on" style={{ cursor: "pointer" }} onClick={() => setDrillEtapa(null)} title="Clique para remover">
                Etapa: {String(drillEtapa)}
              </span>
            ) : null}

            {drillTecnico ? (
              <span className="chip chip-on" style={{ cursor: "pointer" }} onClick={() => setDrillTecnico(null)} title="Clique para remover">
                Técnico: {String(drillTecnico)}
              </span>
            ) : null}

            {drillRisco ? (
              <span className="chip chip-on" style={{ cursor: "pointer" }} onClick={() => setDrillRisco(null)} title="Clique para remover">
                Risco: {String(drillRisco)}
              </span>
            ) : null}

            {drillOnlySla ? (
              <span className="chip chip-on" style={{ cursor: "pointer" }} onClick={() => setDrillOnlySla(false)} title="Clique para remover">
                Apenas SLA
              </span>
            ) : null}

            <button className="btn btn-secundario btn-secundario-mini" type="button" onClick={() => { setDrillEtapa(null); setDrillTecnico(null); setDrillRisco(null); setDrillOnlySla(false); }}>
              Limpar filtros
            </button>
          </div>
        ) : null}


        </div>

        <details style={{ marginTop: 10 }}>
          <summary className="texto-suave" style={{ cursor: "pointer" }}>
            Como a prioridade é calculada
          </summary>
          <div className="texto-suave" style={{ marginTop: 8, lineHeight: 1.45 }}>
            A ordem é baseada em uma pontuação (score) determinística: risco, SLA da etapa, próximo passo vencido,
            rede sem retorno, sem movimento, sem responsável e encerramentos pendentes (para gestor). Isso evita
            "fila no grito" e deixa a coordenação enxergar o que queima hoje.
          </div>
        </details>

        <div style={{ marginTop: 12 }}>
          {filtrada.length ? (
            <div style={{ display: "grid", gap: 10 }}>
              {filtrada.map((it, idx) => (
                <div
                  key={`${it.kind}_${it.casoId || it.suasId || idx}`}
                  className="card"
                  style={{
                    padding: 12,
                    boxShadow: "none",
                    border: "1px solid rgba(2,6,23,.06)",
                    background: it.kind === "suas" ? "rgba(239, 68, 68, 0.06)" : idx < 3 ? "rgba(99, 102, 241, 0.06)" : undefined,
                  }}
                >
                  <div style={{ display: "flex", justifyContent: "space-between", gap: 12, alignItems: "flex-start" }}>
                    <div style={{ minWidth: 0 }}>
                      <div style={{ display: "flex", gap: 10, alignItems: "center", flexWrap: "wrap" }}>
                        <div
                          style={{
                            fontWeight: 950,
                            padding: "4px 10px",
                            borderRadius: 999,
                            border: "1px solid rgba(2,6,23,.12)",
                            background: "rgba(255,255,255,.9)",
                          }}
                        >
                          Score {Math.round(it.score || 0)}
                        </div>

                        <div style={{ fontWeight: 950, minWidth: 0 }}>{it.title}</div>
                      </div>

                      <div className="texto-suave" style={{ marginTop: 4 }}>
                        {it.subtitle}
                      </div>

                      {Array.isArray(it.tags) && it.tags.length ? (
                        <div style={{ display: "flex", gap: 6, flexWrap: "wrap", marginTop: 8 }}>
                          {it.tags.slice(0, 6).map((t, i) => (
                            <span
                              key={i}
                              style={{
                                fontSize: 12,
                                padding: "3px 8px",
                                borderRadius: 999,
                                border: "1px solid rgba(2,6,23,.10)",
                                background: "rgba(255,255,255,.85)",
                              }}
                            >
                              {t}
                            </span>
                          ))}
                        </div>
                      ) : null}

                      {Array.isArray(it.reasons) && it.reasons.length ? (
                        <details style={{ marginTop: 10 }}>
                          <summary className="texto-suave" style={{ cursor: "pointer", userSelect: "none" }}>
                            <b>Motivos</b> ({it.reasons.length}) — {it.reasons.slice(0, 2).map((r) => r.label).join(" · ")}
                            {it.reasons.length > 2 ? " · ..." : ""}
                          </summary>
                          <div style={{ marginTop: 8, display: "grid", gap: 8 }}>
                            {it.reasons.map((r, i) => (
                              <div
                                key={i}
                                style={{
                                  display: "flex",
                                  justifyContent: "space-between",
                                  gap: 12,
                                  alignItems: "flex-start",
                                }}
                              >
                                <div style={{ minWidth: 0 }}>
                                  <div style={{ fontWeight: 850 }}>{r?.label || "Motivo"}</div>
                                  {r?.detail ? <div className="texto-suave">{r.detail}</div> : null}
                                </div>
                                <div
                                  style={{
                                    fontWeight: 900,
                                    whiteSpace: "nowrap",
                                    paddingLeft: 8,
                                  }}
                                  title="Peso no score"
                                >
                                  {Math.round(r?.weight || 0)}
                                </div>
                              </div>
                            ))}
                            <div
                              style={{
                                borderTop: "1px solid rgba(2,6,23,.08)",
                                paddingTop: 8,
                                display: "flex",
                                justifyContent: "space-between",
                                alignItems: "center",
                              }}
                            >
                              <div className="texto-suave">Total</div>
                              <div style={{ fontWeight: 950, whiteSpace: "nowrap" }}>{Math.round(it.score || 0)}</div>
                            </div>
                          </div>
                        </details>
                      ) : null}
                    </div>

                    <button className="btn btn-primario" type="button" onClick={() => openItem(it)}>
                      Resolver agora
                    </button>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="texto-suave" style={{ marginTop: 10 }}>
              Sem itens na fila.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
