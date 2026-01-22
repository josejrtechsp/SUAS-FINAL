import React from "react";

/**
 * SuasTopHeader (PADRÃO POPRUA)
 * - Usa as MESMAS classes/estrutura do topo do PopRua (App.jsx + App.css)
 * - Mantém a linha 1: Município ativo + Select + Sair (sempre na MESMA linha)
 * - Para CRAS/CREAS, adiciona linha 2: Unidade + Select + Portal (SEM Sair)
 */
export default function SuasTopHeader(props) {
  const titleRight = props.titleRight ?? "Pop Rua";
  const subtitle = props.subtitle ?? "";

  // usuário
  const usuarioLogado = props.usuarioLogado ?? props.user ?? null;
  const userName = props.userName ?? usuarioLogado?.nome ?? "—";

  // perfil/badge
  const rawPerfil =
    props.perfilAtivo ?? usuarioLogado?.perfil ?? usuarioLogado?.role ?? null;

  const perfilLabelOverride =
    props.perfilLabel ?? props.roleLabel ?? props.userRole ?? null;

  function mapPerfilLabel(p) {
    if (!p) return "—";
    if (p === "operador") return "Operador municipal";
    if (p === "coord_municipal") return "Coord. municipal";
    if (p === "gestor_consorcio") return "Gestor do consórcio";
    if (p === "admin") return "Admin do sistema";
    return String(p);
  }

  const perfilLabel = perfilLabelOverride
    ? String(perfilLabelOverride)
    : mapPerfilLabel(rawPerfil);

  const isPerfilMunicipal = Boolean(
    props.isPerfilMunicipal ??
      (rawPerfil === "operador" || rawPerfil === "coord_municipal")
  );

  // município
  const municipioAtivoNome =
    props.municipioAtivoNome ??
    usuarioLogado?.municipio_nome ??
    usuarioLogado?.municipio ??
    "";

  const municipioAtivoId = props.municipioAtivoId ?? "";
  const setMunicipioAtivoId = props.setMunicipioAtivoId ?? (() => {});
  const municipios = props.municipios ?? [];

  // unidade (opcional)
  const unidadeLabel = props.unidadeLabel ?? null;
  const unidadeAtivaId = props.unidadeAtivaId ?? "";
  const setUnidadeAtivaId = props.setUnidadeAtivaId ?? (() => {});
  const unidades = props.unidades ?? [];

  // ações
  const onPortal = typeof props.onPortal === "function" ? props.onPortal : null;
  const onSair = typeof props.onSair === "function" ? props.onSair : null;

  // abas
  const tabs = props.tabs ?? [];
  const activeTab = props.activeTab ?? "";
  const setActiveTab = props.setActiveTab ?? (() => {});

  const SELECT_W = 320;

  return (
    <header className="app-header">
      <div className="app-header-inner">
        <div className="app-header-title">
          <div className="app-title-tag">Plataforma de Assistência Social</div>

          <h1 className="app-title">
            <span className="app-title-prefix">Sistema</span>
            <span className="app-title-highlight">{titleRight}</span>
          </h1>

          <p className="app-subtitle">{subtitle}</p>
        </div>

        {/* BLOCO DIREITA (igual PopRua) */}
        <div className="header-user-row">
          <div className="header-user-top">
            <span className="header-user-nome">{userName}</span>
            <span className="header-user-perfil">{perfilLabel}</span>
          </div>

          {/* CONTROLES: 2 linhas (linha 2 só CRAS/CREAS) */}
          <div style={{ display: "grid", gap: 10, justifyItems: "end" }}>
            {/* LINHA 1 (IDÊNTICA POPRUA): Município + Select + Sair na MESMA linha */}
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "auto auto auto",
                alignItems: "center",
                columnGap: 10,
                justifyContent: "end",
              }}
            >
              {(isPerfilMunicipal || (municipios || []).length <= 1) ? (
                <>
                  <span className="texto-suave" style={{ margin: 0 }}>
                    Município:
                  </span>
                  <div style={{ width: SELECT_W }} className="texto-suave">
                    <strong>{municipioAtivoNome || "—"}</strong>
                  </div>
                </>
              ) : (
                <>
                  <span className="texto-suave" style={{ margin: 0 }}>
                    Município:
                  </span>
                  <select
                    className="input"
                    style={{ width: SELECT_W }}
                    value={municipioAtivoId ?? ""}
                    onChange={(e) =>
                      setMunicipioAtivoId(
                        e.target.value ? Number(e.target.value) : null
                      )
                    }
                  >
                    <option value="">Selecione...</option>
                    {(municipios || []).map((m) => (
                      <option
                        key={m.id ?? m.value ?? m.nome ?? String(m)}
                        value={m.id ?? m.value ?? ""}
                      >
                        {m.nome || m.nome_municipio || m.label || String(m)}
                      </option>
                    ))}
                  </select>
                </>
              )}

              {onSair ? (
                <button
                  type="button"
                  className="btn btn-secundario btn-secundario-mini btn-logout"
                  onClick={onSair}
                >
                  Sair
                </button>
              ) : (
                <span />
              )}
            </div>

            {/* LINHA 2 (CRAS/CREAS): Unidade + Select + Portal (SEM Sair) */}
            {unidadeLabel ? (
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "auto auto auto",
                  alignItems: "center",
                  columnGap: 10,
                  justifyContent: "end",
                }}
              >
                <span className="texto-suave" style={{ margin: 0 }}>
                  {unidadeLabel}
                </span>

                {((unidades || []).length <= 1) ? (
                  <div style={{ width: SELECT_W }} className="texto-suave">
                    <strong>{(unidades && unidades[0]) ? (unidades[0].nome || unidades[0].nome_unidade || unidades[0].label || String(unidades[0])) : "—"}</strong>
                  </div>
                ) : (
                <select
                  className="input"
                  style={{ width: SELECT_W }}
                  value={unidadeAtivaId ?? ""}
                  onChange={(e) =>
                    setUnidadeAtivaId(
                      e.target.value ? Number(e.target.value) : null
                    )
                  }
                >
                  <option value="">Selecione...</option>
                  {(unidades || []).map((u) => (
                    <option
                      key={u.id ?? u.value ?? u.nome ?? String(u)}
                      value={u.id ?? u.value ?? ""}
                    >
                      {u.nome || u.nome_unidade || u.label || String(u)}
                    </option>
                  ))}
                </select>
                )}

                {onPortal ? (
                  <button
                    type="button"
                    className="btn btn-secundario btn-secundario-mini"
                    onClick={onPortal}
                  >
                    Portal
                  </button>
                ) : (
                  <span />
                )}
              </div>
            ) : null}
          </div>
        </div>

        <nav className="app-tabs">
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
        </nav>
      </div>
    </header>
  );
}