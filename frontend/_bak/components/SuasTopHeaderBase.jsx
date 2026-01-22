import React from "react";

function Chip({ active, children, onClick }) {
  return (
    <button
      onClick={onClick}
      style={{
        borderRadius: 999,
        padding: "10px 14px",
        border: active ? "1px solid rgba(122,92,255,0.35)" : "1px solid rgba(0,0,0,0.08)",
        background: active ? "rgba(122,92,255,0.10)" : "rgba(255,255,255,0.75)",
        fontWeight: 900,
        cursor: "pointer",
      }}
    >
      {children}
    </button>
  );
}

function normOptions(arr = []) {
  return arr.map((o) => {
    if (typeof o === "string") return { value: o, label: o, raw: o };
    const value = o.id ?? o.value ?? o.nome ?? o.name ?? o.label ?? String(o);
    const label = o.nome ?? o.name ?? o.label ?? String(value);
    return { value: String(value), label: String(label), raw: o };
  });
}

export default function SuasTopHeaderBase({
  // texto
  systemPill = "PLATAFORMA DE ASSISTÊNCIA SOCIAL",
  titleLeft = "Sistema",
  titleRight = "CRAS",
  subtitle = "",

  // centro
  userName = "Admin Pop Rua",
  userRole = "admin",

  // direita
  municipioAtivo = "",
  setMunicipioAtivo = () => {},
  municipios = [],

  unidadeAtiva = "",
  setUnidadeAtiva = () => {},
  unidades = [],
  unidadeLabel = "Unidade:",

  onPortal = () => {},
  onSair = () => {},

  // chips
  tabs = [],
  activeTab = "",
  setActiveTab = () => {},
}) {
  const cardStyle = {
    borderRadius: 26,
    padding: 18,
    background: "rgba(255,255,255,0.70)",
    border: "1px solid rgba(0,0,0,0.06)",
    boxShadow: "0 18px 60px rgba(0,0,0,0.12)",
    backdropFilter: "blur(10px)",
    WebkitBackdropFilter: "blur(10px)",
  };

  const pillStyle = {
    display: "inline-flex",
    alignItems: "center",
    padding: "6px 10px",
    borderRadius: 999,
    border: "1px solid rgba(122, 92, 255, 0.25)",
    background: "rgba(122, 92, 255, 0.10)",
    fontSize: 12,
    fontWeight: 900,
    letterSpacing: 2,
    textTransform: "uppercase",
    color: "rgba(92, 74, 220, 1)",
    marginBottom: 10,
  };

  const selectStyle = {
    width: "100%",
    padding: "10px 12px",
    borderRadius: 14,
    border: "1px solid rgba(0,0,0,0.10)",
    background: "rgba(255,255,255,0.85)",
    fontWeight: 800,
    outline: "none",
  };

  const btnStyle = {
    padding: "10px 14px",
    borderRadius: 999,
    border: "1px solid rgba(0,0,0,0.10)",
    background: "rgba(255,255,255,0.85)",
    fontWeight: 900,
    cursor: "pointer",
    whiteSpace: "nowrap",
  };

  const rolePill = {
    padding: "6px 10px",
    borderRadius: 999,
    border: "1px solid rgba(122,92,255,0.25)",
    background: "rgba(122,92,255,0.10)",
    fontWeight: 900,
    color: "rgba(92,74,220,1)",
  };

  const mOpts = normOptions(municipios);
  const uOpts = normOptions(unidades);

  const munVal =
    typeof municipioAtivo === "object" && municipioAtivo
      ? String(municipioAtivo.id ?? municipioAtivo.value ?? municipioAtivo.nome ?? "")
      : String(municipioAtivo ?? "");

  const uniVal =
    typeof unidadeAtiva === "object" && unidadeAtiva
      ? String(unidadeAtiva.id ?? unidadeAtiva.value ?? unidadeAtiva.nome ?? "")
      : String(unidadeAtiva ?? "");

  const onMunicipioChange = (v) => {
    if (typeof municipioAtivo === "object" && municipioAtivo) {
      const found = mOpts.find((x) => x.value === v);
      setMunicipioAtivo(found?.raw ?? v);
    } else setMunicipioAtivo(v);
  };

  const onUnidadeChange = (v) => {
    if (typeof unidadeAtiva === "object" && unidadeAtiva) {
      const found = uOpts.find((x) => x.value === v);
      setUnidadeAtiva(found?.raw ?? v);
    } else setUnidadeAtiva(v);
  };

  return (
    <div style={cardStyle}>
      {/* TOPO: 3 BLOCOS (esq / meio / dir) */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "1.25fr 0.55fr 1fr",
          gap: 18,
          alignItems: "start",
        }}
      >
        {/* ESQUERDA */}
        <div style={{ minWidth: 0 }}>
          <div style={pillStyle}>{systemPill}</div>

          <div style={{ fontSize: 54, lineHeight: 1.0, fontWeight: 900 }}>
            <span style={{ color: "rgba(60,60,70,0.70)" }}>{titleLeft} </span>
            <span style={{ color: "rgba(122,92,255,1)" }}>{titleRight}</span>
          </div>

          {subtitle ? (
            <div style={{ marginTop: 8, fontSize: 16, opacity: 0.75, fontWeight: 700 }}>
              {subtitle}
            </div>
          ) : null}
        </div>

        {/* MEIO (CENTRALIZADO) */}
        <div style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 10, paddingTop: 8 }}>
          <div style={{ fontWeight: 900, fontSize: 18, textAlign: "center" }}>{userName}</div>
          <div style={rolePill}>{String(userRole).toLowerCase()}</div>
        </div>

        {/* DIREITA */}
        <div style={{ minWidth: 0 }}>
          <div style={{ display: "grid", gridTemplateColumns: "140px 1fr", gap: 10, alignItems: "center" }}>
            <div style={{ opacity: 0.75, fontWeight: 800 }}>Município ativo:</div>
            <select style={selectStyle} value={munVal} onChange={(e) => onMunicipioChange(e.target.value)}>
              <option value="">Selecione…</option>
              {mOpts.map((m) => (
                <option key={m.value} value={m.value}>{m.label}</option>
              ))}
            </select>

            <div style={{ opacity: 0.75, fontWeight: 800 }}>{unidadeLabel}</div>

            <div style={{ display: "grid", gridTemplateColumns: "1fr auto auto", gap: 10, alignItems: "center" }}>
              <select style={selectStyle} value={uniVal} onChange={(e) => onUnidadeChange(e.target.value)}>
                <option value="">Selecione…</option>
                {uOpts.map((u) => (
                  <option key={u.value} value={u.value}>{u.label}</option>
                ))}
              </select>

              <button style={btnStyle} onClick={onPortal}>Portal</button>
              <button style={btnStyle} onClick={onSair}>Sair</button>
            </div>
          </div>
        </div>
      </div>

      <div style={{ height: 1, background: "rgba(0,0,0,0.08)", margin: "16px 0" }} />

      {/* CHIPS */}
      <div style={{ display: "flex", flexWrap: "wrap", gap: 10 }}>
        {tabs.map((t) => (
          <Chip key={t.key} active={t.key === activeTab} onClick={() => setActiveTab(t.key)}>
            {t.label}
          </Chip>
        ))}
      </div>
    </div>
  );
}
