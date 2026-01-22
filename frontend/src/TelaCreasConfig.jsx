import React, { useEffect, useState } from "react";
import { clearCreasCases, seedCreasDemoCases, setCreasSeedMode, setCreasSelectedCaseId, getCreasWorkflow, saveCreasWorkflow, resetCreasWorkflow } from "./domain/creasStore.js";

export default function TelaCreasConfig() {
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState("");

  const [wfText, setWfText] = useState("");
  const [wfOpen, setWfOpen] = useState(false);

  const [confirmOpen, setConfirmOpen] = useState(false);
  const [confirmTitle, setConfirmTitle] = useState("");
  const [confirmText, setConfirmText] = useState("");
  const [onConfirm, setOnConfirm] = useState(null);

  useEffect(() => {
    try {
      const wf = getCreasWorkflow();
      setWfText(JSON.stringify(wf, null, 2));
    } catch {
      setWfText("{");
    }
  }, []);

  function flash(m) {
    setMsg(m || "");
    if (!m) return;
    setTimeout(() => setMsg(""), 2600);
  }

  function openConfirm({ title, text, onOk }) {
    setConfirmTitle(title || "Confirmar");
    setConfirmText(text || "");
    setOnConfirm(() => onOk || null);
    setConfirmOpen(true);
  }

  function criarDemo() {
    if (busy) return;
    openConfirm({
      title: "Criar casos de demonstração",
      text: "DEMO: isso vai substituir todos os casos do CREAS nesta máquina (somente testes).\n\nDeseja criar 20 casos de demonstração?",
      onOk: () => {
        setBusy(true);
        try {
          setCreasSeedMode("demo");
          const demo = seedCreasDemoCases({ count: 20, overwrite: true });
          if (demo?.[0]?.id != null) setCreasSelectedCaseId(String(demo[0].id));
          flash("Pronto ✅ 20 casos de demonstração foram criados. Vá em 'Casos' e teste o fluxo.");
        } finally {
          setBusy(false);
        }
      },
    });
  }

  function limparTudo() {
    if (busy) return;
    openConfirm({
      title: "Limpar CREAS",
      text: "ATENÇÃO: isso apaga TODOS os casos do CREAS nesta máquina.\n\nDeseja deixar o CREAS vazio para começar do zero?",
      onOk: () => {
        setBusy(true);
        try {
          clearCreasCases({ disableAutoSeed: true });
          flash("Pronto ✅ CREAS limpo. Agora você pode criar casos reais em 'Novo caso'.");
          window.location.reload();
        } finally {
          setBusy(false);
        }
      },
    });
  }


  function carregarWorkflowAtual() {
    try {
      const wf = getCreasWorkflow();
      setWfText(JSON.stringify(wf, null, 2));
      flash("Workflow carregado ✅");
    } catch {
      flash("Não foi possível carregar o workflow.");
    }
  }

  function salvarWorkflow() {
    if (busy) return;
    setBusy(true);
    try {
      const parsed = JSON.parse(wfText || "{}");
      const saved = saveCreasWorkflow(parsed);
      if (!saved || !Array.isArray(saved.etapas) || saved.etapas.length === 0) {
        flash("Workflow inválido: informe uma lista de etapas (etapas[].codigo).");
        return;
      }
      flash("Workflow salvo ✅ (vale para este Município/Unidade)");
    } catch (e) {
      flash("JSON inválido. Verifique vírgulas, aspas e colchetes.");
    } finally {
      setBusy(false);
    }
  }

  function restaurarWorkflowPadrao() {
    if (busy) return;
    openConfirm({
      title: "Restaurar workflow padrão",
      text: "Isso remove o workflow personalizado deste Município/Unidade e volta ao padrão do sistema.\n\nDeseja continuar?",
      onOk: () => {
        setBusy(true);
        try {
          resetCreasWorkflow();
          carregarWorkflowAtual();
          flash("Workflow restaurado ✅");
        } finally {
          setBusy(false);
        }
      },
    });
  }
  return (
    <div className="layout-1col">
      <div className="card">
        <div style={{ fontWeight: 950, fontSize: 18 }}>Configurações (CREAS)</div>
        <div className="texto-suave" style={{ marginTop: 6 }}>
          Aqui entram as listas padronizadas (motivos, encerramento, pausa) e SLAs do município.
        </div>

        {msg ? (
          <div
            className="card"
            style={{
              marginTop: 10,
              padding: 10,
              boxShadow: "none",
              border: "1px solid rgba(59,130,246,.25)",
              background: "rgba(59,130,246,.08)",
            }}
            role="alert"
          >
            <b>{msg}</b>
          </div>
        ) : null}

        <div style={{ marginTop: 14, display: "grid", gap: 10 }}>
          <button className="btn btn-secundario" type="button" onClick={() => setWfOpen((v) => !v)}>
            Workflow do CREAS (por Município/Unidade) {wfOpen ? "▲" : "▼"}
          </button>

          {wfOpen ? (
            <div className="card" style={{ boxShadow: "none", border: "1px solid rgba(2,6,23,.08)" }}>
              <div className="texto-suave" style={{ marginBottom: 8 }}>
                Dica: você pode editar o JSON abaixo para adaptar etapas, nomes e SLAs (sla_dias) por município/unidade.
              </div>

              <textarea
                className="input"
                style={{ minHeight: 240, fontFamily: "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace" }}
                value={wfText}
                onChange={(e) => setWfText(e.target.value)}
                spellCheck={false}
              />

              <div style={{ marginTop: 10, display: "flex", gap: 10, flexWrap: "wrap" }}>
                <button className="btn btn-primario" type="button" disabled={busy} onClick={salvarWorkflow}>
                  Salvar workflow
                </button>
                <button className="btn btn-secundario" type="button" disabled={busy} onClick={carregarWorkflowAtual}>
                  Recarregar
                </button>
                <button className="btn btn-secundario" type="button" disabled={busy} onClick={restaurarWorkflowPadrao}>
                  Restaurar padrão
                </button>
              </div>
            </div>
          ) : null}

          <button className="btn btn-secundario" type="button" onClick={() => flash("Em breve: listas padronizadas (motivos/encerramento/pausa).")}>
            Listas padronizadas
          </button>
        </div>
      </div>

      <div className="card">
        <div style={{ fontWeight: 950 }}>Ferramentas (admin / demo)</div>
        <div className="texto-suave" style={{ marginTop: 6 }}>
          Use apenas para testes e demonstrações.
        </div>

        <div style={{ marginTop: 12, display: "flex", gap: 10, flexWrap: "wrap" }}>
          <button className="btn btn-primario" type="button" disabled={busy} onClick={criarDemo}>
            Criar 20 casos DEMO
          </button>
          <button className="btn btn-secundario" type="button" disabled={busy} onClick={limparTudo}>
            Limpar CREAS
          </button>
        </div>
      </div>

      {confirmOpen ? (
        <div className="modal" role="dialog" aria-modal="true">
          <div className="modal-card">
            <div className="modal-header">
              <div className="modal-title">{confirmTitle}</div>
              <button className="btn btn-secundario" type="button" onClick={() => setConfirmOpen(false)}>
                Fechar
              </button>
            </div>
            <div className="modal-body">
              <div style={{ whiteSpace: "pre-wrap" }}>{confirmText}</div>
            </div>
            <div className="modal-footer" style={{ display: "flex", justifyContent: "flex-end", gap: 10 }}>
              <button className="btn btn-secundario" type="button" onClick={() => setConfirmOpen(false)}>
                Cancelar
              </button>
              <button
                className="btn btn-primario"
                type="button"
                onClick={() => {
                  const fn = onConfirm;
                  setConfirmOpen(false);
                  if (typeof fn === "function") fn();
                }}
              >
                Confirmar
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
