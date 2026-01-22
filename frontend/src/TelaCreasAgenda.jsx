import React, { useEffect, useMemo, useState } from "react";
import { getCreasCases, seedCreasIfEmpty,
  setCreasSelectedCaseId } from "./domain/creasStore.js";
import { scopeCases } from "./domain/acl.js";

function fmt(iso) {
  if (!iso) return "—";
  try {
    return new Date(iso).toLocaleString("pt-BR");
  } catch {
    return iso;
  }
}

export default function TelaCreasAgenda({ usuarioLogado, onNavigate }) {
  const [cases, setCases] = useState(() => seedCreasIfEmpty());

  useEffect(() => {
    const onStorage = () => setCases(getCreasCases());
    window.addEventListener("storage", onStorage);
    return () => window.removeEventListener("storage", onStorage);
  }, []);

  const scopedCases = useMemo(() => scopeCases(cases, usuarioLogado), [cases, usuarioLogado]);

  const lista = useMemo(() => {
    return (scopedCases || [])
      .filter((c) => c.status === "ativo" && c.proximo_passo_em)
      .sort((a, b) => new Date(a.proximo_passo_em) - new Date(b.proximo_passo_em));
  }, [scopedCases]);

  return (
    <div className="layout-1col">
      <div className="card">
        <div className="card-header-row">
          <div>
            <div style={{ fontWeight: 950, fontSize: 18 }}>Agenda (CREAS)</div>
            <div className="texto-suave">Próximos passos por data. Clique para abrir o caso.</div>
          </div>
        </div>

        {lista.length ? (
          <div style={{ display: "grid", gap: 10 }}>
            {lista.slice(0, 200).map((c) => {
              const semResp = !c?.responsavel_id;
              const resp = c?.responsavel_nome || null;

              return (
                <button
                  key={c.id}
                  type="button"
                  className="btn"
                  style={{ display: "flex", justifyContent: "space-between", textAlign: "left" }}
                  onClick={() => {
                    try {
                      setCreasSelectedCaseId(String(c.id));
                    } catch {}
                    onNavigate?.({ tab: "casos" });
                  }}
                >
                  <div>
                    <div style={{ fontWeight: 950 }}>{c.nome}</div>
                    <div className="texto-suave">
                      {c.proximo_passo || "—"} · {fmt(c.proximo_passo_em)}
                      {semResp ? " · Sem responsável" : resp ? ` · Resp.: ${resp}` : ""}
                    </div>
                  </div>
                  <div style={{ fontWeight: 900, opacity: 0.75 }}>Abrir →</div>
                </button>
              );
            })}
          </div>
        ) : (
          <div className="texto-suave">Sem itens na agenda.</div>
        )}
      </div>
    </div>
  );
}
