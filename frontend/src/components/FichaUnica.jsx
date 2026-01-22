import React, { useEffect, useMemo, useState } from "react";
import { getPessoaById, getPessoas, upsertPessoa } from "../domain/pessoasStore.js";
import { canEditarFichaCompleta, canEditarFichaContato, isLeitura } from "../domain/acl.js";
import { createSuasEncaminhamento, getSuasByPessoa, isSuasOverdue } from "../domain/suasEncaminhamentosStore.js";
function fmtDate(iso) {
  if (!iso) return "—";
  try {
    const d = new Date(iso);
    if (Number.isNaN(d.getTime())) return iso;
    return d.toLocaleDateString("pt-BR");
  } catch {
    return iso;
  }
}

function fmtDateTime(iso) {
  if (!iso) return "—";
  try {
    const d = new Date(iso);
    if (Number.isNaN(d.getTime())) return iso;
    return d.toLocaleString("pt-BR");
  } catch {
    return iso;
  }
}

function fmtEndereco(e) {
  if (!e) return "—";
  const parts = [e.logradouro, e.numero, e.bairro, e.cidade, e.uf].filter(Boolean);
  return parts.length ? parts.join(", ") : "—";
}

function digits(v) {
  return String(v || "").replace(/\D/g, "");
}

function deepClone(obj) {
  try {
    return JSON.parse(JSON.stringify(obj));
  } catch {
    return obj;
  }
}

function datePlusDays(days) {
  const d = new Date();
  d.setDate(d.getDate() + (days || 0));
  const yyyy = d.getFullYear();
  const mm = String(d.getMonth() + 1).padStart(2, "0");
  const dd = String(d.getDate()).padStart(2, "0");
  return `${yyyy}-${mm}-${dd}`;
}

export default function FichaUnica({ pessoaId, casos = [], onOpenCaso, usuarioLogado, origemModulo = "CREAS", origemCasoId = null, origemCasoLabel = null, onCreatedSuasEncaminhamento }) {
  const [refresh, setRefresh] = useState(0);
  const [edit, setEdit] = useState(false);
  const [form, setForm] = useState(null);
  // Encaminhamento SUAS direto pela Ficha Única (autoexplicativo)
  const [showSuasNew, setShowSuasNew] = useState(false);
  const [suasDestino, setSuasDestino] = useState("CRAS");
  const [suasPrioridade, setSuasPrioridade] = useState("media");
  const [suasPrazo, setSuasPrazo] = useState("");
  const [suasMotivo, setSuasMotivo] = useState("");
  const [suasMsg, setSuasMsg] = useState("");


  const canFullEdit = useMemo(() => canEditarFichaCompleta(usuarioLogado), [usuarioLogado]);
  const canContactEdit = useMemo(() => canEditarFichaContato(usuarioLogado), [usuarioLogado]);
  const readOnly = useMemo(() => isLeitura(usuarioLogado) || !canContactEdit, [usuarioLogado, canContactEdit]);
  const editFull = edit && canFullEdit;
  const editContact = edit && !canFullEdit && canContactEdit;

  useEffect(() => {
    const onStorage = () => setRefresh((x) => x + 1);
    window.addEventListener("storage", onStorage);
    return () => window.removeEventListener("storage", onStorage);
  }, []);

  useEffect(() => {
    // ao trocar de pessoa, sai do modo edição
    setEdit(false);
    setForm(null);
    // também reseta o encaminhamento SUAS
    setShowSuasNew(false);
    setSuasMotivo("");
    setSuasMsg("");
  }, [pessoaId]);

  const pessoa = useMemo(() => {
    if (!pessoaId) return null;
    return getPessoaById(pessoaId);
  }, [pessoaId, refresh]);

  const totalPessoas = useMemo(() => {
    try {
      return (getPessoas() || []).length;
    } catch {
      return 0;
    }
  }, [refresh]);

  const casosVinculados = useMemo(() => {
    const pid = pessoaId != null ? Number(pessoaId) : null;
    if (!pid || Number.isNaN(pid)) return [];
    return (casos || []).filter((c) => Number(c?.pessoa_id) === pid);
  }, [casos, pessoaId]);

  const encaminhamentosAbertos = useMemo(() => {
    const out = [];
    (casosVinculados || []).forEach((c) => {
      const encs = Array.isArray(c?.encaminhamentos) ? c.encaminhamentos : [];
      encs.forEach((e) => {
        const st = String(e?.status || "").toLowerCase();
        if (st === "concluido" || st === "concluído") return;
        out.push({
          ...e,
          caso_id: c?.id,
          caso_nome: c?.nome,
        });
      });
    });

    // ordena pelo prazo (se existir)
    return out
      .sort((a, b) => {
        const da = a?.prazo_retorno ? new Date(a.prazo_retorno + "T00:00:00").getTime() : 0;
        const db = b?.prazo_retorno ? new Date(b.prazo_retorno + "T00:00:00").getTime() : 0;
        if (da && db) return da - db;
        if (da && !db) return -1;
        if (!da && db) return 1;
        const ca = new Date(a?.criado_em || 0).getTime();
        const cb = new Date(b?.criado_em || 0).getTime();
        return cb - ca;
      })
      .slice(0, 50);
  }, [casosVinculados]);

  const encaminhamentosSuas = useMemo(() => {
    const pid = pessoaId != null ? Number(pessoaId) : null;
    if (!pid || Number.isNaN(pid)) return [];
    const arr = getSuasByPessoa(pid) || [];
    const open = arr.filter((e) => {
      const st = String(e?.status || "").toLowerCase();
      return st && st !== "concluido" && st !== "cancelado";
    });
    // ordena por prazo (primeiro os vencidos)
    open.sort((a, b) => {
      const oa = isSuasOverdue(a) ? 0 : 1;
      const ob = isSuasOverdue(b) ? 0 : 1;
      if (oa !== ob) return oa - ob;
      const da = a?.prazo_retorno ? new Date(a.prazo_retorno + "T00:00:00").getTime() : 0;
      const db = b?.prazo_retorno ? new Date(b.prazo_retorno + "T00:00:00").getTime() : 0;
      if (da && db) return da - db;
      if (da && !db) return -1;
      if (!da && db) return 1;
      const ta = new Date(a?.criado_em || 0).getTime();
      const tb = new Date(b?.criado_em || 0).getTime();
      return tb - ta;
    });
    return open.slice(0, 50);
  }, [pessoaId, refresh]);

  const historico = useMemo(() => {
    const items = [];
    (casosVinculados || []).forEach((c) => {
      const tl = Array.isArray(c?.timeline) ? c.timeline : [];
      tl.forEach((t) => {
        items.push({
          ...t,
          caso_id: c?.id,
          caso_nome: c?.nome,
          _ts: new Date(t?.criado_em || 0).getTime(),
        });
      });
    });
    return items.sort((a, b) => (b._ts || 0) - (a._ts || 0)).slice(0, 120);
  }, [casosVinculados]);

  function startEdit() {
    if (!pessoa) return;
    if (readOnly) {
      alert("Seu perfil não pode editar esta ficha.");
      return;
    }
    setForm(deepClone(pessoa));
    setEdit(true);
  }

  function cancelEdit() {
    setEdit(false);
    setForm(null);
  }

  function saveEdit() {
    if (readOnly) return alert("Seu perfil não pode editar esta ficha.");

    let toSave = null;

    // Edição completa (gestor/técnico)
    if (canFullEdit) {
      if (!form?.nome || !String(form.nome).trim()) return alert("Nome é obrigatório.");
      toSave = {
        ...form,
        nome: String(form.nome).trim(),
        cpf: form.cpf ? digits(form.cpf) : null,
        nis: form.nis ? digits(form.nis) : null,
        telefone: form.telefone || null,
        data_nascimento: form.data_nascimento || null,
        endereco: form.endereco || null,
        membros: Array.isArray(form.membros) ? form.membros.filter((m) => m?.nome) : [],
        observacoes: form.observacoes || null,
      };
    } else {
      // Recepção: só contato/endereço
      toSave = {
        ...(pessoa || {}),
        id: pessoa?.id,
        telefone: form?.telefone || null,
        endereco: form?.endereco || null,
      };
    }

    upsertPessoa(toSave);
    setEdit(false);
    setForm(null);
    setRefresh((x) => x + 1);
    alert(canFullEdit ? "Ficha salva ✅" : "Contato/endereço salvos ✅");
  }

  function msgSuasTemp(t) {
    setSuasMsg(t || "");
    if (!t) return;
    setTimeout(() => setSuasMsg(""), 2500);
  }

  function startSuasNew() {
    if (!canFullEdit) {
      alert("Seu perfil não pode criar encaminhamentos SUAS.");
      return;
    }
    const origem = String(origemModulo || "CREAS").toUpperCase();
    const defDest = origem === "CREAS" ? "CRAS" : "CREAS";
    setSuasDestino(defDest);
    setSuasPrioridade("media");
    setSuasPrazo(datePlusDays(7));
    setSuasMotivo("");
    setShowSuasNew(true);
    setSuasMsg("");
  }

  function cancelSuasNew() {
    setShowSuasNew(false);
    setSuasMotivo("");
    setSuasMsg("");
  }

  function enviarSuas() {
    if (!canFullEdit) return alert("Seu perfil não pode criar encaminhamentos SUAS.");
    if (!pessoa?.id) return;

    const origem = String(origemModulo || "CREAS").toUpperCase();
    const destino = String(suasDestino || "").toUpperCase();
    if (!destino) return msgSuasTemp("Selecione o destino.");
    if (destino === origem) return msgSuasTemp("O destino deve ser outro equipamento (CRAS/CREAS/PopRua).");
    if (!String(suasMotivo || "").trim()) return msgSuasTemp("Informe o motivo (curto).");

    const item = createSuasEncaminhamento(
      {
        pessoa_id: pessoa.id,
        origem_modulo: origem,
        destino_modulo: destino,
        motivo: String(suasMotivo).trim(),
        prioridade: suasPrioridade || "media",
        prazo_retorno: suasPrazo || null,
        origem_caso_id: origemCasoId ?? null,
        origem_caso_label: origemCasoLabel || null,
      },
      usuarioLogado
    );

    try {
      onCreatedSuasEncaminhamento?.(item);
    } catch {}

    setShowSuasNew(false);
    setSuasMotivo("");
    setRefresh((x) => x + 1);
    msgSuasTemp("Encaminhamento SUAS enviado ✅");
  }

  function setField(key, value) {
    setForm((prev) => ({ ...(prev || {}), [key]: value }));
  }

  function setEnderecoField(key, value) {
    setForm((prev) => ({
      ...(prev || {}),
      endereco: { ...(prev?.endereco || {}), [key]: value },
    }));
  }

  function setMembroField(idx, key, value) {
    setForm((prev) => {
      const membros = Array.isArray(prev?.membros) ? [...prev.membros] : [];
      membros[idx] = { ...(membros[idx] || {}), [key]: value };
      return { ...(prev || {}), membros };
    });
  }

  function addMembro() {
    setForm((prev) => {
      const membros = Array.isArray(prev?.membros) ? [...prev.membros] : [];
      membros.push({ nome: "", parentesco: "" });
      return { ...(prev || {}), membros };
    });
  }

  function removeMembro(idx) {
    setForm((prev) => {
      const membros = Array.isArray(prev?.membros) ? [...prev.membros] : [];
      membros.splice(idx, 1);
      return { ...(prev || {}), membros };
    });
  }

  if (!pessoaId) {
    return <div className="texto-suave">Selecione um caso para ver a ficha.</div>;
  }

  if (!pessoa) {
    return (
      <div className="card" style={{ boxShadow: "none", border: "1px solid rgba(2,6,23,.06)" }}>
        <div style={{ fontWeight: 950 }}>Ficha Única não encontrada</div>
        <div className="texto-suave" style={{ marginTop: 6 }}>
          Esta ficha deveria existir. Se estiver em DEMO, recrie os casos em <b>Configurações</b>.
        </div>
      </div>
    );
  }

  const p = edit ? (form || pessoa) : pessoa;

  return (
    <div style={{ display: "grid", gap: 12 }}>
      <div className="card" style={{ boxShadow: "none", border: "1px solid rgba(2,6,23,.06)", padding: 14 }}>
        <div style={{ display: "flex", justifyContent: "space-between", gap: 12, flexWrap: "wrap" }}>
          <div>
            <div style={{ fontWeight: 950, fontSize: 18 }}>Ficha Única — Usuário/Família</div>
            <div className="texto-suave">Uma ficha só (cadastro-mestre) para usar em todos os módulos.</div>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap" }}>
            <div className="texto-suave" style={{ fontWeight: 900 }}>
              ID: <b>{pessoa.id}</b> · Fichas nesta máquina: <b>{totalPessoas}</b>
            </div>
            {!edit ? (
              readOnly ? (
                <div className="texto-suave" style={{ fontWeight: 900 }}>Somente leitura</div>
              ) : (
                <button className="btn btn-secundario" type="button" onClick={startEdit}>
                  {canFullEdit ? "Editar ficha" : "Editar contato"}
                </button>
              )
            ) : (
              <>
                <button className="btn btn-primario" type="button" onClick={saveEdit}>
                  Salvar
                </button>
                <button className="btn btn-secundario" type="button" onClick={cancelEdit}>
                  Cancelar
                </button>
              </>
            )}
          </div>
        </div>

        <div className="texto-suave" style={{ marginTop: 10 }}>
          {edit ? (
            <>
              {editFull ? (
                <>
                  Preencha só o que souber. Se não souber, deixe em branco. O importante é <b>não perder o caso</b>.
                </>
              ) : (
                <>
                  Seu perfil permite editar <b>apenas contato e endereço</b>. O resto é exibido só para consulta.
                </>
              )}
            </>
          ) : (
            <>
              {readOnly ? (
                <>Seu perfil é <b>somente leitura</b>.</>
              ) : (
                <>Dica: clique em <b>{canFullEdit ? "Editar ficha" : "Editar contato"}</b> para atualizar dados.</>
              )}
            </>
          )}
        </div>
      </div>

      {/* Identificação */}
      <div className="card" style={{ boxShadow: "none", border: "1px solid rgba(2,6,23,.06)", padding: 14 }}>
        <div style={{ fontWeight: 950, fontSize: 16 }}>Identificação e contatos</div>
        <div className="texto-suave">Dados mínimos para localizar e atender a pessoa/família.</div>

        {!edit ? (
          <div style={{ marginTop: 12, display: "grid", gridTemplateColumns: "1.2fr 1fr", gap: 12 }}>
            <div>
              <div className="texto-suave" style={{ fontWeight: 900 }}>Nome</div>
              <div style={{ fontWeight: 950, fontSize: 16 }}>{p.nome || "—"}</div>
              <div className="texto-suave" style={{ marginTop: 6 }}>
                CPF: <b>{p.cpf || "—"}</b> · NIS: <b>{p.nis || "—"}</b>
              </div>
              <div className="texto-suave">Telefone: <b>{p.telefone || "—"}</b></div>
              <div className="texto-suave">Nascimento: <b>{p.data_nascimento ? fmtDate(p.data_nascimento) : "—"}</b></div>
            </div>
            <div>
              <div className="texto-suave" style={{ fontWeight: 900 }}>Observações</div>
              <div className="texto-suave" style={{ marginTop: 6 }}>{p.observacoes || "(Sem observações.)"}</div>
              <div className="texto-suave" style={{ marginTop: 10 }}>
                Criado: <b>{fmtDateTime(p.criado_em)}</b>
                <br />
                Atualizado: <b>{fmtDateTime(p.atualizado_em)}</b>
              </div>
            </div>
          </div>
        ) : editFull ? (
          <div style={{ marginTop: 12, display: "grid", gridTemplateColumns: "1.2fr 1fr", gap: 12 }}>
            <div style={{ display: "grid", gap: 10 }}>
              <div>
                <div className="texto-suave" style={{ fontWeight: 900, marginBottom: 6 }}>Nome (obrigatório)</div>
                <input className="input" value={p.nome || ""} onChange={(e) => setField("nome", e.target.value)} placeholder="Nome da pessoa/família" />
              </div>

              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
                <div>
                  <div className="texto-suave" style={{ fontWeight: 900, marginBottom: 6 }}>CPF</div>
                  <input className="input" value={p.cpf || ""} onChange={(e) => setField("cpf", e.target.value)} placeholder="Somente números" />
                </div>
                <div>
                  <div className="texto-suave" style={{ fontWeight: 900, marginBottom: 6 }}>NIS</div>
                  <input className="input" value={p.nis || ""} onChange={(e) => setField("nis", e.target.value)} placeholder="Somente números" />
                </div>
              </div>

              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
                <div>
                  <div className="texto-suave" style={{ fontWeight: 900, marginBottom: 6 }}>Telefone</div>
                  <input className="input" value={p.telefone || ""} onChange={(e) => setField("telefone", e.target.value)} placeholder="(DDD) número" />
                </div>
                <div>
                  <div className="texto-suave" style={{ fontWeight: 900, marginBottom: 6 }}>Nascimento</div>
                  <input className="input" type="date" value={p.data_nascimento ? String(p.data_nascimento).slice(0, 10) : ""} onChange={(e) => setField("data_nascimento", e.target.value)} />
                </div>
              </div>
            </div>

            <div>
              <div className="texto-suave" style={{ fontWeight: 900, marginBottom: 6 }}>Observações</div>
              <textarea className="input" rows={6} value={p.observacoes || ""} onChange={(e) => setField("observacoes", e.target.value)} placeholder="Informações importantes (curto)" />
              <div className="texto-suave" style={{ fontSize: 12, marginTop: 8 }}>
                * Evite informações sensíveis demais. Escreva só o que ajuda a conduzir o caso.
              </div>
            </div>
          </div>
        ) : (
          <div style={{ marginTop: 12, display: "grid", gridTemplateColumns: "1.2fr 1fr", gap: 12 }}>
            <div style={{ display: "grid", gap: 10 }}>
              <div>
                <div className="texto-suave" style={{ fontWeight: 900 }}>Nome</div>
                <div style={{ fontWeight: 950, fontSize: 16 }}>{p.nome || "—"}</div>
                <div className="texto-suave" style={{ marginTop: 6 }}>
                  CPF: <b>{p.cpf || "—"}</b> · NIS: <b>{p.nis || "—"}</b>
                </div>
              </div>

              <div>
                <div className="texto-suave" style={{ fontWeight: 900, marginBottom: 6 }}>Telefone</div>
                <input className="input" value={p.telefone || ""} onChange={(e) => setField("telefone", e.target.value)} placeholder="(DDD) número" />
                <div className="texto-suave" style={{ marginTop: 6 }}>
                  Nascimento: <b>{p.data_nascimento ? fmtDate(p.data_nascimento) : "—"}</b>
                </div>
              </div>
            </div>

            <div>
              <div className="texto-suave" style={{ fontWeight: 900 }}>Observações</div>
              <div className="texto-suave" style={{ marginTop: 6 }}>{p.observacoes || "(Sem observações.)"}</div>
              <div className="texto-suave" style={{ marginTop: 10 }}>
                Criado: <b>{fmtDateTime(p.criado_em)}</b>
                <br />
                Atualizado: <b>{fmtDateTime(p.atualizado_em)}</b>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Endereço */}
      <div className="card" style={{ boxShadow: "none", border: "1px solid rgba(2,6,23,.06)", padding: 14 }}>
        <div style={{ fontWeight: 950, fontSize: 16 }}>Endereço</div>
        <div className="texto-suave">Use o básico. Se não souber, pode deixar em branco.</div>

        {!edit ? (
          <div className="texto-suave" style={{ marginTop: 10 }}>
            <b>{fmtEndereco(p.endereco)}</b>
          </div>
        ) : (
          <div style={{ marginTop: 12, display: "grid", gridTemplateColumns: "1.2fr 200px", gap: 10 }}>
            <div>
              <div className="texto-suave" style={{ fontWeight: 900, marginBottom: 6 }}>Logradouro</div>
              <input className="input" value={p.endereco?.logradouro || ""} onChange={(e) => setEnderecoField("logradouro", e.target.value)} placeholder="Rua/Av." />
            </div>
            <div>
              <div className="texto-suave" style={{ fontWeight: 900, marginBottom: 6 }}>Número</div>
              <input className="input" value={p.endereco?.numero || ""} onChange={(e) => setEnderecoField("numero", e.target.value)} placeholder="Nº" />
            </div>
            <div>
              <div className="texto-suave" style={{ fontWeight: 900, marginBottom: 6 }}>Bairro</div>
              <input className="input" value={p.endereco?.bairro || ""} onChange={(e) => setEnderecoField("bairro", e.target.value)} placeholder="Bairro" />
            </div>
            <div>
              <div className="texto-suave" style={{ fontWeight: 900, marginBottom: 6 }}>Cidade</div>
              <input className="input" value={p.endereco?.cidade || ""} onChange={(e) => setEnderecoField("cidade", e.target.value)} placeholder="Cidade" />
            </div>
            <div>
              <div className="texto-suave" style={{ fontWeight: 900, marginBottom: 6 }}>UF</div>
              <input className="input" value={p.endereco?.uf || ""} onChange={(e) => setEnderecoField("uf", e.target.value)} placeholder="UF" />
            </div>
          </div>
        )}
      </div>

      {/* Família */}
      <div className="card" style={{ boxShadow: "none", border: "1px solid rgba(2,6,23,.06)", padding: 14 }}>
        <div style={{ display: "flex", justifyContent: "space-between", gap: 10, flexWrap: "wrap" }}>
          <div>
            <div style={{ fontWeight: 950, fontSize: 16 }}>Família</div>
            <div className="texto-suave">Composição familiar (simplificada).</div>
          </div>
          {editFull ? (
            <button className="btn btn-secundario" type="button" onClick={addMembro}>
              + Adicionar membro
            </button>
          ) : null}
        </div>

        <div style={{ marginTop: 10, display: "grid", gap: 8 }}>
          {(p.membros || []).length ? (
            (p.membros || []).map((m, idx) => (
              <div key={idx} style={{ display: "grid", gridTemplateColumns: editFull ? "1fr 220px 70px" : "1fr 220px", gap: 10, alignItems: "center" }}>
                {editFull ? (
                  <input className="input" value={m?.nome || ""} onChange={(e) => setMembroField(idx, "nome", e.target.value)} placeholder="Nome" />
                ) : (
                  <div style={{ fontWeight: 900 }}>{m?.nome || "—"}</div>
                )}

                {editFull ? (
                  <input className="input" value={m?.parentesco || ""} onChange={(e) => setMembroField(idx, "parentesco", e.target.value)} placeholder="Parentesco" />
                ) : (
                  <div className="texto-suave" style={{ fontWeight: 900 }}>{m?.parentesco || "—"}</div>
                )}

                {editFull ? (
                  <button className="btn btn-secundario" type="button" onClick={() => removeMembro(idx)}>
                    —
                  </button>
                ) : null}
              </div>
            ))
          ) : (
            <div className="texto-suave">(Sem membros cadastrados.)</div>
          )}
        </div>
      </div>

      {/* Encaminhamentos */}
      <div className="card" style={{ boxShadow: "none", border: "1px solid rgba(2,6,23,.06)", padding: 14 }}>
        <div style={{ fontWeight: 950, fontSize: 16 }}>Rede — encaminhamentos em aberto</div>
        <div className="texto-suave">O que está aguardando retorno (para o gestor cobrar).</div>

        <div style={{ marginTop: 10, display: "grid", gap: 10 }}>
          {encaminhamentosAbertos.length ? (
            encaminhamentosAbertos.map((e) => (
              <div key={e.id} className="card" style={{ padding: 12, boxShadow: "none", border: "1px solid rgba(2,6,23,.06)" }}>
                <div style={{ display: "flex", justifyContent: "space-between", gap: 10 }}>
                  <div style={{ fontWeight: 950 }}>{e.destino || "Rede"}</div>
                  <div className="texto-suave" style={{ fontWeight: 900 }}>{e.status || "aguardando"}</div>
                </div>
                <div className="texto-suave">
                  Prazo: <b>{e.prazo_retorno || "—"}</b> · Caso: <b>{e.caso_nome}</b>
                </div>
                <div style={{ marginTop: 6 }}>{e.motivo || "—"}</div>
              </div>
            ))
          ) : (
            <div className="texto-suave">Nenhum encaminhamento em aberto.</div>
          )}
        </div>

        <div style={{ height: 1, background: "rgba(2,6,23,.06)", margin: "14px 0" }} />

        <div style={{ fontWeight: 950, fontSize: 16 }}>Encaminhamentos SUAS (entre equipamentos)</div>
        <div className="texto-suave">CRAS ⇄ CREAS ⇄ PopRua, com recebimento e contrarreferência.</div>

        {canFullEdit && !readOnly ? (
          <div style={{ marginTop: 10 }}>
            <div className="texto-suave" style={{ marginBottom: 8 }}>
              Use quando precisar pedir ação de outro equipamento. O destino verá em <b>Encaminhamentos SUAS</b>.
            </div>

            {!showSuasNew ? (
              <button className="btn btn-secundario" type="button" onClick={startSuasNew}>
                + Novo encaminhamento SUAS
              </button>
            ) : (
              <div className="card" style={{ padding: 12, marginTop: 10, boxShadow: "none", border: "1px solid rgba(2,6,23,.06)" }}>
                <div style={{ fontWeight: 950 }}>Novo encaminhamento SUAS</div>
                <div className="texto-suave">Preencha só o essencial (motivo + prazo). Depois o destino envia devolutiva.</div>

                <div style={{ marginTop: 10, display: "grid", gap: 10 }}>
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 220px", gap: 10 }}>
                    <div>
                      <div className="texto-suave" style={{ fontWeight: 900, marginBottom: 6 }}>Destino (equipamento)</div>
                      <select className="input" value={suasDestino} onChange={(e) => setSuasDestino(e.target.value)}>
                        <option value="CRAS">CRAS</option>
                        <option value="CREAS">CREAS</option>
                        <option value="POPRUA">PopRua</option>
                      </select>
                    </div>
                    <div>
                      <div className="texto-suave" style={{ fontWeight: 900, marginBottom: 6 }}>Prazo de retorno</div>
                      <input className="input" type="date" value={suasPrazo} onChange={(e) => setSuasPrazo(e.target.value)} />
                    </div>
                  </div>

                  <div>
                    <div className="texto-suave" style={{ fontWeight: 900, marginBottom: 6 }}>Prioridade</div>
                    <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                      <button className={"btn " + (suasPrioridade === "alta" ? "btn-primario" : "btn-secundario")} type="button" onClick={() => setSuasPrioridade("alta")}>Alta</button>
                      <button className={"btn " + (suasPrioridade === "media" ? "btn-primario" : "btn-secundario")} type="button" onClick={() => setSuasPrioridade("media")}>Média</button>
                      <button className={"btn " + (suasPrioridade === "baixa" ? "btn-primario" : "btn-secundario")} type="button" onClick={() => setSuasPrioridade("baixa")}>Baixa</button>
                    </div>
                  </div>

                  <div>
                    <div className="texto-suave" style={{ fontWeight: 900, marginBottom: 6 }}>Motivo (curto)</div>
                    <textarea className="input" rows={3} value={suasMotivo} onChange={(e) => setSuasMotivo(e.target.value)} placeholder="Ex.: Solicito acompanhamento territorial / abordagem no território / atualizar benefícios..." />
                  </div>

                  <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                    <button className="btn btn-primario" type="button" onClick={enviarSuas}>
                      Enviar encaminhamento
                    </button>
                    <button className="btn btn-secundario" type="button" onClick={cancelSuasNew}>
                      Cancelar
                    </button>
                  </div>

                  <div className="texto-suave" style={{ fontSize: 12 }}>
                    Ao enviar, o destino verá em <b>Encaminhamentos SUAS</b> e poderá <b>Receber</b> e enviar devolutiva.
                  </div>
                </div>
              </div>
            )}

            {suasMsg ? (
              <div className="texto-suave" style={{ marginTop: 8 }}><b>{suasMsg}</b></div>
            ) : null}
          </div>
        ) : (
          <div className="texto-suave" style={{ marginTop: 10 }}>
            Seu perfil não pode criar encaminhamentos SUAS (apenas técnico/gestor).
          </div>
        )}


        <div style={{ marginTop: 10, display: "grid", gap: 10 }}>
          {encaminhamentosSuas.length ? (
            encaminhamentosSuas.map((e) => (
              <div key={e.id} className="card" style={{ padding: 12, boxShadow: "none", border: "1px solid rgba(2,6,23,.06)" }}>
                <div style={{ display: "flex", justifyContent: "space-between", gap: 10 }}>
                  <div style={{ fontWeight: 950 }}>
                    {String(e.origem_modulo || "").toUpperCase()} → {String(e.destino_modulo || "").toUpperCase()}
                  </div>
                  <div className="texto-suave" style={{ fontWeight: 900 }}>
                    {isSuasOverdue(e) ? "⚠️ Atrasado" : ""} {String(e.status || "").replace(/_/g, " ")}
                  </div>
                </div>
                <div className="texto-suave">
                  Prazo: <b>{e.prazo_retorno || "—"}</b> · ID: <b>#{e.id}</b>
                </div>
                <div style={{ marginTop: 6 }}>{e.motivo || "—"}</div>
              </div>
            ))
          ) : (
            <div className="texto-suave">Nenhum encaminhamento SUAS em aberto.</div>
          )}
        </div>
      </div>

      {/* Casos vinculados */}
      <div className="card" style={{ boxShadow: "none", border: "1px solid rgba(2,6,23,.06)", padding: 14 }}>
        <div style={{ fontWeight: 950, fontSize: 16 }}>Casos vinculados</div>
        <div className="texto-suave">Lista de casos do usuário/família (neste módulo).</div>
        <div style={{ marginTop: 10, display: "grid", gap: 10 }}>
          {casosVinculados.length ? (
            casosVinculados.map((c) => (
              <button
                key={c.id}
                type="button"
                className="btn btn-secundario"
                style={{ textAlign: "left", justifyContent: "space-between", display: "flex" }}
                onClick={() => onOpenCaso?.(c.id)}
              >
                <div>
                  <div style={{ fontWeight: 950 }}>{c.nome}</div>
                  <div className="texto-suave">
                    Status <b>{c.status}</b> · Etapa <b>{c.etapa_atual}</b> · Resp.: <b>{c.responsavel_nome || "Sem responsável"}</b>
                  </div>
                  <div className="texto-suave">
                    Próximo passo: <b>{c.proximo_passo || "—"}</b> ({fmtDateTime(c.proximo_passo_em)})
                  </div>
                </div>
                <div style={{ fontWeight: 900, opacity: 0.7 }}>→</div>
              </button>
            ))
          ) : (
            <div className="texto-suave">Nenhum caso vinculado encontrado.</div>
          )}
        </div>
      </div>

      {/* Histórico */}
      <div className="card" style={{ boxShadow: "none", border: "1px solid rgba(2,6,23,.06)", padding: 14 }}>
        <div style={{ fontWeight: 950, fontSize: 16 }}>Histórico SUAS</div>
        <div className="texto-suave">Linha do tempo unificada (casos vinculados).</div>
        <div style={{ marginTop: 10, display: "grid", gap: 10 }}>
          {historico.length ? (
            historico.map((t) => (
              <div key={t.id} className="card" style={{ padding: 12, boxShadow: "none", border: "1px solid rgba(2,6,23,.06)" }}>
                <div style={{ fontWeight: 900 }}>{t.texto}</div>
                <div className="texto-suave">
                  {fmtDateTime(t.criado_em)} · {t.por} · Caso: <b>{t.caso_nome}</b>
                </div>
              </div>
            ))
          ) : (
            <div className="texto-suave">Sem histórico ainda.</div>
          )}
        </div>
      </div>

      {/* Documentos (placeholder) */}
      <div className="card" style={{ boxShadow: "none", border: "1px solid rgba(2,6,23,.06)", padding: 14 }}>
        <div style={{ fontWeight: 950, fontSize: 16 }}>Documentos</div>
        <div className="texto-suave">MVP: em breve (upload/arquivos).</div>
      </div>
    </div>
  );
}
