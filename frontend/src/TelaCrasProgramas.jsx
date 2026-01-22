import { useEffect, useMemo, useState } from "react";

function safeStr(v) {
  return (v == null ? "" : String(v)).trim();
}

function downloadTextFile(filename, text) {
  try {
    const blob = new Blob([text], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 500);
  } catch {}
}

function toCsvRow(cols) {
  return cols
    .map((c) => {
      const s = c == null ? "" : String(c);
      const esc = s.replace(/"/g, '""');
      return `"${esc}"`;
    })
    .join(",");
}

export default function TelaCrasProgramas({
  apiBase,
  apiFetch,
  usuarioLogado,
  view = "lista",
  onSetView = () => {},
  onNavigate = () => {},
}) {
  const unidadeAtiva = localStorage.getItem("cras_unidade_ativa") || "";

  const [msg, setMsg] = useState("");
  const [erro, setErro] = useState("");

  const [loading, setLoading] = useState(false);
  const [programas, setProgramas] = useState([]);

  // criar programa (fica recolhido na subtela "Lista")
  const [novoOpen, setNovoOpen] = useState(false);
  const [nome, setNome] = useState("");
  const [publico, setPublico] = useState("");
  const [descricao, setDescricao] = useState("");
  const [capMax, setCapMax] = useState("");
  const [statusProg, setStatusProg] = useState("em_andamento");

  // inscrição / pessoas
  const [pessoas, setPessoas] = useState([]);
  const [programaSel, setProgramaSel] = useState(null);
  const [participantes, setParticipantes] = useState([]);
  const [inscPessoaId, setInscPessoaId] = useState("");

  const viewKey = (view || "lista").toLowerCase();

  const programasOrdenados = useMemo(() => {
    const arr = Array.isArray(programas) ? [...programas] : [];
    arr.sort((a, b) => Number(b?.id || 0) - Number(a?.id || 0));
    return arr;
  }, [programas]);

  const participantesIds = useMemo(() => {
    const s = new Set();
    (Array.isArray(participantes) ? participantes : []).forEach((pt) => {
      if (pt?.pessoa_id != null) s.add(String(pt.pessoa_id));
      else if (pt?.pessoa?.id != null) s.add(String(pt.pessoa.id));
    });
    return s;
  }, [participantes]);

  const pessoasElegiveis = useMemo(() => {
    // elegíveis = pessoas cadastradas que ainda não estão inscritas no programa selecionado
    const arr = Array.isArray(pessoas) ? pessoas : [];
    if (!programaSel?.id) return arr.slice(0, 50);
    return arr.filter((p) => !participantesIds.has(String(p.id)));
  }, [pessoas, programaSel?.id, participantesIds]);

  async function loadProgramas() {
    setErro("");
    setLoading(true);
    try {
      const q = new URLSearchParams();
      if (unidadeAtiva) q.set("unidade_id", unidadeAtiva);
      const r = await apiFetch(`${apiBase}/cras/programas?${q.toString()}`);
      if (!r.ok) throw new Error(await r.text());
      const j = await r.json();
      setProgramas(Array.isArray(j) ? j : []);
    } catch (e) {
      console.error(e);
      setErro("Não foi possível carregar Programas/Projetos.");
    } finally {
      setLoading(false);
    }
  }

  async function loadPessoas() {
    try {
      const r = await apiFetch(`${apiBase}/cras/cadastros/pessoas`);
      if (r.ok) {
        const j = await r.json();
        setPessoas(Array.isArray(j) ? j : []);
      }
    } catch {}
  }

  async function loadParticipantes(programaId) {
    if (!programaId) return setParticipantes([]);
    try {
      const r = await apiFetch(`${apiBase}/cras/programas/${programaId}/participantes`);
      if (r.ok) {
        const j = await r.json();
        setParticipantes(Array.isArray(j) ? j : []);
      }
    } catch {
      setParticipantes([]);
    }
  }

  useEffect(() => {
    loadProgramas();
    loadPessoas();
    // eslint-disable-next-line
  }, []);

  useEffect(() => {
    if (programaSel?.id) loadParticipantes(programaSel.id);
    // eslint-disable-next-line
  }, [programaSel?.id]);

  // Se trocar subtela, recolhe o "novo programa" para não poluir
  useEffect(() => {
    setNovoOpen(false);
    setMsg("");
    // eslint-disable-next-line
  }, [viewKey]);

  async function criarPrograma() {
    setMsg("");
    if (!safeStr(nome)) return setMsg("Nome do programa/projeto é obrigatório.");

    try {
      const r = await apiFetch(`${apiBase}/cras/programas`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          nome: safeStr(nome),
          publico: safeStr(publico) || null,
          descricao: safeStr(descricao) || null,
          capacidade_max: capMax ? Number(capMax) : null,
          status: safeStr(statusProg) || "em_andamento",
          unidade_id: unidadeAtiva ? Number(unidadeAtiva) : null,
        }),
      });
      if (!r.ok) throw new Error(await r.text());
      const created = await r.json();
      setMsg("Programa/Projeto criado ✅");
      setNome(""); setPublico(""); setDescricao(""); setCapMax(""); setStatusProg("em_andamento");
      setNovoOpen(false);
      await loadProgramas();
      setProgramaSel(created);
      try { onSetView("lista"); } catch {}
    } catch (e) {
      console.error(e);
      setMsg("Erro ao criar programa/projeto.");
    }
  }

  async function inscreverPessoa() {
    setMsg("");
    if (!programaSel?.id) return setMsg("Selecione um programa/projeto.");
    if (!inscPessoaId) return setMsg("Selecione uma pessoa.");

    try {
      const r = await apiFetch(`${apiBase}/cras/programas/${programaSel.id}/inscrever`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ pessoa_id: Number(inscPessoaId) }),
      });
      if (!r.ok) throw new Error(await r.text());
      setMsg("Participante inscrito ✅");
      setInscPessoaId("");
      await loadParticipantes(programaSel.id);
    } catch (e) {
      console.error(e);
      setMsg("Erro ao inscrever participante (capacidade/duplicidade).");
    }
  }

  function exportarCsvResumo() {
    const rows = [];
    rows.push(toCsvRow(["programa_id", "nome", "status", "publico", "capacidade_max", "participantes_qtd"]));
    for (const p of programasOrdenados) {
      const qtd = (p.participantes_qtd != null ? p.participantes_qtd : p.qtd_participantes);
      rows.push(
        toCsvRow([
          p.id,
          p.nome,
          p.status || "",
          p.publico || "",
          p.capacidade_max ?? "",
          qtd ?? "",
        ])
      );
    }
    downloadTextFile(`programas_resumo_unidade_${unidadeAtiva || "todas"}.csv`, rows.join("\n"));
  }

  const CardMsg = () => (
    <>
      {erro ? (
        <div className="card" style={{ padding: 12, borderRadius: 14 }}>
          <strong>{erro}</strong>
        </div>
      ) : null}
      {msg ? (
        <div className="card" style={{ padding: 12, borderRadius: 14 }}>
          <strong>{msg}</strong>
        </div>
      ) : null}
    </>
  );

  const ProgramasList = ({ dense = false }) => (
    <div className="card" style={{ padding: 12, borderRadius: 18, minHeight: dense ? 220 : 380 }}>
      <div style={{ display: "flex", justifyContent: "space-between", gap: 10, alignItems: "center", flexWrap: "wrap" }}>
        <h3 style={{ margin: 0 }}>Programas/Projetos</h3>
        <button className="btn btn-secundario" type="button" onClick={loadProgramas}>
          Atualizar
        </button>
      </div>
      {loading ? <div className="texto-suave" style={{ marginTop: 10 }}>Carregando…</div> : null}

      <div style={{ display: "grid", gap: 8, marginTop: 10, maxHeight: dense ? 260 : 520, overflow: "auto" }}>
        {programasOrdenados.map((p) => (
          <button
            key={p.id}
            type="button"
            className="card"
            onClick={() => setProgramaSel(p)}
            style={{
              textAlign: "left",
              padding: 10,
              borderRadius: 14,
              cursor: "pointer",
              background: "rgba(255,255,255,.92)",
              border: programaSel?.id === p.id ? "2px solid rgba(99,102,241,.55)" : "1px solid rgba(2,6,23,.08)",
            }}
          >
            <div style={{ fontWeight: 900 }}>#{p.id} · {p.nome}</div>
            <div className="texto-suave">
              Status: {p.status || "—"} · Público: {p.publico || "—"}
            </div>
            {p.capacidade_max != null ? (
              <div className="texto-suave">Capacidade: {p.capacidade_max}</div>
            ) : null}
          </button>
        ))}
        {!programasOrdenados.length ? <div className="texto-suave">Sem programas/projetos cadastrados.</div> : null}
      </div>
    </div>
  );

  const NovoProgramaCard = () => (
    <div className="card" style={{ padding: 12, borderRadius: 18 }}>
      <div style={{ display: "flex", justifyContent: "space-between", gap: 10, alignItems: "center", flexWrap: "wrap" }}>
        <div>
          <div style={{ fontWeight: 900 }}>Criar programa/projeto</div>
          <div className="texto-suave">Recolhido por padrão para manter a tela limpa.</div>
        </div>
        <button className={"btn " + (novoOpen ? "btn-secundario" : "btn-primario")} type="button" onClick={() => setNovoOpen((v) => !v)}>
          {novoOpen ? "Fechar" : "Novo programa"}
        </button>
      </div>

      {novoOpen ? (
        <div style={{ display: "grid", gap: 8, marginTop: 10 }}>
          <input className="input" placeholder="Nome (ex.: Grupo de Idosos / Oficinas…)" value={nome} onChange={(e) => setNome(e.target.value)} />
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
            <select className="input" value={publico} onChange={(e) => setPublico(e.target.value)}>
              <option value="">Público-alvo (opcional)…</option>
              <option value="crianca">Criança</option>
              <option value="adolescente">Adolescente</option>
              <option value="adulto">Adulto</option>
              <option value="idoso">Idoso</option>
              <option value="mulher">Mulheres</option>
              <option value="pcd">PCD</option>
              <option value="outros">Outros</option>
            </select>

            <select className="input" value={statusProg} onChange={(e) => setStatusProg(e.target.value)}>
              <option value="em_andamento">Em andamento</option>
              <option value="aguardando">Aguardando</option>
              <option value="finalizado">Finalizado</option>
            </select>
          </div>

          <textarea className="input" rows={3} placeholder="Descrição (opcional)" value={descricao} onChange={(e) => setDescricao(e.target.value)} />
          <input className="input" placeholder="Capacidade máxima (opcional)" value={capMax} onChange={(e) => setCapMax(e.target.value)} />

          <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
            <button className="btn btn-primario" type="button" onClick={criarPrograma}>Criar</button>
            <button className="btn btn-secundario" type="button" onClick={() => setNovoOpen(false)}>Cancelar</button>
          </div>
        </div>
      ) : null}
    </div>
  );

  const ListaView = () => (
    <div className="layout-1col" style={{ display: "grid", gap: 12 }}>
      <NovoProgramaCard />

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
        <ProgramasList />
        <div className="card" style={{ padding: 12, borderRadius: 18, minHeight: 380 }}>
          <h3 style={{ margin: 0 }}>Detalhes</h3>
          {!programaSel ? (
            <div className="texto-suave" style={{ marginTop: 10 }}>Selecione um programa/projeto.</div>
          ) : (
            <>
              <div style={{ marginTop: 10, fontWeight: 900 }}>{programaSel.nome}</div>
              <div className="texto-suave">Status: {programaSel.status || "—"} · Público: {programaSel.publico || "—"}</div>
              {programaSel.descricao ? <div className="texto-suave" style={{ marginTop: 8 }}>{programaSel.descricao}</div> : null}
              {programaSel.capacidade_max != null ? (
                <div className="texto-suave" style={{ marginTop: 8 }}>Capacidade: <strong>{programaSel.capacidade_max}</strong></div>
              ) : null}

              <div style={{ display: "flex", gap: 10, flexWrap: "wrap", marginTop: 12 }}>
                <button className="btn btn-primario" type="button" onClick={() => onSetView("elegiveis")}>Ir para Elegíveis</button>
                <button className="btn btn-secundario" type="button" onClick={() => onSetView("acompanhamento")}>Ir para Acompanhamento</button>
              </div>

              <div className="texto-suave" style={{ marginTop: 10 }}>
                Dica: crie o programa aqui e faça inscrição em <strong>Elegíveis</strong>.
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );

  const ElegiveisView = () => (
    <div className="layout-1col" style={{ display: "grid", gap: 12 }}>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
        <ProgramasList dense />
        <div className="card" style={{ padding: 12, borderRadius: 18, minHeight: 220 }}>
          <h3 style={{ margin: 0 }}>Inscrição</h3>
          {!programaSel ? (
            <div className="texto-suave" style={{ marginTop: 10 }}>Selecione um programa/projeto ao lado.</div>
          ) : (
            <>
              <div className="texto-suave" style={{ marginTop: 10 }}>
                Programa: <strong>{programaSel.nome}</strong>
              </div>

              <div style={{ display: "flex", gap: 10, flexWrap: "wrap", alignItems: "center", marginTop: 10 }}>
                <select className="input" value={inscPessoaId} onChange={(e) => setInscPessoaId(e.target.value)} style={{ minWidth: 280 }}>
                  <option value="">Selecione uma pessoa…</option>
                  {pessoasElegiveis.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.nome_social ? `${p.nome_social} (${p.nome})` : p.nome}
                    </option>
                  ))}
                </select>

                <button className="btn btn-primario" type="button" onClick={inscreverPessoa}>
                  Inscrever
                </button>

                <button className="btn btn-secundario" type="button" onClick={() => onSetView("acompanhamento")}>
                  Ver participantes
                </button>
              </div>

              <div className="texto-suave" style={{ marginTop: 10 }}>
                Elegíveis exibidos: <strong>{pessoasElegiveis.length}</strong> (não inscritos neste programa)
              </div>
            </>
          )}
        </div>
      </div>

      <div className="card" style={{ padding: 12, borderRadius: 18 }}>
        <h3 style={{ margin: 0 }}>Lista de elegíveis</h3>
        <div className="texto-suave" style={{ marginTop: 6 }}>
          Pessoas cadastradas que ainda não estão inscritas no programa selecionado.
        </div>
        <div style={{ display: "grid", gap: 8, marginTop: 10, maxHeight: 420, overflow: "auto" }}>
          {(pessoasElegiveis || []).slice(0, 200).map((p) => (
            <div key={p.id} className="card" style={{ padding: 10, borderRadius: 14 }}>
              <div style={{ fontWeight: 900 }}>#{p.id} · {p.nome_social ? `${p.nome_social} (${p.nome})` : p.nome}</div>
              <div className="texto-suave">CPF: {p.cpf || "—"} · NIS: {p.nis || "—"}</div>
            </div>
          ))}
          {!pessoasElegiveis.length ? <div className="texto-suave">Sem elegíveis (ou selecione um programa).</div> : null}
        </div>
      </div>
    </div>
  );

  const AcompanhamentoView = () => (
    <div className="layout-1col" style={{ display: "grid", gap: 12 }}>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
        <ProgramasList dense />
        <div className="card" style={{ padding: 12, borderRadius: 18, minHeight: 220 }}>
          <h3 style={{ margin: 0 }}>Participantes</h3>
          {!programaSel ? (
            <div className="texto-suave" style={{ marginTop: 10 }}>Selecione um programa/projeto ao lado.</div>
          ) : (
            <>
              <div className="texto-suave" style={{ marginTop: 10 }}>
                Programa: <strong>{programaSel.nome}</strong>
              </div>
              <div style={{ display: "flex", gap: 10, flexWrap: "wrap", marginTop: 10 }}>
                <button className="btn btn-secundario" type="button" onClick={() => loadParticipantes(programaSel.id)}>
                  Atualizar participantes
                </button>
                <button className="btn btn-primario" type="button" onClick={() => onSetView("elegiveis")}>
                  Inscrever elegíveis
                </button>
              </div>
              <div className="texto-suave" style={{ marginTop: 10 }}>
                Total: <strong>{(Array.isArray(participantes) ? participantes.length : 0)}</strong>
              </div>
            </>
          )}
        </div>
      </div>

      <div className="card" style={{ padding: 12, borderRadius: 18 }}>
        <h3 style={{ margin: 0 }}>Lista de participantes</h3>
        <div className="texto-suave" style={{ marginTop: 6 }}>
          Consulta por programa. Para evidências e ações, use a Ficha/ Caso quando aplicável.
        </div>

        <div style={{ display: "grid", gap: 8, marginTop: 10, maxHeight: 520, overflow: "auto" }}>
          {(Array.isArray(participantes) ? participantes : []).map((pt) => (
            <div key={pt.id || `${pt.programa_id}-${pt.pessoa_id}`} className="card" style={{ padding: 10, borderRadius: 14 }}>
              <div style={{ fontWeight: 900 }}>
                {pt.pessoa?.nome_social ? `${pt.pessoa.nome_social} (${pt.pessoa.nome})` : (pt.pessoa?.nome || "Pessoa")}
              </div>
              <div className="texto-suave">Status: {pt.status || "—"}</div>
              <div className="texto-suave">CPF: {pt.pessoa?.cpf || "—"} · NIS: {pt.pessoa?.nis || "—"}</div>
            </div>
          ))}
          {!participantes?.length ? <div className="texto-suave">Sem participantes (ou selecione um programa).</div> : null}
        </div>
      </div>
    </div>
  );

  const RelatoriosView = () => (
    <div className="layout-1col" style={{ display: "grid", gap: 12 }}>
      <div className="card" style={{ padding: 12, borderRadius: 18 }}>
        <h3 style={{ margin: 0 }}>Resumo</h3>
        <div className="texto-suave" style={{ marginTop: 6 }}>
          Indicadores por programa (por unidade). Use para gestão, metas e evidências.
        </div>

        <div style={{ display: "flex", gap: 10, flexWrap: "wrap", marginTop: 10 }}>
          <button className="btn btn-primario" type="button" onClick={exportarCsvResumo}>
            Exportar CSV
          </button>
          <button className="btn btn-secundario" type="button" onClick={loadProgramas}>
            Atualizar
          </button>
        </div>
      </div>

      <div className="card" style={{ padding: 12, borderRadius: 18 }}>
        <h3 style={{ margin: 0 }}>Programas cadastrados</h3>
        <div style={{ display: "grid", gap: 8, marginTop: 10, maxHeight: 520, overflow: "auto" }}>
          {programasOrdenados.map((p) => (
            <div key={p.id} className="card" style={{ padding: 10, borderRadius: 14 }}>
              <div style={{ fontWeight: 900 }}>#{p.id} · {p.nome}</div>
              <div className="texto-suave">Status: {p.status || "—"} · Público: {p.publico || "—"}</div>
              {p.capacidade_max != null ? <div className="texto-suave">Capacidade: {p.capacidade_max}</div> : null}
            </div>
          ))}
          {!programasOrdenados.length ? <div className="texto-suave">Sem programas/projetos cadastrados.</div> : null}
        </div>
      </div>
    </div>
  );

  return (
    <div className="layout-1col">
      <CardMsg />

      {viewKey === "lista" ? <ListaView /> : null}
      {viewKey === "elegiveis" ? <ElegiveisView /> : null}
      {viewKey === "acompanhamento" ? <AcompanhamentoView /> : null}
      {viewKey === "relatorios" ? <RelatoriosView /> : null}
    </div>
  );
}

// PROGRAMAS_SUBTABS_HELP_V1
