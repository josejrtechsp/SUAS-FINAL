import React, { useMemo, useState } from "react";

/**
 * LinhaMetro (Padrão do sistema)
 *
 * Compatibilidade:
 * 1) Modo DETALHADO (padrão CRAS/PopRua): quando receber `linhaMetro` (objeto com `etapas`).
 * 2) Modo SIMPLES: quando receber `etapas` + `etapaAtual` (mantém usos antigos).
 */
export default function LinhaMetro(props) {
  if (props?.linhaMetro && Array.isArray(props.linhaMetro.etapas)) {
    return <LinhaMetroDetalhado {...props} />;
  }
  return <LinhaMetroSimples {...props} />;
}

function LinhaMetroSimples({
  title = "Fluxo",
  etapas = [],
  etapaAtual = null, // pode ser string (key) ou número (index)
  nextLabel = "",
}) {
  const steps = (etapas || []).map((e, i) =>
    typeof e === "string"
      ? { key: e, title: e }
      : { key: e.key ?? String(i), title: e.title ?? String(e), subtitle: e.subtitle }
  );

  let currentIndex = 0;
  if (typeof etapaAtual === "number") currentIndex = etapaAtual;
  if (typeof etapaAtual === "string") {
    const idx = steps.findIndex((s) => s.key === etapaAtual || s.title === etapaAtual);
    currentIndex = idx >= 0 ? idx : 0;
  }

  return (
    <div
      style={{
        borderRadius: 22,
        padding: 16,
        background: "rgba(255,255,255,0.70)",
        border: "1px solid rgba(0,0,0,0.06)",
        boxShadow: "0 18px 60px rgba(0,0,0,0.12)",
        backdropFilter: "blur(10px)",
        WebkitBackdropFilter: "blur(10px)",
      }}
    >
      <div style={{ fontWeight: 900, marginBottom: 10 }}>{title}</div>

      {nextLabel ? (
        <div
          style={{
            borderRadius: 14,
            padding: "10px 12px",
            background: "rgba(122,92,255,0.10)",
            border: "1px solid rgba(122,92,255,0.18)",
            marginBottom: 12,
            fontWeight: 800,
            color: "rgba(92,74,220,1)",
          }}
        >
          {nextLabel}
        </div>
      ) : null}

      <div style={{ display: "grid", gap: 10 }}>
        {steps.map((s, i) => {
          const isDone = i < currentIndex;
          const isCurrent = i === currentIndex;

          return (
            <div key={s.key} style={{ display: "grid", gridTemplateColumns: "24px 1fr", gap: 12 }}>
              <div style={{ display: "flex", flexDirection: "column", alignItems: "center" }}>
                <div
                  style={{
                    width: 14,
                    height: 14,
                    borderRadius: 999,
                    border: "2px solid rgba(122,92,255,0.45)",
                    background: isCurrent
                      ? "rgba(122,92,255,0.95)"
                      : isDone
                      ? "rgba(122,92,255,0.55)"
                      : "rgba(255,255,255,0.9)",
                    boxShadow: isCurrent ? "0 10px 24px rgba(122,92,255,0.25)" : "none",
                    marginTop: 3,
                  }}
                />
                {i < steps.length - 1 ? (
                  <div
                    style={{
                      width: 2,
                      flex: 1,
                      background: isDone ? "rgba(122,92,255,0.35)" : "rgba(0,0,0,0.10)",
                      marginTop: 6,
                      borderRadius: 999,
                      minHeight: 18,
                    }}
                  />
                ) : null}
              </div>

              <div
                style={{
                  borderRadius: 16,
                  padding: "10px 12px",
                  border: isCurrent ? "1px solid rgba(122,92,255,0.25)" : "1px solid rgba(0,0,0,0.06)",
                  background: isCurrent ? "rgba(122,92,255,0.08)" : "rgba(255,255,255,0.55)",
                }}
              >
                <div style={{ fontWeight: 900, opacity: isDone ? 0.8 : 1 }}>{s.title}</div>
                {s.subtitle ? (
                  <div style={{ fontSize: 12, opacity: 0.7, marginTop: 2 }}>{s.subtitle}</div>
                ) : null}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function LinhaMetroDetalhado({
  linhaMetro,
  casoId,
  apiBase,
  apiFetch,
  atendimentos = [],
  encaminhamentos: encaminhamentosProp = [],
  municipios = [],
  onRefresh,
  onRegisterLocal,
  currentKey,
}) {
  const [openCodigo, setOpenCodigo] = useState(null);
  const [modalEtapa, setModalEtapa] = useState(null);
  const [obs, setObs] = useState("");
  const [atendimentoId, setAtendimentoId] = useState("");
  const [encaminhamentos, setEncaminhamentos] = useState([]);
  const [encSel, setEncSel] = useState({});
  const [loadingEnc, setLoadingEnc] = useState(false);
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState("");

  const etapas = Array.isArray(linhaMetro?.etapas) ? linhaMetro.etapas : [];

  const statusByCodigo = useMemo(() => {
    const cur = String(currentKey || linhaMetro?.etapa_atual || linhaMetro?.etapaAtual || "").trim();
    if (!cur) return {};
    const idx = etapas.findIndex((e) => String(e?.codigo || e?.key || "") === cur);
    const curIndex = idx >= 0 ? idx : 0;
    const map = {};
    etapas.forEach((e, i) => {
      const codigo = String(e?.codigo || e?.key || i);
      if (i < curIndex) map[codigo] = "concluida";
      else if (i === curIndex) map[codigo] = "em_andamento";
      else map[codigo] = "nao_iniciada";
    });
    return map;
  }, [etapas, currentKey]);

  function label(st) {
    if (st === "concluida") return "Concluída";
    if (st === "em_andamento") return "Em andamento";
    return "Não iniciada";
  }

  function fmtDataHora(iso) {
    if (!iso) return "—";
    const d = new Date(iso);
    if (isNaN(d.getTime())) return String(iso);
    return d.toLocaleString("pt-BR");
  }

  function nomeMunicipio(mId) {
    const id = Number(mId);
    const m = (municipios || []).find((x) => Number(x?.id) === id);
    return m?.nome || m?.nome_municipio || (mId != null ? String(mId) : "—");
  }

  function labelEnc(e) {
    if (!e) return "—";
    const found = (e?.id != null && Array.isArray(encaminhamentosProp))
      ? (encaminhamentosProp || []).find((x) => String(x?.id) === String(e.id))
      : null;
    const x = found ? { ...e, ...found } : e;
    // modo intermunicipal (CRAS/PopRua)
    if (x.municipio_origem_id != null || x.municipio_destino_id != null) {
      return `${nomeMunicipio(x.municipio_origem_id)} → ${nomeMunicipio(x.municipio_destino_id)} — ${x.status || ""}`.trim();
    }
    // modo rede (CREAS local)
    if (x.destino) {
      return `${x.destino}${x.status ? ` — ${x.status}` : ""}`;
    }
    return x.status ? String(x.status) : "—";
  }

  async function abrirModalRegistrar(codigo) {
    setMsg("");
    setModalEtapa(codigo);
    setObs("");
    setAtendimentoId("");
    setEncSel({});

    // lista de encaminhamentos para seleção
    if (apiFetch && apiBase && casoId != null) {
      setLoadingEnc(true);
      try {
        const res = await apiFetch(`${apiBase}/encaminhamentos/?caso_id=${Number(casoId)}`);
        if (res.ok) {
          const data = await res.json();
          setEncaminhamentos(Array.isArray(data) ? data : []);
        } else {
          setEncaminhamentos([]);
        }
      } catch {
        setEncaminhamentos([]);
      } finally {
        setLoadingEnc(false);
      }
    } else {
      // modo local (CREAS)
      setEncaminhamentos(Array.isArray(encaminhamentosProp) ? encaminhamentosProp : []);
      setLoadingEnc(false);
    }
  }

  async function salvarRegistro() {
    if (!modalEtapa) return;
    setSaving(true);
    setMsg("");

    const ids = Object.keys(encSel)
      .filter((k) => encSel[k])
      .map((k) => {
        const n = Number(k);
        return Number.isNaN(n) ? k : n;
      })
      .filter((v) => v !== "" && v != null);

    const body = {
      etapa: modalEtapa,
      obs: obs || null,
      atendimento_id: atendimentoId || null,
      encaminhamentos_ids: ids,
    };

    try {
      if (apiFetch && apiBase && casoId != null) {
        const res = await apiFetch(`${apiBase}/casos/${Number(casoId)}/linha-metro/registrar`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body),
        });

        if (!res.ok) {
          const txt = await res.text().catch(() => "");
          setMsg(`Falha ao registrar: HTTP ${res.status}. ${txt || ""}`);
          return;
        }
      } else if (typeof onRegisterLocal === "function") {
        await onRegisterLocal(body);
      } else {
        setMsg("Falha ao registrar: modo inválido (sem API e sem callback local).");
        return;
      }

      setModalEtapa(null);
      if (typeof onRefresh === "function") {
        await onRefresh();
      }
    } catch (e) {
      setMsg(`Falha ao registrar: ${e?.message || "erro"}`);
    } finally {
      setSaving(false);
    }
  }

  if (!Array.isArray(etapas) || etapas.length === 0) return null;

  return (
    <div>
      <div className="linha-metro metro-elegante metro-premium">
        {etapas.map((etapa, i) => {
          const codigo = etapa?.codigo || etapa?.key || String(i);
          const st = etapa?.status || statusByCodigo[String(codigo)] || "nao_iniciada";
          const aberto = openCodigo === codigo;
          const ordemTxt = etapa?.ordem != null ? `${etapa.ordem}. ` : "";
          const ur = etapa?.ultimo_registro || null;
          const regs = Array.isArray(etapa?.registros) ? etapa.registros : [];

          return (
            <div key={codigo} className={`etapa-linha metro-card metro-card-${st}`}>
              <button
                type="button"
                className="metro-click"
                onClick={() => setOpenCodigo(aberto ? null : codigo)}
              >
                <div className={`etapa-bolinha etapa-bolinha-${st}`} aria-hidden="true" />

                <div className="etapa-conteudo">
                  <div className="etapa-titulo">
                    {ordemTxt}
                    {etapa?.nome || etapa?.title || "Etapa"}
                  </div>
                  <div className="etapa-descricao">{etapa?.descricao || etapa?.description || ""}</div>
                  {Number.isFinite(Number(etapa?.sla_dias)) ? (
                    <div className="texto-suave" style={{ marginTop: 2, fontSize: 12 }}>
                      SLA: {Number(etapa.sla_dias)} dias
                    </div>
                  ) : null}
                </div>

                <span className={`badge-status badge-pequena badge-${st}`}>{label(st)}</span>
              </button>

              {aberto ? (
                <div className="metro-detalhe">
                  <div className="metro-detalhe-top">
                    <div>
                      <div className="metro-detalhe-titulo">Último registro</div>
                      {ur ? (
                        <div className="texto-suave" style={{ marginTop: 6 }}>
                          <div>
                            <strong>Responsável:</strong> {ur?.responsavel_nome || "—"}
                          </div>
                          <div>
                            <strong>Data/hora:</strong> {fmtDataHora(ur?.data_hora)}
                          </div>
                          {ur?.atendimento_id ? (
                            <div>
                              <strong>Atendimento:</strong> #{ur.atendimento_id}
                            </div>
                          ) : null}
                          {ur?.obs ? (
                            <div style={{ marginTop: 6 }}>
                              <strong>Obs:</strong> {ur.obs}
                            </div>
                          ) : null}
                        </div>
                      ) : (
                        <div className="texto-suave" style={{ marginTop: 6 }}>
                          Nenhum registro ainda para esta etapa.
                        </div>
                      )}
                    </div>

                    <div style={{ display: "flex", gap: 10, alignItems: "center", flexWrap: "wrap" }}>
                      <button
                        type="button"
                        className="btn btn-secundario btn-secundario-mini"
                        onClick={() => abrirModalRegistrar(codigo)}
                        disabled={apiFetch && casoId == null}
                      >
                        Registrar avanço
                      </button>
                    </div>
                  </div>

                  {ur?.encaminhamentos?.length ? (
                    <div className="metro-box">
                      <div className="metro-box-title">Encaminhamentos vinculados</div>
                      <ul className="metro-list">
                        {ur.encaminhamentos.map((e) => (
                          <li key={e.id || Math.random()}>
                            <strong>#{e.id || "—"}</strong> — {labelEnc(e)}
                          </li>
                        ))}
                      </ul>
                    </div>
                  ) : null}

                  {regs.length ? (
                    <div className="metro-box">
                      <div className="metro-box-title">Histórico da etapa (últimos registros)</div>
                      <ul className="metro-list">
                        {regs.slice(0, 5).map((r) => (
                          <li key={r.id || Math.random()}>
                            <div>
                              <strong>{r.responsavel_nome || "—"}</strong> — {fmtDataHora(r.data_hora)}
                            </div>
                            {r.obs ? <div className="muted">{r.obs}</div> : null}
                            {r.encaminhamentos?.length ? (
                              <div className="muted">
                                Encaminhamentos: {r.encaminhamentos.map((x) => `#${x.id}`).join(", ")}
                              </div>
                            ) : null}
                          </li>
                        ))}
                      </ul>
                    </div>
                  ) : null}
                </div>
              ) : null}
            </div>
          );
        })}
      </div>

      {modalEtapa ? (
        <div className="modal-overlay" role="dialog" aria-modal="true">
          <div className="modal-card">
            <div className="modal-header">
              <div>
                <div className="modal-title">Registrar avanço — {modalEtapa}</div>
                <div className="muted">Registra histórico (não muda etapa automaticamente).</div>
              </div>
              <button
                type="button"
                className="btn btn-secundario btn-secundario-mini"
                onClick={() => setModalEtapa(null)}
              >
                Fechar
              </button>
            </div>

            {msg ? <div className="erro-global" style={{ marginTop: 10 }}>{msg}</div> : null}

            <div className="modal-body">
              <label className="form-label">
                Observação (curta)
                <textarea className="input" rows={3} value={obs} onChange={(e) => setObs(e.target.value)} />
              </label>

              <label className="form-label">
                Vincular atendimento (opcional)
                <select className="input" value={atendimentoId} onChange={(e) => setAtendimentoId(e.target.value)}>
                  <option value="">Não vincular</option>
                  {(atendimentos || []).map((a) => (
                    <option key={a.id} value={a.id}>
                      #{a.id} — {(a.tipo_atendimento || a.tipo || "atendimento")} — {a.data_atendimento ? new Date(a.data_atendimento).toLocaleDateString("pt-BR") : a.data_hora ? new Date(a.data_hora).toLocaleDateString("pt-BR") : ""}
                    </option>
                  ))}
                </select>
              </label>

              <div className="form-label" style={{ marginTop: 6 }}>
                Vincular encaminhamentos (opcional)
              </div>
              <div className="metro-enc-list">
                {loadingEnc ? (
                  <div className="texto-suave">Carregando encaminhamentos…</div>
                ) : encaminhamentos.length ? (
                  encaminhamentos.map((e) => (
                    <label key={e.id} className="metro-enc-item">
                      <input
                        type="checkbox"
                        checked={!!encSel[e.id]}
                        onChange={(ev) => setEncSel({ ...encSel, [e.id]: ev.target.checked })}
                      />
                      <span>
                        <strong>#{e.id}</strong> — {labelEnc(e)}
                      </span>
                    </label>
                  ))
                ) : (
                  <div className="texto-suave">Nenhum encaminhamento encontrado para este caso.</div>
                )}
              </div>
            </div>

            <div className="modal-footer">
              <button type="button" className="btn" onClick={salvarRegistro} disabled={saving}>
                {saving ? "Salvando…" : "Salvar registro"}
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
