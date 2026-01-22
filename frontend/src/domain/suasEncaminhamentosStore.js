// frontend/src/domain/suasEncaminhamentosStore.js
// Encaminhamentos INTERNOS entre equipamentos (CRAS/CREAS/PopRua) — MVP local.
// Objetivo: rastreabilidade + contrarreferência entre módulos sem depender do backend.

const KEY = "suas_encaminhamentos_v1";

function nowIso() {
  return new Date().toISOString();
}

function safeParseArray(raw) {
  try {
    const j = JSON.parse(raw);
    return Array.isArray(j) ? j : [];
  } catch {
    return [];
  }
}

function normModule(v) {
  const s = String(v || "").trim().toUpperCase();
  if (s === "POP RUA") return "POPRUA";
  if (s === "POP_RUA") return "POPRUA";
  if (s === "POP-RUA") return "POPRUA";
  if (s === "POP") return "POPRUA";
  if (s === "RUa".toUpperCase()) return "POPRUA";
  if (s === "CRAS" || s === "CREAS" || s === "POPRUA") return s;
  return s || "CRAS";
}

function normStatus(v) {
  const s = String(v || "enviado").trim().toLowerCase();
  const ok = ["enviado", "recebido", "em_atendimento", "retorno_enviado", "concluido", "cancelado"];
  return ok.includes(s) ? s : "enviado";
}

function normPrioridade(v) {
  const s = String(v || "media").trim().toLowerCase();
  if (["alta", "alto"].includes(s)) return "alta";
  if (["baixa", "baixo"].includes(s)) return "baixa";
  return "media";
}

function normalizeUser(u) {
  if (!u) return null;
  const id = u?.id != null ? Number(u.id) : null;
  return {
    id: id && !Number.isNaN(id) ? id : null,
    nome: u?.nome || u?.name || "—",
    email: u?.email || u?.mail || null,
    perfil: u?.perfil || u?.role || null,
  };
}

function nextId(list) {
  const max = (list || []).reduce((m, x) => Math.max(m, Number(x?.id || 0)), 0);
  return max + 1;
}

function safeText(v, max = 1200) {
  const s = String(v || "").trim();
  if (!s) return "";
  return s.length > max ? s.slice(0, max) : s;
}

function buildRetornoResumo(model) {
  // Resumo curto para listas
  const situacao = safeText(model?.situacao_atual || model?.situacao || "", 220);
  const proxima = safeText(model?.origem_deve_fazer_agora || model?.proxima_acao || "", 220);
  const prazo = safeText(model?.prazo_sugerido || model?.prazo || "", 40);

  const parts = [];
  if (situacao) parts.push(`Situação: ${situacao}`);
  if (proxima) parts.push(`Origem: ${proxima}`);
  if (prazo) parts.push(`Prazo sugerido: ${prazo}`);

  const resumo = parts.join(" · ");
  if (resumo) return resumo;

  const feito = safeText(model?.o_que_foi_feito || model?.feito || "", 240);
  return feito || "Devolutiva enviada ✅";
}

function buildRetornoDetalhado(model) {
  const feito = safeText(model?.o_que_foi_feito || model?.feito || "", 2500);
  const situacao = safeText(model?.situacao_atual || model?.situacao || "", 900);
  const proxima = safeText(model?.origem_deve_fazer_agora || model?.proxima_acao || "", 1200);
  const prazo = safeText(model?.prazo_sugerido || model?.prazo || "", 40);
  const obs = safeText(model?.observacoes || model?.obs || "", 1200);

  const lines = ["✅ Devolutiva (contrarreferência)"];
  if (feito) lines.push(`• O que foi feito: ${feito}`);
  if (situacao) lines.push(`• Situação atual: ${situacao}`);
  if (proxima) lines.push(`• Origem deve fazer agora: ${proxima}`);
  if (prazo) lines.push(`• Prazo sugerido: ${prazo}`);
  if (obs) lines.push(`• Observações: ${obs}`);
  return lines.join("\n");
}

export function getSuasEncaminhamentos() {
  try {
    return safeParseArray(localStorage.getItem(KEY));
  } catch {
    return [];
  }
}

export function saveSuasEncaminhamentos(list) {
  try {
    localStorage.setItem(KEY, JSON.stringify(list || []));
  } catch {}
}

export function clearSuasEncaminhamentos() {
  try {
    localStorage.removeItem(KEY);
  } catch {}
  saveSuasEncaminhamentos([]);
  return [];
}

export function createSuasEncaminhamento(payload, usuario) {
  const list = getSuasEncaminhamentos();
  const id = nextId(list);
  const iso = nowIso();
  const u = normalizeUser(usuario);

  const item = {
    id,
    pessoa_id: payload?.pessoa_id != null ? Number(payload.pessoa_id) : null,

    origem_modulo: normModule(payload?.origem_modulo || payload?.origem || "CRAS"),
    origem_caso_id: payload?.origem_caso_id ?? null,
    origem_caso_label: payload?.origem_caso_label || null,
    origem_unidade: payload?.origem_unidade || null,

    destino_modulo: normModule(payload?.destino_modulo || payload?.destino || "CREAS"),
    destino_unidade: payload?.destino_unidade || null,

    assunto: String(payload?.assunto || "Encaminhamento interno").trim(),
    motivo: String(payload?.motivo || "").trim(),
    prioridade: normPrioridade(payload?.prioridade || "media"),
    prazo_retorno: payload?.prazo_retorno || null, // YYYY-MM-DD

    status: "enviado",
    status_em: iso,

    destino_caso_id: null,
    destino_responsavel_id: null,
    destino_responsavel_nome: null,

    // contrarreferência (devolutiva)
    retorno_texto: null, // resumo
    retorno_detalhe: null, // texto completo
    retorno_modelo: null, // campos estruturados
    retorno_em: null,

    // cobrança (origem) — para rastrear follow-up quando prazo vence
    cobranca_total: 0,
    cobranca_ultimo_em: null,
    cobranca_ultimo_texto: null,

    criado_em: iso,
    atualizado_em: iso,

    timeline: [
      {
        id: `suas_tl_${id}_${Date.now()}`,
        tipo: "enviado",
        texto: "Encaminhamento enviado ✅",
        por_id: u?.id || null,
        por_nome: u?.nome || "—",
        em: iso,
      },
    ],
  };

  saveSuasEncaminhamentos([item, ...(list || [])]);

  // UX: após criar, sugerir foco em "Enviados" no módulo de origem (ex.: CREAS) e rolar até o item.
  try {
    const mod = String(item?.origem_modulo || '').trim();
    if (mod) {
      localStorage.setItem("suas_nav_modulo", mod);
      localStorage.setItem("suas_nav_view", "outbox");
      localStorage.setItem("suas_nav_selected_id", String(item?.id));
    }
  } catch {}
  return item;
}

function patchItem(id, patch, usuario, timelineEntry) {
  const list = getSuasEncaminhamentos();
  const idx = (list || []).findIndex((x) => Number(x?.id) === Number(id));
  if (idx < 0) return null;

  const iso = nowIso();
  const u = normalizeUser(usuario);

  const cur = list[idx];
  const next = {
    ...cur,
    ...patch,
    atualizado_em: iso,
  };

  if (timelineEntry) {
    const tl = Array.isArray(next.timeline) ? [...next.timeline] : [];
    tl.unshift({
      id: `suas_tl_${id}_${Date.now()}`,
      por_id: u?.id || null,
      por_nome: u?.nome || "—",
      em: iso,
      ...timelineEntry,
    });
    next.timeline = tl;
  }

  const out = [...list];
  out[idx] = next;
  saveSuasEncaminhamentos(out);
  return next;
}

export function marcarRecebidoSuasEncaminhamento(id, usuario, { destino_caso_id = null } = {}) {
  return patchItem(
    id,
    {
      status: "recebido",
      status_em: nowIso(),
      destino_caso_id: destino_caso_id ?? null,
      destino_responsavel_id: null,
      destino_responsavel_nome: null,
    },
    usuario,
    { tipo: "recebido", texto: "Recebido pelo destino ✅" }
  );
}

export function marcarEmAtendimentoSuasEncaminhamento(id, usuario) {
  return patchItem(
    id,
    { status: "em_atendimento", status_em: nowIso() },
    usuario,
    { tipo: "em_atendimento", texto: "Em atendimento no destino" }
  );
}

export function registrarRetornoSuasEncaminhamento(id, usuario, texto) {
  // Compatibilidade: devolutiva simples por texto (antigo)
  const t = String(texto || "").trim();
  if (!t) return null;
  const iso = nowIso();
  return patchItem(
    id,
    {
      status: "retorno_enviado",
      status_em: iso,
      retorno_texto: t,
      retorno_detalhe: t,
      retorno_modelo: null,
      retorno_em: iso,
    },
    usuario,
    { tipo: "retorno", texto: "Contrarreferência enviada ✅" }
  );
}

export function registrarRetornoSuasEncaminhamentoModelo(id, usuario, model) {
  // Novo padrão (autoexplicativo): campos mínimos e texto gerado.
  const m = {
    o_que_foi_feito: safeText(model?.o_que_foi_feito || "", 2500),
    situacao_atual: safeText(model?.situacao_atual || "", 900),
    origem_deve_fazer_agora: safeText(model?.origem_deve_fazer_agora || "", 1200),
    prazo_sugerido: safeText(model?.prazo_sugerido || "", 40),
    observacoes: safeText(model?.observacoes || "", 1200),
  };

  // exige o mínimo (para ficar “pronto para auditoria”)
  if (!m.o_que_foi_feito && !m.situacao_atual && !m.origem_deve_fazer_agora) return null;

  const iso = nowIso();
  const resumo = buildRetornoResumo(m);
  const detalhe = buildRetornoDetalhado(m);

  return patchItem(
    id,
    {
      status: "retorno_enviado",
      status_em: iso,
      retorno_texto: resumo,
      retorno_detalhe: detalhe,
      retorno_modelo: m,
      retorno_em: iso,
    },
    usuario,
    { tipo: "retorno", texto: "Contrarreferência enviada ✅" }
  );
}

export function registrarCobrancaSuasEncaminhamento(id, usuario, texto) {
  const list = getSuasEncaminhamentos();
  const cur = (list || []).find((x) => Number(x?.id) === Number(id)) || null;
  if (!cur) return null;

  const t = String(texto || "").trim() || "Cobrança registrada";
  const iso = nowIso();
  const total = Number(cur?.cobranca_total || 0) + 1;

  return patchItem(
    id,
    {
      cobranca_total: total,
      cobranca_ultimo_em: iso,
      cobranca_ultimo_texto: t,
    },
    usuario,
    { tipo: "cobranca", texto: `Cobrança enviada: ${t}` }
  );
}

export function concluirSuasEncaminhamento(id, usuario, texto) {
  const t = String(texto || "").trim();
  return patchItem(
    id,
    { status: "concluido", status_em: nowIso() },
    usuario,
    { tipo: "concluido", texto: t ? `Concluído: ${t}` : "Concluído ✅" }
  );
}

export function cancelarSuasEncaminhamento(id, usuario, motivo) {
  const t = String(motivo || "").trim();
  return patchItem(
    id,
    { status: "cancelado", status_em: nowIso() },
    usuario,
    { tipo: "cancelado", texto: t ? `Cancelado: ${t}` : "Cancelado" }
  );
}

export function getSuasInbox(modulo) {
  const m = normModule(modulo);
  return (getSuasEncaminhamentos() || []).filter((x) => normModule(x?.destino_modulo) === m);
}

export function getSuasOutbox(modulo) {
  const m = normModule(modulo);
  return (getSuasEncaminhamentos() || []).filter((x) => normModule(x?.origem_modulo) === m);
}

export function getSuasByPessoa(pessoaId) {
  const pid = pessoaId != null ? Number(pessoaId) : null;
  if (!pid || Number.isNaN(pid)) return [];
  return (getSuasEncaminhamentos() || []).filter((x) => Number(x?.pessoa_id) === pid);
}

export function getSuasById(id) {
  const nid = id != null ? Number(id) : null;
  if (!nid || Number.isNaN(nid)) return null;
  return (getSuasEncaminhamentos() || []).find((x) => Number(x?.id) === nid) || null;
}

export function isSuasOverdue(item) {
  const st = normStatus(item?.status);
  if (["concluido", "cancelado"].includes(st)) return false;
  const prazo = item?.prazo_retorno;
  if (!prazo) return false;
  try {
    const today = new Date();
    const t0 = new Date(today.getFullYear(), today.getMonth(), today.getDate()).getTime();
    const d = new Date(prazo + "T00:00:00").getTime();
    if (!d) return false;
    return d < t0;
  } catch {
    return false;
  }
}

export function getSuasOverdueForModulo(modulo) {
  const m = normModule(modulo);
  return (getSuasEncaminhamentos() || []).filter((x) => {
    const rel = normModule(x?.destino_modulo) === m || normModule(x?.origem_modulo) === m;
    return rel && isSuasOverdue(x);
  });
}

// Qual é a ação principal (autoexplicativa) para este módulo neste item?
export function inferSuasActionForModulo(item, modulo) {
  const m = normModule(modulo);
  const st = normStatus(item?.status);

  const inbox = normModule(item?.destino_modulo) === m;
  const outbox = normModule(item?.origem_modulo) === m;

  if (inbox) {
    if (st === "enviado") return "receber";
    if (["recebido", "em_atendimento"].includes(st)) return "devolutiva";
    return "acompanhar";
  }

  if (outbox) {
    if (st === "retorno_enviado") return "concluir";
    if (["enviado", "recebido", "em_atendimento"].includes(st)) return "cobrar";
    return "acompanhar";
  }

  return "acompanhar";
}


// ===== Integração: levar contrarreferência para dentro do CASO (linha do tempo + linha do metrô) =====
// Retorna eventos prontos para UI, derivados dos encaminhamentos SUAS:
// - devolutiva (contrarreferência)
// - cobrança por atraso
//
// Uso:
//   const { timeline, metroRegistros } = getSuasUpdatesForCase({ modulo: "CREAS", casoId, pessoaId });
function _ts(iso) {
  try {
    const t = new Date(String(iso || "")).getTime();
    return Number.isFinite(t) ? t : 0;
  } catch {
    return 0;
  }
}

function _pickPorNome(item, tipo) {
  const tl = Array.isArray(item?.timeline) ? item.timeline : [];
  const found = tl.find((x) => String(x?.tipo || "") === String(tipo || "")) || null;
  const nome = found?.por_nome || found?.por || found?.usuario_nome || null;
  return nome || "—";
}

export function getSuasUpdatesForCase({ modulo, casoId = null, pessoaId = null } = {}) {
  const m = normModule(modulo);
  const cid = casoId != null && !Number.isNaN(Number(casoId)) ? Number(casoId) : null;
  const pid = pessoaId != null && !Number.isNaN(Number(pessoaId)) ? Number(pessoaId) : null;

  const list = getSuasEncaminhamentos() || [];
  const rel = (list || []).filter((x) => {
    const byPessoa = pid != null && Number(x?.pessoa_id) === pid;
    const byCaso =
      cid != null &&
      ((normModule(x?.origem_modulo) === m && Number(x?.origem_caso_id) === cid) ||
        (normModule(x?.destino_modulo) === m && Number(x?.destino_caso_id) === cid));
    return byPessoa || byCaso;
  });

  const timeline = [];
  const metroRegistros = [];

  for (const it of rel) {
    const isOrigin = normModule(it?.origem_modulo) === m;
    const isDest = normModule(it?.destino_modulo) === m;
    const dir = isOrigin ? "in" : isDest ? "out" : "x";
    const baseId = Number(it?.id || 0) || 0;

    // Devolutiva (contrarreferência)
    if (it?.retorno_em) {
      const por = _pickPorNome(it, "retorno");
      const titulo =
        isOrigin
          ? `Devolutiva recebida de ${String(it?.destino_modulo || "").toUpperCase()} · #${baseId}`
          : isDest
          ? `Devolutiva enviada para ${String(it?.origem_modulo || "").toUpperCase()} · #${baseId}`
          : `Devolutiva (SUAS) · #${baseId}`;
      const resumo = it?.retorno_texto ? String(it.retorno_texto) : "Devolutiva enviada ✅";
      const detalhe = it?.retorno_detalhe ? String(it.retorno_detalhe) : resumo;

      timeline.push({
        id: `suas_ret_${baseId}_${dir}`,
        tipo: "suas_retorno",
        texto: resumo ? `${titulo} — ${resumo}` : titulo,
        criado_em: it?.retorno_em,
        por,
        detalhe,
        suas_id: baseId,
      });

      metroRegistros.push({
        id: `suas_ret_${baseId}_${dir}`,
        responsavel_nome: por,
        data_hora: it?.retorno_em,
        obs: isOrigin ? `Devolutiva recebida · ${resumo}` : `Devolutiva enviada · ${resumo}`,
        encaminhamentos: [{ id: baseId, destino: it?.destino_modulo, status: it?.status }],
      });
    }

    // Cobrança
    if (it?.cobranca_ultimo_em) {
      const por = _pickPorNome(it, "cobranca");
      const titulo =
        isOrigin
          ? `Cobrança enviada para ${String(it?.destino_modulo || "").toUpperCase()} · #${baseId}`
          : isDest
          ? `Cobrança recebida de ${String(it?.origem_modulo || "").toUpperCase()} · #${baseId}`
          : `Cobrança (SUAS) · #${baseId}`;
      const resumo = it?.cobranca_ultimo_texto ? String(it.cobranca_ultimo_texto) : "Cobrança registrada";
      const detalhe = `Cobranças registradas: ${Number(it?.cobranca_total || 0)}\nÚltima cobrança: ${resumo}`;

      timeline.push({
        id: `suas_cob_${baseId}`,
        tipo: "suas_cobranca",
        texto: `${titulo} — ${resumo}`,
        criado_em: it?.cobranca_ultimo_em,
        por,
        detalhe,
        suas_id: baseId,
      });

      metroRegistros.push({
        id: `suas_cob_${baseId}`,
        responsavel_nome: por,
        data_hora: it?.cobranca_ultimo_em,
        obs: `Cobrança · ${resumo}`,
        encaminhamentos: [{ id: baseId, destino: it?.destino_modulo, status: it?.status }],
      });
    }
  }

  timeline.sort((a, b) => _ts(b?.criado_em) - _ts(a?.criado_em));
  metroRegistros.sort((a, b) => _ts(b?.data_hora) - _ts(a?.data_hora));

  return { timeline: timeline.slice(0, 60), metroRegistros: metroRegistros.slice(0, 60) };
}


// DEMO: cria alguns encaminhamentos internos para teste.
export function seedSuasEncaminhamentosDemo({ pessoaIds = [] } = {}) {
  const current = getSuasEncaminhamentos();
  if ((current || []).length) return current;

  const ids = (pessoaIds || []).filter(Boolean).slice(0, 10);
  const pick = (i) => ids[i % ids.length];

  const demo = [];
  const base = nowIso();

  function prazoPlus(dias) {
    if (!dias) return null;
    const d = new Date();
    d.setDate(d.getDate() + dias);
    const yyyy = d.getFullYear();
    const mm = String(d.getMonth() + 1).padStart(2, "0");
    const dd = String(d.getDate()).padStart(2, "0");
    return `${yyyy}-${mm}-${dd}`;
  }

  function pushDemo(pessoa_id, origem, destino, motivo, prioridade, prazoDias) {
    const prazo = prazoPlus(prazoDias);

    demo.push({
      id: demo.length + 1,
      pessoa_id,
      origem_modulo: origem,
      origem_caso_id: null,
      origem_caso_label: null,
      origem_unidade: null,
      destino_modulo: destino,
      destino_unidade: null,
      assunto: "Encaminhamento interno (DEMO)",
      motivo,
      prioridade,
      prazo_retorno: prazo,
      status: "enviado",
      status_em: base,
      destino_caso_id: null,
      destino_responsavel_id: null,
      destino_responsavel_nome: null,
      retorno_texto: null,
      retorno_detalhe: null,
      retorno_modelo: null,
      retorno_em: null,
      cobranca_total: 0,
      cobranca_ultimo_em: null,
      cobranca_ultimo_texto: null,
      criado_em: base,
      atualizado_em: base,
      timeline: [
        {
          id: `suas_tl_demo_${Date.now()}_${demo.length}`,
          tipo: "enviado",
          texto: "Encaminhamento enviado ✅",
          por_id: 1,
          por_nome: "Sistema DEMO",
          em: base,
        },
      ],
    });
  }

  if (ids.length) {
    pushDemo(pick(0), "CRAS", "CREAS", "Caso complexo — solicitar acompanhamento especializado.", "alta", 3);
    pushDemo(pick(1), "CREAS", "CRAS", "Solicito acompanhamento territorial/benefícios.", "media", 7);
    pushDemo(pick(2), "POPRUA", "CREAS", "Situação de rua com possível violação de direitos.", "alta", 2);
    pushDemo(pick(3), "CREAS", "POPRUA", "Abordagem/contato no território — sem localização fixa.", "media", 5);
    // Um vencido para testar cobrança
    pushDemo(pick(4), "CRAS", "POPRUA", "Contato no território e devolutiva.", "media", -2);
  }

  const normalized = demo.map((x) => ({ ...x, origem_modulo: normModule(x.origem_modulo), destino_modulo: normModule(x.destino_modulo) }));
  saveSuasEncaminhamentos(normalized);
  return normalized;
}