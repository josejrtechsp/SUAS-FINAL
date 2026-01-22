import React, { useEffect, useMemo, useState } from "react";
import { getCreasCases, seedCreasIfEmpty } from "./domain/creasStore.js";
import { scopeCases } from "./domain/acl.js";

export default function TelaCreasRelatorios({ usuarioLogado }) {
  const [cases, setCases] = useState(() => seedCreasIfEmpty());

  useEffect(() => {
    const onStorage = () => setCases(getCreasCases());
    window.addEventListener("storage", onStorage);
    return () => window.removeEventListener("storage", onStorage);
  }, []);

  const scopedCases = useMemo(() => scopeCases(cases, usuarioLogado), [cases, usuarioLogado]);

  const resumo = useMemo(() => {
    const ativos = (scopedCases || []).filter((c) => c.status === "ativo");
    const encerrados = (scopedCases || []).filter((c) => c.status === "encerrado");
    const porTema = {};
    for (const c of ativos) {
      const k = c.motivo_tema || "Outro";
      porTema[k] = (porTema[k] || 0) + 1;
    }
    return { ativos: ativos.length, encerrados: encerrados.length, porTema };
  }, [scopedCases]);

  return (
    <div className="layout-1col">
      <div className="card">
        <div style={{ fontWeight: 950, fontSize: 18 }}>Relatórios (CREAS)</div>
        <div className="texto-suave" style={{ marginTop: 6 }}>
          MVP local: números básicos para validação do módulo. Depois, trocamos por consultas no backend.
        </div>

        <div style={{ marginTop: 14, display: "grid", gridTemplateColumns: "repeat(2, minmax(0,1fr))", gap: 12 }}>
          <div className="card" style={{ padding: 14, boxShadow: "none", border: "1px solid rgba(2,6,23,.06)" }}>
            <div className="texto-suave">Casos ativos</div>
            <div style={{ fontWeight: 950, fontSize: 28 }}>{resumo.ativos}</div>
          </div>
          <div className="card" style={{ padding: 14, boxShadow: "none", border: "1px solid rgba(2,6,23,.06)" }}>
            <div className="texto-suave">Casos encerrados</div>
            <div style={{ fontWeight: 950, fontSize: 28 }}>{resumo.encerrados}</div>
          </div>
        </div>

        <div style={{ marginTop: 14 }}>
          <div style={{ fontWeight: 950 }}>Ativos por tema</div>
          <div className="texto-suave" style={{ marginTop: 6 }}>Ajuda a enxergar demanda do município.</div>
          <div style={{ marginTop: 10, display: "grid", gap: 8 }}>
            {Object.keys(resumo.porTema).length ? (
              Object.entries(resumo.porTema).map(([k, v]) => (
                <div key={k} className="card" style={{ padding: 12, boxShadow: "none", border: "1px solid rgba(2,6,23,.06)" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", gap: 10 }}>
                    <div style={{ fontWeight: 900 }}>{k}</div>
                    <div style={{ fontWeight: 950 }}>{v}</div>
                  </div>
                </div>
              ))
            ) : (
              <div className="texto-suave">Sem dados.</div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
