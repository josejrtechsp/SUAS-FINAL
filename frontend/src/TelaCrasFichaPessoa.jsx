import { useEffect, useMemo, useState } from "react";

function fmt(iso) {
  if (!iso) return "—";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleString("pt-BR");
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

function esc(v) {
  const s = v == null ? "" : String(v);
  if (s.includes('"') || s.includes(",") || s.includes("\n")) return `"${s.replace(/"/g,'""')}"`;
  return s;
}

function exportPDFSimple(data, periodoStr) {
  const pessoa = data?.pessoa || {};
  const pend = data?.pendencias || [];
  const tl = data?.timeline || [];
  const htmlPend = pend.map((p) => `<tr><td>${esc(p.tipo)}</td><td>${esc(p.gravidade)}</td><td>${esc(p.detalhe)}</td></tr>`).join("");
  const htmlTl = tl.slice(0,80).map((e) => `<tr><td>${esc(e.quando)}</td><td>${esc(e.titulo)}</td><td>${esc(e.detalhe)}</td></tr>`).join("");

  const html = `
  <html><head><meta charset="utf-8"/>
  <title>Ficha</title>
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
    <h2 style="margin-top:18px;">Timeline</h2>
    <table><thead><tr><th>Quando</th><th>Evento</th><th>Obs</th></tr></thead><tbody>${htmlTl}</tbody></table>
  </body></html>`;
  const w = window.open("", "_blank");
  if (!w) return alert("Pop-up bloqueado. Permita pop-ups para exportar PDF.");
  w.document.open();
  w.document.write(html);
  w.document.close();
  setTimeout(() => { w.focus(); w.print(); }, 400);
}

export default function TelaCrasFichaPessoa({ apiBase, apiFetch, pessoaId, ano, mes, onNavigate }) {
  const [erro, setErro] = useState("");
  const [loading, setLoading] = useState(false);

  const [pessoas, setPessoas] = useState([]);
  const [pessoaSel, setPessoaSel] = useState(pessoaId || null);
  const [data, setData] = useState(null);

  const [cadAgendarOpen, setCadAgendarOpen] = useState(false);
  const [cadAgendarDT, setCadAgendarDT] = useState("");

  const periodo = useMemo(() => {
    const d = new Date();
    return { ano: ano || d.getFullYear(), mes: mes || (d.getMonth() + 1) };
  }, [ano, mes]);

  const periodoStr = `${periodo.ano}-${String(periodo.mes).padStart(2, "0")}`;

  const cad = data?.cadunico?.atual || null;
  const casoId = data?.casos_cras?.[0]?.id || null;

  async function loadPessoas() {
    try {
      const r = await apiFetch(`${apiBase}/cras/cadastros/pessoas`);
      if (!r.ok) {
        setErro(`Erro ao carregar pessoas (${r.status})`);
        setPessoas([]);
        return;
      }
      const j = await r.json();
      setPessoas(Array.isArray(j) ? j : []);
    } catch (e) {
      console.error(e);
      setErro("Erro ao carregar pessoas (token/rede).");
      setPessoas([]);
    }
  }

  async function loadFicha() {
    if (!pessoaSel) {
      setData(null);
      return;
    }
    setErro("");
    setLoading(true);
    try {
      const qs = new URLSearchParams();
      qs.set("ano", String(periodo.ano));
      qs.set("mes", String(periodo.mes));
      const r = await apiFetch(`${apiBase}/cras/ficha/pessoas/${Number(pessoaSel)}?${qs.toString()}`);
      if (!r.ok) throw new Error(await r.text());
      setData(await r.json());
    } catch (e) {
      console.error(e);
      setErro("Erro ao carregar ficha.");
      setData(null);
    } finally {
      setLoading(false);
    }
  }

  
  // ===== AÇÕES DIRETAS (CadÚnico / PIA) =====
  async function cadCriar() {
    if (!pessoaSel) return;
    setErro("");
    try {
      const unidade = Number(localStorage.getItem("cras_unidade_ativa") || 1);
      const payload = {
        unidade_id: unidade,
        pessoa_id: Number(pessoaSel),
        caso_id: casoId || null,
        observacoes: "Pré-cadastro criado pela Ficha do Usuário",
      };
      const r = await apiFetch(`${apiBase}/cras/cadunico/precadastros`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!r.ok) throw new Error(await r.text());
      await loadFicha();
    } catch (e) {
      console.error(e);
      setErro("Erro ao criar pré-cadastro CadÚnico.");
    }
  }

  async function cadAgendarSalvar() {
    if (!cad?.id) return;
    if (!cadAgendarDT) return setErro("Informe data/hora para agendar.");
    setErro("");
    try {
      const r = await apiFetch(`${apiBase}/cras/cadunico/precadastros/${cad.id}/agendar`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ data_agendada: cadAgendarDT }),
      });
      if (!r.ok) throw new Error(await r.text());
      setCadAgendarOpen(false);
      setCadAgendarDT("");
      await loadFicha();
    } catch (e) {
      console.error(e);
      setErro("Erro ao agendar CadÚnico.");
    }
  }

  async function cadFinalizar() {
    if (!cad?.id) return;
    setErro("");
    try {
      const r = await apiFetch(`${apiBase}/cras/cadunico/precadastros/${cad.id}/finalizar`, { method: "POST" });
      if (!r.ok) throw new Error(await r.text());
      await loadFicha();
    } catch (e) {
      console.error(e);
      setErro("Erro ao finalizar CadÚnico.");
    }
  }

  async function piaCriarPlano() {
    if (!casoId) return setErro("Sem caso CRAS vinculado para criar PIA/PAIF.");
    setErro("");
    try {
      const r = await apiFetch(`${apiBase}/cras/casos/${Number(casoId)}/pia/plano`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ resumo_diagnostico: "Criado via Ficha", objetivos: "—" }),
      });
      if (!r.ok) throw new Error(await r.text());
      await loadFicha();
    } catch (e) {
      console.error(e);
      setErro("Erro ao criar plano PIA/PAIF.");
    }
  }

useEffect(() => { loadPessoas(); }, []); // eslint-disable-line
  useEffect(() => { if (pessoaId) setPessoaSel(pessoaId); }, [pessoaId]);
  useEffect(() => { loadFicha(); }, [pessoaSel, periodo.ano, periodo.mes]); // eslint-disable-line

  return (
    <div className="layout-1col">
      <div className="card" style={{ padding: 14, borderRadius: 18 }}>
        <div style={{ display: "flex", justifyContent: "space-between", gap: 12, flexWrap: "wrap", alignItems: "center" }}>
          <div>
            <div style={{ fontWeight: 900, fontSize: 18 }}>Ficha do Usuário</div>
            <div className="texto-suave">Período: <strong>{periodoStr}</strong></div>
          </div>

          <div style={{ minWidth: 420 }}>
            <div className="texto-suave">Selecionar pessoa: <strong>{pessoas.length}</strong></div>
            <select
              className="input"
              value={pessoaSel || ""}
              onChange={(e) => {
                const v = e.target.value;
                const id = v ? Number(v) : null;
                setPessoaSel(id);
                try { if (v) localStorage.setItem("cras_ficha_pessoa_id", v); } catch {}
              }}
            >
              <option value="">Selecione…</option>
              {pessoas.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.nome_social ? `${p.nome_social} (${p.nome})` : p.nome}
                </option>
              ))}
            </select>
          </div>

          <div style={{ display: "flex", gap: 10, flexWrap: "wrap", alignItems: "center" }}>
            <button className="btn btn-secundario" type="button" onClick={loadFicha}>Atualizar</button>
            <button className="btn btn-secundario btn-secundario-mini" type="button" disabled={!data} onClick={() => {
              const pessoa = data?.pessoa || {};
              const header = ["campo","valor"];
              const lines = [header.join(",")];
              [["nome",pessoa.nome],["cpf",pessoa.cpf],["nis",pessoa.nis],["periodo",periodoStr],["pendencias_total",(data.pendencias||[]).length]].forEach(([k,v]) => lines.push([esc(k),esc(v)].join(",")));
              dlCSV(`ficha_resumo_${pessoa.id || "pessoa"}_${periodoStr}.csv`, lines.join("\n"));
            }}>CSV resumo</button>
            <button className="btn btn-secundario btn-secundario-mini" type="button" disabled={!data} onClick={() => {
              const header = ["tipo","gravidade","detalhe"];
              const lines = [header.join(",")];
              (data.pendencias||[]).forEach((p) => lines.push([p.tipo,p.gravidade,p.detalhe].map(esc).join(",")));
              dlCSV(`ficha_pendencias_${data.pessoa?.id || "pessoa"}_${periodoStr}.csv`, lines.join("\n"));
            }}>CSV pendências</button>
            <button className="btn btn-secundario btn-secundario-mini" type="button" disabled={!data} onClick={() => {
              const header = ["quando","titulo","detalhe"];
              const lines = [header.join(",")];
              (data.timeline||[]).forEach((e) => lines.push([e.quando,e.titulo,e.detalhe].map(esc).join(",")));
              dlCSV(`ficha_timeline_${data.pessoa?.id || "pessoa"}_${periodoStr}.csv`, lines.join("\n"));
            }}>CSV timeline</button>
            <button className="btn btn-primario btn-primario-mini" type="button" disabled={!data} onClick={() => exportPDFSimple(data, periodoStr)}>PDF</button>
            <button className="btn btn-secundario btn-secundario-mini" type="button" onClick={() => onNavigate?.("cadunico")}>CadÚnico</button>
            <button className="btn btn-secundario btn-secundario-mini" type="button" onClick={() => onNavigate?.("casos")}>Casos</button>
            <button className="btn btn-secundario btn-secundario-mini" type="button" onClick={() => onNavigate?.("scfv")}>SCFV</button>
          </div>
        </div>

        {erro ? <div className="card" style={{ padding: 12, borderRadius: 14, marginTop: 10 }}><strong>{erro}</strong></div> : null}
        {loading ? <div className="texto-suave" style={{ marginTop: 10 }}>Carregando…</div> : null}
      </div>

      {data ? (
        <div className="card" style={{ padding: 14, borderRadius: 18, marginTop: 12 }}>
          <div style={{ fontWeight: 900 }}>Resumo</div>
          <div className="texto-suave" style={{ marginTop: 8 }}>
            Nome: <strong>{data.pessoa?.nome}</strong> · CPF: <strong>{data.pessoa?.cpf || "—"}</strong> · NIS: <strong>{data.pessoa?.nis || "—"}</strong>
          </div>
          <div className="texto-suave">
            Pendências: <strong>{(data.pendencias || []).length}</strong> · Eventos timeline: <strong>{(data.timeline || []).length}</strong>
          </div>
          <div className="texto-suave">
            Último evento: <strong>{data.timeline?.[0]?.titulo || "—"}</strong> · {fmt(data.timeline?.[0]?.quando)}
          </div>
        </div>
      ) : null}

      {data ? (
        <div className="card" style={{ padding: 14, borderRadius: 18, marginTop: 12 }}>
          {/* CHECKLIST_CONDICIONALIDADES */}
          <div style={{ display: "flex", justifyContent: "space-between", gap: 10, flexWrap: "wrap", alignItems: "center" }}>
            <div style={{ fontWeight: 900 }}>Checklist de condicionalidades</div>
            <div className="texto-suave">O que está pendente e para onde ir.</div>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "repeat(3, minmax(0, 1fr))", gap: 12, marginTop: 12 }}>
            
            <div className="card" style={{ padding: 12, borderRadius: 16 }}>
              <div style={{ fontWeight: 900 }}>CadÚnico</div>
              <div className="texto-suave" style={{ marginTop: 8 }}>
                Status: <strong>{cad?.status || "—"}</strong>
              </div>

              <div style={{ display: "flex", gap: 10, flexWrap: "wrap", marginTop: 10 }}>
                {!cad ? (
                  <button className="btn btn-primario btn-primario-mini" type="button" onClick={cadCriar}>
                    Criar pré-cadastro
                  </button>
                ) : (
                  <>
                    <button className="btn btn-secundario btn-secundario-mini" type="button" onClick={() => setCadAgendarOpen((v) => !v)}>
                      Agendar
                    </button>
                    <button className="btn btn-secundario btn-secundario-mini" type="button" onClick={cadFinalizar}>
                      Finalizar
                    </button>
                    <button className="btn btn-secundario btn-secundario-mini" type="button" onClick={() => onNavigate?.("cadunico")}>
                      Abrir
                    </button>
                  </>
                )}
              </div>

              {cad && cadAgendarOpen ? (
                <div className="card" style={{ padding: 10, borderRadius: 14, marginTop: 10 }}>
                  <div className="texto-suave" style={{ fontWeight: 900 }}>Data/Hora</div>
                  <div style={{ display: "grid", gridTemplateColumns: "1fr auto", gap: 10, marginTop: 8 }}>
                    <input type="datetime-local" className="input" value={cadAgendarDT} onChange={(e) => setCadAgendarDT(e.target.value)} />
                    <button className="btn btn-primario btn-primario-mini" type="button" onClick={cadAgendarSalvar}>
                      Salvar
                    </button>
                  </div>
                </div>
              ) : null}
            </div>


            
            <div className="card" style={{ padding: 12, borderRadius: 16 }}>
              <div style={{ fontWeight: 900 }}>PAIF/PIA</div>
              <div className="texto-suave" style={{ marginTop: 8 }}>
                Plano: <strong>{data?.pia?.plano ? "Existe" : "—"}</strong>
              </div>

              <div style={{ display: "flex", gap: 10, flexWrap: "wrap", marginTop: 10 }}>
                {!data?.pia?.plano ? (
                  <button className="btn btn-primario btn-primario-mini" type="button" onClick={piaCriarPlano} disabled={!casoId}>
                    Criar plano
                  </button>
                ) : null}

                <button className="btn btn-secundario btn-secundario-mini" type="button" onClick={() => onNavigate?.("casos")}>
                  Abrir Casos
                </button>
              </div>

              {!casoId ? <div className="texto-suave" style={{ marginTop: 8 }}>Sem caso vinculado para criar PIA.</div> : null}
            </div>


            <div className="card" style={{ padding: 12, borderRadius: 16 }}>
              <div style={{ fontWeight: 900 }}>SCFV</div>
              <div className="texto-suave" style={{ marginTop: 8 }}>
                Participação: <strong>{(data.scfv?.participacoes || []).length ? "Sim" : "—"}</strong>
              </div>
              <div style={{ display: "flex", gap: 10, flexWrap: "wrap", marginTop: 10 }}>
                <button className="btn btn-secundario btn-secundario-mini" type="button" onClick={() => onNavigate?.("scfv")}>Abrir SCFV</button>
                <button className="btn btn-primario btn-primario-mini" type="button" onClick={() => {
                  const d = new Date();
                  const ym = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`;
                  // tenta usar a turma da primeira participação, se existir
                  const turmaId = data?.scfv?.participacoes?.[0]?.turma_id || null;
                  onNavigate?.("scfv", { turmaId, mes: ym, limite: 3, presMin: 75, auto: true, scrollRel: true });
                }}>
                  Abrir relatório
                </button>
              </div>
            </div>
          </div>

          <div className="texto-suave" style={{ marginTop: 12 }}>
            Pendências detectadas: <strong>{(data.pendencias || []).length}</strong>
          </div>
        </div>
      ) : null}

    </div>
  );
}
