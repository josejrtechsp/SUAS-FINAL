import React, { useEffect, useMemo, useState } from "react";
import "./cras_actions_kebab.css"; // CRAS_ACTIONS_KEBAB_V1
import { rmaCollect } from "./domain/rmaCollector.js";


function fmtDateBR(d) {
  if (!d) return "—";
  try {
    const dt = typeof d === "string" ? new Date(d) : d;
    if (Number.isNaN(dt.getTime())) return String(d);
    return dt.toLocaleDateString();
  } catch {
    return String(d);
  }
}

function todayISO() {
  const d = new Date();
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const dd = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${dd}`;
}

function isOverdue(row) {
  if (!row) return false;
  if (String(row.status || "").toLowerCase() === "concluida") return false;
  if (!row.data_vencimento) return false;
  try {
    const dv = new Date(row.data_vencimento);
    const t = new Date();
    dv.setHours(0, 0, 0, 0);
    t.setHours(0, 0, 0, 0);
    return dv.getTime() < t.getTime();
  } catch {
    return false;
  }
}

function Modal({ open, title, onClose, children }) {
  if (!open) return null;
  return (
    <div
      role="dialog"
      aria-modal="true"
      onMouseDown={(e) => {
        if (e.target === e.currentTarget) onClose?.();
      }}
      style={{
        position: "fixed",
        inset: 0,
        background: "rgba(2,6,23,0.45)",
        display: "grid",
        placeItems: "center",
        padding: 16,
        zIndex: 9999,
      }}
    >
      <div
        className="card"
        style={{
          width: "min(980px, 100%)",
          maxHeight: "85vh",
          overflow: "auto",
          borderRadius: 18,
          padding: 14,
        }}
      >
        <div style={{ display: "flex", justifyContent: "space-between", gap: 10, alignItems: "center" }}>
          <div style={{ fontWeight: 950, fontSize: 16 }}>{title}</div>
          <button className="btn btn-secundario btn-secundario-mini" type="button" onClick={onClose}>
            Fechar
          </button>
        </div>
        <div style={{ marginTop: 12 }}>{children}</div>
      </div>
    </div>
  );
}

export default function TelaCrasTarefas({ apiBase, apiFetch, usuarioLogado, onNavigate, onChanged, municipioId: municipioIdProp, unidadeId: unidadeIdProp, subView = "por_tecnico", onSubViewChange }) {
  const unidadeId = unidadeIdProp != null ? String(unidadeIdProp || "") : (localStorage.getItem("cras_unidade_ativa") || "");
  const municipioId = municipioIdProp != null ? String(municipioIdProp || "") : (localStorage.getItem("cras_municipio_ativo") || "");

  const view = String(subView || "por_tecnico");

  const [usuarios, setUsuarios] = useState([]);
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(false);
  const [erro, setErro] = useState("");
  const [msg, setMsg] = useState("");

  const [fStatus, setFStatus] = useState("");
  const [fResp, setFResp] = useState("");
  const [fVencidas, setFVencidas] = useState(false);
  const [fMinha, setFMinha] = useState(false);


  // CRAS_TAREFAS_SUBVIEWS_V1
  useEffect(() => {
    // sempre limpa mensagens ao trocar de subtela
    setMsg("");
    setErro("");

    if (view === "vencidas") {
      setFStatus("");
      setFResp("");
      setFMinha(false);
      setFVencidas(true);
      return;
    }

    if (view === "por_tecnico") {
      setFStatus("");
      setFResp("");
      setFMinha(false);
      setFVencidas(false);
      return;
    }

    if (view === "metas" || view === "lote") {
      setFStatus("");
      setFResp("");
      setFMinha(false);
      setFVencidas(false);
      return;
    }
  // eslint-disable-next-line
  }, [view]);

  const [openNovo, setOpenNovo] = useState(false);
  const [openEdit, setOpenEdit] = useState(false);
  const [editRow, setEditRow] = useState(null);

  const [batchSel, setBatchSel] = useState({});
  const [batchWorking, setBatchWorking] = useState(false);

  const emptyForm = {
    titulo: "",
    descricao: "",
    prioridade: "media",
    status: "aberta",
    data_vencimento: "",
    responsavel_id: "",
    responsavel_nome: "",
    ref_tipo: "manual",
    ref_id: "",
  };
  const [form, setForm] = useState(emptyForm);

  const usuariosMap = useMemo(() => {
    const m = {};
    (usuarios || []).forEach((u) => {
      if (u?.id != null) m[String(u.id)] = u;
    });
    return m;
  }, [usuarios]);

  const rowsSorted = useMemo(() => {
    const arr = Array.isArray(rows) ? [...rows] : [];
    // vencidas primeiro, depois prioridade, depois data
    const prioRank = { critica: 0, alta: 1, media: 2, baixa: 3 };
    arr.sort((a, b) => {
      const ao = isOverdue(a) ? 0 : 1;
      const bo = isOverdue(b) ? 0 : 1;
      if (ao !== bo) return ao - bo;

      const ap = prioRank[String(a?.prioridade || "media")] ?? 2;
      const bp = prioRank[String(b?.prioridade || "media")] ?? 2;
      if (ap !== bp) return ap - bp;

      const adv = a?.data_vencimento ? new Date(a.data_vencimento).getTime() : 9999999999999;
      const bdv = b?.data_vencimento ? new Date(b.data_vencimento).getTime() : 9999999999999;
      if (adv !== bdv) return adv - bdv;

      return Number(b?.id || 0) - Number(a?.id || 0);
    });
    return arr;
  }, [rows]);

  async function loadUsuarios() {
    try {
      const qs = new URLSearchParams();
      if (municipioId) qs.set("municipio_id", municipioId);
      const r = await apiFetch(`${apiBase}/usuarios?${qs.toString()}`);
      if (!r.ok) return setUsuarios([]);
      const j = await r.json();
      setUsuarios(Array.isArray(j) ? j : []);
    } catch {
      setUsuarios([]);
    }
  }

  async function load() {
    if (!unidadeId) {
      setRows([]);
      return;
    }
    setErro("");
    setMsg("");
    setLoading(true);
    try {
      const qs = new URLSearchParams();
      qs.set("unidade_id", String(unidadeId));
      if (municipioId) qs.set("municipio_id", String(municipioId));

      const status = fStatus || "";
      const resp = fMinha ? String(usuarioLogado?.id || "") : (fResp || "");
      if (status) qs.set("status", status);
      if (resp) qs.set("responsavel_id", resp);
      if (fVencidas) qs.set("vencidas", "true");

      const r = await apiFetch(`${apiBase}/cras/tarefas?${qs.toString()}`);
      if (!r.ok) throw new Error(await r.text());
      const j = await r.json();
      setRows(Array.isArray(j) ? j : []);
    } catch (e) {
      console.error(e);
      setErro("Não foi possível carregar tarefas.");
      setRows([]);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadUsuarios();
    // eslint-disable-next-line
  }, [municipioId]);

  useEffect(() => {
    load();
    // eslint-disable-next-line
  }, [unidadeId, municipioId, fStatus, fResp, fVencidas, fMinha]);

  function openNovoModal() {
    setForm({ ...emptyForm, data_vencimento: "" });
    setOpenNovo(true);
  }

  function openEditModal(row) {
    setEditRow(row);
    setForm({
      titulo: row?.titulo || "",
      descricao: row?.descricao || "",
      prioridade: row?.prioridade || "media",
      status: row?.status || "aberta",
      data_vencimento: row?.data_vencimento || "",
      responsavel_id: row?.responsavel_id != null ? String(row.responsavel_id) : "",
      responsavel_nome: row?.responsavel_nome || "",
      ref_tipo: row?.ref_tipo || "manual",
      ref_id: row?.ref_id != null ? String(row.ref_id) : "",
    });
    setOpenEdit(true);
  }

  function syncResponsavelNome(nextRespId) {
    const u = usuariosMap[String(nextRespId || "")];
    return u?.nome || "";
  }

  async function criar() {
    setMsg("");
    if (!unidadeId) return setMsg("Selecione a Unidade CRAS no cabeçalho.");
    if (!String(form.titulo || "").trim()) return setMsg("Título é obrigatório.");
    if (!String(form.ref_tipo || "").trim()) return setMsg("Ref. tipo é obrigatória.");

    try {
      const respId = form.responsavel_id ? Number(form.responsavel_id) : null;
      const payload = {
        municipio_id: municipioId ? Number(municipioId) : null,
        unidade_id: Number(unidadeId),
        responsavel_id: respId,
        responsavel_nome: respId ? syncResponsavelNome(respId) : (form.responsavel_nome || null),
        ref_tipo: form.ref_tipo || "manual",
        ref_id: form.ref_id ? Number(form.ref_id) : null,
        titulo: String(form.titulo || "").trim(),
        descricao: form.descricao ? String(form.descricao) : null,
        prioridade: form.prioridade || "media",
        status: form.status || "aberta",
        data_vencimento: form.data_vencimento || null,
      };

      const r = await apiFetch(`${apiBase}/cras/tarefas`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!r.ok) throw new Error(await r.text());
      setMsg("Tarefa criada ✅");
      setOpenNovo(false);
      await load();
      onChanged?.();
    } catch (e) {
      console.error(e);
      setMsg("Erro ao criar tarefa.");
    }
  }

  async function salvarEdicao() {
    if (!editRow?.id) return;
    setMsg("");
    try {
      const respId = form.responsavel_id ? Number(form.responsavel_id) : null;
      const patch = {
        titulo: String(form.titulo || "").trim(),
        descricao: form.descricao ? String(form.descricao) : null,
        prioridade: form.prioridade || "media",
        status: form.status || "aberta",
        data_vencimento: form.data_vencimento || null,
        responsavel_id: respId,
        responsavel_nome: respId ? syncResponsavelNome(respId) : (form.responsavel_nome || null),
        ref_tipo: form.ref_tipo || "manual",
        ref_id: form.ref_id ? Number(form.ref_id) : null,
      };

      const r = await apiFetch(`${apiBase}/cras/tarefas/${editRow.id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(patch),
      });
      if (!r.ok) throw new Error(await r.text());
      setMsg("Atualizado ✅");
      setOpenEdit(false);
      setEditRow(null);
      await load();
      onChanged?.();
    } catch (e) {
      console.error(e);
      setMsg("Erro ao salvar edição.");
    }
  }

  async function concluir(row) {
    if (!row?.id) return;
    try {
      const r = await apiFetch(`${apiBase}/cras/tarefas/${row.id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: "concluida" }),
      });
      if (!r.ok) throw new Error(await r.text());
      setMsg("Concluída ✅");
      // RMA_COLLECT_V1 TAREFA_CONCLUIR
      try {
        await rmaCollect({
          apiBase,
          apiFetch,
          servico: "TAREFA",
          acao: "concluir",
          unidade_id: (typeof unidadeId !== "undefined" && unidadeId) ? Number(unidadeId) : null,
          alvo_tipo: "tarefa",
          alvo_id: row?.id ?? null,
          meta: { responsavel_id: row?.responsavel_id ?? null },
        });
      } catch {}
      await load();
      onChanged?.();
    } catch (e) {
      console.error(e);
      setMsg("Erro ao concluir.");
    }
  }

  async function concluirSelecionadas(ids) {
    const list = Array.isArray(ids) ? ids.filter(Boolean) : [];
    if (!list.length) return;
    setBatchWorking(true);
    setMsg("");
    try {
      const erros = [];
      for (const id of list) {
        const r = await apiFetch(`${apiBase}/cras/tarefas/${id}`, {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ status: "concluida" }),
        });
        if (!r.ok) {
          const t = await r.text().catch(() => "");
          erros.push(`#${id}` + (t ? ` (${t})` : ""));
        }
      }
      if (erros.length) {
        setMsg(`Concluídas com avisos: ${erros.length} falharam.`);
      } else {
        setMsg(`Concluídas ✅ (${list.length})`);
      }
      setBatchSel({});
      await load();
      onChanged?.();
    } catch (e) {
      console.error(e);
      setMsg("Erro ao concluir em lote.");
    } finally {
      setBatchWorking(false);
    }
  }


  async function excluir(row) {
    if (!row?.id) return;
    if (!window.confirm(`Excluir tarefa #${row.id}?`)) return;
    try {
      const r = await apiFetch(`${apiBase}/cras/tarefas/${row.id}`, { method: "DELETE" });
      if (!r.ok) throw new Error(await r.text());
      setMsg("Excluída ✅");
      await load();
      onChanged?.();
    } catch (e) {
      console.error(e);
      setMsg("Erro ao excluir.");
    }
  }

  function abrirReferencia(row) {
    const tipo = String(row?.ref_tipo || "").toLowerCase();
    const id = row?.ref_id != null ? Number(row.ref_id) : null;
    if (!tipo) return;

    // Navegação básica: você pode ampliar depois por tipo
    if (tipo === "caso") {
      onNavigate?.({ tab: "casos" });
      return;
    }
    if (tipo === "cadunico") {
      onNavigate?.({ tab: "cadunico" });
      return;
    }
    if (tipo === "scfv") {
      onNavigate?.({ tab: "scfv", focus: { turmaId: id || null, mes: ymNow(), limite: 3, presMin: 75, auto: true, scrollRel: true } });
      return;
    }
    if (tipo === "ficha") {
      onNavigate?.({ tab: "ficha" });
      return;
    }
    // manual/outros
  }

  function ymNow() {
    const d = new Date();
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`;
  }

  const counts = useMemo(() => {
    const total = rowsSorted.length;
    const venc = rowsSorted.filter((r) => isOverdue(r)).length;
    const abertas = rowsSorted.filter((r) => String(r.status || "") !== "concluida").length;
    return { total, venc, abertas };
  }, [rowsSorted]);

  const tecnicos = useMemo(() => {
    const map = new Map();
    (rowsSorted || []).forEach((r) => {
      const respId = r?.responsavel_id;
      if (respId == null) return;
      if (String(r.status || "").toLowerCase() === "concluida") return;
      const key = String(respId);
      const nome = r?.responsavel_nome || usuariosMap[key]?.nome || `ID ${key}`;
      const cur = map.get(key) || { id: key, nome, total: 0, vencidas: 0 };
      cur.total += 1;
      if (isOverdue(r)) cur.vencidas += 1;
      map.set(key, cur);
    });
    const arr = Array.from(map.values());
    arr.sort((a, b) => (b.vencidas - a.vencidas) || (b.total - a.total) || String(a.nome).localeCompare(String(b.nome)));
    return arr;
  }, [rowsSorted, usuariosMap]);


  return (
    <div className="layout-1col">
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


      {view === "metas" ? (

      <div className="card" style={{ padding: 12, borderRadius: 18 }}>
        <div style={{ display: "flex", justifyContent: "space-between", gap: 10, flexWrap: "wrap", alignItems: "center" }}>
          <div>
            <div style={{ fontWeight: 950 }}>Metas e visão de equipe</div>
            <div className="texto-suave">
              Total: <strong>{counts.total}</strong> · Abertas: <strong>{counts.abertas}</strong> · Vencidas:{" "}
              <strong style={{ color: counts.venc ? "rgba(220,38,38,.95)" : "inherit" }}>{counts.venc}</strong>
            </div>
          </div>

          <div style={{ display: "flex", gap: 10, flexWrap: "wrap", alignItems: "center" }}>
            <button className="btn btn-primario" type="button" onClick={openNovoModal}>
              Nova tarefa
            </button>
            <button className="btn btn-secundario" type="button" onClick={load}>
              Atualizar
            </button>
          </div>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: 10, marginTop: 12 }}>
          <div className="card" style={{ padding: 12, borderRadius: 16 }}>
            <div className="texto-suave">Abertas</div>
            <div style={{ fontSize: 22, fontWeight: 950 }}>{counts.abertas}</div>
          </div>

          <div className="card" style={{ padding: 12, borderRadius: 16, border: counts.venc ? "1px solid rgba(220,38,38,.22)" : undefined, background: counts.venc ? "rgba(254,242,242,.55)" : undefined }}>
            <div className="texto-suave">Vencidas</div>
            <div style={{ fontSize: 22, fontWeight: 950, color: counts.venc ? "rgba(220,38,38,.95)" : "inherit" }}>{counts.venc}</div>
          </div>

          <div className="card" style={{ padding: 12, borderRadius: 16 }}>
            <div className="texto-suave">Total (carregado)</div>
            <div style={{ fontSize: 22, fontWeight: 950 }}>{counts.total}</div>
          </div>
        </div>

        <div style={{ marginTop: 12 }}>
          <div style={{ fontWeight: 950, marginBottom: 8 }}>Fila por técnico (abertas)</div>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: 10 }}>
            {(tecnicos || []).slice(0, 12).map((t) => (
              <div key={t.id} className="card" style={{ padding: 12, borderRadius: 16 }}>
                <div style={{ fontWeight: 950 }}>{t.nome}</div>
                <div className="texto-suave" style={{ marginTop: 4 }}>
                  Abertas: <b>{t.total}</b> · Vencidas: <b style={{ color: t.vencidas ? "rgba(220,38,38,.95)" : "inherit" }}>{t.vencidas}</b>
                </div>
              </div>
            ))}
            {!tecnicos?.length ? <div className="texto-suave">Sem dados para metas (nenhuma tarefa aberta).</div> : null}
          </div>
        </div>
      </div>

      ) : view === "lote" ? (

      <div className="card" style={{ padding: 12, borderRadius: 18 }}>
        <div style={{ display: "flex", justifyContent: "space-between", gap: 10, flexWrap: "wrap", alignItems: "center" }}>
          <div>
            <div style={{ fontWeight: 950 }}>Concluir em lote</div>
            <div className="texto-suave">Selecione tarefas abertas e conclua de uma vez.</div>
          </div>

          <div style={{ display: "flex", gap: 10, flexWrap: "wrap", alignItems: "center" }}>
            <button className="btn btn-primario" type="button" onClick={openNovoModal}>
              Nova tarefa
            </button>
            <button className="btn btn-secundario" type="button" onClick={load}>
              Atualizar
            </button>
          </div>
        </div>

        <div style={{ display: "flex", gap: 10, flexWrap: "wrap", alignItems: "center", marginTop: 12 }}>
          <button
            className="btn btn-secundario"
            type="button"
            onClick={() => {
              const next = {};
              rowsSorted
                .filter((r) => String(r.status || "").toLowerCase() !== "concluida")
                .slice(0, 200)
                .forEach((r) => {
                  next[String(r.id)] = true;
                });
              setBatchSel(next);
            }}
            disabled={batchWorking}
          >
            Selecionar (até 200)
          </button>

          <button className="btn btn-secundario" type="button" onClick={() => setBatchSel({})} disabled={batchWorking}>
            Limpar seleção
          </button>

          <button
            className="btn btn-primario"
            type="button"
            onClick={() => {
              const ids = Object.keys(batchSel).filter((k) => batchSel[k]).map((k) => Number(k)).filter((n) => Number.isFinite(n));
              if (!ids.length) return setMsg("Selecione ao menos uma tarefa.");
              if (!window.confirm(`Concluir ${ids.length} tarefas?`)) return;
              concluirSelecionadas(ids);
            }}
            disabled={batchWorking}
          >
            Concluir selecionadas
          </button>

          <div className="texto-suave">
            Selecionadas: <b>{Object.keys(batchSel).filter((k) => batchSel[k]).length}</b>
          </div>

          {batchWorking ? <div className="texto-suave">Processando…</div> : null}
        </div>

        <div style={{ marginTop: 12, display: "grid", gap: 8 }}>
          {rowsSorted
            .filter((r) => String(r.status || "").toLowerCase() !== "concluida")
            .slice(0, 400)
            .map((r) => {
              const checked = !!batchSel[String(r.id)];
              const overdue = isOverdue(r);
              return (
                <label
                  key={r.id}
                  className="card"
                  style={{
                    padding: 10,
                    borderRadius: 14,
                    display: "flex",
                    gap: 10,
                    alignItems: "flex-start",
                    border: checked ? "2px solid rgba(59,130,246,.35)" : overdue ? "1px solid rgba(220,38,38,.22)" : "1px solid rgba(226,232,240,.92)",
                    background: checked ? "rgba(239,246,255,.55)" : overdue ? "rgba(254,242,242,.55)" : "rgba(255,255,255,.92)",
                    cursor: "pointer",
                  }}
                >
                  <input
                    type="checkbox"
                    checked={checked}
                    onChange={(e) => {
                      const v = e.target.checked;
                      setBatchSel((prev) => ({ ...(prev || {}), [String(r.id)]: v }));
                    }}
                    style={{ marginTop: 4 }}
                  />
                  <div style={{ minWidth: 0 }}>
                    <div style={{ fontWeight: 950 }}>
                      #{r.id} · {r.titulo}
                    </div>
                    <div className="texto-suave" style={{ marginTop: 4 }}>
                      Resp.: {r.responsavel_nome || "—"} · Venc.:{" "}
                      <b style={{ color: overdue ? "rgba(220,38,38,.95)" : "inherit" }}>{fmtDateBR(r.data_vencimento)}</b>
                      {" · "}Ref.: {r.ref_tipo}
                      {r.ref_id != null ? ` #${r.ref_id}` : ""}
                    </div>
                  </div>
                </label>
              );
            })}

          {!rowsSorted.filter((r) => String(r.status || "").toLowerCase() !== "concluida").length ? (
            <div className="texto-suave">Nenhuma tarefa aberta.</div>
          ) : null}
        </div>
      </div>

      ) : (

      <div className="card" style={{ padding: 12, borderRadius: 18 }}>
        <div style={{ display: "flex", justifyContent: "space-between", gap: 10, flexWrap: "wrap", alignItems: "center" }}>
          <div>
            <div style={{ fontWeight: 950 }}>
              {view === "vencidas" ? "Tarefas vencidas" : "Tarefas por técnico"}
            </div>
            <div className="texto-suave">
              Total: <strong>{counts.total}</strong> · Abertas: <strong>{counts.abertas}</strong> · Vencidas: <strong style={{ color: counts.venc ? "rgba(220,38,38,.95)" : "inherit" }}>{counts.venc}</strong>
            </div>
          </div>

          <div style={{ display: "flex", gap: 10, flexWrap: "wrap", alignItems: "center" }}>
            <button className="btn btn-primario" type="button" onClick={openNovoModal}>
              Nova tarefa
            </button>
            <button className="btn btn-secundario" type="button" onClick={load}>
              Atualizar
            </button>
          </div>
        </div>

        {/* Por técnico: escolha um responsável e veja a lista (1 subtela por vez) */}
        {view === "por_tecnico" ? (
          <div style={{ marginTop: 12 }}>
            {!fResp && !fMinha ? (
              <>
                <div className="texto-suave" style={{ marginBottom: 8 }}>
                  Selecione um técnico para ver a fila. (As tarefas sem responsável aparecem na lista completa em “Metas”.)
                </div>

                <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: 10 }}>
                  {(tecnicos || []).map((t) => (
                    <button
                      key={t.id}
                      type="button"
                      className="card"
                      style={{
                        padding: 12,
                        borderRadius: 16,
                        textAlign: "left",
                        cursor: "pointer",
                        border: t.vencidas ? "1px solid rgba(220,38,38,.22)" : "1px solid rgba(226,232,240,.92)",
                        background: t.vencidas ? "rgba(254,242,242,.55)" : "rgba(255,255,255,.92)",
                      }}
                      onClick={() => setFResp(String(t.id))}
                    >
                      <div style={{ fontWeight: 950 }}>{t.nome}</div>
                      <div className="texto-suave" style={{ marginTop: 4 }}>
                        Abertas: <b>{t.total}</b> · Vencidas: <b style={{ color: t.vencidas ? "rgba(220,38,38,.95)" : "inherit" }}>{t.vencidas}</b>
                      </div>
                    </button>
                  ))}

                  {!tecnicos?.length ? (
                    <div className="texto-suave">Nenhuma tarefa aberta para agrupar por técnico.</div>
                  ) : null}
                </div>
              </>
            ) : (
              <div style={{ display: "flex", justifyContent: "space-between", gap: 10, flexWrap: "wrap", alignItems: "center" }}>
                <div>
                  <div className="texto-suave">Você está vendo a fila do responsável:</div>
                  <div style={{ fontWeight: 950, fontSize: 14 }}>
                    {usuariosMap[String(fResp)]?.nome || rowsSorted?.[0]?.responsavel_nome || `ID ${String(fResp)}`}
                  </div>
                </div>
                <button
                  className="btn btn-secundario"
                  type="button"
                  onClick={() => {
                    setFResp("");
                    setFMinha(false);
                  }}
                >
                  Trocar técnico
                </button>
              </div>
            )}
          </div>
        ) : null}

        {/* Vencidas: visão direta (sem filtros duplicados) */}
        {view === "vencidas" ? (
          <div className="texto-suave" style={{ marginTop: 12 }}>
            Mostrando apenas tarefas vencidas (SLA).
          </div>
        ) : null}


        {loading ? <div className="texto-suave" style={{ marginTop: 12 }}>Carregando…</div> : null}

        {(view === "vencidas" || (view === "por_tecnico" && (fResp || fMinha))) ? (
        <div style={{ marginTop: 12, overflow: "auto" }}>
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr>
                {[
                  "#",
                  "Título",
                  "Responsável",
                  "Prioridade",
                  "Status",
                  "Vencimento",
                  "Ref.",
                  "Ações",
                ].map((h) => (
                  <th key={h} style={{ textAlign: "left", padding: 8, borderBottom: "1px solid rgba(2,6,23,.10)" }}>
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rowsSorted.map((r) => {
                const overdue = isOverdue(r);
                return (
                  <tr key={r.id} style={{ background: overdue ? "rgba(239,68,68,.06)" : "transparent" }}>
                    <td style={{ padding: 8, borderBottom: "1px solid rgba(2,6,23,.06)" }}>
                      <strong>#{r.id}</strong>
                    </td>
                    <td style={{ padding: 8, borderBottom: "1px solid rgba(2,6,23,.06)" }}>
                      <div style={{ fontWeight: 900 }}>{r.titulo}</div>
                      {r.descricao ? <div className="texto-suave" style={{ marginTop: 4, maxWidth: 520 }}>{r.descricao}</div> : null}
                    </td>
                    <td style={{ padding: 8, borderBottom: "1px solid rgba(2,6,23,.06)" }}>
                      {r.responsavel_nome || "—"}
                      {r.responsavel_id ? <div className="texto-suave">ID: {r.responsavel_id}</div> : null}
                    </td>
                    <td style={{ padding: 8, borderBottom: "1px solid rgba(2,6,23,.06)" }}>{r.prioridade}</td>
                    <td style={{ padding: 8, borderBottom: "1px solid rgba(2,6,23,.06)" }}>{r.status}</td>
                    <td style={{ padding: 8, borderBottom: "1px solid rgba(2,6,23,.06)" }}>
                      <span style={{ color: overdue ? "rgba(220,38,38,.95)" : "inherit", fontWeight: overdue ? 900 : 700 }}>
                        {fmtDateBR(r.data_vencimento)}
                      </span>
                      {r.data_conclusao ? <div className="texto-suave">Concl.: {fmtDateBR(r.data_conclusao)}</div> : null}
                    </td>
                    <td style={{ padding: 8, borderBottom: "1px solid rgba(2,6,23,.06)" }}>
                      <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                        <span className="texto-suave">
                          {r.ref_tipo}{r.ref_id != null ? ` #${r.ref_id}` : ""}
                        </span>
                        <button className="btn btn-secundario btn-secundario-mini" type="button" onClick={() => abrirReferencia(r)}>
                          Abrir
                        </button>
                      </div>
                    </td>
                    <td style={{ padding: 8, borderBottom: "1px solid rgba(2,6,23,.06)" }}>
                      <div className="cras-actions-cell">
                        {String(r.status || "") !== "concluida" ? (
                          <button className="btn btn-primario btn-primario-mini" type="button" onClick={() => concluir(r)}>
                            Concluir
                          </button>
                        ) : null}

                        <details className="cras-actions-menu">
                          <summary className="cras-actions-kebab" aria-label="Mais ações">⋯</summary>
                          <div className="cras-actions-pop">
                            <button
                              className="btn btn-secundario btn-secundario-mini"
                              type="button"
                              onClick={(e) => {
                                openEditModal(r);
                                const d = e.currentTarget && e.currentTarget.closest("details");
                                if (d) d.removeAttribute("open");
                              }}
                            >
                              Editar
                            </button>
                            <button
                              className="btn btn-secundario btn-secundario-mini"
                              type="button"
                              onClick={(e) => {
                                excluir(r);
                                const d = e.currentTarget && e.currentTarget.closest("details");
                                if (d) d.removeAttribute("open");
                              }}
                            >
                              Excluir
                            </button>
                          </div>
                        </details>
                      </div>
                    </td>
                  </tr>
                );
              })}

              {!rowsSorted.length ? (
                <tr>
                  <td colSpan={8} className="texto-suave" style={{ padding: 10 }}>
                    Nenhuma tarefa no filtro.
                  </td>
                </tr>
              ) : null}
            </tbody>
          </table>
        </div>
        ) : null}
      </div>
      )}


      <Modal open={openNovo} title="Nova tarefa" onClose={() => setOpenNovo(false)}>
        <FormTarefa
          form={form}
          setForm={setForm}
          usuarios={usuarios}
          onCancel={() => setOpenNovo(false)}
          onSubmit={criar}
          submitLabel="Criar"
        />
      </Modal>

      <Modal open={openEdit} title={editRow ? `Editar tarefa #${editRow.id}` : "Editar tarefa"} onClose={() => setOpenEdit(false)}>
        <FormTarefa
          form={form}
          setForm={setForm}
          usuarios={usuarios}
          onCancel={() => setOpenEdit(false)}
          onSubmit={salvarEdicao}
          submitLabel="Salvar"
          showQuickDue
        />
      </Modal>
    </div>
  );
}

function FormTarefa({ form, setForm, usuarios, onCancel, onSubmit, submitLabel, showQuickDue }) {
  return (
    <div style={{ display: "grid", gap: 10 }}>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
        <input
          className="input"
          placeholder="Título (obrigatório)"
          value={form.titulo}
          onChange={(e) => setForm((s) => ({ ...s, titulo: e.target.value }))}
        />

        <select
          className="input"
          value={form.prioridade}
          onChange={(e) => setForm((s) => ({ ...s, prioridade: e.target.value }))}
        >
          <option value="baixa">Prioridade: baixa</option>
          <option value="media">Prioridade: média</option>
          <option value="alta">Prioridade: alta</option>
          <option value="critica">Prioridade: crítica</option>
        </select>
      </div>

      <textarea
        className="input"
        style={{ minHeight: 92 }}
        placeholder="Descrição (opcional)"
        value={form.descricao}
        onChange={(e) => setForm((s) => ({ ...s, descricao: e.target.value }))}
      />

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 10 }}>
        <select className="input" value={form.status} onChange={(e) => setForm((s) => ({ ...s, status: e.target.value }))}>
          <option value="aberta">Status: aberta</option>
          <option value="em_andamento">Status: em andamento</option>
          <option value="concluida">Status: concluída</option>
          <option value="cancelada">Status: cancelada</option>
        </select>

        <input
          type="date"
          className="input"
          value={form.data_vencimento || ""}
          onChange={(e) => setForm((s) => ({ ...s, data_vencimento: e.target.value }))}
        />

        <select
          className="input"
          value={form.responsavel_id}
          onChange={(e) => {
            const id = e.target.value;
            const u = (usuarios || []).find((x) => String(x.id) === String(id));
            setForm((s) => ({ ...s, responsavel_id: id, responsavel_nome: u?.nome || "" }));
          }}
        >
          <option value="">Responsável (opcional)…</option>
          {(usuarios || []).map((u) => (
            <option key={u.id} value={String(u.id)}>
              {u.nome} ({u.perfil})
            </option>
          ))}
        </select>
      </div>

      {showQuickDue ? (
        <div className="texto-suave" style={{ display: "flex", gap: 10, flexWrap: "wrap", alignItems: "center" }}>
          Atalhos de vencimento:
          <button
            type="button"
            className="btn btn-secundario btn-secundario-mini"
            onClick={() => setForm((s) => ({ ...s, data_vencimento: todayISO() }))}
          >
            Hoje
          </button>
          <button
            type="button"
            className="btn btn-secundario btn-secundario-mini"
            onClick={() => {
              const d = new Date();
              d.setDate(d.getDate() + 7);
              const y = d.getFullYear();
              const m = String(d.getMonth() + 1).padStart(2, "0");
              const dd = String(d.getDate()).padStart(2, "0");
              setForm((s) => ({ ...s, data_vencimento: `${y}-${m}-${dd}` }));
            }}
          >
            +7 dias
          </button>
        </div>
      ) : null}

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
        <select
          className="input"
          value={form.ref_tipo}
          onChange={(e) => setForm((s) => ({ ...s, ref_tipo: e.target.value }))}
        >
          <option value="manual">Ref.: manual</option>
          <option value="caso">Ref.: caso</option>
          <option value="cadunico">Ref.: CadÚnico</option>
          <option value="scfv">Ref.: SCFV</option>
          <option value="programa">Ref.: programa</option>
          <option value="ficha">Ref.: ficha</option>
          <option value="encaminhamento">Ref.: encaminhamento</option>
        </select>

        <input
          className="input"
          placeholder="Ref. ID (opcional, ex: 123)"
          value={form.ref_id}
          onChange={(e) => setForm((s) => ({ ...s, ref_id: e.target.value }))}
        />
      </div>

      <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
        <button className="btn btn-primario" type="button" onClick={onSubmit}>
          {submitLabel || "Salvar"}
        </button>
        <button className="btn btn-secundario" type="button" onClick={onCancel}>
          Cancelar
        </button>
      </div>
    </div>
  );
}
