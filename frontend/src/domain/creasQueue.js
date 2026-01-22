// frontend/src/domain/creasQueue.js
// Fila inteligente (MVP local): prioridade e motivos (determinístico, sem IA).

import { getCreasEtapasDef } from "./creasStore.js";

const MS_DAY = 1000 * 60 * 60 * 24;

function safeTime(iso) {
  if (!iso) return 0;
  const t = new Date(iso).getTime();
  return Number.isFinite(t) ? t : 0;
}

function daysSince(iso) {
  if (!iso) return 0;
  const ms = Date.now() - safeTime(iso);
  return Math.max(0, Math.floor(ms / MS_DAY));
}

function daysOverdueIso(iso) {
  if (!iso) return null;
  const t = safeTime(iso);
  if (!t) return null;
  const diff = Date.now() - t;
  return diff <= 0 ? 0 : Math.floor(diff / MS_DAY);
}

function daysOverdueDateStr(dateStr) {
  if (!dateStr) return null;
  return daysOverdueIso(String(dateStr) + "T23:59:59");
}

function parseEtapaFromTexto(texto) {
  const s = String(texto || "");
  const m = s.match(/Etapa\s+atual:\s*([a-zA-Z0-9_-]+)/i);
  return m ? m[1] : null;
}

function findEtapaStartIso(c, etapaCodigo) {
  const tl = Array.isArray(c?.timeline) ? c.timeline : [];
  for (const e of tl) {
    if (String(e?.tipo || "") !== "etapa") continue;
    const code = parseEtapaFromTexto(e?.texto);
    if (!code) continue;
    if (String(code) === String(etapaCodigo)) return e?.criado_em || null;
  }
  return null;
}

function computeStageSlaOverdue(c) {
  const etapa = String(c?.etapa_atual || "entrada");
  const def = (getCreasEtapasDef() || []).find((x) => String(x?.codigo) === etapa);
  const sla = def?.sla_dias != null ? Number(def.sla_dias) : null;
  if (!sla || !Number.isFinite(sla) || sla <= 0) return null;

  const startIso =
    findEtapaStartIso(c, etapa) || c?.ultimo_registro_em || c?.criado_em || c?.atualizado_em || null;
  if (!startIso) return null;

  const startT = safeTime(startIso);
  if (!startT) return null;

  const dueT = startT + sla * MS_DAY;
  const diff = Date.now() - dueT;
  const overdueDays = diff <= 0 ? 0 : Math.floor(diff / MS_DAY);

  return {
    etapa,
    sla,
    startIso,
    dueIso: new Date(dueT).toISOString(),
    overdueDays,
  };
}

function computeProximoPassoOverdue(c) {
  const iso = c?.proximo_passo_em;
  if (!iso) return null;
  const t = safeTime(iso);
  if (!t) return null;
  const diff = Date.now() - t;
  const overdueDays = diff <= 0 ? 0 : Math.floor(diff / MS_DAY);
  const vencido = diff >= 0;
  return { iso, overdueDays, vencido };
}

function computeSemMovimento(c) {
  const last = c?.ultimo_registro_em || c?.atualizado_em || c?.criado_em || null;
  const days = daysSince(last);
  const risco = String(c?.risco || "medio").toLowerCase();
  const limite = risco === "alto" ? 7 : 14;
  const flagged = days >= limite;
  return { days, limite, flagged, excesso: flagged ? days - limite : 0 };
}

function computeRedeOverdue(c) {
  const encs = Array.isArray(c?.encaminhamentos) ? c.encaminhamentos : [];
  let maxDays = 0;
  let worst = null;
  for (const e of encs) {
    if (String(e?.status || "") !== "aguardando") continue;
    const prazo = e?.prazo_retorno;
    if (!prazo) continue;
    const d = daysOverdueDateStr(prazo);
    if (d == null) continue;
    if (d > maxDays) {
      maxDays = d;
      worst = e;
    }
  }
  if (!worst || maxDays <= 0) return null;
  return {
    overdueDays: maxDays,
    destino: worst?.destino || "Rede",
    prazo: worst?.prazo_retorno || null,
  };
}

function addReason(reasons, flags, label, detail, weight, flagKey) {
  reasons.push({ label, detail, weight });
  if (flagKey) flags[flagKey] = true;
  return weight;
}

export function computeCreasQueueItemForCase(c, { gestor = false } = {}) {
  if (!c || String(c?.status || "") !== "ativo") return null;

  const reasons = [];
  const flags = {};
  let score = 0;

  const risco = String(c?.risco || "medio").toLowerCase();
  if (risco === "alto") {
    score += addReason(reasons, flags, "Risco alto", "Prioridade", 30, "risco_alto");
  } else if (risco === "medio") {
    score += addReason(reasons, flags, "Risco médio", "Atenção", 12, "risco_medio");
  }

  if (!c?.responsavel_id) {
    score += addReason(reasons, flags, "Sem responsável", "Assuma/atribua o caso", 28, "sem_responsavel");
  }

  const encSt = String(c?.encerramento_status || "").toLowerCase();
  if (gestor && encSt === "solicitado") {
    score += addReason(reasons, flags, "Encerramento pendente", "Aprovar/recusar", 40, "encerramento");
  }

  const prox = computeProximoPassoOverdue(c);
  if (prox && prox.vencido) {
    const extra = Math.min(30, prox.overdueDays * 4);
    score += addReason(
      reasons,
      flags,
      "Próximo passo vencido",
      `${c?.proximo_passo || "—"} (+${prox.overdueDays}d)`,
      25 + extra,
      "proximo_passo"
    );
  }

  const semMov = computeSemMovimento(c);
  if (semMov.flagged) {
    const extra = Math.min(25, semMov.excesso * 2);
    score += addReason(
      reasons,
      flags,
      "Sem movimento",
      `${semMov.days} dias (limite ${semMov.limite})`,
      15 + extra,
      "sem_movimento"
    );
  }

  const rede = computeRedeOverdue(c);
  if (rede) {
    const extra = Math.min(24, rede.overdueDays * 3);
    score += addReason(
      reasons,
      flags,
      "Rede sem retorno",
      `${rede.destino} (+${rede.overdueDays}d)`,
      18 + extra,
      "rede"
    );
  }

  const stage = computeStageSlaOverdue(c);
  if (stage && stage.overdueDays > 0) {
    const extra = Math.min(40, stage.overdueDays * 5);
    score += addReason(
      reasons,
      flags,
      "SLA da etapa vencido",
      `${stage.etapa} (SLA ${stage.sla}d, +${stage.overdueDays}d)`,
      22 + extra,
      "sla_etapa"
    );
  }

  // micro ajuste (prioriza levemente casos muito parados)
  const last = c?.ultimo_registro_em || c?.atualizado_em || c?.criado_em || null;
  const idle = daysSince(last);
  score += Math.min(10, Math.floor(idle / 7));

  const updatedIso = last || c?.criado_em || null;

  const tags = [];
  if (flags.risco_alto) tags.push("RISCO ALTO");
  if (flags.sem_responsavel) tags.push("SEM RESPONSÁVEL");
  if (flags.encerramento) tags.push("ENCERRAMENTO");
  if (flags.sla_etapa && stage?.overdueDays) tags.push(`SLA +${stage.overdueDays}d`);
  if (flags.proximo_passo && prox?.overdueDays != null) tags.push(`PRÓXIMO +${prox.overdueDays}d`);
  if (flags.rede && rede?.overdueDays) tags.push(`REDE +${rede.overdueDays}d`);
  if (flags.sem_movimento && semMov?.days != null) tags.push(`SEM MOV ${semMov.days}d`);

  const etapa = String(c?.etapa_atual || "entrada");
  const proximo = c?.proximo_passo || "—";

  return {
    kind: "case",
    casoId: c?.id,
    etapaCodigo: String(c?.etapa_atual || "").trim(),
    responsavelNome: c?.responsavel_nome ? String(c.responsavel_nome) : "",
    risco: String(c?.risco || "").toLowerCase(),
    score,
    title: c?.nome || "Caso",
    subtitle: `Etapa: ${etapa} · Próximo: ${proximo}`,
    updatedIso,
    tags,
    flags,
    reasons,
  };
}

export function buildCreasCaseQueue(cases, { gestor = false } = {}) {
  const arr = Array.isArray(cases) ? cases : [];
  const items = arr.map((c) => computeCreasQueueItemForCase(c, { gestor })).filter(Boolean);
  items.sort((a, b) => {
    if ((b?.score || 0) !== (a?.score || 0)) return (b?.score || 0) - (a?.score || 0);
    // empate: o mais parado/antigo primeiro
    return safeTime(a?.updatedIso) - safeTime(b?.updatedIso);
  });
  return items;
}

