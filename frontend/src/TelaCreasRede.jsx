import React, { useEffect, useMemo, useState } from "react";
import {
  getCreasCases,
  seedCreasIfEmpty,
  registrarRetornoRede,
  addTimeline,
  createCreasCaseFromSuasEncaminhamento,
  setCreasSelectedCaseId,
} from "./domain/creasStore.js";
import { scopeCases } from "./domain/acl.js";
import EncaminhamentosSuas from "./components/EncaminhamentosSuas.jsx";

export default function TelaCreasRede({ usuarioLogado, onNavigate }) {
  const [cases, setCases] = useState(() => seedCreasIfEmpty());
  const [msg, setMsg] = useState("");
  const [retOpen, setRetOpen] = useState(false);
  const [retItem, setRetItem] = useState(null);
  const [retTxt, setRetTxt] = useState("Retorno recebido.");

  function flash(m) {
    setMsg(m || "");
    if (!m) return;
    setTimeout(() => setMsg(""), 2600);
  }

  useEffect(() => {
    const onStorage = () => setCases(getCreasCases());
    window.addEventListener("storage", onStorage);
    return () => window.removeEventListener("storage", onStorage);
  }, []);

  const scopedCases = useMemo(() => scopeCases(cases, usuarioLogado), [cases, usuarioLogado]);

  const itens = useMemo(() => {
    const out = [];
    for (const c of scopedCases || []) {
      if (c.status !== "ativo") continue;
      for (const e of c.encaminhamentos || []) {
        out.push({ caso: c, enc: e });
      }
    }
    return out;
  }, [scopedCases]);

  const pendentes = itens.filter((x) => x.enc?.status === "aguardando");

  function registrar(x) {
    setRetItem(x);
    setRetTxt("Retorno recebido.");
    setRetOpen(true);
  }

  return (
    <>
      <div className="layout-1col">
      <EncaminhamentosSuas
        modulo="CREAS"
        usuarioLogado={usuarioLogado}
        allowCreate={false}
        onAcceptCreateCaso={(item) => createCreasCaseFromSuasEncaminhamento(item, usuarioLogado)}
        onOpenDestinoCaso={(item) => {
          if (!item?.destino_caso_id) return;
          try {
            setCreasSelectedCaseId(String(item.destino_caso_id));
          } catch {}
          onNavigate?.({ tab: "casos" });
        }}
        title="Encaminhamentos SUAS"
        subtitle="CRAS ⇄ CREAS ⇄ PopRua, com recebimento e contrarreferência."
      />
      <div className="card">
        <div className="card-header-row">
          <div>
            <div style={{ fontWeight: 950, fontSize: 18 }}>Rede (CREAS)</div>
            <div className="texto-suave">Encaminhamentos e retornos. Clique em "Registrar retorno".</div>
          </div>
          <button className="btn btn-secundario" type="button" onClick={() => onNavigate?.({ tab: "casos" })}>
            Abrir casos
          </button>
        </div>

        {pendentes.length ? (
          <div style={{ display: "grid", gap: 10 }}>
            {pendentes.map((x) => (
              <div
                key={x.enc.id}
                className="card"
                style={{ padding: 12, boxShadow: "none", border: "1px solid rgba(2,6,23,.06)" }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", gap: 10, alignItems: "flex-start" }}>
                  <div>
                    <div style={{ fontWeight: 950 }}>{x.enc.destino}</div>
                    <div className="texto-suave">
                      Caso: <b>{x.caso.nome}</b> · Prazo: <b>{x.enc.prazo_retorno || "—"}</b>
                    </div>
                    <div style={{ marginTop: 6 }}>{x.enc.motivo}</div>
                  </div>
                  <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
                    <button
                      className="btn btn-secundario"
                      type="button"
                      onClick={() => {
                        try {
                          setCreasSelectedCaseId(String(x.caso.id));
                        } catch {}
                        onNavigate?.({ tab: "casos" });
                      }}
                    >
                      Abrir caso
                    </button>
                    <button className="btn btn-primario" type="button" onClick={() => registrar(x)}>
                      Registrar retorno
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="texto-suave">Nenhum encaminhamento pendente.</div>
        )}
      </div>
    </div>

    {retOpen ? (
      <div className="modal-backdrop" role="dialog" aria-modal="true">
        <div className="modal-card">
          <div className="modal-header">
            <div className="modal-title">Registrar retorno da rede</div>
            <button className="btn btn-secundario" type="button" onClick={() => setRetOpen(false)}>
              Fechar
            </button>
          </div>
          <div className="modal-body">
            <label className="label">Texto do retorno (curto)</label>
            <textarea className="input" style={{ minHeight: 120 }} value={retTxt} onChange={(e) => setRetTxt(e.target.value)} />
          </div>
          <div className="modal-footer" style={{ display: "flex", justifyContent: "flex-end", gap: 10 }}>
            <button className="btn btn-secundario" type="button" onClick={() => setRetOpen(false)}>
              Cancelar
            </button>
            <button
              className="btn btn-primario"
              type="button"
              onClick={() => {
                if (!retItem) return;
                const txt = String(retTxt || "").trim();
                if (!txt) return flash("Informe um texto curto.");
                registrarRetornoRede(retItem.caso.id, retItem.enc.id, txt);
                addTimeline(retItem.caso.id, {
                  tipo: "retorno",
                  texto: `Retorno da rede (${retItem.enc.destino}): ${txt}`,
                  por: usuarioLogado?.nome || "—",
                });
                setCases(getCreasCases());
                setRetOpen(false);
                flash("Retorno registrado ✅ Pendência resolvida.");
              }}
            >
              Registrar
            </button>
          </div>
        </div>
      </div>
    ) : null}
    </>
  );
}