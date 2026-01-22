import React, { useEffect, useMemo, useState } from "react";

function buildChecklist() {
  return [
    {
      id: "planejamento",
      title: "Planejamento e formalização (MROSC)",
      items: [
        { id: "plano_trabalho", label: "Plano de trabalho com metas, indicadores, público-alvo e cronograma" },
        { id: "orcamento", label: "Orçamento detalhado e memória de cálculo (metas precificadas)" },
        { id: "chamamento", label: "Chamamento público/justificativa de dispensa ou inexigibilidade (quando aplicável)" },
        { id: "termo", label: "Termo de colaboração/fomento ou instrumento equivalente assinado e publicado" },
        { id: "certidoes", label: "Certidões e regularidade da OSC (conforme regras locais)" },
      ],
    },
    {
      id: "execucao",
      title: "Execução e monitoramento",
      items: [
        { id: "designacao", label: "Designação de gestor/fiscal da parceria e rotina de acompanhamento" },
        { id: "registros", label: "Registros de execução do objeto (relatórios, listas, fotos, evidências)" },
        { id: "visitas", label: "Visitas técnicas e relatórios de monitoramento (quando aplicável)" },
        { id: "aditivos", label: "Aditivos, apostilamentos e termos de ajuste registrados" },
        { id: "publicidade", label: "Transparência: publicação de repasses, termos e resultados" },
      ],
    },
    {
      id: "financeiro",
      title: "Execução financeira (evidências)",
      items: [
        { id: "conta", label: "Conta bancária específica da parceria, extratos e conciliações" },
        { id: "nf", label: "Notas fiscais/documentos equivalentes vinculados às metas e ao plano de trabalho" },
        { id: "pagamentos", label: "Comprovantes de pagamento e rastreabilidade (PIX/TED/cheque)" },
        { id: "folha", label: "Folha/recibos/encargos quando houver equipe custeada pela parceria" },
        { id: "saldo", label: "Controle de saldos, rendimentos e devoluções, quando houver" },
      ],
    },
    {
      id: "prestacao",
      title: "Prestação de contas e controle",
      items: [
        { id: "rel_objeto", label: "Relatório de execução do objeto (entregas x metas, evidências)" },
        { id: "rel_fin", label: "Relatório de execução financeira (previsto x realizado, demonstrativos)" },
        { id: "parecer", label: "Parecer do gestor/fiscal + manifestação do controle interno" },
        { id: "arquivamento", label: "Arquivamento organizado (pastas digitais) e trilha de auditoria" },
      ],
    },
  ];
}

function pct(done, total) {
  if (!total) return 0;
  return Math.round((done / total) * 100);
}

export default function TelaTerceiroSetorPrestacao({ municipioId }) {
  const key = useMemo(() => `terceiro_setor_checklist_${municipioId || "all"}`, [municipioId]);
  const checklist = useMemo(() => buildChecklist(), []);

  const allIds = useMemo(() => {
    const ids = [];
    for (const s of checklist) for (const it of s.items) ids.push(`${s.id}:${it.id}`);
    return ids;
  }, [checklist]);

  const [state, setState] = useState(() => {
    try {
      const raw = localStorage.getItem(key);
      const j = raw ? JSON.parse(raw) : null;
      if (j && typeof j === "object") return j;
    } catch {}
    return {};
  });

  useEffect(() => {
    try { localStorage.setItem(key, JSON.stringify(state || {})); } catch {}
  }, [key, state]);

  const total = allIds.length;
  const done = allIds.filter((id) => Boolean(state[id])).length;
  const progresso = pct(done, total);

  function toggle(id) {
    setState((prev) => ({ ...(prev || {}), [id]: !prev?.[id] }));
  }

  function marcarTudo(v) {
    const next = {};
    for (const id of allIds) next[id] = Boolean(v);
    setState(next);
  }

  return (
    <div className="layout-1col">
      <div className="card card-wide">
        <div className="card-header-row">
          <div>
            <h2 style={{ margin: 0 }}>Prestação de contas</h2>
            <div className="card-subtitle">
              Checklist prático (baseado em MROSC – Lei 13.019/2014 e rotinas típicas do controle externo). Ajustamos os itens finos assim que você anexar a IN do TCE.
            </div>
          </div>

          <div style={{ display: "flex", gap: 10, alignItems: "center", flexWrap: "wrap" }}>
            <div className="texto-suave" style={{ margin: 0 }}>
              Progresso: <b>{progresso}%</b> ({done}/{total})
            </div>
            <button className="btn btn-secundario" type="button" onClick={() => marcarTudo(false)}>
              Zerar
            </button>
            <button className="btn btn-secundario" type="button" onClick={() => marcarTudo(true)}>
              Marcar tudo
            </button>
          </div>
        </div>

        <div className="layout-2col" style={{ marginTop: 10 }}>
          <div className="card" style={{ padding: 14 }}>
            <div style={{ fontWeight: 900 }}>Dica de uso</div>
            <div className="texto-suave" style={{ marginTop: 6 }}>
              A ideia é marcar <b>apenas quando</b> o documento/evidência estiver anexado e identificado.
              Depois vamos ligar cada item a um campo de upload e um registro de auditoria.
            </div>
          </div>

          <div className="card" style={{ padding: 14 }}>
            <div style={{ fontWeight: 900 }}>Padrão de evidência</div>
            <div className="texto-suave" style={{ marginTop: 6 }}>
              Nomeie arquivos com padrão: <b>ANO_MÊS · OSC · Parceria · Item</b>.
              Ex.: <i>2026-01 · Casa Viver · TC-003/2026 · Extratos.pdf</i>
            </div>
          </div>
        </div>

        <div style={{ marginTop: 12, display: "grid", gap: 12 }}>
          {checklist.map((sec) => {
            const secIds = sec.items.map((it) => `${sec.id}:${it.id}`);
            const secDone = secIds.filter((id) => state[id]).length;
            const secPct = pct(secDone, secIds.length);

            return (
              <div key={sec.id} className="card" style={{ padding: 14 }}>
                <div className="card-header-row" style={{ marginBottom: 8 }}>
                  <div>
                    <div style={{ fontWeight: 900 }}>{sec.title}</div>
                    <div className="texto-suave">{secPct}% concluído ({secDone}/{secIds.length})</div>
                  </div>
                </div>

                <div style={{ display: "grid", gap: 8 }}>
                  {sec.items.map((it) => {
                    const id = `${sec.id}:${it.id}`;
                    const checked = Boolean(state[id]);
                    return (
                      <label key={id} style={{ display: "flex", gap: 10, alignItems: "flex-start", cursor: "pointer" }}>
                        <input type="checkbox" checked={checked} onChange={() => toggle(id)} style={{ marginTop: 3 }} />
                        <span style={{ lineHeight: 1.25 }}>
                          <span style={{ fontWeight: 700 }}>{it.label}</span>
                        </span>
                      </label>
                    );
                  })}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
