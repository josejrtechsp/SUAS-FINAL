import React, { useEffect, useMemo, useRef, useState } from "react";
import { API_BASE } from "./config.js";
import { setCreasSelectedCaseId } from "./domain/creasStore.js";

import ErrorBoundary from "./components/ErrorBoundary.jsx";
import GestaoTopHeader from "./components/GestaoTopHeader.jsx";
import GestaoPageHeader from "./components/GestaoPageHeader.jsx";

/**
 * Gestão (Dashboard do Secretário)
 * - Consolida CRAS + PopRua + CREAS + Rede (encaminhamentos) + OSC (quando existir)
 * - Consome /gestao/dashboard/resumo, /gestao/dashboard/sla, /gestao/fila
 */

function fmtNum(v) {
  const n = Number(v || 0);
  return Number.isFinite(n) ? n.toLocaleString("pt-BR") : "0";
}

function normStr(v) {
  return String(v || "").trim().toLowerCase();
}

function isPctKpi(kpi) {
  return normStr(kpi).startsWith("pct_");
}

function fmtPct(v) {
  const n = Number(v);
  if (!Number.isFinite(n)) return "—";
  return `${n.toFixed(1)}%`;
}

function fmtHours(v) {
  const n = Number(v);
  if (!Number.isFinite(n)) return "—";
  if (n < 1) return `${Math.round(n * 60)} min`;
  return `${n.toFixed(1)} h`;
}

function fmtDays(v) {
  const n = Number(v);
  if (!Number.isFinite(n)) return "—";
  return `${n.toFixed(1)} d`;
}

function fmtDateTime(iso) {
  if (!iso) return "—";
  try {
    const d = new Date(iso);
    if (Number.isNaN(d.getTime())) return String(iso);
    return d.toLocaleString("pt-BR");
  } catch {
    return String(iso);
  }
}

function buildQS(params) {
  const qs = new URLSearchParams();
  Object.entries(params || {}).forEach(([k, v]) => {
    if (v === null || v === undefined || v === "") return;
    qs.set(k, String(v));
  });
  const s = qs.toString();
  return s ? `?${s}` : "";
}

function KpiCard({ label, value, hint, tone }) {
  const cls = "gestao-kpi" + (tone === "warn" ? " gestao-kpi-warn" : tone === "bad" ? " gestao-kpi-bad" : "");
  return (
    <div className={cls}>
      <div className="gestao-kpi-label">{label}</div>
      <div className="gestao-kpi-number">{value}</div>
      {hint ? <div className="gestao-kpi-sub">{hint}</div> : null}
    </div>
  );
}

function Table({ columns, rows, emptyText = "Sem dados." }) {
  return (
    <div className="regional-table-wrapper">
      <table className="regional-table">
        <thead>
          <tr>
            {columns.map((c) => (
              <th key={c.key}>{c.label}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {!rows?.length ? (
            <tr>
              <td colSpan={columns.length} style={{ padding: 14, color: "#6b7280" }}>
                {emptyText}
              </td>
            </tr>
          ) : (
            rows.map((r, idx) => (
              <tr key={r.id || r.key || idx}>
                {columns.map((c) => (
                  <td key={c.key}>{typeof c.render === "function" ? c.render(r) : r?.[c.key]}</td>
                ))}
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}

export default function GestaoApp({ usuarioLogado, onLogout }) {
  // Tabs
  const tabs = useMemo(
    () => [
      { key: "visao", label: "Visão" },
      { key: "sla", label: "SLA & Gargalos" },
      { key: "fila", label: "Fila de Pendências" },
      { key: "rede", label: "Rede" },
    ],
    []
  );

  const [activeTab, setActiveTab] = useState(() => localStorage.getItem("gestao_active_tab") || "visao");
  useEffect(() => {
    try {
      localStorage.setItem("gestao_active_tab", activeTab);
    } catch {}
  }, [activeTab]);

  // Filtros (escopo)
  const perfil = String(usuarioLogado?.perfil || "").toLowerCase();
  const isGlobal = perfil === "admin" || perfil === "gestor_consorcio";

  const [municipios, setMunicipios] = useState([]);
  const [municipioAtivoId, setMunicipioAtivoId] = useState(() => {
    const fromUser = usuarioLogado?.municipio_id;
    const fromLs = localStorage.getItem("gestao_municipio_ativo");
    return isGlobal ? (fromLs ? Number(fromLs) : fromUser || null) : fromUser || null;
  });

  const [unidades, setUnidades] = useState([]);
  const [unidadeAtivaId, setUnidadeAtivaId] = useState(() => localStorage.getItem("gestao_unidade_ativa") || "");
  const [territorio, setTerritorio] = useState(() => localStorage.getItem("gestao_territorio") || "");
  const [de, setDe] = useState(() => localStorage.getItem("gestao_de") || "");
  const [ate, setAte] = useState(() => localStorage.getItem("gestao_ate") || "");

  // Parâmetros de regra
  const [janelaRiscoHoras, setJanelaRiscoHoras] = useState(() => Number(localStorage.getItem("gestao_janela_risco_horas") || 24));
  const [diasCadunico, setDiasCadunico] = useState(() => Number(localStorage.getItem("gestao_dias_cadunico") || 30));
  const [diasPia, setDiasPia] = useState(() => Number(localStorage.getItem("gestao_dias_pia") || 15));

  // Fila
  const [filaModulo, setFilaModulo] = useState(() => localStorage.getItem("gestao_fila_modulo") || "");
  const [somenteAtrasos, setSomenteAtrasos] = useState(() => (localStorage.getItem("gestao_fila_atrasos") || "1") === "1");
  const [somenteEmRisco, setSomenteEmRisco] = useState(() => (localStorage.getItem("gestao_fila_risco") || "0") === "1");

  // SLA
  const [slaGroupBy, setSlaGroupBy] = useState(() => localStorage.getItem("gestao_sla_group") || "modulo");

  // Dados
  const [loading, setLoading] = useState(false);
  const [erro, setErro] = useState("");
  const [resumo, setResumo] = useState(null);
  const [sla, setSla] = useState(null);
  const [fila, setFila] = useState(null);

  // Metas (MetaKpi) — Real x Meta (semaforização)
  const [metas, setMetas] = useState([]);

  // Ações rápidas (docs)
  const [usarIADocs, setUsarIADocs] = useState(() => (localStorage.getItem("gestao_usar_ia_docs") || "0") === "1");
  const [acaoMsg, setAcaoMsg] = useState("");
  const [acaoLoadingId, setAcaoLoadingId] = useState(null);

  // evitar race condition
  const lastReq = useRef(0);

  function getToken() {
    return (
      localStorage.getItem("poprua_token") ||
      localStorage.getItem("access_token") ||
      localStorage.getItem("token") ||
      ""
    );
  }

  async function apiFetch(url, options = {}) {
    const token = getToken();
    const headers = new Headers(options.headers || {});
    if (token && !headers.get("Authorization")) headers.set("Authorization", `Bearer ${token}`);
    if (!headers.get("Content-Type") && options.body) headers.set("Content-Type", "application/json");
    return fetch(url, { ...options, headers });
  }

  async function apiJson(path, options = undefined) {
    const res = await apiFetch(`${API_BASE}${path}`, options || {});
    const json = await res.json().catch(() => null);
    if (!res.ok) throw new Error(json?.detail || `Falha (HTTP ${res.status})`);
    return json;
  }

  async function downloadByAuth(downloadPath, filename) {
    if (!downloadPath) return;
    const res = await apiFetch(`${API_BASE}${downloadPath}`);
    if (!res.ok) {
      const txt = await res.text().catch(() => "");
      throw new Error(txt || `Falha no download (HTTP ${res.status})`);
    }
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    try {
      const a = document.createElement("a");
      a.href = url;
      a.download = filename || "documento.pdf";
      document.body.appendChild(a);
      a.click();
      a.remove();
    } finally {
      setTimeout(() => URL.revokeObjectURL(url), 5000);
    }
  }

  function buildContextoItem(item) {
    const mod = String(item?.modulo || "").trim();
    const tipo = String(item?.tipo || "").trim();
    const rid = item?.referencia_id != null ? `#${item.referencia_id}` : "—";
    const titulo = item?.titulo || "—";
    const motivo = item?.motivo_trava || item?.descricao || "—";
    const atraso = item?.dias_em_atraso ? `${item.dias_em_atraso} dias` : "—";
    const vence = item?.sla_due_at ? fmtDateTime(item.sla_due_at) : "—";
    return (
      `Pendência identificada no Dashboard do Secretário (Gestão).\n` +
      `Módulo: ${mod}\n` +
      `Tipo: ${tipo}\n` +
      `Referência: ${rid}\n` +
      `Título: ${titulo}\n` +
      `Motivo: ${motivo}\n` +
      `Atraso: ${atraso}\n` +
      `Vencimento: ${vence}\n`
    );
  }

  function openModuloFromItem(item) {
    const mod = normStr(item?.modulo);
    const tipo = normStr(item?.tipo);
    const refId = item?.referencia_id != null ? Number(item.referencia_id) : null;

    try {
      if (mod.includes("cras")) {
        if (tipo === "caso" && refId) {
          localStorage.setItem("cras_selected_case", String(refId));
          localStorage.setItem("cras_active_tab", "casos");
        } else if (tipo === "encaminhamento" && refId) {
          localStorage.setItem("cras_open_enc_id", String(refId));
          localStorage.setItem("cras_active_tab", "encaminhamentos");
        } else {
          localStorage.setItem("cras_active_tab", "inicio");
        }
        window.location.href = "/app?mod=cras";
        return;
      }

      if (mod.includes("creas")) {
        if (refId) setCreasSelectedCaseId(String(refId));
        localStorage.setItem("creas_active_tab", refId ? "casos" : "painel");
        window.location.href = "/app?mod=creas";
        return;
      }

      if (mod.includes("poprua")) {
        if (refId) localStorage.setItem("poprua_open_case_id", String(refId));
        window.location.href = "/app?mod=poprua";
        return;
      }

      if (mod.includes("rede")) {
        // Rede (DB): abre CRAS → Encaminhamentos e destaca o ID
        if (refId) localStorage.setItem("cras_open_enc_id", String(refId));
        localStorage.setItem("cras_active_tab", "encaminhamentos");
        window.location.href = "/app?mod=cras";
        return;
      }
    } catch {}
  }

  async function gerarRelatorio(item) {
    const idKey = item?.referencia_id || item?.id || "";
    setAcaoLoadingId(idKey);
    setAcaoMsg("");
    try {
      const contexto = buildContextoItem(item);

      let draft;
      if (usarIADocs) {
        draft = await apiJson("/ia/rascunho/documento", {
          method: "POST",
          body: JSON.stringify({
            modelo: "relatorio_padrao",
            tipo: "relatorio",
            contexto,
            preferencias: "curto, objetivo, formal, sem dados pessoais",
          }),
        });
      } else {
        draft = {
          tipo: "relatorio",
          modelo: "relatorio_padrao",
          assunto: "Relatório — Pendência",
          destinatario_nome: "",
          destinatario_cargo: "",
          destinatario_orgao: "",
          campos: {
            contexto,
            descricao: item?.motivo_trava || item?.descricao || "",
            encaminhamentos: "Solicita-se providências e registro de retorno no sistema, com justificativa e previsão.",
          },
        };
      }

      const docPayload = {
        municipio_id: isGlobal ? municipioAtivoId : undefined,
        tipo: draft?.tipo || "relatorio",
        modelo: draft?.modelo || "relatorio_padrao",
        assunto: draft?.assunto || "Relatório",
        destinatario_nome: draft?.destinatario_nome || "",
        destinatario_cargo: draft?.destinatario_cargo || "",
        destinatario_orgao: draft?.destinatario_orgao || "",
        campos: draft?.campos || {},
        emissor: "gestao",
        salvar: true,
      };

      const resp = await apiJson("/documentos/gerar", {
        method: "POST",
        body: JSON.stringify(docPayload),
      });

      const numero = resp?.numero ? ` ${resp.numero}` : "";
      setAcaoMsg(`Relatório gerado${numero} ✅`);
      if (resp?.download) {
        await downloadByAuth(resp.download, `RELATORIO_${resp?.numero || resp?.id || ""}.pdf`);
      }
    } catch (e) {
      setAcaoMsg(`Erro ao gerar relatório: ${e?.message || e}`);
    } finally {
      setAcaoLoadingId(null);
    }
  }

  async function gerarOficioOuCobranca(item) {
    const idKey = item?.referencia_id || item?.id || "";
    setAcaoLoadingId(idKey);
    setAcaoMsg("");
    try {
      const mod = normStr(item?.modulo);
      const refId = item?.referencia_id != null ? Number(item.referencia_id) : null;

      // Rede (DB): cobrança de devolutiva (modelo guiado)
      if (mod.includes("rede") && refId) {
        const resp = await apiJson("/documentos/gerar/cobranca-devolutiva", {
          method: "POST",
          body: JSON.stringify({
            encaminhamento_id: refId,
            emissor: "smas",
            usar_ia: !!usarIADocs,
            salvar: true,
          }),
        });
        const numero = resp?.numero ? ` ${resp.numero}` : "";
        setAcaoMsg(`Ofício de cobrança gerado${numero} ✅`);
        if (resp?.download) {
          await downloadByAuth(resp.download, `OFICIO_COBRANCA_${resp?.numero || resp?.id || ""}.pdf`);
        }
        return;
      }

      // Fallback: ofício padrão para qualquer item
      const contexto = buildContextoItem(item);
      let draft;
      if (usarIADocs) {
        draft = await apiJson("/ia/rascunho/documento", {
          method: "POST",
          body: JSON.stringify({
            modelo: "oficio_padrao",
            tipo: "oficio",
            contexto,
            preferencias: "curto, objetivo, formal, sem dados pessoais",
          }),
        });
      } else {
        draft = {
          tipo: "oficio",
          modelo: "oficio_padrao",
          assunto: `Providências — ${item?.titulo || "Pendência"}`,
          destinatario_nome: "",
          destinatario_cargo: "",
          destinatario_orgao: "",
          campos: { texto: contexto },
        };
      }

      const docPayload = {
        municipio_id: isGlobal ? municipioAtivoId : undefined,
        tipo: draft?.tipo || "oficio",
        modelo: draft?.modelo || "oficio_padrao",
        assunto: draft?.assunto || "Ofício",
        destinatario_nome: draft?.destinatario_nome || "",
        destinatario_cargo: draft?.destinatario_cargo || "",
        destinatario_orgao: draft?.destinatario_orgao || "",
        campos: draft?.campos || {},
        emissor: "gestao",
        salvar: true,
      };

      const resp = await apiJson("/documentos/gerar", {
        method: "POST",
        body: JSON.stringify(docPayload),
      });

      const numero = resp?.numero ? ` ${resp.numero}` : "";
      setAcaoMsg(`Ofício gerado${numero} ✅`);
      if (resp?.download) {
        await downloadByAuth(resp.download, `OFICIO_${resp?.numero || resp?.id || ""}.pdf`);
      }
    } catch (e) {
      setAcaoMsg(`Erro ao gerar ofício: ${e?.message || e}`);
    } finally {
      setAcaoLoadingId(null);
    }
  }

  const municipioAtivoNome = useMemo(() => {
    const id = Number(municipioAtivoId || 0);
    const m = municipios.find((x) => Number(x?.id) === id);
    return m?.nome || m?.nome_municipio || (id ? `Município ${id}` : "—");
  }, [municipios, municipioAtivoId]);

  
  const headerCfg = useMemo(() => {
    const muni = municipioAtivoNome || "Município";
    if (activeTab === "sla") {
      return {
        title: "Gestão — SLA & Gargalos",
        subtitle: `Prazos, risco e atrasos. ${muni}.`,
        bullets: [
          "Ranking por módulo/unidade/território/etapa/destino",
          "Tempo médio e % dentro do prazo",
          "Pontos críticos e tendência",
        ],
      };
    }
    if (activeTab === "fila") {
      return {
        title: "Gestão — Fila de Pendências",
        subtitle: `Pendências unificadas (CRAS, CREAS, PopRua e Rede). ${muni}.`,
        bullets: [
          "Somente atrasos / somente em risco",
          "Responsáveis e prazos por item",
          "Ações rápidas de gestão",
        ],
      };
    }
    if (activeTab === "rede") {
      return {
        title: "Gestão — Rede & Encaminhamentos",
        subtitle: `Compliance da rede e devolutivas. ${muni}.`,
        bullets: [
          "Piores/melhores destinos (intermunicipal)",
          "Prazos de recebimento, devolutiva e conclusão",
          "Rastreabilidade e evidências",
        ],
      };
    }
    return {
      title: "Gestão — Visão Consolidada",
      subtitle: `KPIs do município + distribuição por módulo/unidade/território. ${muni}.`,
      bullets: [
        "Casos ativos, atrasos e risco (SLA)",
        "Distribuição por módulo, unidade e território",
        "Sinais de atenção e gargalos",
      ],
    };
  }, [activeTab, municipioAtivoNome]);
function portal() {
    window.location.href = "/hub";
  }

  function persistFilters() {
    try {
      localStorage.setItem("gestao_municipio_ativo", municipioAtivoId ? String(municipioAtivoId) : "");
      localStorage.setItem("gestao_unidade_ativa", unidadeAtivaId || "");
      localStorage.setItem("gestao_territorio", territorio || "");
      localStorage.setItem("gestao_de", de || "");
      localStorage.setItem("gestao_ate", ate || "");
      localStorage.setItem("gestao_janela_risco_horas", String(janelaRiscoHoras || 24));
      localStorage.setItem("gestao_dias_cadunico", String(diasCadunico || 30));
      localStorage.setItem("gestao_dias_pia", String(diasPia || 15));
      localStorage.setItem("gestao_fila_modulo", filaModulo || "");
      localStorage.setItem("gestao_fila_atrasos", somenteAtrasos ? "1" : "0");
      localStorage.setItem("gestao_fila_risco", somenteEmRisco ? "1" : "0");
      localStorage.setItem("gestao_sla_group", slaGroupBy || "modulo");
      localStorage.setItem("gestao_usar_ia_docs", usarIADocs ? "1" : "0");
    } catch {}
  }

  // Carrega municípios
  useEffect(() => {
    (async () => {
      try {
        setMunicipios(await apiJson("/municipios"));
      } catch {
        setMunicipios([]);
      }
    })();
  }, []);

  // Carrega unidades (se existir município)
  useEffect(() => {
    if (!municipioAtivoId) {
      setUnidades([]);
      return;
    }
    (async () => {
      try {
        setUnidades(await apiJson(`/cras/unidades?municipio_id=${encodeURIComponent(municipioAtivoId)}`));
      } catch {
        setUnidades([]);
      }
    })();
  }, [municipioAtivoId]);

  // Se mudou município, zera unidade (evita filtro inválido)
  useEffect(() => {
    if (!unidadeAtivaId) return;
    const uid = Number(unidadeAtivaId || 0);
    if (!uid) return;
    const ok = (unidades || []).some((u) => Number(u?.id) === uid);
    if (!ok) setUnidadeAtivaId("");
  }, [unidades]);

  const filtrosResumo = useMemo(() => {
    return {
      municipio_id: isGlobal ? municipioAtivoId : undefined,
      unidade_id: unidadeAtivaId ? Number(unidadeAtivaId) : undefined,
      territorio: territorio || undefined,
      de: de || undefined,
      ate: ate || undefined,
      dias_cadunico: diasCadunico,
      dias_pia: diasPia,
      janela_risco_horas: janelaRiscoHoras,
    };
  }, [municipioAtivoId, unidadeAtivaId, territorio, de, ate, diasCadunico, diasPia, janelaRiscoHoras, isGlobal]);

  const filtrosFila = useMemo(() => {
    return {
      municipio_id: isGlobal ? municipioAtivoId : undefined,
      unidade_id: unidadeAtivaId ? Number(unidadeAtivaId) : undefined,
      territorio: territorio || undefined,
      dias_cadunico: diasCadunico,
      dias_pia: diasPia,
      modulo: filaModulo || undefined,
      somente_atrasos: somenteAtrasos ? 1 : 0,
      somente_em_risco: somenteEmRisco ? 1 : 0,
      janela_risco_horas: janelaRiscoHoras,
      limit: 80,
      offset: 0,
    };
  }, [municipioAtivoId, unidadeAtivaId, territorio, diasCadunico, diasPia, filaModulo, somenteAtrasos, somenteEmRisco, janelaRiscoHoras, isGlobal]);

  const filtrosSla = useMemo(() => {
    return {
      municipio_id: isGlobal ? municipioAtivoId : undefined,
      group_by: slaGroupBy || "modulo",
      janela_risco_horas: janelaRiscoHoras,
    };
  }, [municipioAtivoId, slaGroupBy, janelaRiscoHoras, isGlobal]);

  const filtrosMetas = useMemo(() => {
    return {
      municipio_id: isGlobal ? municipioAtivoId : undefined,
      include_globais: 1,
      ativo: 1,
    };
  }, [municipioAtivoId, isGlobal]);

  async function carregarTudo() {
    const rid = Date.now();
    lastReq.current = rid;
    persistFilters();

    setErro("");
    setLoading(true);

    try {
      const [r, s, f, m] = await Promise.all([
        apiJson(`/gestao/dashboard/resumo${buildQS(filtrosResumo)}`),
        apiJson(`/gestao/dashboard/sla${buildQS(filtrosSla)}`),
        apiJson(`/gestao/fila${buildQS(filtrosFila)}`),
        apiJson(`/config/metas${buildQS(filtrosMetas)}`),
      ]);

      if (lastReq.current !== rid) return;

      setResumo(r);
      setSla(s);
      setFila(f);
      setMetas(Array.isArray(m) ? m : []);
    } catch (e) {
      if (lastReq.current !== rid) return;
      setErro(e?.message || "Erro ao carregar dados da Gestão.");
      setResumo(null);
      setSla(null);
      setFila(null);
      setMetas([]);
    } finally {
      if (lastReq.current === rid) setLoading(false);
    }
  }

  // auto-load (1ª carga e quando filtros mudarem)
  useEffect(() => {
    carregarTudo();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [municipioAtivoId, unidadeAtivaId, territorio, de, ate, janelaRiscoHoras, diasCadunico, diasPia, filaModulo, somenteAtrasos, somenteEmRisco, slaGroupBy]);

  const kpis = resumo?.kpis || {};
  const porModulo = resumo?.por_modulo || {};
  const porUnidade = resumo?.por_unidade || [];
  const porTerritorio = resumo?.por_territorio || [];
  const rede = porModulo?.rede || {};
  const rankings = rede?.rankings || {};

  const redeWorst = rankings?.cras?.pior || [];
  const redeBest = rankings?.cras?.melhor || [];
  const interWorst = rankings?.intermunicipal?.pior || [];
  const interBest = rankings?.intermunicipal?.melhor || [];

  const filaItems = fila?.items || [];

  const slaItems = sla?.items || [];
  const slaIsDestino = String(sla?.group_by || "").toLowerCase() === "destino";

  // dropdown território: usa por_territorio do resumo
  const territoriosDisponiveis = useMemo(() => {
    const xs = (porTerritorio || []).map((x) => String(x?.territorio || "")).filter(Boolean);
    return Array.from(new Set(xs)).sort((a, b) => a.localeCompare(b, "pt-BR"));
  }, [porTerritorio]);

  const metasAtivas = useMemo(() => {
    const arr = Array.isArray(metas) ? metas : [];
    return arr.filter((m) => m && m.ativo !== false);
  }, [metas]);

  function pickMeta(moduloKey, kpiKey) {
    const mod = normStr(moduloKey);
    const kpi = normStr(kpiKey);

    const mid = municipioAtivoId != null ? Number(municipioAtivoId) : null;
    const uid = unidadeAtivaId ? Number(unidadeAtivaId) : null;
    const ut = uid ? "cras" : null;

    const candidates = metasAtivas.filter((m) => normStr(m?.modulo) === mod && normStr(m?.kpi) === kpi);
    if (!candidates.length) return null;

    // 1) unidade específica
    if (uid) {
      const u = candidates.find((m) => Number(m?.unidade_id || 0) === uid && (ut ? normStr(m?.unidade_tipo) === ut : true));
      if (u) return u;
    }

    // 2) município específico
    if (mid) {
      const mm = candidates.find((m) => Number(m?.municipio_id || 0) === mid);
      if (mm) return mm;
    }

    // 3) global
    const g = candidates.find((m) => m?.municipio_id == null);
    return g || candidates[0];
  }

  function metaCompareValue(kpiKey, metaVal) {
    const mv = Number(metaVal);
    if (!Number.isFinite(mv)) return null;
    if (isPctKpi(kpiKey)) {
      // aceita meta em fração (0–1) ou em porcentagem (0–100)
      return mv <= 1 ? mv * 100 : mv;
    }
    return mv;
  }

  function metaStatus(kpiKey, realVal, metaVal) {
    const rv = Number(realVal);
    const mv = metaCompareValue(kpiKey, metaVal);
    if (!Number.isFinite(rv) || mv == null) return { tone: "", label: "" };

    // percentuais: quanto maior melhor
    if (isPctKpi(kpiKey)) {
      if (rv >= mv) return { tone: "", label: "OK" };
      if (rv >= mv * 0.9) return { tone: "warn", label: "Atenção" };
      return { tone: "bad", label: "Crítico" };
    }

    // contagens/atrasos: quanto menor melhor
    if (rv <= mv) return { tone: "", label: "OK" };
    if (mv === 0) {
      if (rv <= 3) return { tone: "warn", label: "Atenção" };
      return { tone: "bad", label: "Crítico" };
    }
    if (rv <= mv * 1.2) return { tone: "warn", label: "Atenção" };
    return { tone: "bad", label: "Crítico" };
  }

  function metaHintForCard(kpiKey, realVal, metaObj) {
    if (!metaObj) return { hint: "", tone: "" };
    const mv = metaCompareValue(kpiKey, metaObj?.valor_meta);
    const st = metaStatus(kpiKey, realVal, metaObj?.valor_meta);
    const metaText = mv == null ? "—" : (isPctKpi(kpiKey) ? fmtPct(mv) : fmtNum(mv));
    const hint = `Meta: ${metaText}` + (st?.label ? ` · ${st.label}` : "");
    return { hint, tone: st?.tone || "" };
  }

  // Metas principais (cards)
  const metaCasosAtivos = pickMeta("gestao", "casos_ativos_total");
  const metaAtrasos = pickMeta("gestao", "pendencias_atrasadas_total");
  const metaRisco = pickMeta("gestao", "pendencias_em_risco_total");
  const metaAguardando = pickMeta("gestao", "encaminhamentos_aguardando_total");

  const metaRecebido = pickMeta("rede", "pct_recebido_no_prazo");
  const metaDevolutiva = pickMeta("rede", "pct_devolutiva_no_prazo");
  const metaConclusao = pickMeta("rede", "pct_conclusao_no_prazo");
  const metaContato = pickMeta("rede", "pct_contato_no_prazo");

  return (
    <div className="app-root">
      <GestaoTopHeader
        titleRight="Gestão"
        subtitle="Dashboard do Secretário: visão consolidada, gargalos (SLA), fila e rede."
        usuarioLogado={usuarioLogado}
        municipioAtivoId={municipioAtivoId}
        setMunicipioAtivoId={(v) => setMunicipioAtivoId(v ? Number(v) : null)}
        municipios={municipios}
        podeSelecionarMunicipio={isGlobal}
        municipioLabel={isGlobal ? "Município:" : "Município:"}
        unidadeLabel="Unidade (opcional):"
        unidadeAtivaId={unidadeAtivaId}
        setUnidadeAtivaId={setUnidadeAtivaId}
        unidades={unidades}
        tabs={tabs}
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        onPortal={portal}
        onSair={onLogout}
      />

      <main className="app-main">
        <ErrorBoundary label="Gestão · Cabeçalho">
          <GestaoPageHeader
            userName={usuarioLogado?.nome ?? "—"}
            title={headerCfg.title}
            subtitle={headerCfg.subtitle}
            bullets={headerCfg.bullets}
          />
        </ErrorBoundary>

        <div style={{ maxWidth: 1180, width: "100%", margin: "0 auto" }}>
          <div className="card gestao-fila-card" style={{ marginTop: 14 }}>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 12, flexWrap: "wrap" }}>
              <div>
                <div style={{ fontWeight: 950, fontSize: 16 }}>Filtros</div>
                <div className="texto-suave" style={{ marginTop: 4 }}>
                  {municipioAtivoNome} · Janela de risco: {janelaRiscoHoras}h · CadÚnico: {diasCadunico}d · PIA: {diasPia}d
                </div>
              </div>

              <div style={{ display: "flex", gap: 10, flexWrap: "wrap", alignItems: "center" }}>
                <div>
                  <div className="texto-suave" style={{ fontSize: 11, marginBottom: 4 }}>Território</div>
                  <select className="select" style={{ width: 220 }} value={territorio} onChange={(e) => setTerritorio(e.target.value || "")}>
                    <option value="">Todos</option>
                    {territoriosDisponiveis.map((t) => (
                      <option key={t} value={t}>{t}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <div className="texto-suave" style={{ fontSize: 11, marginBottom: 4 }}>De</div>
                  <input className="input" type="date" value={de} onChange={(e) => setDe(e.target.value || "")} />
                </div>

                <div>
                  <div className="texto-suave" style={{ fontSize: 11, marginBottom: 4 }}>Até</div>
                  <input className="input" type="date" value={ate} onChange={(e) => setAte(e.target.value || "")} />
                </div>

                <button type="button" className="btn btn-primario" onClick={carregarTudo} disabled={loading}>
                  {loading ? "Atualizando..." : "Atualizar"}
                </button>
              </div>
            </div>

            <div className="gestao-filtros-row">
              <div className="gestao-field">
                <div className="texto-suave" style={{ fontSize: 11, marginBottom: 4 }}>Janela risco (h)</div>
                <input className="input" type="number" min="1" max="168" value={janelaRiscoHoras} onChange={(e) => setJanelaRiscoHoras(Number(e.target.value || 24))} />
              </div>
              <div className="gestao-field">
                <div className="texto-suave" style={{ fontSize: 11, marginBottom: 4 }}>CadÚnico (dias)</div>
                <input className="input" type="number" min="1" max="365" value={diasCadunico} onChange={(e) => setDiasCadunico(Number(e.target.value || 30))} />
              </div>
              <div className="gestao-field">
                <div className="texto-suave" style={{ fontSize: 11, marginBottom: 4 }}>PIA (dias)</div>
                <input className="input" type="number" min="1" max="365" value={diasPia} onChange={(e) => setDiasPia(Number(e.target.value || 15))} />
              </div>

              <label className="gestao-check" title="Se marcado, o sistema tenta gerar rascunhos com IA (e cai para modelo padrão se a IA estiver indisponível).">
                <input type="checkbox" checked={usarIADocs} onChange={(e) => setUsarIADocs(!!e.target.checked)} />
                <span>Usar IA nos documentos</span>
              </label>

              {activeTab === "sla" ? (
                <div className="gestao-field" style={{ minWidth: 240 }}>
                  <div className="texto-suave" style={{ fontSize: 11, marginBottom: 4 }}>Agrupar SLA</div>
                  <select className="select" value={slaGroupBy} onChange={(e) => setSlaGroupBy(e.target.value || "modulo")}>
                    <option value="modulo">Módulo</option>
                    <option value="unidade">Unidade</option>
                    <option value="territorio">Território</option>
                    <option value="etapa">Etapa</option>
                    <option value="responsavel">Responsável</option>
                    <option value="destino">Destinos da rede (compliance)</option>
                  </select>
                </div>
              ) : null}

              {activeTab === "fila" ? (
                <>
                  <div className="gestao-field" style={{ minWidth: 220 }}>
                    <div className="texto-suave" style={{ fontSize: 11, marginBottom: 4 }}>Módulo</div>
                    <select className="select" value={filaModulo} onChange={(e) => setFilaModulo(e.target.value || "")}>
                      <option value="">Todos</option>
                      <option value="cras">CRAS</option>
                      <option value="poprua">PopRua</option>
                      <option value="creas">CREAS</option>
                      <option value="rede">Rede</option>
                      <option value="osc">OSC</option>
                    </select>
                  </div>

                  <label className="gestao-check">
                    <input type="checkbox" checked={somenteAtrasos} onChange={(e) => setSomenteAtrasos(!!e.target.checked)} />
                    <span>Somente atrasos</span>
                  </label>

                  <label className="gestao-check">
                    <input type="checkbox" checked={somenteEmRisco} onChange={(e) => setSomenteEmRisco(!!e.target.checked)} />
                    <span>Somente em risco</span>
                  </label>
                </>
              ) : null}
            </div>

            {erro ? (
              <p className="erro-global">{erro}</p>
            ) : null}

            {acaoMsg ? (
              <div className="card" style={{ marginTop: 10, padding: 10, borderRadius: 14, border: "1px solid rgba(229,231,235,0.9)", background: "rgba(255,255,255,0.75)" }}>
                <div style={{ fontWeight: 800 }}>{acaoMsg}</div>
              </div>
            ) : null}
          </div>

          {/* VISÃO */}
          {activeTab === "visao" ? (
            <ErrorBoundary label="GestaoVisao">
              <div className="card" style={{ marginTop: 14 }}>
                <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 12, flexWrap: "wrap" }}>
                  <div>
                    <div style={{ fontWeight: 950, fontSize: 16 }}>Visão consolidada</div>
                    <div className="texto-suave" style={{ marginTop: 4 }}>
                      KPIs do município + distribuição por módulo/unidade/território.
                    </div>
                  </div>
                  <span className="badge-status">Gestão</span>
                </div>

                <div className="gestao-kpis-row">
                  {(() => {
                    const h = metaHintForCard("casos_ativos_total", kpis?.casos_ativos_total, metaCasosAtivos);
                    return <KpiCard label="Casos ativos" value={fmtNum(kpis?.casos_ativos_total)} hint={h.hint} tone={h.tone} />;
                  })()}
                  {(() => {
                    const h = metaHintForCard("pendencias_atrasadas_total", kpis?.pendencias_atrasadas_total, metaAtrasos);
                    const fallbackTone = Number(kpis?.pendencias_atrasadas_total || 0) > 0 ? "bad" : "";
                    return <KpiCard label="Pendências atrasadas" value={fmtNum(kpis?.pendencias_atrasadas_total)} hint={h.hint} tone={h.tone || fallbackTone} />;
                  })()}
                  {(() => {
                    const h = metaHintForCard("pendencias_em_risco_total", kpis?.pendencias_em_risco_total, metaRisco);
                    const fallbackTone = Number(kpis?.pendencias_em_risco_total || 0) > 0 ? "warn" : "";
                    return <KpiCard label="Pendências em risco" value={fmtNum(kpis?.pendencias_em_risco_total)} hint={h.hint} tone={h.tone || fallbackTone} />;
                  })()}
                  {(() => {
                    const h = metaHintForCard("encaminhamentos_aguardando_total", kpis?.encaminhamentos_aguardando_total, metaAguardando);
                    return <KpiCard label="Encaminhamentos aguardando" value={fmtNum(kpis?.encaminhamentos_aguardando_total)} hint={h.hint} tone={h.tone} />;
                  })()}
                </div>

                <div style={{ marginTop: 14, fontWeight: 950 }}>Por módulo</div>
                <Table
                  columns={[
                    { key: "mod", label: "Módulo", render: (r) => <strong>{r.mod}</strong> },
                    { key: "ativos", label: "Ativos", render: (r) => fmtNum(r.ativos) },
                    { key: "atrasos", label: "Atrasos", render: (r) => fmtNum(r.atrasos) },
                    { key: "em_risco", label: "Em risco", render: (r) => fmtNum(r.em_risco) },
                    { key: "obs", label: "Obs.", render: (r) => r.obs || "—" },
                  ]}
                  rows={[
                    { mod: "CRAS", ativos: porModulo?.cras?.ativos, atrasos: porModulo?.cras?.atrasos, em_risco: porModulo?.cras?.em_risco, obs: porModulo?.cras?.validacao_pendente ? `Validação pendente: ${fmtNum(porModulo?.cras?.validacao_pendente)}` : "" },
                    { mod: "PopRua", ativos: porModulo?.poprua?.ativos, atrasos: porModulo?.poprua?.atrasos, em_risco: porModulo?.poprua?.em_risco, obs: "" },
                    { mod: "CREAS", ativos: porModulo?.creas?.ativos, atrasos: porModulo?.creas?.atrasos, em_risco: porModulo?.creas?.em_risco, obs: porModulo?.creas?.validacao_pendente ? `Validação pendente: ${fmtNum(porModulo?.creas?.validacao_pendente)}` : "" },
                    { mod: "Rede", ativos: porModulo?.rede?.aguardando, atrasos: porModulo?.rede?.atrasados, em_risco: porModulo?.rede?.em_risco, obs: "" },
                    { mod: "OSC", ativos: porModulo?.osc?.pendencias, atrasos: porModulo?.osc?.criticas, em_risco: porModulo?.osc?.em_risco, obs: "" },
                  ]}
                />

                <div style={{ marginTop: 14, display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14 }}>
                  <div>
                    <div style={{ fontWeight: 950 }}>Por unidade</div>
                    <Table
                      columns={[
                        { key: "unidade_nome", label: "Unidade" },
                        { key: "ativos", label: "Ativos", render: (r) => fmtNum(r.ativos) },
                        { key: "atrasos", label: "Atrasos", render: (r) => fmtNum(r.atrasos) },
                        { key: "em_risco", label: "Em risco", render: (r) => fmtNum(r.em_risco) },
                      ]}
                      rows={porUnidade}
                      emptyText="Sem dados por unidade."
                    />
                  </div>

                  <div>
                    <div style={{ fontWeight: 950 }}>Por território</div>
                    <Table
                      columns={[
                        { key: "territorio", label: "Território" },
                        { key: "ativos", label: "Ativos", render: (r) => fmtNum(r.ativos) },
                        { key: "atrasos", label: "Atrasos", render: (r) => fmtNum(r.atrasos) },
                        { key: "em_risco", label: "Em risco", render: (r) => fmtNum(r.em_risco) },
                      ]}
                      rows={porTerritorio}
                      emptyText="Sem dados por território."
                    />
                  </div>
                </div>
              </div>
            </ErrorBoundary>
          ) : null}

          {/* SLA */}
          {activeTab === "sla" ? (
            <ErrorBoundary label="GestaoSla">
              <div className="card" style={{ marginTop: 14 }}>
                <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 12, flexWrap: "wrap" }}>
                  <div>
                    <div style={{ fontWeight: 950, fontSize: 16 }}>SLA & Gargalos</div>
                    <div className="texto-suave" style={{ marginTop: 4 }}>
                      Ranking de onde o atraso está concentrado (por {slaGroupBy}).
                    </div>
                  </div>
                  <span className="badge-status">SLA</span>
                </div>

                {slaIsDestino ? (
                  <Table
                    columns={[
                      { key: "label", label: "Destino" },
                      { key: "atrasados", label: "Atrasos", render: (r) => fmtNum(r.atrasados) },
                      { key: "em_risco", label: "Em risco", render: (r) => fmtNum(r.em_risco) },
                      { key: "pct_devolutiva_no_prazo", label: "Devolutiva no prazo", render: (r) => fmtPct(r.pct_devolutiva_no_prazo ?? r.pct_contato_no_prazo) },
                      { key: "avg_horas_ate_devolutiva", label: "Tempo médio", render: (r) => fmtHours(r.avg_horas_ate_devolutiva ?? r.avg_horas_ate_contato) },
                      { key: "score", label: "Score", render: (r) => (Number.isFinite(Number(r.score)) ? Number(r.score).toFixed(1) : "—") },
                      { key: "faixa", label: "Faixa", render: (r) => r.faixa || "—" },
                    ]}
                    rows={slaItems}
                    emptyText="Sem dados para destinos."
                  />
                ) : (
                  <Table
                    columns={[
                      { key: "label", label: "Grupo" },
                      { key: "count", label: "Itens", render: (r) => fmtNum(r.count) },
                      { key: "media_dias_atraso", label: "Média atraso (d)", render: (r) => (Number.isFinite(Number(r.media_dias_atraso)) ? Number(r.media_dias_atraso).toFixed(1) : "—") },
                      { key: "max_dias_atraso", label: "Máx atraso (d)", render: (r) => fmtNum(r.max_dias_atraso) },
                    ]}
                    rows={slaItems}
                    emptyText="Sem dados de SLA."
                  />
                )}
              </div>
            </ErrorBoundary>
          ) : null}

          {/* FILA */}
          {activeTab === "fila" ? (
            <ErrorBoundary label="GestaoFila">
              <div className="card" style={{ marginTop: 14 }}>
                <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 12, flexWrap: "wrap" }}>
                  <div>
                    <div style={{ fontWeight: 950, fontSize: 16 }}>Fila de pendências</div>
                    <div className="texto-suave" style={{ marginTop: 4 }}>
                      {fila?.total != null ? `${fmtNum(fila.total)} itens` : "—"} · ordenado por criticidade (SLA/atraso/risco).
                    </div>
                  </div>
                  <span className="badge-status">Fila</span>
                </div>

                <Table
                  columns={[
                    { key: "modulo", label: "Módulo", render: (r) => <span className="badge-info">{String(r.modulo || "").toUpperCase()}</span> },
                    { key: "titulo", label: "Item", render: (r) => <div style={{ fontWeight: 800 }}>{r.titulo || "—"}</div> },
                    { key: "motivo_trava", label: "Motivo", render: (r) => <span className="texto-suave">{r.motivo_trava || r.descricao || "—"}</span> },
                    { key: "dias_em_atraso", label: "Atraso", render: (r) => (Number(r.dias_em_atraso || 0) > 0 ? `${fmtNum(r.dias_em_atraso)} d` : "—") },
                    { key: "sla_due_at", label: "Vence em", render: (r) => fmtDateTime(r.sla_due_at) },
                    {
                      key: "acoes",
                      label: "Ações",
                      render: (r) => {
                        const idKey = r?.referencia_id || r?.id || "";
                        const busy = String(acaoLoadingId || "") === String(idKey);
                        const isRede = normStr(r?.modulo).includes("rede");
                        return (
                          <div className="gestao-fila-actions">
                            <button className="btn btn-primario btn-primario-mini" type="button" disabled={busy} onClick={() => openModuloFromItem(r)}>
                              Abrir
                            </button>
                            <button className="btn btn-secundario btn-secundario-mini gestao-fila-btn-doc" type="button" disabled={busy} onClick={() => gerarOficioOuCobranca(r)}>
                              {isRede ? "Cobrar" : "Ofício"}
                            </button>
                            <button className="btn btn-secundario btn-secundario-mini" type="button" disabled={busy} onClick={() => gerarRelatorio(r)}>
                              Relatório
                            </button>
                          </div>
                        );
                      },
                    },
                  ]}
                  rows={filaItems.map((x, idx) => ({ ...x, id: x.referencia_id || x.id || idx }))}
                  emptyText="Sem itens na fila com os filtros atuais."
                />

                <div className="texto-suave" style={{ marginTop: 10 }}>
                  Dica: use <strong>Somente atrasos</strong> para enxergar o que já estourou e <strong>Somente em risco</strong> para atuar antes do prazo.
                </div>
              </div>
            </ErrorBoundary>
          ) : null}

          {/* REDE */}
          {activeTab === "rede" ? (
            <ErrorBoundary label="GestaoRede">
              <div className="card" style={{ marginTop: 14 }}>
                <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 12, flexWrap: "wrap" }}>
                  <div>
                    <div style={{ fontWeight: 950, fontSize: 16 }}>Rede (encaminhamentos)</div>
                    <div className="texto-suave" style={{ marginTop: 4 }}>
                      Compliance e desempenho por destino (CRAS e intermunicipal).
                    </div>
                  </div>
                  <span className="badge-status">Rede</span>
                </div>

                <div className="gestao-kpis-row" style={{ marginTop: 12 }}>
                  {(() => {
                    const h = metaHintForCard("pct_recebido_no_prazo", rede?.pct_recebido_no_prazo, metaRecebido);
                    const hint = [h.hint, `Tempo médio até recebido: ${fmtHours(rede?.avg_horas_ate_recebido)}`].filter(Boolean).join(" · ");
                    return <KpiCard label="Recebido no prazo" value={fmtPct(rede?.pct_recebido_no_prazo)} hint={hint} tone={h.tone} />;
                  })()}
                  {(() => {
                    const h = metaHintForCard("pct_devolutiva_no_prazo", rede?.pct_devolutiva_no_prazo, metaDevolutiva);
                    const hint = [h.hint, `Tempo médio até devolutiva: ${fmtHours(rede?.avg_horas_ate_devolutiva)}`].filter(Boolean).join(" · ");
                    return <KpiCard label="Devolutiva no prazo" value={fmtPct(rede?.pct_devolutiva_no_prazo)} hint={hint} tone={h.tone} />;
                  })()}
                  {(() => {
                    const h = metaHintForCard("pct_conclusao_no_prazo", rede?.pct_conclusao_no_prazo, metaConclusao);
                    const hint = [h.hint, `Tempo médio até conclusão: ${fmtDays(rede?.avg_dias_ate_conclusao)}`].filter(Boolean).join(" · ");
                    return <KpiCard label="Conclusão no prazo" value={fmtPct(rede?.pct_conclusao_no_prazo)} hint={hint} tone={h.tone} />;
                  })()}
                  {(() => {
                    const h = metaHintForCard("pct_contato_no_prazo", rede?.pct_contato_no_prazo, metaContato);
                    const hint = [h.hint, `Tempo médio até contato: ${fmtHours(rede?.avg_horas_ate_contato)}`].filter(Boolean).join(" · ");
                    return <KpiCard label="Intermun.: contato no prazo" value={fmtPct(rede?.pct_contato_no_prazo)} hint={hint} tone={h.tone} />;
                  })()}
                </div>

                <div style={{ marginTop: 14, display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14 }}>
                  <div>
                    <div style={{ fontWeight: 950 }}>Piores destinos (CRAS)</div>
                    <Table
                      columns={[
                        { key: "label", label: "Destino", render: (r) => r.label || `${r.destino_tipo || ""} · ${r.destino_nome || ""}` || "—" },
                        { key: "atrasados", label: "Atrasos", render: (r) => fmtNum(r.atrasados) },
                        { key: "em_risco", label: "Em risco", render: (r) => fmtNum(r.em_risco) },
                        { key: "pct_devolutiva_no_prazo", label: "Devolutiva no prazo", render: (r) => fmtPct(r.pct_devolutiva_no_prazo) },
                        { key: "avg_horas_ate_devolutiva", label: "Tempo médio", render: (r) => fmtHours(r.avg_horas_ate_devolutiva) },
                        { key: "score", label: "Score", render: (r) => (Number.isFinite(Number(r.score)) ? Number(r.score).toFixed(1) : "—") },
                      ]}
                      rows={redeWorst.map((x, i) => ({ ...x, id: x.key || i }))}
                      emptyText="Sem dados de ranking."
                    />
                  </div>

                  <div>
                    <div style={{ fontWeight: 950 }}>Melhores destinos (CRAS)</div>
                    <Table
                      columns={[
                        { key: "label", label: "Destino", render: (r) => r.label || `${r.destino_tipo || ""} · ${r.destino_nome || ""}` || "—" },
                        { key: "pct_devolutiva_no_prazo", label: "Devolutiva no prazo", render: (r) => fmtPct(r.pct_devolutiva_no_prazo) },
                        { key: "avg_horas_ate_devolutiva", label: "Tempo médio", render: (r) => fmtHours(r.avg_horas_ate_devolutiva) },
                        { key: "concluidos", label: "Concluídos", render: (r) => fmtNum(r.concluidos) },
                        { key: "score", label: "Score", render: (r) => (Number.isFinite(Number(r.score)) ? Number(r.score).toFixed(1) : "—") },
                      ]}
                      rows={redeBest.map((x, i) => ({ ...x, id: x.key || i }))}
                      emptyText="Sem dados de ranking."
                    />
                  </div>
                </div>

                <div style={{ marginTop: 14, display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14 }}>
                  <div>
                    <div style={{ fontWeight: 950 }}>Piores municípios destino (intermunicipal)</div>
                    <Table
                      columns={[
                        { key: "municipio_destino_nome", label: "Município" },
                        { key: "atrasados", label: "Atrasos", render: (r) => fmtNum(r.atrasados) },
                        { key: "em_risco", label: "Em risco", render: (r) => fmtNum(r.em_risco) },
                        { key: "pct_contato_no_prazo", label: "Contato no prazo", render: (r) => fmtPct(r.pct_contato_no_prazo) },
                        { key: "avg_horas_ate_contato", label: "Tempo médio", render: (r) => fmtHours(r.avg_horas_ate_contato) },
                        { key: "score", label: "Score", render: (r) => (Number.isFinite(Number(r.score)) ? Number(r.score).toFixed(1) : "—") },
                      ]}
                      rows={interWorst.map((x, i) => ({ ...x, id: x.municipio_destino_id || i }))}
                      emptyText="Sem dados intermunicipais."
                    />
                  </div>

                  <div>
                    <div style={{ fontWeight: 950 }}>Melhores municípios destino (intermunicipal)</div>
                    <Table
                      columns={[
                        { key: "municipio_destino_nome", label: "Município" },
                        { key: "pct_contato_no_prazo", label: "Contato no prazo", render: (r) => fmtPct(r.pct_contato_no_prazo) },
                        { key: "avg_horas_ate_contato", label: "Tempo médio", render: (r) => fmtHours(r.avg_horas_ate_contato) },
                        { key: "concluidos", label: "Concluídos", render: (r) => fmtNum(r.concluidos) },
                        { key: "score", label: "Score", render: (r) => (Number.isFinite(Number(r.score)) ? Number(r.score).toFixed(1) : "—") },
                      ]}
                      rows={interBest.map((x, i) => ({ ...x, id: x.municipio_destino_id || i }))}
                      emptyText="Sem dados intermunicipais."
                    />
                  </div>
                </div>
              </div>
            </ErrorBoundary>
          ) : null}
        </div>
      </main>
    </div>
  );
}