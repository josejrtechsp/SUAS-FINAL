import { useEffect, useMemo, useState } from "react";
import { rmaCollect } from "./domain/rmaCollector.js";


function hojeISO() {
  const d = new Date();
  const yyyy = d.getFullYear();
  const mm = String(d.getMonth() + 1).padStart(2, "0");
  const dd = String(d.getDate()).padStart(2, "0");
  return `${yyyy}-${mm}-${dd}`;
}

function toCSV(rows) {
  const esc = (v) => {
    const s = v == null ? "" : String(v);
    const needs = /[\n\r",;]/.test(s);
    const ss = s.replace(/"/g, '""');
    return needs ? `"${ss}"` : ss;
  };
  return rows.map((r) => r.map(esc).join(",")).join("\n");
}

function downloadText(filename, text, mime = "text/plain;charset=utf-8") {
  try {
    const blob = new Blob([text], { type: mime });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 800);
  } catch (e) {
    console.error(e);
    alert("Não foi possível baixar o arquivo.");
  }
}

export default function TelaCras({ apiBase, apiFetch, usuarioLogado, view = "fila", onSetView = () => {} }) {
  const activeView = view || "fila";

  const [pessoas, setPessoas] = useState([]);
  const [unidades, setUnidades] = useState([]);
  const [unidadeId, setUnidadeId] = useState(localStorage.getItem("cras_unidade_ativa") || "");
  const municipioAtivo = localStorage.getItem("cras_municipio_ativo") || "";

  const [triagens, setTriagens] = useState([]);
  const [resumoTriagem, setResumoTriagem] = useState(null);

  const [pessoaId, setPessoaId] = useState("");
  const [demanda, setDemanda] = useState("");
  const [prioridade, setPrioridade] = useState("media");
  const [canal, setCanal] = useState("espontanea");
  const [obs, setObs] = useState("");
  const [desfecho, setDesfecho] = useState("em_atendimento");

  const [paifs, setPaifs] = useState([]);
  const [paifId, setPaifId] = useState("");
  const [resumoPaif, setResumoPaif] = useState(null);

  const [novaAcao, setNovaAcao] = useState({ objetivo: "", acao: "", responsavel: "", prazo: "" });
  const [msg, setMsg] = useState("");

  // histórico
  const [histData, setHistData] = useState(() => hojeISO());
  const [histTriagens, setHistTriagens] = useState([]);
  const [histResumo, setHistResumo] = useState(null);

  const etapas = useMemo(() => ["TRIAGEM", "DIAGNOSTICO", "PLANO", "EXECUCAO", "MONITORAMENTO", "ENCERRAMENTO"], []);

  const mapaUn = useMemo(() => {
    const m = new Map();
    unidades.forEach((u) => m.set(u.id, u.nome));
    return m;
  }, [unidades]);

  const unidadeNome = useMemo(() => {
    const n = unidadeId ? (mapaUn.get(Number(unidadeId)) || "—") : "—";
    return n;
  }, [unidadeId, mapaUn]);

  useEffect(() => {
    try {
      localStorage.setItem("cras_unidade_ativa", unidadeId || "");
    } catch {}
  }, [unidadeId]);

  async function loadPessoas() {
    const r = await apiFetch(`${apiBase}/pessoas/`);
    if (r.ok) setPessoas(await r.json());
  }

  async function loadUnidades() {
    const q = new URLSearchParams();
    if (municipioAtivo) q.set("municipio_id", municipioAtivo);
    const r = await apiFetch(`${apiBase}/cras/unidades?${q.toString()}`);
    if (r.ok) {
      const data = await r.json();
      setUnidades(data);
      if (!unidadeId && data.length) setUnidadeId(String(data[0].id));
    }
  }

  async function criarUnidadePadrao() {
    setMsg("");
    const r = await apiFetch(`${apiBase}/cras/unidades`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        municipio_id: municipioAtivo ? Number(municipioAtivo) : undefined,
        nome: "CRAS 1",
      }),
    });
    if (!r.ok) return setMsg("Sem permissão para criar unidade (precisa admin/coordenação)."
    );
    setMsg("Unidade CRAS criada ✅");
    await loadUnidades();
  }

  async function loadTriagensDia(d, setList, setResumo) {
    const q = new URLSearchParams();
    if (municipioAtivo) q.set("municipio_id", municipioAtivo);
    q.set("data", d);
    if (unidadeId) q.set("unidade_id", unidadeId);

    const r = await apiFetch(`${apiBase}/cras/triagens?${q.toString()}`);
    if (r.ok) setList(await r.json());

    const r2 = await apiFetch(`${apiBase}/cras/triagens/resumo?${q.toString()}`);
    if (r2.ok) setResumo(await r2.json());
  }

  async function loadTriagens() {
    return loadTriagensDia(hojeISO(), setTriagens, setResumoTriagem);
  }

  async function loadTriagensHistorico() {
    if (!histData) return;
    return loadTriagensDia(histData, setHistTriagens, setHistResumo);
  }

  async function loadPaifs() {
    const r = await apiFetch(`${apiBase}/cras/paif?status=ativo`);
    if (r.ok) setPaifs(await r.json());
  }

  async function loadResumoPaif(id) {
    if (!id) return;
    const r = await apiFetch(`${apiBase}/cras/paif/${id}/protocolo`);
    if (r.ok) setResumoPaif(await r.json());
  }

  useEffect(() => {
    loadPessoas();
    loadUnidades();
    loadPaifs();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    loadTriagens();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [unidadeId]);

  useEffect(() => {
    if (paifId) loadResumoPaif(paifId);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [paifId]);

  useEffect(() => {
    if (activeView === "historico") loadTriagensHistorico();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeView, unidadeId, histData]);

  async function criarTriagem() {
    setMsg("");
    if (!unidadeId) return setMsg("Selecione uma unidade CRAS.");
    if (!demanda.trim()) return setMsg("Informe a demanda principal.");

    const r = await apiFetch(`${apiBase}/cras/triagens`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        unidade_id: Number(unidadeId),
        pessoa_id: pessoaId ? Number(pessoaId) : null,
        canal,
        prioridade,
        demanda_principal: demanda.trim(),
        observacao_operacional: obs.trim() || null,
        desfecho,
      }),
    });

    if (!r.ok) return setMsg("Erro ao criar triagem (verifique unidade/pessoa/permissão)."
    );

    setDemanda("");
    setObs("");
    setDesfecho("em_atendimento");
    setMsg("Triagem criada ✅");
    await loadTriagens();
  }

  async function encerrarTriagem(t) {
    await apiFetch(`${apiBase}/cras/triagens/${t.id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status: "encerrada", desfecho: t.desfecho || "orientado" }),
    });
    await loadTriagens();
  }

  async function converterEmPaif(t) {
    setMsg("");
    const r = await apiFetch(`${apiBase}/cras/triagens/${t.id}/converter-paif`, { method: "POST" });
    if (!r.ok) return setMsg("Não foi possível converter em PAIF (triagem precisa ter pessoa vinculada)."
    );
    const data = await r.json();
    await loadPaifs();
    setPaifId(String(data.paif?.id || ""));
    setMsg("Convertido em PAIF ✅");
    // RMA_COLLECT_V1 TRIAGEM
    try {
      const casoId = data?.caso?.id ?? data?.caso_id ?? null;
      const pessoaId = data?.paif?.pessoa_suas_id ?? data?.paif?.pessoa_id ?? t?.pessoa_id ?? null;
      await rmaCollect({
        apiBase,
        apiFetch,
        servico: "PAIF",
        acao: "converter",
        unidade_id: (typeof unidadeSel !== "undefined" && unidadeSel) ? Number(unidadeSel) : null,
        pessoa_id: pessoaId ? Number(pessoaId) : null,
        caso_id: casoId ? Number(casoId) : null,
        alvo_tipo: "triagem",
        alvo_id: t?.id ?? null,
        meta: { triagem_id: t?.id ?? null, paif_id: data?.paif?.id ?? null },
      });
    } catch {}
    await loadTriagens();

    // dica: ao converter, ir direto para a fila (onde fica o PAIF ao lado)
    try {
      onSetView?.("fila");
    } catch {}
  }

  async function mudarEtapa(etapa) {
    if (!paifId) return;
    await apiFetch(`${apiBase}/cras/paif/${paifId}/protocolo/etapa`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ etapa }),
    });
    await loadResumoPaif(paifId);
  }

  async function toggleChecklist(item) {
    if (!paifId) return;
    await apiFetch(`${apiBase}/cras/paif/${paifId}/protocolo/checklist/${item.chave}/toggle`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ etapa: item.etapa, titulo: item.titulo }),
    });
    await loadResumoPaif(paifId);
  }

  async function adicionarAcao() {
    setMsg("");
    if (!paifId) return setMsg("Selecione um PAIF.");
    if (!novaAcao.objetivo || !novaAcao.acao || !novaAcao.responsavel) return setMsg("Objetivo, Ação e Responsável são obrigatórios.");

    const r = await apiFetch(`${apiBase}/cras/paif/${paifId}/protocolo/plano`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(novaAcao),
    });
    if (!r.ok) return setMsg("Erro ao salvar ação.");
    setNovaAcao({ objetivo: "", acao: "", responsavel: "", prazo: "" });
    await loadResumoPaif(paifId);
    setMsg("Ação adicionada ✅");
  }

  const etapaAtual = resumoPaif?.protocolo?.etapa_atual || "TRIAGEM";
  const checklistEtapa = useMemo(() => {
    const all = Array.isArray(resumoPaif?.checklist) ? resumoPaif.checklist : [];
    return all.filter((x) => x.etapa === etapaAtual);
  }, [resumoPaif, etapaAtual]);

  const pendTriagens = useMemo(() => {
    const arr = Array.isArray(triagens) ? triagens : [];
    return arr.filter((t) => t.status !== "encerrada" && t.status !== "convertida");
  }, [triagens]);

  const pendSemPessoa = useMemo(() => {
    return pendTriagens.filter((t) => !t.pessoa_id);
  }, [pendTriagens]);

  const relStats = useMemo(() => {
    const arr = Array.isArray(triagens) ? triagens : [];
    const by = (k) => {
      const m = new Map();
      for (const t of arr) {
        const v = String(t?.[k] || "—");
        m.set(v, (m.get(v) || 0) + 1);
      }
      return [...m.entries()].sort((a, b) => b[1] - a[1]);
    };
    return {
      total: arr.length,
      porPrioridade: by("prioridade"),
      porCanal: by("canal"),
      porStatus: by("status"),
    };
  }, [triagens]);

  function exportarCSVHoje() {
    const rows = Array.isArray(triagens) ? triagens : [];
    const header = ["id", "unidade_id", "status", "prioridade", "canal", "demanda_principal", "pessoa_id", "desfecho"];
    const data = rows.map((t) => [
      t?.id,
      t?.unidade_id,
      t?.status,
      t?.prioridade,
      t?.canal,
      t?.demanda_principal,
      t?.pessoa_id,
      t?.desfecho,
    ]);
    const csv = toCSV([header, ...data]);
    downloadText(`triagens_${hojeISO()}.csv`, csv, "text/csv;charset=utf-8");
  }

  function renderUnidade() {
    return (
      <>
        <div className="card" style={{ padding: 12, borderRadius: 18 }}>
          <div style={{ display: "flex", gap: 10, flexWrap: "wrap", alignItems: "center" }}>
            <label className="label" style={{ margin: 0 }}>Unidade CRAS</label>
            <select className="input" value={unidadeId} onChange={(e) => setUnidadeId(e.target.value)} style={{ minWidth: 240 }}>
              <option value="">Selecione…</option>
              {unidades.map((u) => (
                <option key={u.id} value={u.id}>{u.nome}</option>
              ))}
            </select>

            {!unidades.length ? (
              <button className="btn btn-secundario" type="button" onClick={criarUnidadePadrao}>
                Criar unidade "CRAS 1"
              </button>
            ) : null}

            <button className="btn btn-secundario" type="button" onClick={loadTriagens}>
              Atualizar fila
            </button>

            {resumoTriagem ? (
              <div className="texto-suave" style={{ marginLeft: "auto" }}>
                Hoje: <b>{resumoTriagem.total}</b> · Abertas: <b>{resumoTriagem.abertas}</b> · Encerradas: <b>{resumoTriagem.encerradas}</b> · Convertidas: <b>{resumoTriagem.convertidas}</b>
              </div>
            ) : null}
          </div>
        </div>

        <div className="card" style={{ padding: 12, borderRadius: 18, marginTop: 12 }}>
          <div style={{ fontWeight: 950 }}>Unidade ativa</div>
          <div className="texto-suave" style={{ marginTop: 4 }}>
            Tudo o que você fizer nas telas de Triagem/PAIF será filtrado e registrado na unidade: <b>{unidadeNome}</b>.
          </div>
          <div style={{ marginTop: 10 }}>
            <button className="btn btn-primario" type="button" onClick={() => onSetView?.("fila")}>
              Ir para Fila
            </button>
          </div>
        </div>
      </>
    );
  }

  function renderFilaComPaif() {
    return (
      <div style={{ display: "grid", gridTemplateColumns: "1.05fr 1fr", gap: 12 }}>
        {/* COLUNA 1: FILA + FORM */}
        <div className="card" style={{ padding: 12, borderRadius: 18 }}>
          <h3 style={{ margin: 0 }}>Fila de triagem (hoje)</h3>
          <p className="texto-suave" style={{ marginTop: 6 }}>
            Unidade: <b>{unidadeNome}</b>
          </p>

          <div style={{ display: "grid", gap: 8, marginTop: 10 }}>
            {triagens.length ? triagens.map((t) => (
              <div key={t.id} className="card" style={{ padding: 10, borderRadius: 14 }}>
                <div style={{ display: "flex", justifyContent: "space-between", gap: 10, flexWrap: "wrap" }}>
                  <div><b>#{t.id}</b> · {mapaUn.get(t.unidade_id) || `Unidade ${t.unidade_id}`}</div>
                  <div className="texto-suave">
                    {t.status} · prioridade: <b>{t.prioridade}</b>
                  </div>
                </div>
                <div style={{ marginTop: 6 }}>
                  <b>Demanda:</b> {t.demanda_principal}
                </div>
                <div className="texto-suave" style={{ marginTop: 4 }}>
                  Pessoa: {t.pessoa_id ? `#${t.pessoa_id}` : "não vinculada"} · Canal: {t.canal} · Desfecho: {t.desfecho}
                </div>

                <div style={{ display: "flex", gap: 8, marginTop: 8, flexWrap: "wrap" }}>
                  {t.status !== "encerrada" ? (
                    <button className="btn btn-secundario" type="button" onClick={() => encerrarTriagem(t)}>
                      Encerrar
                    </button>
                  ) : null}

                  {t.status !== "convertida" ? (
                    <button className="btn btn-primario" type="button" onClick={() => converterEmPaif(t)}>
                      Converter em PAIF
                    </button>
                  ) : (
                    <span className="texto-suave">PAIF: #{t.paif_id || "—"}</span>
                  )}
                </div>
              </div>
            )) : (
              <div className="texto-suave">Sem triagens para hoje (nesta unidade).</div>
            )}
          </div>

          <div style={{ height: 14 }} />
          <h3 style={{ margin: 0 }}>Nova triagem (rápida)</h3>

          <div style={{ height: 10 }} />
          <label className="label">Pessoa (opcional, mas obrigatório para converter em PAIF)</label>
          <select className="input" value={pessoaId} onChange={(e) => setPessoaId(e.target.value)}>
            <option value="">Selecione…</option>
            {pessoas.map((p) => (
              <option key={p.id} value={p.id}>
                #{p.id} — {p.nome_social || p.nome_civil || "Pessoa"}
              </option>
            ))}
          </select>

          <div style={{ height: 8 }} />
          <label className="label">Demanda principal</label>
          <input className="input" value={demanda} onChange={(e) => setDemanda(e.target.value)} placeholder="Ex.: atualização CadÚnico, orientação benefício, conflito familiar..." />

          <div style={{ height: 8 }} />
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 8 }}>
            <div>
              <label className="label">Prioridade</label>
              <select className="input" value={prioridade} onChange={(e) => setPrioridade(e.target.value)}>
                <option value="baixa">baixa</option>
                <option value="media">média</option>
                <option value="alta">alta</option>
              </select>
            </div>
            <div>
              <label className="label">Canal</label>
              <select className="input" value={canal} onChange={(e) => setCanal(e.target.value)}>
                <option value="espontanea">espontânea</option>
                <option value="agendada">agendada</option>
                <option value="telefone">telefone</option>
              </select>
            </div>
            <div>
              <label className="label">Desfecho</label>
              <select className="input" value={desfecho} onChange={(e) => setDesfecho(e.target.value)}>
                <option value="em_atendimento">em atendimento</option>
                <option value="orientado">orientado</option>
                <option value="agendado">agendado</option>
                <option value="encaminhado">encaminhado</option>
                <option value="abrir_paif">abrir PAIF</option>
              </select>
            </div>
          </div>

          <div style={{ height: 8 }} />
          <label className="label">Observação operacional</label>
          <textarea className="input" rows={3} value={obs} onChange={(e) => setObs(e.target.value)} />

          <div style={{ marginTop: 10 }}>
            <button className="btn btn-primario" type="button" onClick={criarTriagem}>
              Criar triagem
            </button>
          </div>
        </div>

        {/* COLUNA 2: PAIF */}
        <div className="card" style={{ padding: 12, borderRadius: 18 }}>
          <h3 style={{ margin: 0 }}>PAIF (ativos)</h3>

          <div style={{ display: "flex", gap: 10, marginTop: 10, flexWrap: "wrap" }}>
            <select className="input" value={paifId} onChange={(e) => setPaifId(e.target.value)} style={{ minWidth: 280 }}>
              <option value="">Selecione um PAIF…</option>
              {paifs.map((p) => (
                <option key={p.id} value={p.id}>
                  PAIF #{p.id} — Pessoa #{p.pessoa_id} — {p.status}
                </option>
              ))}
            </select>
            <button className="btn btn-secundario" type="button" onClick={loadPaifs}>
              Atualizar
            </button>
          </div>

          {resumoPaif ? (
            <>
              <div style={{ height: 12 }} />
              <div style={{ display: "flex", gap: 10, alignItems: "center", flexWrap: "wrap" }}>
                <strong>Etapa atual:</strong>
                <select className="input" style={{ width: 260 }} value={etapaAtual} onChange={(e) => mudarEtapa(e.target.value)}>
                  {etapas.map((e) => <option key={e} value={e}>{e}</option>)}
                </select>
              </div>

              <div style={{ height: 10 }} />
              <strong>Checklist (etapa atual)</strong>
              <div style={{ display: "grid", gap: 8, marginTop: 8 }}>
                {checklistEtapa.map((it) => (
                  <button
                    key={it.id || it.chave}
                    type="button"
                    className="btn btn-secundario"
                    onClick={() => toggleChecklist(it)}
                    style={{ justifyContent: "space-between", display: "flex" }}
                  >
                    <span>{it.titulo}</span>
                    <span>{it.concluido ? "✅" : "⬜"}</span>
                  </button>
                ))}
                {!checklistEtapa.length ? <div className="texto-suave">Sem itens para esta etapa.</div> : null}
              </div>

              <div style={{ height: 14 }} />
              <strong>Plano de ação</strong>

              <div style={{ display: "grid", gap: 8, marginTop: 8 }}>
                {(resumoPaif.plano || []).map((a) => (
                  <div key={a.id} className="card" style={{ padding: 10, borderRadius: 14 }}>
                    <div><b>{a.objetivo}</b></div>
                    <div className="texto-suave">{a.acao}</div>
                    <div style={{ fontSize: 12 }} className="texto-suave">
                      Resp: {a.responsavel} · Prazo: {a.prazo || "—"} · Status: {a.status}
                    </div>
                  </div>
                ))}
              </div>

              <div style={{ height: 10 }} />
              <div className="card" style={{ padding: 10, borderRadius: 14 }}>
                <div style={{ fontWeight: 900, marginBottom: 6 }}>Adicionar ação</div>
                <input className="input" placeholder="Objetivo" value={novaAcao.objetivo} onChange={(e) => setNovaAcao({ ...novaAcao, objetivo: e.target.value })} />
                <div style={{ height: 8 }} />
                <input className="input" placeholder="Ação" value={novaAcao.acao} onChange={(e) => setNovaAcao({ ...novaAcao, acao: e.target.value })} />
                <div style={{ height: 8 }} />
                <input className="input" placeholder="Responsável" value={novaAcao.responsavel} onChange={(e) => setNovaAcao({ ...novaAcao, responsavel: e.target.value })} />
                <div style={{ height: 8 }} />
                <input className="input" placeholder="Prazo (YYYY-MM-DD)" value={novaAcao.prazo} onChange={(e) => setNovaAcao({ ...novaAcao, prazo: e.target.value })} />
                <div style={{ height: 8 }} />
                <button className="btn btn-primario" type="button" onClick={adicionarAcao}>
                  Salvar ação
                </button>
              </div>
            </>
          ) : (
            <div style={{ marginTop: 12 }} className="texto-suave">
              Selecione um PAIF para ver protocolo, checklist e plano.
            </div>
          )}
        </div>
      </div>
    );
  }

  function renderPendencias() {
    return (
      <>
        <div className="card" style={{ padding: 12, borderRadius: 18 }}>
          <div style={{ display: "flex", gap: 10, flexWrap: "wrap", alignItems: "center" }}>
            <div style={{ fontWeight: 950 }}>Pendências do dia</div>
            <div className="texto-suave">Unidade: <b>{unidadeNome}</b></div>
            <div style={{ marginLeft: "auto" }}>
              <button className="btn btn-secundario" type="button" onClick={loadTriagens}>
                Atualizar
              </button>
            </div>
          </div>
        </div>

        <div style={{ height: 12 }} />

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
          <div className="card" style={{ padding: 12, borderRadius: 18 }}>
            <h3 style={{ margin: 0 }}>Triagens abertas</h3>
            <p className="texto-suave" style={{ marginTop: 6 }}>
              Itens que ainda precisam ser encerrados ou convertidos.
            </p>

            <div style={{ display: "grid", gap: 8, marginTop: 10 }}>
              {pendTriagens.length ? pendTriagens.map((t) => (
                <div key={t.id} className="card" style={{ padding: 10, borderRadius: 14 }}>
                  <div style={{ display: "flex", justifyContent: "space-between", gap: 10, flexWrap: "wrap" }}>
                    <div><b>#{t.id}</b> · prioridade: <b>{t.prioridade}</b></div>
                    <div className="texto-suave">{t.status} · canal: {t.canal}</div>
                  </div>
                  <div style={{ marginTop: 6 }}><b>Demanda:</b> {t.demanda_principal}</div>
                  <div className="texto-suave" style={{ marginTop: 4 }}>
                    Pessoa: {t.pessoa_id ? `#${t.pessoa_id}` : "não vinculada"} · Desfecho: {t.desfecho}
                  </div>
                  <div style={{ display: "flex", gap: 8, marginTop: 8, flexWrap: "wrap" }}>
                    <button className="btn btn-secundario" type="button" onClick={() => encerrarTriagem(t)}>
                      Encerrar
                    </button>
                    <button className="btn btn-primario" type="button" onClick={() => converterEmPaif(t)}>
                      Converter em PAIF
                    </button>
                  </div>
                </div>
              )) : (
                <div className="texto-suave">Sem triagens abertas.</div>
              )}
            </div>
          </div>

          <div className="card" style={{ padding: 12, borderRadius: 18 }}>
            <h3 style={{ margin: 0 }}>Sem pessoa vinculada</h3>
            <p className="texto-suave" style={{ marginTop: 6 }}>
              Essas triagens não podem ser convertidas em PAIF sem vincular a pessoa.
            </p>

            <div style={{ display: "grid", gap: 8, marginTop: 10 }}>
              {pendSemPessoa.length ? pendSemPessoa.map((t) => (
                <div key={t.id} className="card" style={{ padding: 10, borderRadius: 14 }}>
                  <div><b>#{t.id}</b> · {t.demanda_principal}</div>
                  <div className="texto-suave" style={{ marginTop: 4 }}>
                    prioridade: <b>{t.prioridade}</b> · canal: {t.canal}
                  </div>
                </div>
              )) : (
                <div className="texto-suave">Nenhuma triagem sem pessoa vinculada.</div>
              )}
            </div>

            <div style={{ marginTop: 12 }}>
              <button className="btn btn-secundario" type="button" onClick={() => onSetView?.("fila")}>
                Ir para Fila
              </button>
            </div>
          </div>
        </div>
      </>
    );
  }

  function renderHistorico() {
    return (
      <>
        <div className="card" style={{ padding: 12, borderRadius: 18 }}>
          <div style={{ display: "flex", gap: 10, flexWrap: "wrap", alignItems: "center" }}>
            <div style={{ fontWeight: 950 }}>Histórico de triagens</div>
            <div className="texto-suave">Unidade: <b>{unidadeNome}</b></div>
            <div style={{ marginLeft: "auto", display: "flex", gap: 8, flexWrap: "wrap", alignItems: "center" }}>
              <input className="input" style={{ width: 170 }} type="date" value={histData} onChange={(e) => setHistData(e.target.value)} />
              <button className="btn btn-secundario" type="button" onClick={loadTriagensHistorico}>
                Buscar
              </button>
              <button className="btn btn-secundario" type="button" onClick={() => setHistData(hojeISO())}>
                Hoje
              </button>
            </div>
          </div>
        </div>

        {histResumo ? (
          <div className="card" style={{ padding: 12, borderRadius: 18, marginTop: 12 }}>
            <div className="texto-suave">
              Data: <b>{histData}</b> · Total: <b>{histResumo.total}</b> · Abertas: <b>{histResumo.abertas}</b> · Encerradas: <b>{histResumo.encerradas}</b> · Convertidas: <b>{histResumo.convertidas}</b>
            </div>
          </div>
        ) : null}

        <div className="card" style={{ padding: 12, borderRadius: 18, marginTop: 12 }}>
          <div style={{ display: "grid", gap: 8 }}>
            {histTriagens.length ? histTriagens.map((t) => (
              <div key={t.id} className="card" style={{ padding: 10, borderRadius: 14 }}>
                <div style={{ display: "flex", justifyContent: "space-between", gap: 10, flexWrap: "wrap" }}>
                  <div><b>#{t.id}</b> · {mapaUn.get(t.unidade_id) || `Unidade ${t.unidade_id}`}</div>
                  <div className="texto-suave">{t.status} · prioridade: <b>{t.prioridade}</b> · canal: {t.canal}</div>
                </div>
                <div style={{ marginTop: 6 }}><b>Demanda:</b> {t.demanda_principal}</div>
                <div className="texto-suave" style={{ marginTop: 4 }}>
                  Pessoa: {t.pessoa_id ? `#${t.pessoa_id}` : "não vinculada"} · Desfecho: {t.desfecho}
                </div>
              </div>
            )) : (
              <div className="texto-suave">Sem registros para esta data.</div>
            )}
          </div>
        </div>
      </>
    );
  }

  function renderRelatorios() {
    const badge = (label, value) => (
      <div className="card" style={{ padding: 10, borderRadius: 14 }}>
        <div className="texto-suave" style={{ fontSize: 12 }}>{label}</div>
        <div style={{ fontWeight: 950, fontSize: 18 }}>{value}</div>
      </div>
    );

    return (
      <>
        <div className="card" style={{ padding: 12, borderRadius: 18 }}>
          <div style={{ display: "flex", gap: 10, flexWrap: "wrap", alignItems: "center" }}>
            <div style={{ fontWeight: 950 }}>Relatórios (dia)</div>
            <div className="texto-suave">Unidade: <b>{unidadeNome}</b></div>
            <div className="texto-suave">Data: <b>{hojeISO()}</b></div>
            <div style={{ marginLeft: "auto", display: "flex", gap: 8, flexWrap: "wrap" }}>
              <button className="btn btn-secundario" type="button" onClick={loadTriagens}>
                Atualizar
              </button>
              <button className="btn btn-primario" type="button" onClick={exportarCSVHoje}>
                Exportar CSV
              </button>
            </div>
          </div>
        </div>

        <div style={{ height: 12 }} />

        <div style={{ display: "grid", gridTemplateColumns: "repeat(4, minmax(0, 1fr))", gap: 12 }}>
          {badge("Total", relStats.total)}
          {badge("Abertas", resumoTriagem?.abertas ?? "—")}
          {badge("Encerradas", resumoTriagem?.encerradas ?? "—")}
          {badge("Convertidas", resumoTriagem?.convertidas ?? "—")}
        </div>

        <div style={{ height: 12 }} />

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 12 }}>
          <div className="card" style={{ padding: 12, borderRadius: 18 }}>
            <h3 style={{ margin: 0 }}>Por prioridade</h3>
            <div style={{ display: "grid", gap: 6, marginTop: 10 }}>
              {relStats.porPrioridade.map(([k, v]) => (
                <div key={k} style={{ display: "flex", justifyContent: "space-between", gap: 10 }}>
                  <span className="texto-suave">{k}</span>
                  <b>{v}</b>
                </div>
              ))}
            </div>
          </div>

          <div className="card" style={{ padding: 12, borderRadius: 18 }}>
            <h3 style={{ margin: 0 }}>Por canal</h3>
            <div style={{ display: "grid", gap: 6, marginTop: 10 }}>
              {relStats.porCanal.map(([k, v]) => (
                <div key={k} style={{ display: "flex", justifyContent: "space-between", gap: 10 }}>
                  <span className="texto-suave">{k}</span>
                  <b>{v}</b>
                </div>
              ))}
            </div>
          </div>

          <div className="card" style={{ padding: 12, borderRadius: 18 }}>
            <h3 style={{ margin: 0 }}>Por status</h3>
            <div style={{ display: "grid", gap: 6, marginTop: 10 }}>
              {relStats.porStatus.map(([k, v]) => (
                <div key={k} style={{ display: "flex", justifyContent: "space-between", gap: 10 }}>
                  <span className="texto-suave">{k}</span>
                  <b>{v}</b>
                </div>
              ))}
            </div>
          </div>
        </div>
      </>
    );
  }

  return (
    <div className="layout-1col">
      {msg ? (
        <div className="card" style={{ padding: 12, borderRadius: 14 }}>
          <strong>{msg}</strong>
        </div>
      ) : null}

      {/* Linha leve de contexto (sem poluição) */}
      {activeView !== "unidade" ? (
        <div className="texto-suave" style={{ margin: "6px 0 10px" }}>
          Unidade ativa: <b>{unidadeNome}</b> · para trocar, vá em <b>“Unidade CRAS”</b>.
        </div>
      ) : null}

      {activeView === "unidade" ? renderUnidade() : null}
      {activeView === "fila" ? renderFilaComPaif() : null}
      {activeView === "pendencias" ? renderPendencias() : null}
      {activeView === "historico" ? renderHistorico() : null}
      {activeView === "relatorios" ? renderRelatorios() : null}

      {/* fallback */}
      {!activeView ? (
        <div className="card" style={{ padding: 12, borderRadius: 18 }}>
          <div className="texto-suave">Selecione uma subtela no topo.</div>
        </div>
      ) : null}
    </div>
  );
}
