import { useEffect, useMemo, useState } from "react";
import TelaCrasFichaPessoa360 from "./TelaCrasFichaPessoa360.jsx";
import TelaCrasFichaFamilia360 from "./TelaCrasFichaFamilia360.jsx";

/**
 * TelaCrasFicha (UI v2)
 * - Subtelas no header (CrasPageHeader): Resumo | Documentos | Histórico | Impressão/PDF
 * - Aqui mantemos apenas o "alvo" (Pessoa/Família) e o conteúdo de 1 subtela por vez.
 */

function esc(v) {
  const s = v == null ? "" : String(v);
  if (s.includes('"') || s.includes(",") || s.includes("\n")) return `"${s.replace(/"/g, '""')}"`;
  return s;
}

function dlCSV(filename, csvText) {
  const blob = new Blob([csvText], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

function exportPessoaPDFSimple(data, periodoStr) {
  const pessoa = data?.pessoa || {};
  const pend = data?.pendencias || [];
  const tl = data?.timeline || [];
  const htmlPend = pend.map((p) => `<tr><td>${esc(p.tipo)}</td><td>${esc(p.gravidade)}</td><td>${esc(p.detalhe)}</td></tr>`).join("");
  const htmlTl = tl.slice(0, 120).map((e) => `<tr><td>${esc(e.quando)}</td><td>${esc(e.titulo)}</td><td>${esc(e.detalhe)}</td></tr>`).join("");

  const html = `
  <html><head><meta charset="utf-8"/>
  <title>Ficha do Usuário</title>
  <style>
    body{font-family:system-ui,-apple-system,Segoe UI,Roboto,Arial;padding:24px}
    h1{margin:0 0 6px 0}
    .muted{color:#555;margin:0 0 14px 0}
    table{border-collapse:collapse;width:100%}
    th,td{border-bottom:1px solid #e5e7eb;padding:8px;text-align:left;vertical-align:top}
    th{background:#f8fafc}
  </style>
  </head><body>
    <h1>Ficha do Usuário</h1>
    <p class="muted">Período: ${esc(periodoStr)} · Nome: ${esc(pessoa.nome)} · CPF: ${esc(pessoa.cpf)} · NIS: ${esc(pessoa.nis)}</p>
    <h2>Pendências</h2>
    <table><thead><tr><th>Tipo</th><th>Gravidade</th><th>Detalhe</th></tr></thead><tbody>${htmlPend}</tbody></table>
    <h2 style="margin-top:18px;">Histórico (Timeline)</h2>
    <table><thead><tr><th>Quando</th><th>Evento</th><th>Obs</th></tr></thead><tbody>${htmlTl}</tbody></table>
  </body></html>`;
  const w = window.open("", "_blank");
  if (!w) return alert("Pop-up bloqueado. Permita pop-ups para exportar PDF.");
  w.document.open();
  w.document.write(html);
  w.document.close();
  setTimeout(() => { w.focus(); w.print(); }, 400);
}

function exportFamiliaPDFSimple(data, periodoStr) {
  const fam = data?.familia || {};
  const pend = data?.pendencias || [];
  const tl = data?.timeline || [];
  const membros = data?.membros || [];

  const htmlM = membros.map((m) => `<tr><td>${esc(m.pessoa?.nome || "")}</td><td>${esc(m.pessoa?.cpf || "")}</td><td>${esc(m.pessoa?.nis || "")}</td></tr>`).join("");
  const htmlPend = pend.map((p) => `<tr><td>${esc(p.tipo)}</td><td>${esc(p.gravidade)}</td><td>${esc(p.detalhe)}</td></tr>`).join("");
  const htmlTl = tl.slice(0, 120).map((e) => `<tr><td>${esc(e.quando)}</td><td>${esc(e.titulo)}</td><td>${esc(e.detalhe)}</td></tr>`).join("");

  const html = `
  <html><head><meta charset="utf-8"/>
  <title>Ficha da Família</title>
  <style>
    body{font-family:system-ui,-apple-system,Segoe UI,Roboto,Arial;padding:24px}
    h1{margin:0 0 6px 0}
    .muted{color:#555;margin:0 0 14px 0}
    table{border-collapse:collapse;width:100%}
    th,td{border-bottom:1px solid #e5e7eb;padding:8px;text-align:left;vertical-align:top}
    th{background:#f8fafc}
  </style>
  </head><body>
    <h1>Ficha da Família</h1>
    <p class="muted">Período: ${esc(periodoStr)} · Família: ${esc(fam.id)} · Endereço: ${esc(fam.endereco || "")}</p>

    <h2>Membros</h2>
    <table><thead><tr><th>Nome</th><th>CPF</th><th>NIS</th></tr></thead><tbody>${htmlM}</tbody></table>

    <h2 style="margin-top:18px;">Pendências</h2>
    <table><thead><tr><th>Tipo</th><th>Gravidade</th><th>Detalhe</th></tr></thead><tbody>${htmlPend}</tbody></table>

    <h2 style="margin-top:18px;">Histórico (Timeline)</h2>
    <table><thead><tr><th>Quando</th><th>Evento</th><th>Obs</th></tr></thead><tbody>${htmlTl}</tbody></table>
  </body></html>`;
  const w = window.open("", "_blank");
  if (!w) return alert("Pop-up bloqueado. Permita pop-ups para exportar PDF.");
  w.document.open();
  w.document.write(html);
  w.document.close();
  setTimeout(() => { w.focus(); w.print(); }, 400);
}

export default function TelaCrasFicha({
  apiBase,
  apiFetch,
  onNavigate,
  view = "resumo", // "resumo" | "documentos" | "historico" | "impressao"
}) {
  const [modo, setModo] = useState(() => (localStorage.getItem("cras_ficha_modo") || "pessoa"));

  const [pessoaIdAtiva, setPessoaIdAtiva] = useState(() => {
    const v = localStorage.getItem("cras_ficha_pessoa_id");
    return v ? Number(v) : null;
  });

  const [familiaIdAtiva, setFamiliaIdAtiva] = useState(() => {
    const v = localStorage.getItem("cras_ficha_familia_id");
    return v ? Number(v) : null;
  });

  // contexto: de qual família eu vim quando abro a pessoa
  const [familiaContextoId, setFamiliaContextoId] = useState(() => {
    const v = localStorage.getItem("cras_ficha_last_familia_id");
    return v ? Number(v) : null;
  });

  useEffect(() => {
    try { localStorage.setItem("cras_ficha_modo", modo); } catch {}
  }, [modo]);

  // -------- Impressão / export --------
  const periodoDefault = useMemo(() => {
    const d = new Date();
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`;
  }, []);
  const [periodoStr, setPeriodoStr] = useState(periodoDefault);
  const [expErro, setExpErro] = useState("");
  const [expLoading, setExpLoading] = useState(false);
  const [expData, setExpData] = useState(null);

  const forcedTab = useMemo(() => {
    if (view === "historico") return "timeline";
    if (view === "documentos") return "documentos";
    return "resumo";
  }, [view]);

  function backToFamilia() {
    const fid = familiaContextoId || familiaIdAtiva;
    if (!fid) return;
    try { localStorage.setItem("cras_ficha_familia_id", String(fid)); } catch {}
    setFamiliaIdAtiva(Number(fid));
    setModo("familia");
  }

  async function loadExport() {
    setExpErro("");
    setExpLoading(true);
    setExpData(null);
    try {
      const [anoS, mesS] = String(periodoStr || "").split("-");
      const ano = Number(anoS || 0);
      const mes = Number(mesS || 0);
      if (!ano || !mes) throw new Error("Período inválido.");

      const qs = new URLSearchParams();
      qs.set("ano", String(ano));
      qs.set("mes", String(mes));
      qs.set("limite_faltas_seguidas", "3");
      qs.set("presenca_minima", "75");

      if (modo === "pessoa") {
        if (!pessoaIdAtiva) throw new Error("Selecione uma pessoa.");
        const r = await apiFetch(`${apiBase}/cras/ficha/pessoas/${Number(pessoaIdAtiva)}?${qs.toString()}`);
        if (!r.ok) throw new Error(await r.text());
        setExpData(await r.json());
      } else {
        if (!familiaIdAtiva) throw new Error("Selecione uma família.");
        const r = await apiFetch(`${apiBase}/cras/ficha/familias/${Number(familiaIdAtiva)}?${qs.toString()}`);
        if (!r.ok) throw new Error(await r.text());
        setExpData(await r.json());
      }
    } catch (e) {
      setExpErro(e?.message || "Erro ao carregar dados.");
    } finally {
      setExpLoading(false);
    }
  }

  useEffect(() => {
    if (view !== "impressao") return;
    // carrega automaticamente quando entra em Impressão/PDF (sem atrapalhar as outras)
    loadExport();
    // eslint-disable-next-line
  }, [view]);

  // -------- UI --------
  return (
    <div className="layout-1col">
      {/* seletor de alvo (pessoa/família) — simples e constante */}
      <div className="card" style={{ padding: 12, borderRadius: 18 }}>
        <div style={{ display: "flex", gap: 10, flexWrap: "wrap", alignItems: "center" }}>
          <div style={{ fontWeight: 900 }}>Alvo da ficha</div>

          <button
            className={"btn btn-secundario btn-secundario-mini" + (modo === "pessoa" ? " btn-primario" : "")}
            type="button"
            onClick={() => setModo("pessoa")}
          >
            Pessoa
          </button>

          <button
            className={"btn btn-secundario btn-secundario-mini" + (modo === "familia" ? " btn-primario" : "")}
            type="button"
            onClick={() => setModo("familia")}
          >
            Família
          </button>

          {modo === "pessoa" && (familiaContextoId || familiaIdAtiva) ? (
            <button className="btn btn-secundario btn-secundario-mini" type="button" onClick={backToFamilia}>
              Voltar para Família #{familiaContextoId || familiaIdAtiva}
            </button>
          ) : null}

          <div style={{ flex: 1 }} />

          <button className="btn btn-secundario btn-secundario-mini" type="button" onClick={() => onNavigate?.("casos")}>
            Abrir Casos
          </button>
          <button className="btn btn-secundario btn-secundario-mini" type="button" onClick={() => onNavigate?.("cadunico")}>
            Abrir CadÚnico
          </button>
        </div>
      </div>

      {/* Conteúdo: 1 subtela por vez */}
      {view !== "impressao" ? (
        modo === "pessoa" ? (
          <TelaCrasFichaPessoa360
            apiBase={apiBase}
            apiFetch={apiFetch}
            pessoaId={pessoaIdAtiva}
            onNavigate={onNavigate}
            onBackFamilia={backToFamilia}
            familiaContextoId={familiaContextoId || familiaIdAtiva || null}
            forcedTab={forcedTab}
            hideTabBar={true}
          />
        ) : (
          <TelaCrasFichaFamilia360
            apiBase={apiBase}
            apiFetch={apiFetch}
            familiaId={familiaIdAtiva}
            onOpenPessoa={(pid) => {
              if (!pid) return;
              try { localStorage.setItem("cras_ficha_pessoa_id", String(pid)); } catch {}
              setPessoaIdAtiva(Number(pid));
              // guarda contexto para voltar
              if (familiaIdAtiva) {
                try { localStorage.setItem("cras_ficha_last_familia_id", String(familiaIdAtiva)); } catch {}
                setFamiliaContextoId(Number(familiaIdAtiva));
              }
              setModo("pessoa");
            }}
            forcedTab={forcedTab}
            hideTabBar={true}
          />
        )
      ) : (
        <div className="card" style={{ padding: 14, borderRadius: 18 }}>
          <div style={{ display: "flex", justifyContent: "space-between", gap: 10, flexWrap: "wrap", alignItems: "center" }}>
            <div>
              <div style={{ fontWeight: 900 }}>Impressão / PDF</div>
              <div className="texto-suave">Gere evidência do período (PDF/CSV). Selecione o mês e atualize.</div>
            </div>

            <div style={{ display: "flex", gap: 10, flexWrap: "wrap", alignItems: "center" }}>
              <input
                className="input"
                type="month"
                value={periodoStr}
                onChange={(e) => setPeriodoStr(e.target.value)}
                style={{ maxWidth: 180 }}
              />
              <button className="btn btn-secundario btn-secundario-mini" type="button" onClick={loadExport} disabled={expLoading}>
                {expLoading ? "Carregando…" : "Atualizar"}
              </button>
              <button
                className="btn btn-primario btn-primario-mini"
                type="button"
                disabled={!expData || expLoading}
                onClick={() => {
                  if (modo === "pessoa") exportPessoaPDFSimple(expData, periodoStr);
                  else exportFamiliaPDFSimple(expData, periodoStr);
                }}
              >
                PDF
              </button>
            </div>
          </div>

          {expErro ? (
            <div className="card" style={{ padding: 12, borderRadius: 14, marginTop: 10 }}>
              <strong>{expErro}</strong>
            </div>
          ) : null}

          {expData ? (
            <div className="card" style={{ padding: 12, borderRadius: 16, marginTop: 12 }}>
              <div style={{ fontWeight: 900 }}>Resumo do período</div>
              {modo === "pessoa" ? (
                <div className="texto-suave" style={{ marginTop: 6 }}>
                  Pessoa: <strong>{expData?.pessoa?.nome}</strong> · CPF: <strong>{expData?.pessoa?.cpf || "—"}</strong> · NIS: <strong>{expData?.pessoa?.nis || "—"}</strong>
                </div>
              ) : (
                <div className="texto-suave" style={{ marginTop: 6 }}>
                  Família: <strong>#{expData?.familia?.id}</strong> · Bairro: <strong>{expData?.familia?.bairro || "—"}</strong> · Território: <strong>{expData?.familia?.territorio || "—"}</strong>
                </div>
              )}
              <div className="texto-suave">
                Pendências: <strong>{(expData?.pendencias || []).length}</strong> · Eventos: <strong>{(expData?.timeline || []).length}</strong>
              </div>

              <div style={{ display: "flex", gap: 10, flexWrap: "wrap", marginTop: 10 }}>
                <button
                  className="btn btn-secundario btn-secundario-mini"
                  type="button"
                  onClick={() => {
                    const lines = [["periodo", periodoStr]];
                    if (modo === "pessoa") {
                      const p = expData?.pessoa || {};
                      lines.push(["pessoa_id", p.id], ["nome", p.nome], ["cpf", p.cpf], ["nis", p.nis]);
                    } else {
                      const f = expData?.familia || {};
                      lines.push(["familia_id", f.id], ["nis_familia", f.nis_familia], ["bairro", f.bairro], ["territorio", f.territorio]);
                    }
                    lines.push(["pendencias_total", (expData?.pendencias || []).length], ["timeline_total", (expData?.timeline || []).length]);
                    dlCSV(`ficha_resumo_${modo}_${periodoStr}.csv`, ["chave,valor", ...lines.map(([k, v]) => `${esc(k)},${esc(v)}`)].join("\n"));
                  }}
                >
                  CSV resumo
                </button>

                <button
                  className="btn btn-secundario btn-secundario-mini"
                  type="button"
                  onClick={() => {
                    const header = ["tipo", "gravidade", "detalhe"];
                    const lines = [header.join(",")];
                    (expData?.pendencias || []).forEach((p) => lines.push([p.tipo, p.gravidade, p.detalhe].map(esc).join(",")));
                    dlCSV(`ficha_pendencias_${modo}_${periodoStr}.csv`, lines.join("\n"));
                  }}
                >
                  CSV pendências
                </button>

                <button
                  className="btn btn-secundario btn-secundario-mini"
                  type="button"
                  onClick={() => {
                    const header = ["quando", "titulo", "detalhe"];
                    const lines = [header.join(",")];
                    (expData?.timeline || []).forEach((e) => lines.push([e.quando, e.titulo, e.detalhe].map(esc).join(",")));
                    dlCSV(`ficha_timeline_${modo}_${periodoStr}.csv`, lines.join("\n"));
                  }}
                >
                  CSV histórico
                </button>
              </div>
            </div>
          ) : (
            <div className="texto-suave" style={{ marginTop: 10 }}>
              {expLoading ? "Carregando…" : "Selecione Pessoa ou Família e clique em Atualizar."}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// FICHA_SUBTABS_HELP_V1
