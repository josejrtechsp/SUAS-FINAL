import { useEffect, useMemo, useState } from "react";

function safeStr(v) {
  return (v == null ? "" : String(v)).trim();
}

export default function TelaCrasCadastros({
  apiBase,
  apiFetch,
  usuarioLogado,
  view = "pessoas",
  onSetView = () => {},
}) {
  const [msg, setMsg] = useState("");
  const [erro, setErro] = useState("");

  const [pessoas, setPessoas] = useState([]);
  const [familias, setFamilias] = useState([]);

  // pessoa form
  const [nome, setNome] = useState("");
  const [cpf, setCpf] = useState("");
  const [nis, setNis] = useState("");
  const [bairro, setBairro] = useState("");
  const [territorio, setTerritorio] = useState("");

  // família form
  const [nisFam, setNisFam] = useState("");
  const [enderecoFam, setEnderecoFam] = useState("");
  const [bairroFam, setBairroFam] = useState("");
  const [territorioFam, setTerritorioFam] = useState("");
  const [refPessoaId, setRefPessoaId] = useState("");

  // detalhe família / vínculos
  const [familiaSel, setFamiliaSel] = useState(null);
  const [membros, setMembros] = useState([]);
  const [addPessoaId, setAddPessoaId] = useState("");
  const [addParentesco, setAddParentesco] = useState("");
  const [addResp, setAddResp] = useState(false);

  const pessoasOrdenadas = useMemo(() => {
    const arr = Array.isArray(pessoas) ? [...pessoas] : [];
    arr.sort((a, b) => Number(b?.id || 0) - Number(a?.id || 0));
    return arr;
  }, [pessoas]);

  const familiasOrdenadas = useMemo(() => {
    const arr = Array.isArray(familias) ? [...familias] : [];
    arr.sort((a, b) => Number(b?.id || 0) - Number(a?.id || 0));
    return arr;
  }, [familias]);

  async function loadAll() {
    setErro("");
    try {
      const [rp, rf] = await Promise.all([
        apiFetch(`${apiBase}/cras/cadastros/pessoas`),
        apiFetch(`${apiBase}/cras/cadastros/familias`),
      ]);
      if (rp.ok) setPessoas(await rp.json());
      if (rf.ok) setFamilias(await rf.json());
    } catch (e) {
      console.error(e);
      setErro("Não foi possível carregar cadastros.");
    }
  }

  async function loadMembros(familiaId) {
    if (!familiaId) return setMembros([]);
    try {
      const r = await apiFetch(`${apiBase}/cras/cadastros/familias/${familiaId}/membros`);
      if (r.ok) setMembros(await r.json());
      else setMembros([]);
    } catch {
      setMembros([]);
    }
  }

  useEffect(() => {
    loadAll();
    // eslint-disable-next-line
  }, []);

  useEffect(() => {
    if (familiaSel?.id) loadMembros(familiaSel.id);
    // eslint-disable-next-line
  }, [familiaSel?.id]);

  async function criarPessoa() {
    setMsg("");
    if (!safeStr(nome)) return setMsg("Nome é obrigatório.");
    try {
      const r = await apiFetch(`${apiBase}/cras/cadastros/pessoas`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          nome: safeStr(nome),
          cpf: safeStr(cpf) || null,
          nis: safeStr(nis) || null,
          bairro: safeStr(bairro) || null,
          territorio: safeStr(territorio) || null,
        }),
      });
      if (!r.ok) throw new Error(await r.text());
      setMsg("Pessoa cadastrada ✅");
      setNome("");
      setCpf("");
      setNis("");
      setBairro("");
      setTerritorio("");
      await loadAll();
      try {
        onSetView("pessoas");
      } catch {}
    } catch (e) {
      console.error(e);
      setMsg("Erro ao cadastrar pessoa (verifique município/permissão).");
    }
  }

  async function criarFamilia() {
    setMsg("");
    try {
      const r = await apiFetch(`${apiBase}/cras/cadastros/familias`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          nis_familia: safeStr(nisFam) || null,
          endereco: safeStr(enderecoFam) || null,
          bairro: safeStr(bairroFam) || null,
          territorio: safeStr(territorioFam) || null,
          referencia_pessoa_id: refPessoaId ? Number(refPessoaId) : null,
        }),
      });
      if (!r.ok) throw new Error(await r.text());
      const created = await r.json();
      setMsg("Família cadastrada ✅");
      setNisFam("");
      setEnderecoFam("");
      setBairroFam("");
      setTerritorioFam("");
      setRefPessoaId("");
      await loadAll();
      setFamiliaSel(created);
      // após criar, leva para vínculos para montar a composição
      try {
        onSetView("vinculos");
      } catch {}
    } catch (e) {
      console.error(e);
      setMsg("Erro ao cadastrar família.");
    }
  }

  async function adicionarMembro() {
    setMsg("");
    if (!familiaSel?.id) return setMsg("Selecione uma família.");
    if (!addPessoaId) return setMsg("Selecione uma pessoa.");

    try {
      const r = await apiFetch(`${apiBase}/cras/cadastros/familias/${familiaSel.id}/membros`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          pessoa_id: Number(addPessoaId),
          parentesco: safeStr(addParentesco) || null,
          responsavel_bool: !!addResp,
        }),
      });
      if (!r.ok) throw new Error(await r.text());
      setMsg("Membro adicionado ✅");
      setAddPessoaId("");
      setAddParentesco("");
      setAddResp(false);
      await loadMembros(familiaSel.id);
    } catch (e) {
      console.error(e);
      setMsg("Erro ao adicionar membro (pode já estar vinculado).");
    }
  }

  const viewKey = (view || "pessoas").toLowerCase();

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

  const PessoasView = () => (
    <div className="card" style={{ padding: 12, borderRadius: 18 }}>
      <h3 style={{ margin: 0 }}>Pessoas</h3>
      <div className="texto-suave" style={{ marginTop: 6 }}>
        Cadastre e localize pessoas para vincular em famílias, casos e CadÚnico.
      </div>

      <div style={{ display: "grid", gap: 10, marginTop: 12 }}>
        <div className="card" style={{ padding: 12, borderRadius: 16 }}>
          <div style={{ fontWeight: 900, marginBottom: 8 }}>Nova pessoa</div>
          <div style={{ display: "grid", gap: 8 }}>
            <input className="input" placeholder="Nome completo" value={nome} onChange={(e) => setNome(e.target.value)} />
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
              <input className="input" placeholder="CPF (opcional)" value={cpf} onChange={(e) => setCpf(e.target.value)} />
              <input className="input" placeholder="NIS (opcional)" value={nis} onChange={(e) => setNis(e.target.value)} />
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
              <input className="input" placeholder="Bairro (opcional)" value={bairro} onChange={(e) => setBairro(e.target.value)} />
              <input className="input" placeholder="Território (opcional)" value={territorio} onChange={(e) => setTerritorio(e.target.value)} />
            </div>
            <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
              <button className="btn btn-primario" type="button" onClick={criarPessoa}>
                Cadastrar pessoa
              </button>
              <button className="btn btn-secundario" type="button" onClick={loadAll}>
                Atualizar
              </button>
            </div>
          </div>
        </div>

        <div className="card" style={{ padding: 12, borderRadius: 16 }}>
          <div style={{ fontWeight: 900, marginBottom: 6 }}>Pessoas cadastradas</div>
          <div style={{ display: "grid", gap: 8, maxHeight: 520, overflow: "auto" }}>
            {pessoasOrdenadas.map((p) => (
              <div key={p.id} className="card" style={{ padding: 10, borderRadius: 14 }}>
                <div style={{ fontWeight: 900 }}>
                  #{p.id} · {p.nome_social ? `${p.nome_social} (${p.nome})` : p.nome}
                </div>
                <div className="texto-suave">CPF: {p.cpf || "—"} · NIS: {p.nis || "—"}</div>
                <div className="texto-suave">Bairro: {p.bairro || "—"} · Território: {p.territorio || "—"}</div>
              </div>
            ))}
            {!pessoasOrdenadas.length ? <div className="texto-suave">Sem pessoas cadastradas.</div> : null}
          </div>
        </div>
      </div>
    </div>
  );

  const FamiliasView = () => (
    <div className="card" style={{ padding: 12, borderRadius: 18 }}>
      <h3 style={{ margin: 0 }}>Famílias</h3>
      <div className="texto-suave" style={{ marginTop: 6 }}>
        Crie famílias e mantenha endereço/território atualizados para gestão territorial.
      </div>

      <div style={{ display: "grid", gap: 10, marginTop: 12 }}>
        <div className="card" style={{ padding: 12, borderRadius: 16 }}>
          <div style={{ fontWeight: 900, marginBottom: 8 }}>Nova família</div>
          <div style={{ display: "grid", gap: 8 }}>
            <input className="input" placeholder="NIS da família (opcional)" value={nisFam} onChange={(e) => setNisFam(e.target.value)} />
            <input className="input" placeholder="Endereço (opcional)" value={enderecoFam} onChange={(e) => setEnderecoFam(e.target.value)} />
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
              <input className="input" placeholder="Bairro (opcional)" value={bairroFam} onChange={(e) => setBairroFam(e.target.value)} />
              <input className="input" placeholder="Território (opcional)" value={territorioFam} onChange={(e) => setTerritorioFam(e.target.value)} />
            </div>
            <select className="input" value={refPessoaId} onChange={(e) => setRefPessoaId(e.target.value)}>
              <option value="">Pessoa de referência (opcional)…</option>
              {pessoasOrdenadas.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.nome_social ? `${p.nome_social} (${p.nome})` : p.nome}
                </option>
              ))}
            </select>

            <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
              <button className="btn btn-primario" type="button" onClick={criarFamilia}>
                Cadastrar família
              </button>
              <button className="btn btn-secundario" type="button" onClick={loadAll}>
                Atualizar
              </button>
            </div>
          </div>
        </div>

        <div className="card" style={{ padding: 12, borderRadius: 16 }}>
          <div style={{ fontWeight: 900, marginBottom: 6 }}>Famílias cadastradas</div>
          <div style={{ display: "grid", gap: 8, maxHeight: 520, overflow: "auto" }}>
            {familiasOrdenadas.map((f) => (
              <button
                key={f.id}
                type="button"
                className="card"
                onClick={() => setFamiliaSel(f)}
                style={{
                  textAlign: "left",
                  padding: 10,
                  borderRadius: 14,
                  cursor: "pointer",
                  border: familiaSel?.id === f.id ? "2px solid rgba(99,102,241,.55)" : "1px solid rgba(2,6,23,.08)",
                  background: "rgba(255,255,255,.9)",
                }}
              >
                <div style={{ fontWeight: 900 }}>Família #{f.id}</div>
                <div className="texto-suave">NIS: {f.nis_familia || "—"} · Bairro: {f.bairro || "—"}</div>
                <div className="texto-suave">Território: {f.territorio || "—"}</div>
              </button>
            ))}
            {!familiasOrdenadas.length ? <div className="texto-suave">Sem famílias cadastradas.</div> : null}
          </div>

          {familiaSel ? (
            <div className="texto-suave" style={{ marginTop: 10 }}>
              Selecionada: <strong>Família #{familiaSel.id}</strong> — para adicionar membros, vá em <strong>Vínculos</strong>.
            </div>
          ) : null}

          <div style={{ display: "flex", gap: 10, flexWrap: "wrap", marginTop: 10 }}>
            <button className="btn btn-secundario" type="button" onClick={() => onSetView("vinculos")}>Ir para Vínculos</button>
          </div>
        </div>
      </div>
    </div>
  );

  const VinculosView = () => (
    <div className="card" style={{ padding: 12, borderRadius: 18 }}>
      <h3 style={{ margin: 0 }}>Vínculos</h3>
      <div className="texto-suave" style={{ marginTop: 6 }}>
        Monte a composição familiar: membros, parentesco e responsável.
      </div>

      <div style={{ display: "grid", gap: 10, marginTop: 12 }}>
        <div className="card" style={{ padding: 12, borderRadius: 16 }}>
          <div style={{ fontWeight: 900, marginBottom: 6 }}>Selecione uma família</div>
          <div style={{ display: "grid", gap: 8, maxHeight: 260, overflow: "auto" }}>
            {familiasOrdenadas.map((f) => (
              <button
                key={f.id}
                type="button"
                className="card"
                onClick={() => setFamiliaSel(f)}
                style={{
                  textAlign: "left",
                  padding: 10,
                  borderRadius: 14,
                  cursor: "pointer",
                  border: familiaSel?.id === f.id ? "2px solid rgba(99,102,241,.55)" : "1px solid rgba(2,6,23,.08)",
                  background: "rgba(255,255,255,.9)",
                }}
              >
                <div style={{ fontWeight: 900 }}>Família #{f.id}</div>
                <div className="texto-suave">Bairro: {f.bairro || "—"} · Território: {f.territorio || "—"}</div>
              </button>
            ))}
            {!familiasOrdenadas.length ? <div className="texto-suave">Sem famílias cadastradas.</div> : null}
          </div>
        </div>

        <div className="card" style={{ padding: 12, borderRadius: 16 }}>
          <div style={{ fontWeight: 900 }}>Membros da família</div>

          {!familiaSel ? (
            <div className="texto-suave" style={{ marginTop: 8 }}>
              Selecione uma família acima para ver e editar membros.
            </div>
          ) : (
            <>
              <div className="texto-suave" style={{ marginTop: 8 }}>
                Família selecionada: <strong>#{familiaSel.id}</strong>
              </div>

              <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr", gap: 8, marginTop: 10 }}>
                <select className="input" value={addPessoaId} onChange={(e) => setAddPessoaId(e.target.value)}>
                  <option value="">Selecione uma pessoa…</option>
                  {pessoasOrdenadas.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.nome_social ? `${p.nome_social} (${p.nome})` : p.nome}
                    </option>
                  ))}
                </select>

                <input className="input" placeholder="Parentesco (opcional)" value={addParentesco} onChange={(e) => setAddParentesco(e.target.value)} />
              </div>

              <label className="texto-suave" style={{ display: "flex", gap: 8, alignItems: "center", marginTop: 8 }}>
                <input type="checkbox" checked={addResp} onChange={(e) => setAddResp(e.target.checked)} />
                Responsável
              </label>

              <div style={{ display: "flex", gap: 10, flexWrap: "wrap", marginTop: 10 }}>
                <button className="btn btn-primario" type="button" onClick={adicionarMembro}>
                  Adicionar membro
                </button>
                <button className="btn btn-secundario" type="button" onClick={() => loadMembros(familiaSel.id)}>
                  Atualizar membros
                </button>
              </div>

              <div style={{ display: "grid", gap: 8, marginTop: 10, maxHeight: 260, overflow: "auto" }}>
                {membros.map((m) => (
                  <div key={m.id} className="card" style={{ padding: 10, borderRadius: 14 }}>
                    <div style={{ fontWeight: 900 }}>Pessoa #{m.pessoa_id}</div>
                    <div className="texto-suave">
                      {m.parentesco ? `Parentesco: ${m.parentesco} · ` : ""}
                      {m.responsavel_bool ? "Responsável" : "Membro"}
                    </div>
                  </div>
                ))}
                {!membros.length ? <div className="texto-suave">Sem membros ainda.</div> : null}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );

  const AtualizacaoView = () => (
    <div className="card" style={{ padding: 12, borderRadius: 18 }}>
      <h3 style={{ margin: 0 }}>Atualização</h3>
      <div className="texto-suave" style={{ marginTop: 6 }}>
        Atualize a base e confira consistência antes de operar atendimentos.
      </div>

      <div style={{ display: "grid", gap: 10, marginTop: 12 }}>
        <div className="card" style={{ padding: 12, borderRadius: 16 }}>
          <div style={{ display: "flex", justifyContent: "space-between", gap: 10, flexWrap: "wrap", alignItems: "center" }}>
            <div>
              <div style={{ fontWeight: 900 }}>Resumo</div>
              <div className="texto-suave">
                Pessoas: <strong>{pessoasOrdenadas.length}</strong> · Famílias: <strong>{familiasOrdenadas.length}</strong>
              </div>
            </div>
            <button className="btn btn-primario" type="button" onClick={loadAll}>
              Atualizar agora
            </button>
          </div>
        </div>

        <div className="card" style={{ padding: 12, borderRadius: 16 }}>
          <div style={{ fontWeight: 900, marginBottom: 6 }}>Dica</div>
          <div className="texto-suave">
            Se aparecer duplicidade (mesmo CPF/NIS) ou família incompleta, volte para <strong>Pessoas</strong> ou <strong>Famílias</strong> e corrija antes de avançar.
          </div>
          <div style={{ display: "flex", gap: 10, flexWrap: "wrap", marginTop: 10 }}>
            <button className="btn btn-secundario" type="button" onClick={() => onSetView("pessoas")}>
              Ir para Pessoas
            </button>
            <button className="btn btn-secundario" type="button" onClick={() => onSetView("familias")}>
              Ir para Famílias
            </button>
            <button className="btn btn-secundario" type="button" onClick={() => onSetView("vinculos")}>
              Ir para Vínculos
            </button>
          </div>
        </div>
      </div>
    </div>
  );

  return (
    <div className="layout-1col">
      <CardMsg />

      {viewKey === "pessoas" ? <PessoasView /> : null}
      {viewKey === "familias" ? <FamiliasView /> : null}
      {viewKey === "vinculos" ? <VinculosView /> : null}
      {viewKey === "atualizacao" ? <AtualizacaoView /> : null}
    </div>
  );
}

// CADASTROS_SUBTABS_HELP_V1
