import React, { useEffect, useMemo, useState } from "react";
import { API_BASE } from "./config";

/**
 * SAÚDE (INTERSETORIAL) — MÍNIMO NECESSÁRIO (LGPD)
 * - NÃO é prontuário clínico.
 * - Registra apenas: necessidade/urgência, serviço de referência, agenda e status de comparecimento/retorno.
 *
 * Endpoints esperados:
 * - GET  /saude/etapas
 * - GET  /saude/casos/{caso_id}/intersetorial
 * - POST /saude/casos/{caso_id}/intersetorial
 *
 * Props:
 * - apiBase: string
 * - apiFetch: function(url, options) => fetch Response (com Bearer)
 * - usuarioLogado: { nome, perfil, ... }
 * - municipios: array (opcional)
 * - pessoa: objeto pessoa (opcional)
 * - casos: array de casos (para escolher o caso)
 * - casoIdInicial: id do caso pré-selecionado (opcional)
 */
function formatarDataHora(isoString) {
  if (!isoString) return "—";
  try {
    const d = new Date(isoString);
    if (isNaN(d.getTime())) return isoString;
    const dia = String(d.getDate()).padStart(2, "0");
    const mes = String(d.getMonth() + 1).padStart(2, "0");
    const ano = d.getFullYear();
    const hora = String(d.getHours()).padStart(2, "0");
    const min = String(d.getMinutes()).padStart(2, "0");
    return `${dia}/${mes}/${ano} ${hora}:${min}`;
  } catch {
    return isoString;
  }
}

function toInt(v) {
  const n = Number(v);
  return Number.isFinite(n) ? n : null;
}

function nomePessoa(p) {
  if (!p) return "Pessoa";
  return p.nome_social || p.nome_civil || "Pessoa";
}

function getTokenFallback() {
  return localStorage.getItem("poprua_token") || localStorage.getItem("access_token") || "";
}

function labelMetro(st) {
  if (st === "concluida") return "Concluída";
  if (st === "em_andamento") return "Em andamento";
  return "Não iniciada";
}

export default function TelaSaudeIntersetorial({
  apiBase = API_BASE,
  apiFetch,
  usuarioLogado,
  municipios = [],
  pessoa = null,
  casos = [],
  casoIdInicial = "",
}) {
  const [casoId, setCasoId] = useState("");
  const [etapas, setEtapas] = useState([]);
  const [registros, setRegistros] = useState([]);

  const [loading, setLoading] = useState(false);
  const [erro, setErro] = useState("");

  // Form (próximo passo)
  const [prioridade, setPrioridade] = useState("rotina"); // rotina | urgente | emergencia
  const [servico, setServico] = useState("UBS");
  const [dataHora, setDataHora] = useState("");
  const [statusAtendimento, setStatusAtendimento] = useState("encaminhado"); // encaminhado | agendado | compareceu | nao_compareceu | retorno_registrado
  const [obs, setObs] = useState("");

  const casosOrdenados = useMemo(() => {
    const arr = Array.isArray(casos) ? [...casos] : [];
    arr.sort((a, b) => Number(b?.id || 0) - Number(a?.id || 0));
    return arr;
  }, [casos]);

  // aplica casoIdInicial quando entrar na tela (ou quando mudar)
  useEffect(() => {
    const cid = (casoIdInicial ?? "").toString().trim();
    if (!cid) return;
    setCasoId((prev) => (String(prev) === String(cid) ? prev : String(cid)));
  }, [casoIdInicial]);

  // fallback: escolhe caso mais recente se não houver casoId selecionado
  useEffect(() => {
    if (!casoId && casosOrdenados.length > 0) {
      setCasoId(String(casosOrdenados[0].id));
      return;
    }
    if (casoId && casosOrdenados.length > 0) {
      const existe = casosOrdenados.some((c) => String(c.id) === String(casoId));
      if (!existe) setCasoId(String(casosOrdenados[0].id));
    }
    if (casosOrdenados.length === 0) setCasoId("");
  }, [casosOrdenados, casoId]);

  const mapaMunicipios = useMemo(() => {
    const m = new Map();
    (municipios || []).forEach((x) => {
      const id = Number(x?.id);
      if (!isNaN(id)) m.set(id, x?.nome || x?.nome_municipio || "Município");
    });
    return m;
  }, [municipios]);

  const casoAtual = useMemo(() => {
    const id = toInt(casoId);
    if (!id) return null;
    return casosOrdenados.find((c) => Number(c?.id) === id) || null;
  }, [casoId, casosOrdenados]);

  const municipioCasoNome = useMemo(() => {
    const mid = casoAtual?.municipio_id;
    if (mid == null) return "—";
    return mapaMunicipios.get(Number(mid)) || "Município";
  }, [casoAtual, mapaMunicipios]);

  async function fetchComAuth(url, options = {}) {
    if (typeof apiFetch === "function") return apiFetch(url, options);

    const token = getTokenFallback();
    return fetch(url, {
      ...options,
      headers: {
        ...(options.headers || {}),
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
    });
  }

  async function carregarEtapas() {
    try {
      const res = await fetchComAuth(`${apiBase}/saude/etapas`);
      if (!res.ok) return;
      const data = await res.json();
      if (Array.isArray(data)) setEtapas(data);
    } catch {
      // silencioso
    }
  }

  async function carregarRegistros(cId) {
    const id = toInt(cId);
    if (!id) {
      setRegistros([]);
      return;
    }

    setErro("");
    setLoading(true);
    try {
      const res = await fetchComAuth(`${apiBase}/saude/casos/${id}/intersetorial`);
      if (!res.ok) {
        const txt = await res.text().catch(() => "");
        throw new Error(`Falha ao carregar Saúde (HTTP ${res.status}). ${txt}`);
      }
      const data = await res.json();
      setRegistros(Array.isArray(data) ? data : []);
    } catch (e) {
      setErro(e?.message || "Erro ao carregar Saúde (intersetorial).");
      setRegistros([]);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    carregarEtapas();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    carregarRegistros(casoId);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [casoId]);

  // ==== FLUXO (linha do metrô) - intersetorial (sem prontuário)
  const etapasDefault = useMemo(
    () => [
      {
        codigo: "ENCAMINHAMENTO",
        ordem: 1,
        nome: "Encaminhamento",
        descricao: "Necessita avaliação em saúde + serviço de referência.",
      },
      {
        codigo: "AGENDAMENTO",
        ordem: 2,
        nome: "Agendamento",
        descricao: "Data/hora e local (quando houver).",
      },
      {
        codigo: "ATENDIMENTO",
        ordem: 3,
        nome: "Atendimento",
        descricao: "Compareceu / não compareceu (sem detalhes clínicos).",
      },
      {
        codigo: "RETORNO",
        ordem: 4,
        nome: "Retorno",
        descricao: "Retorno intersetorial (próximos passos logísticos).",
      },
    ],
    []
  );

  const etapasUsadas = useMemo(() => {
    if (Array.isArray(etapas) && etapas.length > 0) return etapas;
    return etapasDefault;
  }, [etapas, etapasDefault]);

  const etapaAtual = useMemo(() => {
    const r = Array.isArray(registros) ? registros[0] : null;
    const p = r?.payload || {};
    const etapa = p.etapa || p.etapa_codigo || p.etapaAtu || p.status_etapa || null;
    const status = p.status || p.status_atendimento || null;

    const codigos = etapasUsadas.map((e) => e.codigo);
    if (etapa && codigos.includes(etapa)) return etapa;

    if (status === "agendado") return "AGENDAMENTO";
    if (status === "compareceu" || status === "nao_compareceu") return "ATENDIMENTO";
    if (status === "retorno_registrado") return "RETORNO";

    return "ENCAMINHAMENTO";
  }, [registros, etapasUsadas]);

  function idxEtapa(cod) {
    const i = etapasUsadas.findIndex((e) => e.codigo === cod);
    return i < 0 ? 0 : i;
  }

  function statusUI(etapaCod) {
    const iAtual = idxEtapa(etapaAtual);
    const i = idxEtapa(etapaCod);
    if (i < iAtual) return "concluida";
    if (i === iAtual) return "em_andamento";
    return "nao_iniciada";
  }

  const proximoPasso = useMemo(() => {
    const ordem = etapasUsadas.map((e) => e.codigo);
    const i = ordem.indexOf(etapaAtual);
    if (i < 0) return ordem[0] || "ENCAMINHAMENTO";
    return ordem[Math.min(i + 1, ordem.length - 1)];
  }, [etapasUsadas, etapaAtual]);

  function placeholderPorPasso(passo) {
    if (passo === "ENCAMINHAMENTO")
      return "Ex.: Necessita avaliação em saúde; encaminhado para UBS/UPA/CAPS. (Sem diagnóstico, sem CID, sem medicação).";
    if (passo === "AGENDAMENTO")
      return "Ex.: Agendamento informado pela unidade. Local de referência e orientações de chegada.";
    if (passo === "ATENDIMENTO") return "Ex.: Compareceu / não compareceu. (Sem relato clínico).";
    return "Ex.: Próximos passos logísticos para continuidade (sem detalhes clínicos).";
  }

  async function registrar() {
    const id = toInt(casoId);
    if (!id) {
      setErro("Selecione um caso Pop Rua para registrar Saúde (intersetorial).");
      return;
    }

    setErro("");

    if (!obs.trim()) {
      setErro("Escreva uma observação intersetorial (sem clínica).");
      return;
    }

    const payload = {
      tipo_registro: "intersetorial",
      etapa: proximoPasso,
      prioridade,
      servico,
      status: statusAtendimento,
      data_hora: dataHora ? new Date(dataHora).toISOString() : null,
      observacao: obs.trim(),
    };

    setLoading(true);
    try {
      const res = await fetchComAuth(`${apiBase}/saude/casos/${id}/intersetorial`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const txt = await res.text().catch(() => "");
        throw new Error(`Falha ao registrar (HTTP ${res.status}). ${txt}`);
      }

      setObs("");
      setDataHora("");
      await carregarRegistros(id);
    } catch (e) {
      setErro(e?.message || "Erro ao registrar Saúde (intersetorial).");
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="card card-wide">
      <div className="card-header-row">
        <div>
          <h2 style={{ margin: 0 }}>Saúde (intersetorial)</h2>
          <p className="card-subtitle" style={{ marginTop: 6 }}>
            Registro mínimo necessário para fluxo com a Saúde (LGPD). <strong>Não</strong> é prontuário clínico.
          </p>
          <p className="texto-suave" style={{ marginTop: 6 }}>
            Pessoa: <strong>{nomePessoa(pessoa)}</strong>{" "}
            {casoAtual ? (
              <>
                · Caso: <strong>#{casoAtual.id}</strong> · Município: <strong>{municipioCasoNome}</strong>
              </>
            ) : (
              <>· Selecione um caso abaixo</>
            )}
          </p>
        </div>

        <div style={{ display: "flex", gap: 8 }}>
          <button type="button" className="btn btn-secundario" onClick={() => carregarRegistros(casoId)} disabled={loading}>
            {loading ? "Carregando..." : "Recarregar"}
          </button>
        </div>
      </div>

      {/* seletor de caso */}
      <div className="grid-2cols" style={{ marginTop: 10 }}>
        <label className="form-label">
          Caso Pop Rua
          <select className="input" value={casoId} onChange={(e) => setCasoId(e.target.value)}>
            {casosOrdenados.length === 0 ? (
              <option value="">Nenhum caso — crie um caso Pop Rua</option>
            ) : (
              <>
                <option value="">Selecione...</option>
                {casosOrdenados.map((c) => (
                  <option key={c.id} value={c.id}>
                    Caso #{c.id} · Etapa {c.etapa_atual || "—"} · {c.status || "—"}
                  </option>
                ))}
              </>
            )}
          </select>
        </label>

        <div className="texto-suave" style={{ alignSelf: "end" }}>
          Regra: aqui só entra logística/fluxo. <strong>Sem diagnóstico</strong>, sem CID, sem medicação.
        </div>
      </div>

      {erro && (
        <p className="erro-global" style={{ marginTop: 10 }}>
          {erro}
        </p>
      )}

      {/* FLUXO — padrão visual do metrô do Pop Rua */}
      <div style={{ marginTop: 14 }}>
        <h3 style={{ margin: 0 }}>Fluxo</h3>
        <p className="texto-suave" style={{ marginTop: 6 }}>
          Estado atual: <strong>{etapaAtual}</strong>
        </p>

        <div className="linha-metro metro-elegante metro-premium" style={{ marginTop: 10 }}>
          {etapasUsadas.map((e) => {
            const st = statusUI(e.codigo);
            return (
              <div key={e.codigo} className={`etapa-linha metro-card metro-card-${st}`}>
                <div className={`etapa-bolinha etapa-bolinha-${st}`} aria-hidden="true" />

                <div className="etapa-conteudo">
                  <div className="etapa-titulo">
                    {e.ordem}. {e.nome}
                  </div>
                  <div className="etapa-descricao">{e.descricao}</div>
                </div>

                <span className={`badge-status badge-pequena badge-${st}`}>{labelMetro(st)}</span>
              </div>
            );
          })}
        </div>
      </div>

      {/* registrar próximo passo */}
      <div style={{ marginTop: 16 }}>
        <h3 style={{ margin: 0 }}>Registrar atualização</h3>
        <p className="texto-suave" style={{ marginTop: 6 }}>
          Próximo passo sugerido: <strong>{proximoPasso}</strong>
        </p>

        <div className="grid-2cols" style={{ marginTop: 10 }}>
          <label className="form-label">
            Prioridade
            <select className="input" value={prioridade} onChange={(e) => setPrioridade(e.target.value)}>
              <option value="rotina">Rotina</option>
              <option value="urgente">Urgente</option>
              <option value="emergencia">Emergência</option>
            </select>
          </label>

          <label className="form-label">
            Serviço de referência
            <select className="input" value={servico} onChange={(e) => setServico(e.target.value)}>
              <option value="UBS">UBS</option>
              <option value="UPA">UPA</option>
              <option value="CAPS">CAPS</option>
              <option value="CONSULTORIO_NA_RUA">Consultório na Rua</option>
              <option value="OUTRO">Outro</option>
            </select>
          </label>

          <label className="form-label">
            Data/hora (se agendado)
            <input type="datetime-local" className="input" value={dataHora} onChange={(e) => setDataHora(e.target.value)} />
          </label>

          <label className="form-label">
            Status do encaminhamento
            <select className="input" value={statusAtendimento} onChange={(e) => setStatusAtendimento(e.target.value)}>
              <option value="encaminhado">Encaminhado</option>
              <option value="agendado">Agendado</option>
              <option value="compareceu">Compareceu</option>
              <option value="nao_compareceu">Não compareceu</option>
              <option value="retorno_registrado">Retorno registrado</option>
            </select>
          </label>
        </div>

        <label className="form-label" style={{ marginTop: 10 }}>
          Observação intersetorial (sem clínica)
          <textarea className="input" rows={3} value={obs} onChange={(e) => setObs(e.target.value)} placeholder={placeholderPorPasso(proximoPasso)} />
        </label>

        <div className="card-footer-right">
          <button type="button" className="btn btn-primario" onClick={registrar} disabled={loading || !casoId}>
            {loading ? "Salvando..." : "Registrar"}
          </button>
        </div>
      </div>

      {/* histórico */}
      <div style={{ marginTop: 18 }}>
        <h3 style={{ margin: 0 }}>Histórico</h3>
        <p className="texto-suave" style={{ marginTop: 6 }}>
          Mostra quem registrou e quando (auditoria).
        </p>

        {registros.length === 0 ? (
          <p className="texto-suave" style={{ marginTop: 10 }}>
            Sem registros de saúde (intersetorial) para este caso.
          </p>
        ) : (
          <ul className="lista-atendimentos" style={{ marginTop: 10 }}>
            {registros.slice(0, 12).map((r) => {
              const p = r?.payload || {};
              return (
                <li key={r.id} className="item-atendimento">
                  <div className="item-atendimento-header">
                    <div>
                      <div className="item-atendimento-titulo">{p.etapa || r.tipo_registro || "Registro"}</div>
                      <div className="item-atendimento-sub">
                        {formatarDataHora(r.criado_em)} · Por: {r.criado_por_nome || "—"} · Status: {p.status || "—"}
                      </div>
                    </div>
                    <span className="badge-status badge-pequena">{(p.prioridade || "rotina").toString().replace(/_/g, " ")}</span>
                  </div>

                  <div className="item-atendimento-texto" style={{ marginTop: 6 }}>
                    <div>
                      <strong>Serviço:</strong> {(p.servico || "—").toString().replace(/_/g, " ")}
                    </div>
                    {p.data_hora ? (
                      <div>
                        <strong>Data/hora:</strong> {formatarDataHora(p.data_hora)}
                      </div>
                    ) : null}
                    {p.observacao ? <div style={{ marginTop: 6 }}>{String(p.observacao).slice(0, 300)}</div> : null}
                  </div>
                </li>
              );
            })}
          </ul>
        )}
      </div>
    </section>
  );
}