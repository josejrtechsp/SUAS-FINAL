// src/TelaProtocoloCaso.jsx
import { useEffect, useMemo, useState } from "react";
import PageHero from "./components/PageHero";

const STATUS_OPCOES = [
  { v: "pendente", l: "Pendente" },
  { v: "em_andamento", l: "Em andamento" },
  { v: "concluido", l: "Concluído" },
  { v: "cancelado", l: "Cancelado" },
];

function fmtData(iso) {
  if (!iso) return "—";
  try {
    const d = new Date(iso);
    const dd = String(d.getDate()).padStart(2, "0");
    const mm = String(d.getMonth() + 1).padStart(2, "0");
    const yy = d.getFullYear();
    return `${dd}/${mm}/${yy}`;
  } catch {
    return iso;
  }
}

export default function TelaProtocoloCaso({ apiBase, apiFetch, usuarioLogado, pessoas, casos, casoSelecionado }) {
  const [casoId, setCasoId] = useState(casoSelecionado?.id ? String(casoSelecionado.id) : "");
  const [loading, setLoading] = useState(false);
  const [erro, setErro] = useState("");
  const [protocolo, setProtocolo] = useState(null);

  // Plano (form)
  const [obj, setObj] = useState("");
  const [acao, setAcao] = useState("");
  const [resp, setResp] = useState("");
  const [prazo, setPrazo] = useState("");
  const [status, setStatus] = useState("pendente");
  const [obs, setObs] = useState("");

  const [copiado, setCopiado] = useState(false);
  const [mostrarAlertasMun, setMostrarAlertasMun] = useState(false);
  const [loadingAlertasMun, setLoadingAlertasMun] = useState(false);
  const [alertasMun, setAlertasMun] = useState(null);

  const casosOrdenados = useMemo(() => {
    const arr = Array.isArray(casos) ? [...casos] : [];
    arr.sort((a, b) => Number(b?.id || 0) - Number(a?.id || 0));
    return arr;
  }, [casos]);

  useEffect(() => {
    if (casoSelecionado?.id && !casoId) setCasoId(String(casoSelecionado.id));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [casoSelecionado?.id]);

  const pessoaNome = useMemo(() => {
    const c = casosOrdenados.find((x) => String(x?.id) === String(casoId));
    const pid = c?.pessoa_id;
    if (!pid) return "Pessoa";
    const p = (pessoas || []).find((pp) => Number(pp?.id) === Number(pid));
    return p?.nome_social || p?.nome_civil || "Pessoa";
  }, [casoId, casosOrdenados, pessoas]);

  const checklistPorEtapa = useMemo(() => {
    const arr = protocolo?.checklist || [];
    const map = {};
    for (const it of arr) {
      const e = it.etapa || "OUTROS";
      if (!map[e]) map[e] = [];
      map[e].push(it);
    }
    return map;
  }, [protocolo]);

  const resumoTexto = useMemo(() => {
    return protocolo?.resumo?.texto || "";
  }, [protocolo]);

  const resumoContagem = useMemo(() => {
    return protocolo?.resumo || null;
  }, [protocolo]);

  async function carregar() {
    if (!casoId) {
      setProtocolo(null);
      return;
    }
    setErro("");
    setLoading(true);
    try {
      const res = await apiFetch(`${apiBase}/casos/${casoId}/protocolo`);
      if (!res.ok) throw new Error(await res.text());
      const j = await res.json();
      setProtocolo(j);
    } catch (e) {
      console.error(e);
      setErro("Falha ao carregar protocolo.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    carregar();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [casoId]);

  async function atualizarEtapa(novaEtapa) {
    if (!casoId) return;
    setLoading(true);
    setErro("");
    try {
      const res = await apiFetch(`${apiBase}/casos/${casoId}/protocolo/etapa`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ etapa_atual: novaEtapa }),
      });
      if (!res.ok) throw new Error(await res.text());
      const j = await res.json();
      setProtocolo((old) =>
        old
          ? {
              ...old,
              etapa_atual: j.etapa_atual,
              atualizado_em: j.atualizado_em,
              atualizado_por_nome: j.atualizado_por_nome,
            }
          : old
      );
    } catch (e) {
      console.error(e);
      setErro("Falha ao atualizar etapa.");
    } finally {
      setLoading(false);
    }
  }

  async function toggleChecklist(chave, concluido) {
    if (!casoId) return;
    setLoading(true);
    setErro("");
    try {
      const res = await apiFetch(
        `${apiBase}/casos/${casoId}/protocolo/checklist/${encodeURIComponent(chave)}/toggle`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ concluido }),
        }
      );
      if (!res.ok) throw new Error(await res.text());
      const j = await res.json();
      setProtocolo((old) => {
        if (!old) return old;
        const arr = (old.checklist || []).map((x) => (x.chave === j.chave ? j : x));
        return { ...old, checklist: arr };
      });
    } catch (e) {
      console.error(e);
      setErro("Falha ao atualizar checklist.");
    } finally {
      setLoading(false);
    }
  }

  async function criarAcaoPlano() {
    if (!casoId) return;
    if (!obj.trim() || !acao.trim() || !resp.trim()) {
      setErro("Preencha objetivo, ação e responsável.");
      return;
    }
    setLoading(true);
    setErro("");
    try {
      const res = await apiFetch(`${apiBase}/casos/${casoId}/protocolo/plano`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          objetivo: obj,
          acao,
          responsavel: resp,
          prazo: prazo || null,
          status,
          obs: obs || null,
        }),
      });
      if (!res.ok) throw new Error(await res.text());
      const j = await res.json();
      setProtocolo((old) => (old ? { ...old, plano: [j, ...(old.plano || [])] } : old));
      setObj("");
      setAcao("");
      setResp("");
      setPrazo("");
      setStatus("pendente");
      setObs("");
    } catch (e) {
      console.error(e);
      setErro("Falha ao criar ação do plano.");
    } finally {
      setLoading(false);
    }
  }

  async function atualizarPlano(acaoId, patch) {
    if (!casoId) return;
    setLoading(true);
    setErro("");
    try {
      const res = await apiFetch(`${apiBase}/casos/${casoId}/protocolo/plano/${acaoId}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(patch),
      });
      if (!res.ok) throw new Error(await res.text());
      const j = await res.json();
      setProtocolo((old) => {
        if (!old) return old;
        const arr = (old.plano || []).map((x) => (Number(x.id) === Number(j.id) ? j : x));
        return { ...old, plano: arr };
      });
    } catch (e) {
      console.error(e);
      setErro("Falha ao atualizar ação.");
    } finally {
      setLoading(false);
    }
  }

  async function removerPlano(acaoId) {
    if (!casoId) return;
    if (!window.confirm("Remover esta ação do plano?")) return;
    setLoading(true);
    setErro("");
    try {
      const res = await apiFetch(`${apiBase}/casos/${casoId}/protocolo/plano/${acaoId}`, { method: "DELETE" });
      if (!res.ok) throw new Error(await res.text());
      setProtocolo((old) => {
        if (!old) return old;
        const arr = (old.plano || []).filter((x) => Number(x.id) !== Number(acaoId));
        return { ...old, plano: arr };
      });
    } catch (e) {
      console.error(e);
      setErro("Falha ao remover ação.");
    } finally {
      setLoading(false);
    }
  }


  async function copiarResumo() {
    try {
      const txt = resumoTexto || "";
      if (!txt) return;
      await navigator.clipboard.writeText(txt);
      setCopiado(true);
      setTimeout(() => setCopiado(false), 1500);
    } catch (e) {
      console.error(e);
      alert("Não foi possível copiar automaticamente. Selecione o texto e copie manualmente.");
    }
  }

  async function carregarAlertasMunicipio() {
    setLoadingAlertasMun(true);
    try {
      const res = await apiFetch(`${apiBase}/casos/protocolo/alertas?dias_vencer=7&dias_sem_atualizar=14`);
      if (!res.ok) throw new Error(await res.text());
      const j = await res.json();
      setAlertasMun(j);
    } catch (e) {
      console.error(e);
      setAlertasMun({ erro: true });
    } finally {
      setLoadingAlertasMun(false);
    }
  }

  return (
    <div className="layout-1col">
      <PageHero
  kicker="MÓDULO SUAS · POP RUA EM REDE"
  title="Pop Rua — Protocolo do Caso (B1)"
  subtitle="Checklist e plano do caso ficam salvos no sistema com auditoria, data e histórico."
  tips={[
    "Checklist por etapa e plano de ações.",
    "Alertas e pendências alimentam a Gestão.",
    "Use Copiar para relatórios rápidos.",
  ]}
  badge="POP RUA"
  rightText={
    "Pessoa: " +
    String(pessoaNome || "—") +
    " · Caso: #" +
    String(casoId || "—")
  }
/>
<section className="card card-wide">
        <div className="card-header-row">
          <div>
            
            <p className="texto-suave" style={{ marginTop: 6 }}>
              Pessoa: <strong>{pessoaNome}</strong> · Caso: <strong>#{casoId || "—"}</strong>
            </p>
            <p className="texto-suave" style={{ marginTop: 6 }}>
              Atualizado por: <strong>{protocolo?.atualizado_por_nome || usuarioLogado?.nome || "—"}</strong> ·{" "}
              <strong>{fmtData(protocolo?.atualizado_em)}</strong>
            </p>
          </div>
        </div>

        <div className="grid-2cols" style={{ marginTop: 10 }}>
          <label className="form-label">
            Selecionar caso
            <select className="input" value={casoId} onChange={(e) => setCasoId(e.target.value)}>
              <option value="">Selecione...</option>
              {casosOrdenados.map((c) => (
                <option key={c.id} value={c.id}>
                  Caso #{c.id} · Etapa {c.etapa_atual || "—"} · {c.status || "—"}
                </option>
              ))}
            </select>
          </label>
          <div className="texto-suave" style={{ alignSelf: "end" }}>
            Checklist e Plano ficam salvos no sistema (banco) com autoria e data.
          </div>
        </div>

        {erro && <p className="erro-global">{erro}</p>}

        {/* Resumo rápido (B1) */}
        {protocolo?.resumo ? (
          <div style={{ marginTop: 14 }}>
            <div className="item-atendimento">
              <div className="item-atendimento-header">
                <div>
                  <div className="item-atendimento-titulo">Resumo rápido</div>
                  <div className="item-atendimento-sub">
                    Checklist pendente: {resumoContagem?.checklist_pendentes ?? "—"} · Ações atrasadas: {resumoContagem?.plano_atrasadas ?? "—"} · Vencendo: {resumoContagem?.plano_vencendo ?? "—"}
                  </div>
                </div>
                <div style={{ display: "flex", gap: 8, flexWrap: "wrap", justifyContent: "flex-end" }}>
                  <button
                    type="button"
                    className="btn btn-secundario btn-secundario-mini"
                    onClick={() => {
                      setMostrarAlertasMun((v) => !v);
                      if (!alertasMun) carregarAlertasMunicipio();
                    }}
                    disabled={loading}
                    title="Ver alertas de prazo do município"
                  >
                    Alertas
                  </button>
                  <button
                    type="button"
                    className={"btn " + (copiado ? "btn-primario btn-primario-mini" : "btn-secundario btn-secundario-mini")}
                    onClick={copiarResumo}
                    disabled={!resumoTexto}
                    title="Copiar resumo para encaminhamento"
                  >
                    {copiado ? "Copiado" : "Copiar"}
                  </button>
                </div>
              </div>

              <pre
                style={{
                  marginTop: 10,
                  background: "#0b1220",
                  color: "#e5e7eb",
                  padding: 12,
                  borderRadius: 12,
                  whiteSpace: "pre-wrap",
                  fontSize: 12,
                  lineHeight: 1.35,
                }}
              >
                {resumoTexto}
              </pre>

              {mostrarAlertasMun ? (
                <div style={{ marginTop: 12 }}>
                  <div className="texto-suave" style={{ marginBottom: 6 }}>
                    Alertas de prazo (município): ações atrasadas/vencendo e casos sem atualização do protocolo.
                  </div>
                  {loadingAlertasMun ? (
                    <div className="texto-suave">Carregando alertas...</div>
                  ) : alertasMun?.erro ? (
                    <div className="erro-global">Falha ao carregar alertas.</div>
                  ) : alertasMun ? (
                    <div style={{ display: "grid", gap: 10 }}>
                      <div className="item-atendimento">
                        <div className="item-atendimento-header">
                          <div>
                            <div className="item-atendimento-titulo">Ações atrasadas</div>
                            <div className="item-atendimento-sub">{(alertasMun.atrasadas || []).length} item(ns)</div>
                          </div>
                        </div>
                        <div style={{ marginTop: 8, display: "grid", gap: 8 }}>
                          {(alertasMun.atrasadas || []).slice(0, 8).map((x) => (
                            <div key={x.acao_id} className="item-atendimento-detalhes" style={{ marginTop: 0 }}>
                              <span>
                                Caso <strong>#{x.caso_id}</strong> · <strong>{x.pessoa_nome}</strong>
                              </span>
                              <span>
                                Prazo: <strong>{x.prazo}</strong>
                              </span>
                              <span>
                                Resp.: <strong>{x.responsavel}</strong>
                              </span>
                            </div>
                          ))}
                          {(alertasMun.atrasadas || []).length === 0 ? <div className="texto-suave">Nenhuma.</div> : null}
                        </div>
                      </div>

                      <div className="item-atendimento">
                        <div className="item-atendimento-header">
                          <div>
                            <div className="item-atendimento-titulo">Ações vencendo (7 dias)</div>
                            <div className="item-atendimento-sub">{(alertasMun.vencendo || []).length} item(ns)</div>
                          </div>
                        </div>
                        <div style={{ marginTop: 8, display: "grid", gap: 8 }}>
                          {(alertasMun.vencendo || []).slice(0, 8).map((x) => (
                            <div key={x.acao_id} className="item-atendimento-detalhes" style={{ marginTop: 0 }}>
                              <span>
                                Caso <strong>#{x.caso_id}</strong> · <strong>{x.pessoa_nome}</strong>
                              </span>
                              <span>
                                Prazo: <strong>{x.prazo}</strong>
                              </span>
                              <span>
                                Resp.: <strong>{x.responsavel}</strong>
                              </span>
                            </div>
                          ))}
                          {(alertasMun.vencendo || []).length === 0 ? <div className="texto-suave">Nenhuma.</div> : null}
                        </div>
                      </div>

                      <div className="item-atendimento">
                        <div className="item-atendimento-header">
                          <div>
                            <div className="item-atendimento-titulo">Casos sem atualização do protocolo</div>
                            <div className="item-atendimento-sub">{(alertasMun.casos_sem_atualizar || []).length} caso(s)</div>
                          </div>
                        </div>
                        <div style={{ marginTop: 8, display: "grid", gap: 8 }}>
                          {(alertasMun.casos_sem_atualizar || []).slice(0, 8).map((x) => (
                            <div key={x.caso_id} className="item-atendimento-detalhes" style={{ marginTop: 0 }}>
                              <span>
                                Caso <strong>#{x.caso_id}</strong>
                              </span>
                              <span>
                                Etapa: <strong>{x.etapa_atual}</strong>
                              </span>
                              <span>
                                Última atualização: <strong>{fmtData(x.atualizado_em)}</strong>
                              </span>
                            </div>
                          ))}
                          {(alertasMun.casos_sem_atualizar || []).length === 0 ? <div className="texto-suave">Nenhum.</div> : null}
                        </div>
                      </div>
                    </div>
                  ) : null}
                </div>
              ) : null}
            </div>
          </div>
        ) : null}


        {/* Etapas */}
        <div style={{ marginTop: 14 }}>
          <h3 style={{ margin: 0 }}>Etapa do caso</h3>
          <p className="texto-suave" style={{ marginTop: 6 }}>
            Clique para atualizar a etapa atual.
          </p>
          <div style={{ marginTop: 10, display: "flex", gap: 8, flexWrap: "wrap" }}>
            {(protocolo?.etapas || []).map((e) => {
              const ativa = String(protocolo?.etapa_atual) === String(e.codigo);
              return (
                <button
                  key={e.codigo}
                  type="button"
                  className={
                    "btn " + (ativa ? "btn-primario btn-primario-mini" : "btn-secundario btn-secundario-mini")
                  }
                  onClick={() => atualizarEtapa(e.codigo)}
                  disabled={!casoId || loading}
                  title={e.nome}
                >
                  {e.nome}
                </button>
              );
            })}
          </div>
        </div>

        {/* Checklist */}
        <div style={{ marginTop: 18 }}>
          <h3 style={{ margin: 0 }}>Checklist do Protocolo</h3>
          <p className="texto-suave" style={{ marginTop: 6 }}>
            Marque o que já foi realizado. (Operacional, sem dados clínicos.)
          </p>

          <div style={{ marginTop: 10, display: "grid", gap: 10 }}>
            {(protocolo?.etapas || []).map((et) => {
              const itens = checklistPorEtapa[et.codigo] || [];
              return (
                <div key={et.codigo} className="item-atendimento">
                  <div className="item-atendimento-header">
                    <div>
                      <div className="item-atendimento-titulo">{et.nome}</div>
                      <div className="item-atendimento-sub">
                        {itens.length ? `${itens.length} item(ns)` : "Sem itens"}
                      </div>
                    </div>
                  </div>

                  <div style={{ marginTop: 8, display: "grid", gap: 8 }}>
                    {itens.map((it) => (
                      <label
                        key={it.chave}
                        className="texto-suave"
                        style={{ display: "flex", gap: 10, alignItems: "center" }}
                      >
                        <input
                          type="checkbox"
                          checked={!!it.concluido}
                          onChange={(e) => toggleChecklist(it.chave, !!e.target.checked)}
                          style={{ width: 16, height: 16 }}
                          disabled={loading}
                        />
                        <div style={{ display: "grid" }}>
                          <span style={{ fontWeight: 800, textTransform: "none", letterSpacing: 0 }}>{it.titulo}</span>
                          <span style={{ opacity: 0.75, textTransform: "none", letterSpacing: 0 }}>
                            {it.concluido
                              ? `Concluído em ${fmtData(it.concluido_em)} por ${it.concluido_por_nome || "—"}`
                              : "Não concluído"}
                          </span>
                        </div>
                      </label>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Plano de ações */}
        <div style={{ marginTop: 18 }}>
          <h3 style={{ margin: 0 }}>Plano de ações (PIA operacional)</h3>
          <p className="texto-suave" style={{ marginTop: 6 }}>Crie ações com responsável, prazo e status.</p>

          <div className="grid-2cols" style={{ marginTop: 10 }}>
            <label className="form-label">
              Objetivo
              <input className="input" value={obj} onChange={(e) => setObj(e.target.value)} />
            </label>
            <label className="form-label">
              Ação
              <input className="input" value={acao} onChange={(e) => setAcao(e.target.value)} />
            </label>
            <label className="form-label">
              Responsável
              <input className="input" value={resp} onChange={(e) => setResp(e.target.value)} />
            </label>
            <label className="form-label">
              Prazo
              <input className="input" type="date" value={prazo} onChange={(e) => setPrazo(e.target.value)} />
            </label>
            <label className="form-label">
              Status
              <select className="input" value={status} onChange={(e) => setStatus(e.target.value)}>
                {STATUS_OPCOES.map((o) => (
                  <option key={o.v} value={o.v}>
                    {o.l}
                  </option>
                ))}
              </select>
            </label>
            <label className="form-label">
              Observação (opcional)
              <input className="input" value={obs} onChange={(e) => setObs(e.target.value)} />
            </label>
          </div>
          <div style={{ marginTop: 10, display: "flex", justifyContent: "flex-end" }}>
            <button type="button" className="btn btn-primario btn-primario-mini" onClick={criarAcaoPlano} disabled={loading || !casoId}>
              Adicionar ação
            </button>
          </div>

          <div style={{ marginTop: 12, display: "grid", gap: 10 }}>
            {(protocolo?.plano || []).map((a) => (
              <div key={a.id} className="item-atendimento">
                <div className="item-atendimento-header">
                  <div>
                    <div className="item-atendimento-titulo">{a.objetivo}</div>
                    <div className="item-atendimento-sub">
                      {a.acao} · Resp.: {a.responsavel}
                    </div>
                  </div>
                  <div style={{ display: "flex", gap: 8, flexWrap: "wrap", justifyContent: "flex-end" }}>
                    <select
                      className="input"
                      value={a.status || "pendente"}
                      onChange={(e) => atualizarPlano(a.id, { status: e.target.value })}
                      style={{ minWidth: 160 }}
                      disabled={loading}
                    >
                      {STATUS_OPCOES.map((o) => (
                        <option key={o.v} value={o.v}>
                          {o.l}
                        </option>
                      ))}
                    </select>
                    <button type="button" className="btn btn-secundario btn-secundario-mini" onClick={() => removerPlano(a.id)} disabled={loading}>
                      Remover
                    </button>
                  </div>
                </div>
                <div className="item-atendimento-detalhes" style={{ marginTop: 6 }}>
                  <span>
                    Prazo: <strong>{a.prazo ? fmtData(a.prazo) : "—"}</strong>
                  </span>
                  <span>
                    Status: <strong>{a.status || "—"}</strong>
                  </span>
                  <span>
                    Atualizado: <strong>{fmtData(a.atualizado_em)}</strong>
                  </span>
                </div>
                {a.obs ? (
                  <p className="item-atendimento-texto" style={{ marginTop: 8 }}>
                    <strong>Obs:</strong> {a.obs}
                  </p>
                ) : null}
              </div>
            ))}
          </div>
        </div>

        {loading && <p className="texto-suave" style={{ marginTop: 12 }}>Carregando...</p>}
      </section>
    </div>
  );
}