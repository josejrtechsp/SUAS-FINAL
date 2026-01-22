// frontend/src/domain/creasStore.js
// Armazenamento local (MVP) para o módulo CREAS.
// Objetivo: o módulo funcionar e ser testável SEM depender do backend.

import { ensurePessoaBasica, seedPessoasDemoFromCreasCases, getPessoaById } from "./pessoasStore.js";
import { isGestor, isTecnico } from "./acl.js";
import { seedSuasEncaminhamentosDemo } from "./suasEncaminhamentosStore.js";

const CASES_KEY_BASE = "creas_cases_v1";
const CASES_KEY_LEGACY = "creas_cases_v1";
const SELECTED_KEY_BASE = "creas_selected_case_v1";
const SELECTED_KEY_LEGACY = "creas_selected_case";
const SEED_MODE_KEY = "creas_seed_mode_v1"; // "demo" (padrão) | "none"

const WORKFLOW_KEY_BASE = "creas_workflow_v1";
const WORKFLOW_KEY_LEGACY = "creas_workflow_v1";
const WORKFLOW_KEY_LEGACY2 = "creas_workflow";

let _creasScope = { municipioId: "", unidadeId: "" };

function _normScopePart(v) {
  const s = String(v || "").trim();
  return s ? s.replace(/[^a-zA-Z0-9_-]/g, "") : "0";
}

function _scopeSuffix() {
  const m = _normScopePart(_creasScope.municipioId);
  const u = _normScopePart(_creasScope.unidadeId);
  return `${m}_${u}`;
}

function _casesKey() {
  return `${CASES_KEY_BASE}_${_scopeSuffix()}`;
}

function _selectedKey() {
  return `${SELECTED_KEY_BASE}_${_scopeSuffix()}`;
}


function _workflowKey() {
  return `${WORKFLOW_KEY_BASE}_${_scopeSuffix()}`;
}

export function setCreasScope({ municipioId, unidadeId } = {}) {
  _creasScope = { municipioId: municipioId ?? "", unidadeId: unidadeId ?? "" };
}

export function getCreasScope() {
  return { ..._creasScope };
}

function _migrateLegacyOnce() {
  try {
    const scopedKey = _casesKey();
    if (!localStorage.getItem(scopedKey)) {
      const legacyRaw = localStorage.getItem(CASES_KEY_LEGACY);
      if (legacyRaw) localStorage.setItem(scopedKey, legacyRaw);
    }

    const selKey = _selectedKey();
    if (!localStorage.getItem(selKey)) {
      const legacySel = localStorage.getItem(SELECTED_KEY_LEGACY);
      if (legacySel) localStorage.setItem(selKey, legacySel);
    }

    const wfKey = _workflowKey();
    if (!localStorage.getItem(wfKey)) {
      const legacyWf =
        localStorage.getItem(WORKFLOW_KEY_LEGACY) ||
        localStorage.getItem(WORKFLOW_KEY_LEGACY2);
      if (legacyWf) localStorage.setItem(wfKey, legacyWf);
    }
  } catch {}
}

export function getCreasSelectedCaseId() {
  try {
    _migrateLegacyOnce();
    return localStorage.getItem(_selectedKey()) || localStorage.getItem(SELECTED_KEY_LEGACY) || "";
  } catch {
    return "";
  }
}

export function setCreasSelectedCaseId(id) {
  try {
    const v = id == null ? "" : String(id);
    localStorage.setItem(_selectedKey(), v);
    // compatibilidade (outros módulos podem ler o legado)
    localStorage.setItem(SELECTED_KEY_LEGACY, v);
  } catch {}
}

export function clearCreasSelectedCaseId() {
  try {
    localStorage.removeItem(_selectedKey());
    localStorage.removeItem(SELECTED_KEY_LEGACY);
  } catch {}
}

export const CREAS_ETAPAS = [
  { codigo: "entrada", nome: "Entrada", sla_dias: 2, descricao: "Recebimento do caso e checagem mínima." },
  { codigo: "triagem", nome: "Triagem e classificação", sla_dias: 2, descricao: "Classificar risco/prioridade e orientar o fluxo." },
  { codigo: "acolhimento", nome: "Acolhimento inicial", sla_dias: 7, descricao: "Primeiro atendimento e demandas imediatas." },
  { codigo: "diagnostico", nome: "Diagnóstico/estudo do caso", sla_dias: 14, descricao: "Estudo social e entendimento do contexto." },
  { codigo: "plano", nome: "Plano ativo", sla_dias: 30, descricao: "Plano do caso com metas e responsáveis." },
  { codigo: "acompanhamento", nome: "Acompanhamento", sla_dias: 30, descricao: "Execução e monitoramento do plano." },
  { codigo: "rede", nome: "Articulação de rede", sla_dias: 15, descricao: "Encaminhamentos e contrarreferência." },
  { codigo: "reavaliacao", nome: "Reavaliação", sla_dias: 30, descricao: "Revisão de metas e decisão de continuidade." },
  { codigo: "encerramento", nome: "Encerramento", sla_dias: 7, descricao: "Encerramento qualificado e resumo." },
  { codigo: "pos", nome: "Pós-encerramento", sla_dias: 30, descricao: "Acompanhamento pós-encerramento (se necessário)." },
];

function _emitStorage() {
  try {
    window.dispatchEvent(new Event("storage"));
  } catch {}
}

function _normalizeEtapas(raw) {
  const arr = Array.isArray(raw) ? raw : [];
  const seen = new Set();
  const out = [];
  for (const it of arr) {
    if (!it) continue;
    const codigo = String(it.codigo || it.key || "").trim();
    if (!codigo) continue;
    if (seen.has(codigo)) continue;
    seen.add(codigo);
    out.push({
      codigo,
      nome: String(it.nome || it.title || "Etapa").trim() || "Etapa",
      sla_dias: Number.isFinite(Number(it.sla_dias)) ? Number(it.sla_dias) : undefined,
      descricao: String(it.descricao || it.subtitle || "").trim(),
      checklist: Array.isArray(it.checklist) ? it.checklist.map((x) => String(x || "").trim()).filter(Boolean) : [],
    });
  }
  return out;
}

export function getCreasWorkflow() {
  try {
    _migrateLegacyOnce();
    const raw =
      localStorage.getItem(_workflowKey()) ||
      localStorage.getItem(WORKFLOW_KEY_LEGACY) ||
      localStorage.getItem(WORKFLOW_KEY_LEGACY2);
    if (!raw) return { version: 1, etapas: CREAS_ETAPAS };
    const data = JSON.parse(raw);
    const etapas = _normalizeEtapas(data?.etapas || data?.workflow?.etapas || data?.etapas_def || data);
    if (!etapas.length) return { version: 1, etapas: CREAS_ETAPAS };

    const merged = etapas.map((e) => {
      const def = (CREAS_ETAPAS || []).find((x) => String(x?.codigo) === String(e.codigo));
      return {
        ...e,
        sla_dias: Number.isFinite(Number(e.sla_dias)) ? Number(e.sla_dias) : def?.sla_dias,
        descricao: e.descricao || def?.descricao || "",
        nome: e.nome || def?.nome || "Etapa",
      };
    });

    return { version: 1, etapas: merged };
  } catch {
    return { version: 1, etapas: CREAS_ETAPAS };
  }
}

// --- Qualidade / Checklist do encerramento (produto "padrão ouro") ---
const DEFAULT_ENCERRAMENTO_CHECKLIST = [
  "Registro do atendimento final realizado",
  "Encaminhamentos com devolutiva registrada (quando aplicável)",
  "Próximo passo/alta definido",
  "Resumo executivo atualizado",
];

export function getCreasEncerramentoChecklistDef() {
  const etapas = getCreasEtapasDef() || CREAS_ETAPAS || [];
  const enc = (etapas || []).find((e) => String(e?.codigo || "") === "encerramento");
  const list = Array.isArray(enc?.checklist) ? enc.checklist.map((x) => String(x || "").trim()).filter(Boolean) : [];
  return list.length ? list : DEFAULT_ENCERRAMENTO_CHECKLIST;
}

export function getCreasEncerramentoChecklistStatusForCase(caso) {
  const items = getCreasEncerramentoChecklistDef();
  const map = (caso && caso.qualidade_checklist && typeof caso.qualidade_checklist === "object") ? caso.qualidade_checklist : {};
  const missing = items.filter((it) => !map[it]);
  return {
    items,
    map,
    missing,
    done: items.length - missing.length,
    total: items.length,
    complete: missing.length === 0,
  };
}

export function saveCreasCaseQualityChecklist(caseId, checklistMap, usuario) {
  const u = normalizeUser(usuario);
  if (!u) return null;

  const items = getCreasEncerramentoChecklistDef();
  const next = {};
  for (const it of items) next[it] = Boolean(checklistMap && checklistMap[it]);

  const iso = nowIso();
  const c = updateCreasCase(caseId, {
    qualidade_checklist: next,
    qualidade_checklist_salvo_em: iso,
    qualidade_checklist_salvo_por_id: u.id,
    qualidade_checklist_salvo_por_nome: u.nome,
  });

  const detalhe = items.map((it) => `- ${next[it] ? "[x]" : "[ ]"} ${it}`).join("\n");
  addTimeline(caseId, {
    tipo: "qualidade",
    texto: "Checklist de qualidade atualizado ✅",
    detalhe,
    por: u.nome,
  });

  return c;
}


export function saveCreasWorkflow(workflow) {
  try {
    const etapas = _normalizeEtapas(workflow?.etapas || workflow);
    const payload = { version: 1, etapas };
    localStorage.setItem(_workflowKey(), JSON.stringify(payload));
    localStorage.setItem(WORKFLOW_KEY_LEGACY, JSON.stringify(payload));
    _emitStorage();
    return payload;
  } catch {
    return null;
  }
}

export function resetCreasWorkflow() {
  try {
    localStorage.removeItem(_workflowKey());
    _emitStorage();
  } catch {}
}

export function getCreasEtapasDef() {
  const wf = getCreasWorkflow();
  const etapas = Array.isArray(wf?.etapas) && wf.etapas.length ? wf.etapas : CREAS_ETAPAS;
  return etapas;
}


function buildLinhaMetroSkeleton() {
  return {
    etapas: (getCreasEtapasDef() || []).map((e, idx) => ({
      codigo: e.codigo,
      ordem: idx + 1,
      nome: e.nome,
      descricao: e.descricao || "",
      ultimo_registro: null,
      registros: [],
    })),
  };
}


function _reconcileLinhaMetro(lm) {
  const defs = getCreasEtapasDef() || [];
  const defByCodigo = new Map(defs.map((d) => [String(d.codigo), d]));
  const curEtapas = Array.isArray(lm?.etapas) ? lm.etapas : [];
  const byCodigo = new Map(curEtapas.map((e) => [String(e?.codigo || e?.key || ""), e]).filter(([k]) => k));
  const out = [];

  defs.forEach((d, idx) => {
    const codigo = String(d.codigo);
    const prev = byCodigo.get(codigo);
    out.push({
      codigo,
      ordem: prev?.ordem != null ? prev.ordem : idx + 1,
      nome: prev?.nome || d.nome || "Etapa",
      descricao: prev?.descricao || d.descricao || "",
      sla_dias: prev?.sla_dias != null ? prev.sla_dias : d.sla_dias,
      ultimo_registro: prev?.ultimo_registro || null,
      registros: Array.isArray(prev?.registros) ? prev.registros : [],
    });
  });

  curEtapas.forEach((e, idx) => {
    const codigo = String(e?.codigo || e?.key || "");
    if (!codigo) return;
    if (defByCodigo.has(codigo)) return;
    out.push({
      codigo,
      ordem: e?.ordem != null ? e.ordem : defs.length + idx + 1,
      nome: e?.nome || "Etapa",
      descricao: e?.descricao || "",
      sla_dias: e?.sla_dias,
      ultimo_registro: e?.ultimo_registro || null,
      registros: Array.isArray(e?.registros) ? e.registros : [],
    });
  });

  return { ...lm, etapas: out };
}

function ensureLinhaMetroCase(c) {
  if (!c) return c;
  const lm = c?.linha_metro;
  if (lm && Array.isArray(lm.etapas)) return { ...c, linha_metro: _reconcileLinhaMetro(lm) };
  return { ...c, linha_metro: _reconcileLinhaMetro(buildLinhaMetroSkeleton()) };
}

function ensurePessoaRefCase(c) {
  if (!c) return c;
  const cid = c?.id != null ? Number(c.id) : null;
  const pid = c?.pessoa_id != null ? Number(c.pessoa_id) : null;
  const pessoa_id = pid && !Number.isNaN(pid) ? pid : (cid && !Number.isNaN(cid) ? cid : null);

  // Garante a ficha única (mesmo que seja DEMO) — não quebra se localStorage falhar.
  if (pessoa_id) {
    try {
      ensurePessoaBasica({ pessoa_id, nome: c?.nome || "Pessoa" });
    } catch {}
  }

  if (!c?.pessoa_id && pessoa_id) {
    return { ...c, pessoa_id };
  }
  return c;
}


function ensureEncerramentoFields(c) {
  if (!c) return c;

  // casos antigos já encerrados devem aparecer como aprovados
  const defaultStatus = String(c?.status || "").toLowerCase() === "encerrado" ? "aprovado" : null;

  const defaults = {
    encerramento_status: defaultStatus, // null | solicitado | aprovado | recusado
    encerramento_etapa_anterior: null,

    encerramento_solicitado_em: null,
    encerramento_solicitado_por_id: null,
    encerramento_solicitado_por_nome: null,
    encerramento_solicitado_motivo: null,
    encerramento_solicitado_resumo: null,

    encerramento_avaliado_em: null,
    encerramento_avaliado_por_id: null,
    encerramento_avaliado_por_nome: null,
    encerramento_recusa_motivo: null,
  };

  let changed = false;
  const next = { ...c };
  for (const k of Object.keys(defaults)) {
    if (!Object.prototype.hasOwnProperty.call(next, k)) {
      next[k] = defaults[k];
      changed = true;
    }
  }

  // Se o caso já é encerrado e o campo existe como null, corrige para "aprovado".
  if (String(next?.status || "").toLowerCase() === "encerrado" && !next.encerramento_status) {
    next.encerramento_status = "aprovado";
    changed = true;
  }

  return changed ? next : c;
}

function nowIso() {
  return new Date().toISOString();
}

function safeParse(jsonStr) {
  try {
    const j = JSON.parse(jsonStr);
    return Array.isArray(j) ? j : [];
  } catch {
    return [];
  }
}

function normalizeUser(u) {
  if (!u) return null;
  const id = u?.id != null ? Number(u.id) : null;
  if (!id || Number.isNaN(id)) return null;
  return {
    id,
    nome: u?.nome || u?.name || "—",
    email: u?.email || u?.mail || null,
  };
}

export function getCreasCases() {
  _migrateLegacyOnce();
  const raw = localStorage.getItem(_casesKey());
  const arr = safeParse(raw);
  let changed = false;
  const migrated = (arr || []).map((c) => {
    let next = c;
    const lm = ensureLinhaMetroCase(next);
    if (lm !== next) next = lm;
    const pr = ensurePessoaRefCase(next);
    if (pr !== next) next = pr;
    const en = ensureEncerramentoFields(next);
    if (en !== next) next = en;
    if (next !== c) changed = true;
    return next;
  });
  if (changed) saveCreasCases(migrated);
  return migrated;
}

export function saveCreasCases(cases) {
  try {
    localStorage.setItem(_casesKey(), JSON.stringify(cases || []));
    // compatibilidade (apenas leitura antiga)
    localStorage.setItem(CASES_KEY_LEGACY, JSON.stringify(cases || []));
  } catch {}
}

export function getCreasSeedMode() {
  try {
    return String(localStorage.getItem(SEED_MODE_KEY) || "demo").toLowerCase();
  } catch {
    return "demo";
  }
}

export function setCreasSeedMode(mode) {
  try {
    localStorage.setItem(SEED_MODE_KEY, mode || "demo");
  } catch {}
}

export function clearCreasCases({ disableAutoSeed = false } = {}) {
  if (disableAutoSeed) setCreasSeedMode("none");
  try {
    localStorage.removeItem(_casesKey());
    localStorage.removeItem(CASES_KEY_LEGACY);
    clearCreasSelectedCaseId();
} catch {}
  saveCreasCases([]);
  return [];
}

function pad2(n) {
  return String(n).padStart(2, "0");
}

function toDateStr(d) {
  return `${d.getFullYear()}-${pad2(d.getMonth() + 1)}-${pad2(d.getDate())}`;
}

function addDays(base, days) {
  const d = new Date(base);
  d.setDate(d.getDate() + days);
  return d;
}

function suggestDaysByRisk(risco) {
  const r = String(risco || "medio").toLowerCase();
  if (r === "alto") return 2; // 48h
  if (r === "medio") return 7;
  return 15;
}

function buildDemoCases(count = 20) {
  const now = new Date();

  const NAMES = [
    "Maria da Silva",
    "João Pereira",
    "Família Souza",
    "Ana (mãe solo)",
    "Carlos (exemplo)",
    "Adolescente em conflito",
    "Idoso (suspeita maus-tratos)",
    "Mulher vítima de violência",
    "Família Oliveira",
    "Criança em negligência",
    "Pessoa com deficiência (PCD)",
    "Caso de exploração",
    "Conflito familiar (exemplo)",
    "Violação de direitos",
    "Usuário em vulnerabilidade",
    "Família Santos",
    "Trabalho infantil (suspeita)",
    "Evasão escolar",
    "Ameaça/risco (grave)",
    "Encerrado (exemplo)",
  ];

  const ORIGENS = [
    "CRAS",
    "Conselho Tutelar",
    "Judiciário",
    "MP",
    "Escola",
    "Saúde",
    "Segurança",
    "Denúncia",
    "Outro",
  ];

  const TEMAS = [
    { tema: "Violência/Ameaça", detalhe: "violência psicológica" },
    { tema: "Criança e adolescente", detalhe: "negligência" },
    { tema: "Criança e adolescente", detalhe: "abuso" },
    { tema: "Mulher/Família", detalhe: "violência contra a mulher" },
    { tema: "Mulher/Família", detalhe: "conflitos familiares" },
    { tema: "Idoso/PcD", detalhe: "maus-tratos" },
    { tema: "Direitos/Vulnerabilidade grave", detalhe: "violação geral" },
    { tema: "Encaminhamento de órgão/rede", detalhe: "Conselho Tutelar" },
  ];

  const ETAPAS_POOL = [
    "entrada",
    "triagem",
    "acolhimento",
    "diagnostico",
    "plano",
    "acompanhamento",
    "rede",
    "reavaliacao",
  ];

  const DESTINOS_REDE = ["Saúde", "Educação", "Conselho Tutelar", "Judiciário", "Segurança", "MP"];

  const out = [];

  for (let i = 0; i < count; i++) {
    const id = i + 1;

    const risco = i % 6 === 0 ? "alto" : i % 3 === 0 ? "baixo" : "medio";
    const tema = TEMAS[i % TEMAS.length];
    const origem = ORIGENS[i % ORIGENS.length];

    let status = "ativo";
    let etapa_atual = ETAPAS_POOL[i % ETAPAS_POOL.length];

    // datas base
    const criado = addDays(now, -(i * 2 + 1));
    criado.setHours(9, 0, 0, 0);
    const criado_em = criado.toISOString();

    // sem movimento em alguns
    let ultimo_registro_em = addDays(criado, 1).toISOString();
    if ([4, 9, 14].includes(i)) {
      const old = addDays(now, risco === "alto" ? -9 : -20);
      old.setHours(11, 0, 0, 0);
      ultimo_registro_em = old.toISOString();
    }

    // próximo passo sugerido por risco
    const sugDays = suggestDaysByRisk(risco);
    const prox = addDays(now, sugDays);
    prox.setHours(9, 0, 0, 0);
    let proximo_passo_em = prox.toISOString();

    // algumas pendências vencidas
    if ([2, 7, 12, 17].includes(i)) {
      const venc = addDays(now, -1);
      venc.setHours(9, 0, 0, 0);
      proximo_passo_em = venc.toISOString();
    }

    let proximo_passo = "Registrar atendimento";

    if (etapa_atual === "entrada") proximo_passo = "Registrar triagem";
    if (etapa_atual === "triagem") proximo_passo = "Definir técnico de referência";
    if (etapa_atual === "acolhimento") proximo_passo = "Registrar atendimento inicial";
    if (etapa_atual === "diagnostico") proximo_passo = "Visita domiciliar";
    if (etapa_atual === "plano") proximo_passo = "Atualizar plano";
    if (etapa_atual === "acompanhamento") proximo_passo = "Registrar atendimento";
    if (etapa_atual === "reavaliacao") proximo_passo = "Reavaliar metas";

    // alguns encerrados
    if ([15, 19].includes(i)) {
      status = "encerrado";
      etapa_atual = "encerramento";
      proximo_passo = "—";
      proximo_passo_em = null;
    }

    // encaminhamentos (rede) em alguns casos
    const encaminhamentos = [];
    const addRede = etapa_atual === "rede" || [3, 8, 13, 18].includes(i);
    if (status === "ativo" && addRede) {
      const destino = DESTINOS_REDE[i % DESTINOS_REDE.length];
      const prazo = addDays(now, sugDays);
      // alguns atrasados na rede
      if ([3, 13].includes(i)) prazo.setDate(prazo.getDate() - (sugDays + 2));
      const prazoStr = toDateStr(prazo);

      encaminhamentos.push({
        id: `enc_${id}_1`,
        destino,
        motivo: `Encaminhamento DEMO para ${destino}.`,
        prazo_retorno: prazoStr,
        status: "aguardando",
        retorno: null,
        criado_em: now.toISOString(),
        por: "Sistema",
      });

      proximo_passo = `Aguardar retorno: ${destino}`;
      proximo_passo_em = new Date(prazoStr + "T09:00:00").toISOString();
    }

    const timeline = [
      {
        id: `tl_${id}_criacao`,
        tipo: "criacao",
        texto: "Caso criado (DEMO) ✅",
        criado_em,
        por: "Sistema",
      },
    ];

    // um atendimento inicial em alguns casos
    const atendimentos = [];
    if (status === "ativo" && i % 4 === 0) {
      const dt = addDays(criado, 1);
      dt.setHours(10, 0, 0, 0);
      atendimentos.push({
        id: `at_${id}_1`,
        tipo: "atendimento",
        data_hora: dt.toISOString(),
        resumo: "Atendimento inicial (DEMO).",
        proximo_passo,
        proximo_passo_em: proximo_passo_em || now.toISOString(),
        por: "Sistema",
      });
      timeline.push({
        id: `tl_${id}_at1`,
        tipo: "atendimento",
        texto: "Atendimento inicial registrado (DEMO) ✅",
        criado_em: dt.toISOString(),
        por: "Sistema",
      });
    }

    let c = {
      id,
      pessoa_id: id,
      nome: NAMES[i % NAMES.length] + (i >= NAMES.length ? ` ${id}` : ""),
      risco,
      motivo_tema: tema.tema,
      motivo_detalhe: tema.detalhe,
      origem,

      responsavel_id: null,
      responsavel_nome: null,
      responsavel_email: null,

      encerramento_status: null,

      status,
      etapa_atual,
      proximo_passo,
      proximo_passo_em,
      criado_em,
      atualizado_em: now.toISOString(),
      ultimo_registro_em,
      timeline,
      atendimentos,
      encaminhamentos,
      documentos: [],
      linha_metro: buildLinhaMetroSkeleton(),
    };

    // Alimenta a linha do metrô com pelo menos 1 registro na etapa atual
    c = addMetroRegistroToCase(c, etapa_atual === "encerramento" ? "encerramento" : (etapa_atual || "entrada"), {
      responsavel_nome: c.responsavel_nome || "Sistema",
      data_hora: ultimo_registro_em || criado_em,
      obs: "Registro inicial (DEMO).",
      atendimento_id: atendimentos?.[0]?.id || null,
      encaminhamentos: [],
    });

    // se tem rede, registra também no metrô da rede
    if (encaminhamentos.length) {
      c = addMetroRegistroToCase(c, "rede", {
        responsavel_nome: "Sistema",
        data_hora: now.toISOString(),
        obs: `Encaminhamento (DEMO): ${encaminhamentos[0].destino}`,
        atendimento_id: null,
        encaminhamentos: [{ id: encaminhamentos[0].id, destino: encaminhamentos[0].destino, status: encaminhamentos[0].status }],
      });
      timeline.push({
        id: `tl_${id}_enc1`,
        tipo: "encaminhamento",
        texto: `Encaminhado para ${encaminhamentos[0].destino} (DEMO)`,
        criado_em: now.toISOString(),
        por: "Sistema",
      });
    }



    // 2 casos com encerramento solicitado (DEMO) — para testar aprovação do gestor
    if (status === "ativo" && [5, 10].includes(i)) {
      const solEm = now.toISOString();
      timeline.unshift({
        id: `tl_${id}_encsol`,
        tipo: "encerramento",
        texto: "Encerramento solicitado (DEMO) — aguardando aprovação.",
        criado_em: solEm,
        por: "Técnico (DEMO)",
      });
      c = {
        ...c,
        encerramento_status: "solicitado",
        encerramento_etapa_anterior: c.etapa_atual,
        encerramento_solicitado_em: solEm,
        encerramento_solicitado_por_id: 2,
        encerramento_solicitado_por_nome: "Técnico (DEMO)",
        encerramento_solicitado_motivo: "Concluído",
        encerramento_solicitado_resumo: "Solicitação de encerramento (DEMO) para teste de aprovação.",
        proximo_passo: "Aguardando aprovação do encerramento",
        proximo_passo_em: null,
      };
    }
    out.push(c);
  }

  return out;
}

export function seedCreasDemoCases({ count = 20, overwrite = true } = {}) {
  setCreasSeedMode("demo");
  const demo = buildDemoCases(count);
  if (overwrite) {
    saveCreasCases(demo);
    // cria/atualiza fichas DEMO (sem apagar outras fichas)
    seedPessoasDemoFromCreasCases(demo, { overwrite: false });
    // encaminhamentos internos SUAS (DEMO)
    try {
      const ids = (demo || []).map((c) => Number(c?.pessoa_id || c?.id)).filter(Boolean);
      seedSuasEncaminhamentosDemo({ pessoaIds: ids });
    } catch {}
    return demo;
  }
  const current = getCreasCases();
  saveCreasCases([...(demo || []), ...(current || [])]);
  seedPessoasDemoFromCreasCases(getCreasCases(), { overwrite: false });
  try {
    const ids = (getCreasCases() || []).map((c) => Number(c?.pessoa_id || c?.id)).filter(Boolean);
    seedSuasEncaminhamentosDemo({ pessoaIds: ids });
  } catch {}
  return getCreasCases();
}

export function seedCreasIfEmpty() {
  const mode = getCreasSeedMode();
  const current = getCreasCases();
  if (current.length) return current;
  if (mode === "none") return current;

  // padrão: demo com ~20 casos
  const demo = buildDemoCases(20);
  saveCreasCases(demo);
  seedPessoasDemoFromCreasCases(demo, { overwrite: false });
  try {
    const ids = (demo || []).map((c) => Number(c?.pessoa_id || c?.id)).filter(Boolean);
    seedSuasEncaminhamentosDemo({ pessoaIds: ids });
  } catch {}
  return demo;
}

export function nextCreasId() {
  const arr = getCreasCases();
  const max = arr.reduce((m, x) => Math.max(m, Number(x?.id || 0)), 0);
  return max + 1;
}

export function createCreasCase(payload) {
  const arr = getCreasCases();
  const id = nextCreasId();
  const iso = nowIso();

  const rawUser = payload?.usuario || null;
  const u = normalizeUser(rawUser) || null;
  const canAutoAssign = !!rawUser && (isTecnico(rawUser) || isGestor(rawUser));

  // Regra de ouro (autoexplicativo):
  // - Técnico/gestor cria -> já nasce com responsável.
  // - Recepção cria -> fica SEM responsável para um técnico ASSUMIR.
  const responsavel_id =
    payload?.responsavel_id != null
      ? Number(payload.responsavel_id)
      : canAutoAssign
        ? (u?.id ?? null)
        : null;
  const responsavel_nome = payload?.responsavel_nome || (canAutoAssign ? u?.nome : null) || null;
  const responsavel_email = payload?.responsavel_email || (canAutoAssign ? u?.email : null) || null;

  const por = payload?.usuario_nome || u?.nome || "—";

  // FICHA ÚNICA: garante pessoa/família e vincula ao caso.
  const ficha = ensurePessoaBasica({
    nome: payload?.nome || "Pessoa",
    cpf: payload?.cpf,
    nis: payload?.nis,
    telefone: payload?.telefone,
  });
  const pessoa_id = ficha?.id || null;

  const c = {
    id,
    pessoa_id,
    nome: payload?.nome || "Pessoa",
    risco: payload?.risco || "medio",
    motivo_tema: payload?.motivo_tema || "Outro",
    motivo_detalhe: payload?.motivo_detalhe || "—",
    origem: payload?.origem || "Outro",

    // responsabilidade
    responsavel_id: responsavel_id || null,
    responsavel_nome: responsavel_nome || null,
    responsavel_email: responsavel_email || null,

    encerramento_status: null,

    status: "ativo",
    etapa_atual: "entrada",
    proximo_passo: payload?.proximo_passo || "Registrar triagem",
    proximo_passo_em: payload?.proximo_passo_em || iso,
    criado_em: iso,
    atualizado_em: iso,
    ultimo_registro_em: null,
    timeline: [
      {
        id: "tl_" + id + "_" + Date.now(),
        tipo: "criacao",
        texto: "Caso criado ✅",
        criado_em: iso,
        por,
      },
    ],
    atendimentos: [],
    encaminhamentos: [],
    documentos: [],
    linha_metro: buildLinhaMetroSkeleton(),
  };

  saveCreasCases([c, ...arr]);
  return c;
}

function riscoFromPrioridade(prio) {
  const p = String(prio || "media").toLowerCase();
  if (p === "alta" || p === "alto") return "alto";
  if (p === "baixa" || p === "baixo") return "baixo";
  return "medio";
}

/**
 * Aceita um encaminhamento interno (SUAS) e cria um caso no CREAS vinculado.
 * - Retorna o ID do caso criado.
 * - Não altera o layout (apenas dados).
 */
export function createCreasCaseFromSuasEncaminhamento(enc, usuario) {
  if (!enc) return null;
  const pessoa_id = enc?.pessoa_id != null ? Number(enc.pessoa_id) : null;

  // garante ficha básica se necessário
  if (pessoa_id && !Number.isNaN(pessoa_id)) {
    try {
      const p = getPessoaById(pessoa_id);
      if (!p) ensurePessoaBasica({ pessoa_id, nome: `Pessoa #${pessoa_id}` });
    } catch {}
  }

  const p = pessoa_id ? getPessoaById(pessoa_id) : null;
  const nome = p?.nome || `Pessoa #${pessoa_id || "—"}`;

  const created = createCreasCase({
    usuario,
    nome,
    risco: riscoFromPrioridade(enc?.prioridade),
    motivo_tema: "Encaminhamento (SUAS)",
    motivo_detalhe: enc?.motivo || "—",
    origem: enc?.origem_modulo || "Outro",
    proximo_passo: "Iniciar triagem",
    proximo_passo_em: nowIso(),
  });

  if (created?.id != null) {
    // vincula metadados do encaminhamento ao caso
    updateCreasCase(created.id, {
      origem_suas_modulo: enc?.origem_modulo || null,
      origem_suas_enc_id: enc?.id || null,
      origem_suas_caso_id: enc?.origem_caso_id || null,
      origem_suas_caso_label: enc?.origem_caso_label || null,
    });
    addTimeline(created.id, {
      tipo: "suas_enc",
      texto: `Encaminhamento recebido de ${enc?.origem_modulo || "equipamento"} ✅`,
      por: usuario?.nome || "—",
    });
  }

  return created?.id || null;
}

export function updateCreasCase(caseId, patch) {
  const arr = getCreasCases();
  const iso = nowIso();
  const updated = arr.map((c) => {
    if (Number(c?.id) !== Number(caseId)) return c;
    return { ...c, ...patch, atualizado_em: iso };
  });
  saveCreasCases(updated);
  return updated.find((x) => Number(x.id) === Number(caseId)) || null;
}

export function addTimeline(caseId, entry) {
  const arr = getCreasCases();
  const iso = nowIso();
  const updated = arr.map((c) => {
    if (Number(c?.id) !== Number(caseId)) return c;
    const tl = Array.isArray(c.timeline) ? c.timeline : [];
    const e = {
      id: entry?.id || "tl_" + caseId + "_" + Date.now(),
      tipo: entry?.tipo || "evento",
      texto: entry?.texto || "Atualização",
      criado_em: entry?.criado_em || iso,
      por: entry?.por || "—",
    };
    return { ...c, timeline: [e, ...tl], ultimo_registro_em: iso, atualizado_em: iso };
  });
  saveCreasCases(updated);
  return updated.find((x) => Number(x.id) === Number(caseId)) || null;
}

export function assumirCreasCase(caseId, usuario) {
  // Somente técnico/gestor assume caso.
  if (!usuario || (!isTecnico(usuario) && !isGestor(usuario))) return null;
  const u = normalizeUser(usuario);
  if (!u) return null;

  const c = updateCreasCase(caseId, {
    responsavel_id: u.id,
    responsavel_nome: u.nome,
    responsavel_email: u.email,
  });

  addTimeline(caseId, {
    tipo: "responsavel",
    texto: `Responsável definido: ${u.nome}`,
    por: u.nome,
  });

  return c;
}

function addMetroRegistroToCase(c, etapaCodigo, registro) {
  const safe = ensureLinhaMetroCase(c);
  const lm = safe?.linha_metro || buildLinhaMetroSkeleton();
  const etapas = Array.isArray(lm.etapas) ? lm.etapas : [];

  const nextEtapas = etapas.map((et) => {
    if (String(et?.codigo) !== String(etapaCodigo)) return et;
    const regs = Array.isArray(et?.registros) ? et.registros : [];
    const r = {
      id: registro?.id || `lm_${safe?.id || "c"}_${Date.now()}`,
      responsavel_nome: registro?.responsavel_nome || "—",
      data_hora: registro?.data_hora || nowIso(),
      obs: registro?.obs || null,
      atendimento_id: registro?.atendimento_id || null,
      encaminhamentos: Array.isArray(registro?.encaminhamentos) ? registro.encaminhamentos : [],
    };
    return {
      ...et,
      ultimo_registro: r,
      registros: [r, ...regs].slice(0, 50),
    };
  });

  return {
    ...safe,
    linha_metro: { ...lm, etapas: nextEtapas },
  };
}

/**
 * Registrar avanço na Linha do Metrô (MVP local)
 * - não altera etapa_atual automaticamente
 */
export function registrarAvancoMetro(caseId, payload, usuario) {
  const u = normalizeUser(usuario);
  const porNome = u?.nome || payload?.por || "—";
  const iso = nowIso();

  const etapa = payload?.etapa;
  if (!etapa) return null;

  const ids = Array.isArray(payload?.encaminhamentos_ids) ? payload.encaminhamentos_ids : [];

  const arr = getCreasCases();
  const updated = arr.map((c) => {
    if (Number(c?.id) !== Number(caseId)) return c;
    const encList = Array.isArray(c.encaminhamentos) ? c.encaminhamentos : [];
    const encMini = ids
      .map((id) => encList.find((e) => String(e?.id) === String(id)) || { id })
      .map((e) => ({ id: e?.id, destino: e?.destino, status: e?.status }));

    const next = addMetroRegistroToCase(c, etapa, {
      responsavel_nome: porNome,
      data_hora: iso,
      obs: payload?.obs || null,
      atendimento_id: payload?.atendimento_id || null,
      encaminhamentos: encMini,
    });

    return { ...next, ultimo_registro_em: iso, atualizado_em: iso };
  });

  saveCreasCases(updated);
  return updated.find((x) => Number(x.id) === Number(caseId)) || null;
}

export function addAtendimento(caseId, atendimento) {
  const arr = getCreasCases();
  const iso = nowIso();
  const updated = arr.map((c) => {
    if (Number(c?.id) !== Number(caseId)) return c;
    const list = Array.isArray(c.atendimentos) ? c.atendimentos : [];
    const a = {
      id: atendimento?.id || "at_" + caseId + "_" + Date.now(),
      tipo: atendimento?.tipo || "atendimento",
      data_hora: atendimento?.data_hora || iso,
      resumo: atendimento?.resumo || "—",
      proximo_passo: atendimento?.proximo_passo || c.proximo_passo || "—",
      proximo_passo_em: atendimento?.proximo_passo_em || c.proximo_passo_em || iso,
      por: atendimento?.por || "—",
    };

    // registra automaticamente na Linha do Metrô (etapa atual)
    const etapaLog = c?.etapa_atual || "entrada";
    const cMetro = addMetroRegistroToCase(c, etapaLog, {
      responsavel_nome: a.por || "—",
      data_hora: a.data_hora || iso,
      obs: a.resumo || null,
      atendimento_id: a.id,
      encaminhamentos: [],
    });
    return {
      ...cMetro,
      atendimentos: [a, ...list],
      proximo_passo: a.proximo_passo,
      proximo_passo_em: a.proximo_passo_em,
      ultimo_registro_em: iso,
      atualizado_em: iso,
    };
  });
  saveCreasCases(updated);
  return updated.find((x) => Number(x.id) === Number(caseId)) || null;
}

export function addEncaminhamento(caseId, enc) {
  const arr = getCreasCases();
  const iso = nowIso();
  const updated = arr.map((c) => {
    if (Number(c?.id) !== Number(caseId)) return c;
    const list = Array.isArray(c.encaminhamentos) ? c.encaminhamentos : [];
    const e = {
      id: enc?.id || "enc_" + caseId + "_" + Date.now(),
      destino: enc?.destino || "Rede",
      motivo: enc?.motivo || "—",
      prazo_retorno: enc?.prazo_retorno || null,
      status: enc?.status || "aguardando",
      retorno: enc?.retorno || null,
      criado_em: iso,
      por: enc?.por || "—",
    };

    // registra automaticamente na Linha do Metrô (etapa REDE)
    const cMetro = addMetroRegistroToCase(c, "rede", {
      responsavel_nome: e.por || "—",
      data_hora: iso,
      obs: e.destino ? `Encaminhamento: ${e.destino}` : "Encaminhamento",
      atendimento_id: null,
      encaminhamentos: [{ id: e.id, destino: e.destino }],
    });

    return { ...cMetro, encaminhamentos: [e, ...list], ultimo_registro_em: iso, atualizado_em: iso };
  });
  saveCreasCases(updated);
  return updated.find((x) => Number(x.id) === Number(caseId)) || null;
}

export function registrarRetornoRede(caseId, encId, retornoTexto) {
  const arr = getCreasCases();
  const iso = nowIso();
  const updated = arr.map((c) => {
    if (Number(c?.id) !== Number(caseId)) return c;
    const list = Array.isArray(c.encaminhamentos) ? c.encaminhamentos : [];
    const next = list.map((e) => {
      if (String(e.id) !== String(encId)) return e;
      return { ...e, status: "concluido", retorno: retornoTexto || "—", retorno_em: iso };
    });
    return { ...c, encaminhamentos: next, ultimo_registro_em: iso, atualizado_em: iso };
  });
  saveCreasCases(updated);
  return updated.find((x) => Number(x.id) === Number(caseId)) || null;
}

export function closeCreasCase(caseId, motivo_encerramento, resumo, usuarioAprovador = null, opts = null) {
  const iso = nowIso();
  const u = normalizeUser(usuarioAprovador);
  const existing = (getCreasCases() || []).find((x) => Number(x?.id) === Number(caseId)) || null;

  const motivo = motivo_encerramento || existing?.encerramento_solicitado_motivo || existing?.motivo_encerramento || "—";
  const resumoFinal = resumo || existing?.encerramento_solicitado_resumo || existing?.resumo_final || "—";

  const qualMap = (opts && opts.qualidade_checklist_snapshot) ? opts.qualidade_checklist_snapshot : (existing?.qualidade_checklist || null);
  const qualEx = Boolean(opts && opts.qualidade_excecao);
  const qualJust = String((opts && opts.qualidade_excecao_motivo) || "").trim() || null;

  const c = updateCreasCase(caseId, {
    status: "encerrado",
    etapa_atual: "encerramento",
    encerrado_em: iso,
    motivo_encerramento: motivo,
    resumo_final: resumoFinal,

    encerramento_status: "aprovado",
    encerramento_avaliado_em: iso,
    encerramento_avaliado_por_id: u?.id || null,
    encerramento_avaliado_por_nome: u?.nome || null,
    encerramento_recusa_motivo: null,

    encerramento_qualidade_checklist: qualMap,
    encerramento_qualidade_excecao: qualEx,
    encerramento_qualidade_excecao_motivo: qualEx ? qualJust : null,

    proximo_passo: "—",
    proximo_passo_em: null,
  });

  const detChecklist = qualMap
    ? Object.keys(qualMap)
        .map((k) => `- ${qualMap[k] ? "[x]" : "[ ]"} ${k}`)
        .join("\n")
    : "";

  addTimeline(caseId, {
    tipo: "encerramento",
    texto: "Encerramento aprovado e caso encerrado ✅",
    detalhe: detChecklist ? "Checklist:\n" + detChecklist : undefined,
    por: u?.nome || "—",
  });

  if (qualEx) {
    addTimeline(caseId, {
      tipo: "qualidade",
      texto: "Encerramento com exceção de qualidade ⚠️",
      detalhe: qualJust || "—",
      por: u?.nome || "—",
    });
  }

  return c;
}

// Fluxo B: técnico solicita, coordenação aprova
export function solicitarEncerramentoCreasCase(caseId, motivo, resumo, usuarioSolicitante) {
  const u = normalizeUser(usuarioSolicitante);
  if (!u) return null;

  const iso = nowIso();
  const existing = (getCreasCases() || []).find((x) => Number(x?.id) === Number(caseId)) || null;

  const c = updateCreasCase(caseId, {
    encerramento_status: "solicitado",
    encerramento_etapa_anterior: existing?.etapa_atual || null,

    encerramento_solicitado_em: iso,
    encerramento_solicitado_por_id: u.id,
    encerramento_solicitado_por_nome: u.nome,
    encerramento_solicitado_motivo: motivo || "—",
    encerramento_solicitado_resumo: resumo || "—",

    encerramento_avaliado_em: null,
    encerramento_avaliado_por_id: null,
    encerramento_avaliado_por_nome: null,
    encerramento_recusa_motivo: null,

    proximo_passo: "Aguardando aprovação do encerramento",
    proximo_passo_em: null,
  });

  addTimeline(caseId, {
    tipo: "encerramento",
    texto: "Encerramento solicitado — aguardando aprovação.",
    por: u.nome,
  });

  return c;
}

export function aprovarEncerramentoCreasCase(caseId, usuarioAprovador, opts = null) {
  const u = normalizeUser(usuarioAprovador);
  if (!u) return null;

  const existing = (getCreasCases() || []).find((x) => Number(x?.id) === Number(caseId)) || null;
  const motivo = existing?.encerramento_solicitado_motivo || "—";
  const resumo = existing?.encerramento_solicitado_resumo || "—";

  return closeCreasCase(caseId, motivo, resumo, usuarioAprovador, opts);
}

export function recusarEncerramentoCreasCase(caseId, motivoRecusa, usuarioAprovador) {
  const u = normalizeUser(usuarioAprovador);
  if (!u) return null;

  const iso = nowIso();
  const existing = (getCreasCases() || []).find((x) => Number(x?.id) === Number(caseId)) || null;
  const etapaVoltar = existing?.encerramento_etapa_anterior || existing?.etapa_atual || "acompanhamento";

  const c = updateCreasCase(caseId, {
    encerramento_status: "recusado",
    encerramento_avaliado_em: iso,
    encerramento_avaliado_por_id: u.id,
    encerramento_avaliado_por_nome: u.nome,
    encerramento_recusa_motivo: motivoRecusa || "—",

    // volta o caso para a etapa anterior (onde o técnico deve continuar)
    etapa_atual: etapaVoltar,
    proximo_passo: "Registrar atendimento",
    proximo_passo_em: iso,
  });

  addTimeline(caseId, {
    tipo: "encerramento",
    texto: `Encerramento recusado ❌ (${motivoRecusa || "—"})`,
    por: u.nome,
  });

  return c;
}
