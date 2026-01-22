#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TS="$(date +%Y%m%d_%H%M%S)"
BK="$ROOT/scripts/backups_$TS"
mkdir -p "$BK"

echo "== [1/7] Backup de arquivos principais =="
cp -f "$ROOT/frontend/src/CrasApp.jsx" "$BK/CrasApp.jsx" 2>/dev/null || true
cp -f "$ROOT/frontend/src/components/CrasTopHeader.jsx" "$BK/CrasTopHeader.jsx" 2>/dev/null || true
cp -f "$ROOT/frontend/src/components/CrasPageHeader.jsx" "$BK/CrasPageHeader.jsx" 2>/dev/null || true
cp -f "$ROOT/frontend/src/TelaCrasInicioDashboard.jsx" "$BK/TelaCrasInicioDashboard.jsx" 2>/dev/null || true
cp -f "$ROOT/frontend/src/config.js" "$BK/config.js" 2>/dev/null || true

echo "== [2/7] Garantir API_BASE em 8001 (frontend/src/config.js) =="
# macOS sed
sed -i '' 's|127\.0\.0\.1:8000|127.0.0.1:8001|g; s|localhost:8000|localhost:8001|g' "$ROOT/frontend/src/config.js" 2>/dev/null || true
# se config.js for muito diferente, garante um default correto:
if ! grep -q "8001" "$ROOT/frontend/src/config.js"; then
cat > "$ROOT/frontend/src/config.js" <<'EOF'
export const API_BASE =
  import.meta.env.VITE_API_URL || "http://127.0.0.1:8001";
EOF
fi

echo "== [3/7] Compactar CrasPageHeader (sem ficar gigante) =="
cat > "$ROOT/frontend/src/components/CrasPageHeader.jsx" <<'EOF'
import React from "react";

/**
 * Cabeçalho interno (aba) — compacto, largura total.
 * Compatível com props antigas e novas.
 */
export default function CrasPageHeader({
  kicker = "MÓDULO SUAS · INTELIGÊNCIA SOCIAL",
  title,
  subtitle,
  bullets,
  tips,
  rightTag,
  badge,
  rightMetaLabel = "Usuário",
  rightMetaValue = "—",
  rightText,
}) {
  const lista = (bullets && bullets.length ? bullets : tips) || [];
  const tag = rightTag || badge || "CRAS";

  return (
    <div
      className="card"
      style={{
        width: "100%",
        maxWidth: "100%",
        padding: 8,
        borderRadius: 16,
        border: "1px solid rgba(2,6,23,.08)",
        background: "rgba(255,255,255,.75)",
        boxShadow: "0 10px 30px rgba(2,6,23,.06)",
      }}
    >
      <div style={{ display: "grid", gridTemplateColumns: "1fr 220px", gap: 12, alignItems: "start" }}>
        <div>
          <div style={{
            display: "inline-flex",
            alignItems: "center",
            gap: 8,
            padding: "4px 10px",
            borderRadius: 999,
            border: "1px solid rgba(99,102,241,.25)",
            background: "rgba(99,102,241,.08)",
            color: "rgb(79,70,229)",
            fontWeight: 900,
            letterSpacing: ".10em",
            textTransform: "uppercase",
            fontSize: 11,
          }}>
            {kicker}
          </div>

          <div style={{ marginTop: 6, fontSize: 22, fontWeight: 950, color: "rgb(2,6,23)", lineHeight: 1.08 }}>
            {title}
          </div>

          {subtitle ? (
            <div style={{ marginTop: 6, fontSize: 13, color: "rgba(2,6,23,.65)", lineHeight: 1.35 }}>
              {subtitle}
            </div>
          ) : null}

          {lista.length ? (
            <div style={{ marginTop: 8 }}>
              {lista.map((t, idx) => (
                <div key={idx} style={{ display: "flex", gap: 10, alignItems: "flex-start", marginTop: 6, fontSize: 13 }}>
                  <span aria-hidden style={{ lineHeight: "18px" }}>✅</span>
                  <div style={{ color: "rgba(2,6,23,.85)" }}>{t}</div>
                </div>
              ))}
            </div>
          ) : null}
        </div>

        <div>
          <div style={{
            height: 22,
            borderRadius: 999,
            background: "rgba(14,165,233,.12)",
            border: "1px solid rgba(14,165,233,.18)",
            display: "flex",
            alignItems: "center",
            padding: "0 10px",
          }}>
            <span style={{ fontSize: 12, fontWeight: 900, color: "rgb(3,105,161)" }}>{tag}</span>
          </div>

          <div style={{ marginTop: 8, color: "rgba(2,6,23,.65)", fontSize: 13 }}>
            {rightText ? (
              rightText
            ) : (
              <>
                {rightMetaLabel}: <strong style={{ color: "rgba(2,6,23,.9)" }}>{rightMetaValue}</strong>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
EOF

echo "== [4/7] Topo institucional (mantém identidade) via CrasTopHeader.jsx =="
cat > "$ROOT/frontend/src/components/CrasTopHeader.jsx" <<'EOF'
import React from "react";

/**
 * TOPO PADRÃO DO SITE (NÃO BAGUNÇAR)
 * Logo/identidade + município/unidade + Portal/Sair + Abas
 */
export default function CrasTopHeader({
  usuarioLogado,
  municipios,
  municipioAtivoId,
  setMunicipioAtivoId,
  unidades,
  unidadeAtivaId,
  setUnidadeAtivaId,
  municipioAtivoNome,
  unidadeAtivaNome,
  activeTab,
  setActiveTab,
  tabs,
  onPortal,
  onSair,
}) {
  return (
    <div className="app-header">
      <div className="app-header-inner">
        <div>
          <div className="app-title-tag">PLATAFORMA DE ASSISTÊNCIA SOCIAL</div>
          <div className="app-title">Sistema <span className="app-title-accent">CRAS</span></div>
          <div className="app-subtitle">Triagem, PAIF, SCFV e CadÚnico com rastreabilidade e LGPD aplicada</div>
          <div className="app-subtitle" style={{ marginTop: 6 }}>
            Município ativo: <strong>{municipioAtivoNome || "—"}</strong>
            {unidadeAtivaNome ? <> · Unidade: <strong>{unidadeAtivaNome}</strong></> : null}
          </div>
        </div>

        <div className="app-user-panel">
          <div className="app-user-row">
            <div className="app-user-name">{usuarioLogado?.nome || "—"}</div>
            <div className="app-user-badge">Admin do sistema</div>
          </div>

          <div className="app-user-form">
            <div className="app-user-label">Município ativo:</div>
            <select className="input" value={municipioAtivoId || ""} onChange={(e) => { setMunicipioAtivoId(e.target.value); setUnidadeAtivaId(""); }}>
              <option value="">Selecione...</option>
              {(municipios || []).map((m) => (
                <option key={m.id} value={String(m.id)}>{m.nome}</option>
              ))}
            </select>

            <div className="app-user-label">Unidade CRAS:</div>
            <select className="input" value={unidadeAtivaId || ""} onChange={(e) => setUnidadeAtivaId(e.target.value)} disabled={!municipioAtivoId}>
              <option value="">Selecione...</option>
              {(unidades || []).map((u) => (
                <option key={u.id} value={String(u.id)}>{u.nome}</option>
              ))}
            </select>
          </div>

          <div className="app-user-actions">
            <button className="btn btn-secundario" type="button" onClick={onPortal}>Portal</button>
            <button className="btn btn-secundario" type="button" onClick={onSair}>Sair</button>
          </div>
        </div>
      </div>

      <div className="app-tabs">
        {(tabs || []).map((t) => (
          <button
            key={t.key}
            type="button"
            className={"app-tab" + (activeTab === t.key ? " app-tab-active" : "")}
            onClick={() => setActiveTab(t.key)}
          >
            {t.label}
          </button>
        ))}
      </div>
    </div>
  );
}
EOF

echo "== [5/7] Dashboard robusto (parse JSON + erro 401 visível) =="
cat > "$ROOT/frontend/src/TelaCrasInicioDashboard.jsx" <<'EOF'
import React, { useEffect, useMemo, useState } from "react";

export default function TelaCrasInicioDashboard({
  apiBase,
  apiFetch,
  onNavigate,
  unidadeId,
  municipioId,
}) {
  const [data, setData] = useState(null);
  const [tarefasResumo, setTarefasResumo] = useState(null);
  const [erro, setErro] = useState(null);
  const [loading, setLoading] = useState(false);

  async function fetchJson(url) {
    const res = await apiFetch(url);
    const json = await res.json().catch(() => null);
    if (!res.ok) throw new Error(json?.detail || `Falha (HTTP ${res.status})`);
    return json;
  }

  function withQuery(path) {
    const u = new URL(`${apiBase}${path}`);
    if (unidadeId) u.searchParams.set("unidade_id", String(unidadeId));
    if (municipioId) u.searchParams.set("municipio_id", String(municipioId));
    return u.toString();
  }

  async function load() {
    setLoading(true);
    setErro(null);
    try {
      let ov = null;
      try { ov = await fetchJson(withQuery("/cras/dashboard/overview")); }
      catch { ov = await fetchJson(withQuery("/cras/relatorios/overview")); }
      setData(ov);

      try { setTarefasResumo(await fetchJson(withQuery("/cras/tarefas/resumo"))); }
      catch { setTarefasResumo(null); }

    } catch (e) {
      setErro(String(e?.message || e));
      setData(null);
      setTarefasResumo(null);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, [unidadeId, municipioId]);

  const get = (...keys) => {
    const d = data || {};
    for (const k of keys) {
      const parts = String(k).split(".");
      let cur = d; let ok = True;
      ok = True;
      for (const p of parts) {
        if (cur && Object.prototype.hasOwnProperty.call(cur, p)) cur = cur[p];
        else { ok = False; break; }
      }
      if (ok && cur !== undefined && cur !== null) return cur;
    }
    return "—";
  };

  const cards = useMemo(() => ([
    { k: "Usuários", v: get("pessoas_total","total_pessoas","pessoas"), hint: "Pessoas cadastradas/atendidas" },
    { k: "Famílias", v: get("familias_total","total_familias","familias"), hint: "Famílias cadastradas" },
    { k: "Casos abertos", v: get("casos_abertos","total_casos_abertos","casos.abertos"), hint: "Casos em andamento" },
    { k: "Pendências (SLA)", v: get("pendencias_sla","total_pendencias","pendencias.total"), hint: "Itens vencendo/vencidos" },
    { k: "SCFV presença (mês)", v: get("scfv_presencas_mes","scfv.presencas_mes"), hint: "Presenças registradas no mês" },
    { k: "SCFV ausências (mês)", v: get("scfv_ausencias_mes","scfv.ausencias_mes"), hint: "Ausências no mês" },
    { k: "Programas presença (mês)", v: get("programas_presencas_mes","programas.presencas_mes"), hint: "Presenças em encontros" },
    { k: "CadÚnico pendente", v: get("cadunico_pendentes","cadunico.pendentes"), hint: "Pré-cadastro/agendamento/atrasos" },
  ]), [data]);

  return (
    <div>
      {erro ? (
        <div className="card" style={{ padding: 12, borderRadius: 14, marginBottom: 12 }}>
          <strong>Dashboard indisponível:</strong> {erro}
          <div className="texto-suave" style={{ marginTop: 6 }}>
            Se aparecer “Token…”, faça login novamente.
          </div>
        </div>
      ) : null}

      <div style={{ display: "flex", justifyContent: "space-between", gap: 10, flexWrap: "wrap", alignItems: "center" }}>
        <div className="texto-suave">Painel operacional do CRAS</div>
        <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
          <button className="btn btn-secundario" type="button" onClick={load} disabled={loading}>
            {loading ? "Atualizando..." : "Atualizar"}
          </button>
          <button className="btn btn-primario" type="button" onClick={() => onNavigate?.({ tab: "relatorios" })}>
            Ir para Relatórios
          </button>
        </div>
      </div>

      <div style={{ marginTop: 12, display: "grid", gridTemplateColumns: "repeat(4, minmax(220px, 1fr))", gap: 12 }}>
        {cards.map((c) => (
          <div key={c.k} className="card" style={{ padding: 12, borderRadius: 16 }}>
            <div className="texto-suave" style={{ fontSize: 13 }}>{c.k}</div>
            <div style={{ fontSize: 28, fontWeight: 950, marginTop: 6 }}>{c.v}</div>
            <div className="texto-suave" style={{ marginTop: 4 }}>{c.hint}</div>
          </div>
        ))}
      </div>

      <div className="card" style={{ padding: 12, borderRadius: 16, marginTop: 12 }}>
        <div style={{ display: "flex", justifyContent: "space-between", gap: 10, flexWrap: "wrap", alignItems: "center" }}>
          <div style={{ fontWeight: 950 }}>Equipe e prazos (tarefas/SLA)</div>
          <div className="texto-suave">
            Abertas: <strong>{tarefasResumo?.total_abertas ?? "—"}</strong> · Vencidas: <strong>{tarefasResumo?.total_vencidas ?? "—"}</strong>
          </div>
        </div>

        <div style={{ overflowX: "auto", marginTop: 10 }}>
          <table className="table" style={{ width: "100%" }}>
            <thead>
              <tr>
                <th>Técnico</th>
                <th style={{ textAlign: "right" }}>Abertas</th>
                <th style={{ textAlign: "right" }}>Vencidas</th>
                <th style={{ textAlign: "right" }}>Concluídas</th>
              </tr>
            </thead>
            <tbody>
              {(tarefasResumo?.por_tecnico || []).map((x, idx) => (
                <tr key={idx}>
                  <td><strong>{x.responsavel_nome || "—"}</strong></td>
                  <td style={{ textAlign: "right" }}>{x.abertas}</td>
                  <td style={{ textAlign: "right" }}>{x.vencidas}</td>
                  <td style={{ textAlign: "right" }}>{x.concluidas}</td>
                </tr>
              ))}
              {(!tarefasResumo?.por_tecnico || tarefasResumo.por_tecnico.length === 0) ? (
                <tr><td colSpan={4} className="texto-suave">Sem tarefas cadastradas ainda.</td></tr>
              ) : null}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
EOF

# Fix: o JS acima usa True/False por engano? Corrige rapidamente:
sed -i '' 's/ok = True/ok = true/g; s/ok = False/ok = false/g' "$ROOT/frontend/src/TelaCrasInicioDashboard.jsx" || true

echo "== [6/7] HUB CRAS limpo (CrasApp.jsx) usando topo aprovado e sem duplicação =="
cat > "$ROOT/frontend/src/CrasApp.jsx" <<'EOF'
import React, { useEffect, useMemo, useState } from "react";
import { API_BASE } from "./config.js";

import ErrorBoundary from "./components/ErrorBoundary.jsx";
import CrasPageHeader from "./components/CrasPageHeader.jsx";
import CrasTopHeader from "./components/CrasTopHeader.jsx";

import TelaCrasInicioDashboard from "./TelaCrasInicioDashboard.jsx";
import TelaCras from "./TelaCras.jsx";
import TelaCrasCadUnico from "./TelaCrasCadUnico.jsx";
import TelaCrasEncaminhamentos from "./TelaCrasEncaminhamentos.jsx";
import TelaCrasCasos from "./TelaCrasCasos.jsx";
import TelaCrasCadastros from "./TelaCrasCadastros.jsx";
import TelaCrasProgramas from "./TelaCrasProgramas.jsx";
import TelaCrasScfv from "./TelaCrasScfv.jsx";
import TelaCrasFicha from "./TelaCrasFicha.jsx";
import TelaCrasRelatorios from "./TelaCrasRelatorios.jsx";

export default function CrasApp({ usuarioLogado }) {
  const [activeTab, setActiveTab] = useState(() => localStorage.getItem("cras_active_tab") || "inicio");

  const [municipios, setMunicipios] = useState([]);
  const [unidades, setUnidades] = useState([]);

  const [municipioAtivoId, setMunicipioAtivoId] = useState(() => {
    const saved = localStorage.getItem("cras_municipio_ativo");
    if (saved) return saved;
    return usuarioLogado?.municipio_id ? String(usuarioLogado.municipio_id) : "";
  });

  const [unidadeAtivaId, setUnidadeAtivaId] = useState(() => localStorage.getItem("cras_unidade_ativa") || "");

  useEffect(() => { try { localStorage.setItem("cras_active_tab", activeTab); } catch {} }, [activeTab]);
  useEffect(() => { try { localStorage.setItem("cras_municipio_ativo", municipioAtivoId || ""); } catch {} }, [municipioAtivoId]);
  useEffect(() => { try { localStorage.setItem("cras_unidade_ativa", unidadeAtivaId || ""); } catch {} }, [unidadeAtivaId]);

  function getToken() {
    return (
      localStorage.getItem("poprua_token") ||
      localStorage.getItem("access_token") ||
      localStorage.getItem("token") ||
      ""
    );
  }

  async function apiFetch(url, options = {}) {
    const headers = new Headers(options.headers || {});
    const token = getToken();
    if (token && !headers.get("Authorization")) headers.set("Authorization", `Bearer ${token}`);

    const hasBody = options.body != null;
    const isForm = typeof FormData !== "undefined" && options.body instanceof FormData;
    if (hasBody && !isForm && !headers.get("Content-Type")) headers.set("Content-Type", "application/json");

    return fetch(url, { ...options, headers });
  }

  async function apiJson(path) {
    const res = await apiFetch(`${API_BASE}${path}`);
    const json = await res.json().catch(() => null);
    if (!res.ok) throw new Error(json?.detail || `Falha (HTTP ${res.status})`);
    return json;
  }

  useEffect(() => {
    (async () => {
      try { setMunicipios(await apiJson("/municipios")); } catch { setMunicipios([]); }
    })();
  }, []);

  useEffect(() => {
    if (!municipioAtivoId) return;
    (async () => {
      try { setUnidades(await apiJson(`/cras/unidades?municipio_id=${encodeURIComponent(municipioAtivoId)}`)); }
      catch { setUnidades([]); }
    })();
  }, [municipioAtivoId]);

  const municipioAtivoNome = useMemo(() => {
    const id = Number(municipioAtivoId || 0);
    const m = (municipios || []).find((x) => Number(x.id) === id);
    return m?.nome || (usuarioLogado?.municipio_nome || "");
  }, [municipios, municipioAtivoId, usuarioLogado]);

  const unidadeAtivaNome = useMemo(() => {
    const id = Number(unidadeAtivaId || 0);
    const u = (unidades || []).find((x) => Number(x.id) === id);
    return u?.nome || "";
  }, [unidades, unidadeAtivaId]);

  const TABS = useMemo(() => ([
    { key: "inicio", label: "Início" },
    { key: "paif", label: "Triagem+PAIF" },
    { key: "cadunico", label: "CadÚnico" },
    { key: "encaminhamentos", label: "Encaminhamentos" },
    { key: "casos", label: "Casos" },
    { key: "cadastros", label: "Cadastros" },
    { key: "programas", label: "Programas" },
    { key: "scfv", label: "SCFV" },
    { key: "ficha", label: "Ficha" },
    { key: "relatorios", label: "Relatórios" },
  ]), []);

  function sair() {
    localStorage.removeItem("poprua_token");
    localStorage.removeItem("poprua_usuario");
    window.location.reload();
  }

  function portal() {
    window.location.href = "/app";
  }

  const onNavigate = (x) => { if (x?.tab) setActiveTab(x.tab); };

  return (
    <div className="app-root">
      <CrasTopHeader
        usuarioLogado={usuarioLogado}
        municipios={municipios}
        municipioAtivoId={municipioAtivoId}
        setMunicipioAtivoId={setMunicipioAtivoId}
        unidades={unidades}
        unidadeAtivaId={unidadeAtivaId}
        setUnidadeAtivaId={setUnidadeAtivaId}
        municipioAtivoNome={municipioAtivoNome}
        unidadeAtivaNome={unidadeAtivaNome}
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        tabs={TABS}
        onPortal={portal}
        onSair={sair}
      />

      <main className="app-main">
        {activeTab === "inicio" && (
          <ErrorBoundary label="CRAS · Início">
            <>
              <CrasPageHeader
                title="CRAS — Início"
                subtitle="Painel operacional do equipamento: usuários, pendências, prazos e presença."
                bullets={[
                  "Pendências por SLA e ações rápidas.",
                  "Presença/ausência (SCFV e Programas).",
                  "Equipe e prazos (tarefas/SLA por técnico).",
                ]}
                rightTag="CRAS"
                rightMetaLabel="Usuário"
                rightMetaValue={usuarioLogado?.nome || "—"}
              />
              <div style={{ marginTop: 12 }}>
                <TelaCrasInicioDashboard
                  apiBase={API_BASE}
                  apiFetch={apiFetch}
                  onNavigate={onNavigate}
                  unidadeId={unidadeAtivaId || null}
                  municipioId={municipioAtivoId || null}
                />
              </div>
            </>
          </ErrorBoundary>
        )}

        {activeTab === "paif" && (
          <ErrorBoundary label="CRAS · Triagem + PAIF">
            <>
              <CrasPageHeader title="CRAS — Triagem + PAIF" subtitle="Fila do dia e acompanhamento por etapas." bullets={["Triagem vinculada à unidade.", "Checklist e plano por etapa.", "Histórico auditável."]} />
              <TelaCras apiBase={API_BASE} apiFetch={apiFetch} usuarioLogado={usuarioLogado} />
            </>
          </ErrorBoundary>
        )}

        {activeTab === "cadunico" && (
          <ErrorBoundary label="CRAS · CadÚnico">
            <>
              <CrasPageHeader title="CRAS — CadÚnico" subtitle="Pré-cadastro, agendamento, finalização e rastreabilidade." bullets={["Status e histórico.", "Não compareceu e reagendamento.", "Pendências por prazo."]} />
              <TelaCrasCadUnico apiBase={API_BASE} apiFetch={apiFetch} />
            </>
          </ErrorBoundary>
        )}

        {activeTab === "encaminhamentos" && (
          <ErrorBoundary label="CRAS · Encaminhamentos">
            <>
              <CrasPageHeader title="CRAS — Encaminhamentos" subtitle="Encaminhar e controlar devolutiva." bullets={["Sem devolutiva = atraso por prazo.", "Cobrança com evidência.", "Timeline do item."]} />
              <TelaCrasEncaminhamentos apiBase={API_BASE} apiFetch={apiFetch} usuarioLogado={usuarioLogado} />
            </>
          </ErrorBoundary>
        )}

        {activeTab === "casos" && (
          <ErrorBoundary label="CRAS · Casos">
            <>
              <CrasPageHeader title="CRAS — Casos" subtitle="Etapas, validação, SLA e auditoria." bullets={["Linha do metrô por etapa.", "Validação de recebimento.", "Alertas e histórico."]} />
              <TelaCrasCasos apiBase={API_BASE} apiFetch={apiFetch} usuarioLogado={usuarioLogado} />
            </>
          </ErrorBoundary>
        )}

        {activeTab === "cadastros" && (
          <ErrorBoundary label="CRAS · Cadastros">
            <>
              <CrasPageHeader title="CRAS — Cadastros" subtitle="Pessoa + Família (base da rede)." bullets={["Pessoa → família → membros.", "Vínculos para casos e programas.", "Documentos e anexos."]} />
              <TelaCrasCadastros apiBase={API_BASE} apiFetch={apiFetch} usuarioLogado={usuarioLogado} />
            </>
          </ErrorBoundary>
        )}

        {activeTab === "programas" && (
          <ErrorBoundary label="CRAS · Programas">
            <>
              <CrasPageHeader title="CRAS — Programas e Projetos" subtitle="Cadastro, inscrições, encontros e presença." bullets={["Encontros por programa.", "Presença por encontro.", "Abrir ficha 360° do participante."]} />
              <TelaCrasProgramas apiBase={API_BASE} apiFetch={apiFetch} onNavigate={onNavigate} />
            </>
          </ErrorBoundary>
        )}

        {activeTab === "scfv" && (
          <ErrorBoundary label="CRAS · SCFV">
            <>
              <CrasPageHeader title="CRAS — SCFV" subtitle="Turmas, chamada, relatório mensal e evasão." bullets={["Ações: abrir ficha e registrar contato.", "Alertas por evasão.", "Exportação CSV."]} />
              <TelaCrasScfv apiBase={API_BASE} apiFetch={apiFetch} onNavigate={onNavigate} />
            </>
          </ErrorBoundary>
        )}

        {activeTab === "ficha" && (
          <ErrorBoundary label="CRAS · Ficha 360°">
            <>
              <CrasPageHeader title="CRAS — Ficha 360°" subtitle="Tudo do usuário em todos os serviços." bullets={["Casos, CadÚnico, SCFV, Programas.", "Pendências com contexto.", "Timeline/auditoria e anexos."]} />
              <TelaCrasFicha apiBase={API_BASE} apiFetch={apiFetch} onNavigate={onNavigate} />
            </>
          </ErrorBoundary>
        )}

        {activeTab === "relatorios" && (
          <ErrorBoundary label="CRAS · Relatórios">
            <>
              <CrasPageHeader title="Relatórios — Gestão e gargalos" subtitle="Consolidado com drill-down e priorização." bullets={["PIA faltando, CadÚnico atrasado, SCFV (evasão/baixa).", "Abrir ficha já em pendências.", "Visão por SLA."]} />
              <TelaCrasRelatorios apiBase={API_BASE} apiFetch={apiFetch} onNavigate={onNavigate} />
            </>
          </ErrorBoundary>
        )}
      </main>
    </div>
  );
}
EOF

echo "== [7/7] Diagnóstico profundo + ZIP final =="
cd "$ROOT/frontend"
npm install >/dev/null
npm run build

cd "$ROOT"
python3 - <<'PY'
import compileall
ok = compileall.compile_dir("backend/app", quiet=1)
print("Backend compileall:", "OK" if ok else "FALHOU")
raise SystemExit(0 if ok else 1)
PY

ZIP="$ROOT/SUAS_CRAS_FINAL.zip"
rm -f "$ZIP"
zip -r "$ZIP" backend frontend docs scripts \
  -x "backend/.venv/*" \
  -x "frontend/node_modules/*" \
  -x "**/.DS_Store" \
  -x "__MACOSX/*" >/dev/null

echo "OK: ZIP gerado -> $ZIP"
ls -lah "$ZIP"
echo "Backups em: $BK"
