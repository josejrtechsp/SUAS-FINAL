// frontend/src/domain/creasMetrics.js
// Métricas determinísticas (sem IA) para painel gerencial do CREAS.

function _toDate(iso) {
  if (!iso) return null;
  try {
    const d = new Date(iso);
    return Number.isFinite(d.getTime()) ? d : null;
  } catch {
    return null;
  }
}

export function daysBetween(aIso, bIso) {
  const a = _toDate(aIso);
  const b = _toDate(bIso);
  if (!a || !b) return null;
  const ms = b.getTime() - a.getTime();
  return Math.max(0, Math.floor(ms / (1000 * 60 * 60 * 24)));
}

export function daysSince(iso) {
  const d = _toDate(iso);
  if (!d) return null;
  const ms = Date.now() - d.getTime();
  return Math.max(0, Math.floor(ms / (1000 * 60 * 60 * 24)));
}

function _lastMoveIso(c) {
  return c?.ultimo_registro_em || c?.atualizado_em || c?.criado_em || null;
}

function _stageStartIso(c) {
  // Heurística:
  // - Se houver registros na etapa atual na Linha do Metrô, usa o registro mais antigo.
  // - Senão, usa o último movimento (ou criação).
  const code = String(c?.etapa_atual || "").trim();
  const etapas = Array.isArray(c?.linha_metro?.etapas) ? c.linha_metro.etapas : [];
  const et = etapas.find((x) => String(x?.codigo || "") === code);
  const regs = Array.isArray(et?.registros) ? et.registros : [];
  const valid = regs
    .map((r) => r?.data_hora || null)
    .filter(Boolean)
    .map((iso) => ({ iso, d: _toDate(iso) }))
    .filter((x) => x.d);

  if (valid.length) {
    valid.sort((a, b) => a.d.getTime() - b.d.getTime());
    return valid[0].iso;
  }

  // fallback
  return _lastMoveIso(c);
}

function _workflowMap(workflow) {
  const etapas = Array.isArray(workflow?.etapas) ? workflow.etapas : [];
  const byCode = new Map();
  for (const e of etapas) {
    const codigo = String(e?.codigo || "").trim();
    if (!codigo) continue;
    byCode.set(codigo, e);
  }
  return byCode;
}

export function buildCreasGestaoMetrics({ cases = [], workflow = null, semMovDias = 10 } = {}) {
  const now = new Date();
  const wfMap = _workflowMap(workflow);

  const ativos = (Array.isArray(cases) ? cases : []).filter((c) => String(c?.status || "ativo") !== "encerrado");

  const byRisco = { alto: 0, medio: 0, baixo: 0, outro: 0 };
  const byEtapa = new Map(); // codigo -> stats
  const ranking = new Map(); // chave -> stats

  let proxVencidos = 0;
  let semMov = 0;

  for (const c of ativos) {
    const risco = String(c?.risco || "").toLowerCase();
    if (risco === "alto") byRisco.alto += 1;
    else if (risco === "medio" || risco === "médio") byRisco.medio += 1;
    else if (risco === "baixo") byRisco.baixo += 1;
    else byRisco.outro += 1;

    // Próximo passo vencido
    const pp = _toDate(c?.proximo_passo_em);
    if (pp && pp.getTime() <= now.getTime()) proxVencidos += 1;

    // Sem movimento
    const lastMove = _lastMoveIso(c) || null;
    const ds = daysSince(lastMove);
    if (ds != null && ds >= semMovDias) semMov += 1;

    // Por etapa (workflow)
    const etapa = String(c?.etapa_atual || "—").trim() || "—";
    const wf = wfMap.get(etapa) || null;
    const sla = Number.isFinite(Number(wf?.sla_dias)) ? Number(wf.sla_dias) : null;

    const startIso = _stageStartIso(c) || c?.criado_em || null;
    const stageDays = startIso ? daysSince(startIso) : null;
    const estourou = sla != null && stageDays != null ? stageDays > sla : false;

    if (!byEtapa.has(etapa)) {
      byEtapa.set(etapa, {
        codigo: etapa,
        nome: String(wf?.nome || etapa),
        sla_dias: sla,
        total: 0,
        vencidos: 0,
        soma_dias: 0,
        n_dias: 0,
      });
    }
    const st = byEtapa.get(etapa);
    st.total += 1;
    if (estourou) st.vencidos += 1;
    if (stageDays != null) {
      st.soma_dias += stageDays;
      st.n_dias += 1;
    }

    // Ranking por técnico
    const resp = c?.responsavel_nome ? String(c.responsavel_nome) : "— Sem responsável";
    const key = resp;
    if (!ranking.has(key)) {
      ranking.set(key, {
        nome: resp,
        total: 0,
        alto: 0,
        prox_venc: 0,
        sem_mov: 0,
        score: 0,
      });
    }
    const rk = ranking.get(key);
    rk.total += 1;
    if (risco === "alto") rk.alto += 1;
    if (pp && pp.getTime() <= now.getTime()) rk.prox_venc += 1;
    if (ds != null && ds >= semMovDias) rk.sem_mov += 1;

    // Score gerencial (transparente): vencidos pesa mais
    rk.score =
      rk.total +
      rk.alto * 2 +
      rk.sem_mov * 2 +
      rk.prox_venc * 3;
  }

  const etapasArr = Array.from(byEtapa.values()).map((x) => ({
    ...x,
    media_dias: x.n_dias ? Math.round(x.soma_dias / x.n_dias) : null,
    pct_vencidos: x.total ? Math.round((x.vencidos / x.total) * 100) : 0,
  }));

  // Ordena etapas por gargalo (pct vencidos, depois total)
  etapasArr.sort((a, b) => (b.pct_vencidos - a.pct_vencidos) || (b.total - a.total));

  const rankingArr = Array.from(ranking.values());
  rankingArr.sort((a, b) => (b.score - a.score) || (b.total - a.total));

  const gargalos = etapasArr.filter((e) => (e.sla_dias != null) && e.total >= 2).slice(0, 6);

  return {
    totals: {
      ativos: ativos.length,
      prox_vencidos: proxVencidos,
      sem_movimento: semMov,
    },
    byRisco,
    etapas: etapasArr,
    ranking: rankingArr,
    gargalos,
    semMovDias,
  };
}

export function toCsv(rows, headers) {
  const cols = headers && headers.length ? headers : Object.keys(rows?.[0] || {});
  const esc = (v) => {
    const s = v == null ? "" : String(v);
    if (/[",\n\r]/.test(s)) return '"' + s.replace(/"/g, '""') + '"';
    return s;
  };
  const out = [];
  out.push(cols.map(esc).join(","));
  for (const r of rows || []) {
    out.push(cols.map((k) => esc(r?.[k])).join(","));
  }
  return out.join("\n");
}
