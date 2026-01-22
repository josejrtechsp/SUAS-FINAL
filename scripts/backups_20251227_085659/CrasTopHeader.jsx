import React from "react";

/**
 * TOPO PADRÃO CRAS (NÃO ALTERAR)
 * Este componente é a identidade visual do CRAS (logo, usuário, município/unidade, Portal/Sair e abas).
 * Qualquer mudança aqui precisa ser intencional.
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
    <div className="card" style={{ padding: 16, borderRadius: 24, border: "1px solid rgba(2,6,23,.08)", background: "rgba(255,255,255,.78)" }}>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 520px", gap: 14, alignItems: "start" }}>
        <div>
          <div style={{ display: "inline-flex", alignItems: "center", gap: 10, padding: "6px 12px", borderRadius: 999, border: "1px solid rgba(99,102,241,.25)", background: "rgba(99,102,241,.08)", color: "rgb(79,70,229)", fontWeight: 900, letterSpacing: ".10em", textTransform: "uppercase", fontSize: 12 }}>
            PLATAFORMA DE ASSISTÊNCIA SOCIAL
          </div>

          <div style={{ marginTop: 10, fontSize: 42, fontWeight: 950, lineHeight: 1.05 }}>
            Sistema <span style={{ color: "rgb(99,102,241)" }}>CRAS</span>
          </div>

          <div className="texto-suave" style={{ marginTop: 8 }}>
            Triagem, PAIF e rede com LGPD aplicada
          </div>

          <div className="texto-suave" style={{ marginTop: 8 }}>
            Município ativo: <strong>{municipioAtivoNome || "—"}</strong>{unidadeAtivaNome ? <> · Unidade: <strong>{unidadeAtivaNome}</strong></> : null}
          </div>
        </div>

        <div>
          <div style={{ display: "flex", justifyContent: "space-between", gap: 10, alignItems: "center", flexWrap: "wrap" }}>
            <div style={{ fontWeight: 900 }}>{usuarioLogado?.nome || "—"}</div>
            <div style={{ display: "inline-flex", alignItems: "center", padding: "6px 10px", borderRadius: 999, background: "rgba(99,102,241,.10)", border: "1px solid rgba(99,102,241,.18)", fontWeight: 900, color: "rgb(79,70,229)" }}>
              Admin do sistema
            </div>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "140px 1fr", gap: 10, marginTop: 12, alignItems: "center" }}>
            <div className="texto-suave">Município ativo:</div>
            <select className="input" value={municipioAtivoId || ""} onChange={(e) => { setMunicipioAtivoId(e.target.value); setUnidadeAtivaId(""); }}>
              <option value="">Selecione...</option>
              {(municipios || []).map((m) => (
                <option key={m.id} value={String(m.id)}>{m.nome}</option>
              ))}
            </select>

            <div className="texto-suave">Unidade CRAS:</div>
            <select className="input" value={unidadeAtivaId || ""} onChange={(e) => setUnidadeAtivaId(e.target.value)} disabled={!municipioAtivoId}>
              <option value="">Selecione...</option>
              {(unidades || []).map((u) => (
                <option key={u.id} value={String(u.id)}>{u.nome}</option>
              ))}
            </select>
          </div>

          <div style={{ display: "flex", justifyContent: "flex-end", gap: 10, marginTop: 12 }}>
            <button className="btn btn-secundario" type="button" onClick={onPortal}>Portal</button>
            <button className="btn btn-secundario" type="button" onClick={onSair}>Sair</button>
          </div>
        </div>
      </div>

      <div className="app-tabs" style={{ marginTop: 14 }}>
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
