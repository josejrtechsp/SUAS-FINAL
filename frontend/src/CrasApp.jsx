import React, { useEffect, useMemo, useState , useRef, useLayoutEffect} from "react";
import { API_BASE } from "./config.js";
import "./cras_ui_v2.css";
import "./cras_actions_apple.css";

import CrasSidebarNav from "./components/CrasSidebarNav.jsx";

import ErrorBoundary from "./components/ErrorBoundary.jsx";
import CrasPageHeader from "./components/CrasPageHeader.jsx";
import CrasTopHeader from "./components/CrasTopHeader.jsx";

import TelaCrasInicioDashboard from "./TelaCrasInicioDashboard.jsx";
import TelaCras from "./TelaCras.jsx";
import TelaCrasCadUnico from "./TelaCrasCadUnico.jsx";
import TelaCrasEncaminhamentos from "./TelaCrasEncaminhamentos.jsx";
import TelaCrasCasos from "./TelaCrasCasos.jsx";
import TelaCrasCadastros from "./TelaCrasCadastros.jsx";
import TelaCrasProgramas from "./TelaCrasProgramas.jsx";
import TelaCrasScfv from "./TelaCrasScfv.jsx";
import TelaCrasFicha from "./TelaCrasFicha.jsx";
import TelaCrasRelatorios from "./TelaCrasRelatorios.jsx";
import TelaCrasTarefas from "./TelaCrasTarefas.jsx";
import TelaCrasDocumentos from "./TelaCrasDocumentos.jsx";
import TelaCrasAutomacoes from "./TelaCrasAutomacoes.jsx";

export default function CrasApp({ usuarioLogado }) {
  const [activeTab, setActiveTab] = useState(() => localStorage.getItem("cras_active_tab") || "inicio");

  // foco (drilldown) entre telas
  const [scfvFocus, setScfvFocus] = useState(null);

  // Notificações simples (badge no tab)
  const [tarefasResumo, setTarefasResumo] = useState(null);

  const [municipios, setMunicipios] = useState([]);
  const [unidades, setUnidades] = useState([]);

  const [municipioAtivoId, setMunicipioAtivoId] = useState(() => {
    const saved = localStorage.getItem("cras_municipio_ativo");
    if (saved) return saved;
    return usuarioLogado?.municipio_id ? String(usuarioLogado.municipio_id) : "";
  });

  const [unidadeAtivaId, setUnidadeAtivaId] = useState(() => localStorage.getItem("cras_unidade_ativa") || "");

  useEffect(() => { try { localStorage.setItem("cras_active_tab", activeTab); } catch {} }, [activeTab]);
  useEffect(() => { try { localStorage.setItem("cras_municipio_ativo", municipioAtivoId || ""); } catch {} }, [municipioAtivoId]);
  useEffect(() => { try { localStorage.setItem("cras_unidade_ativa", unidadeAtivaId || ""); } catch {} }, [unidadeAtivaId]);

  async function loadTarefasResumo() {
    try {
      const qs = new URLSearchParams();
      if (unidadeAtivaId) qs.set("unidade_id", String(unidadeAtivaId));
      if (municipioAtivoId) qs.set("municipio_id", String(municipioAtivoId));
      const r = await apiFetch(`${API_BASE}/cras/tarefas/resumo?${qs.toString()}`);
      if (!r.ok) return setTarefasResumo(null);
      const j = await r.json();
      setTarefasResumo(j);
    } catch {
      setTarefasResumo(null);
    }
  }

  function getToken() {
    return (
      localStorage.getItem("poprua_token") ||
      localStorage.getItem("access_token") ||
      localStorage.getItem("token") ||
      ""
    );
  }

  async function apiFetch(url, options = {}) {
    const headers = new Headers(options.headers || {});
    const token = getToken();
    if (token && !headers.get("Authorization")) headers.set("Authorization", `Bearer ${token}`);

    const hasBody = options.body != null;
    const isForm = typeof FormData !== "undefined" && options.body instanceof FormData;
    if (hasBody && !isForm && !headers.get("Content-Type")) headers.set("Content-Type", "application/json");

    return fetch(url, { ...options, headers });
  }

  async function apiJson(path) {
    const res = await apiFetch(`${API_BASE}${path}`);
    const json = await res.json().catch(() => null);
    if (!res.ok) throw new Error(json?.detail || `Falha (HTTP ${res.status})`);
    return json;
  }

  useEffect(() => {
    (async () => {
      try { setMunicipios(await apiJson("/municipios")); } catch { setMunicipios([]); }
    })();
  }, []);

  useEffect(() => {
    if (!municipioAtivoId) return;
    (async () => {
      try { setUnidades(await apiJson(`/cras/unidades?municipio_id=${encodeURIComponent(municipioAtivoId)}`)); }
      catch { setUnidades([]); }
    })();
  }, [municipioAtivoId]);

  useEffect(() => {
    loadTarefasResumo();
    // eslint-disable-next-line
  }, [unidadeAtivaId, municipioAtivoId]);

  const municipioAtivoNome = useMemo(() => {
    const id = Number(municipioAtivoId || 0);
    const m = (municipios || []).find((x) => Number(x.id) === id);
    return m?.nome || (usuarioLogado?.municipio_nome || "");
  }, [municipios, municipioAtivoId, usuarioLogado]);

  const unidadeAtivaNome = useMemo(() => {
    const id = Number(unidadeAtivaId || 0);
    const u = (unidades || []).find((x) => Number(x.id) === id);
    return u?.nome || (usuarioLogado?.unidade_nome || usuarioLogado?.unidade_cras_nome || "");
  }, [unidades, unidadeAtivaId, usuarioLogado]);

// Sidebar (v2): colapsável + busca
  const [navCollapsed, setNavCollapsed] = useState(() => {
    try { return localStorage.getItem("cras_nav_collapsed") === "1"; } catch { return false; }
  });
  const [navQuery, setNavQuery] = useState("");

  useEffect(() => {
    try { localStorage.setItem("cras_nav_collapsed", navCollapsed ? "1" : "0"); } catch {}
  }, [navCollapsed]);

  const TAB_GROUPS = useMemo(() => {
    const badgeTarefas = tarefasResumo?.total_vencidas ? tarefasResumo.total_vencidas : 0;

    return [
      {
        title: "Visão geral",
        items: [
          { key: "inicio", label: "Início", icon: "home" },
        ],
      },
      {
        title: "Atendimento",
        items: [
          { key: "paif", label: "Triagem + PAIF", icon: "clipboard" },
          { key: "casos", label: "Casos", icon: "cases" },
          { key: "encaminhamentos", label: "Encaminhamentos", icon: "send" },
          { key: "tarefas", label: "Tarefas", icon: "tasks", badge: badgeTarefas || null },
        ],
      },
      {
        title: "Cadastros e serviços",
        items: [
          { key: "cadunico", label: "CadÚnico", icon: "id" },
          { key: "cadastros", label: "Cadastros", icon: "users" },
          { key: "programas", label: "Programas", icon: "grid" },
          { key: "scfv", label: "SCFV", icon: "calendar" },
          { key: "ficha", label: "Ficha", icon: "file" },
        ],
      },
      {
        title: "Gestão",
        items: [
          { key: "automacoes", label: "Automações", icon: "bolt" },
          { key: "documentos", label: "Documentos", icon: "doc" },
          { key: "relatorios", label: "Relatórios", icon: "chart" },
        ],
      },
    ];
  }, [tarefasResumo]);

  const TAB_META = useMemo(() => ({
    inicio: {
      title: "Início",
      subtitle: "Painel operacional do CRAS: pendências, prazos e presença.",
      chips: ["Pendências por SLA", "Equipe e prazos", "Presença (SCFV/Programas)", "Ações rápidas"],
    },
    paif: {
      title: "Triagem + PAIF",
      subtitle: "Abertura, triagem, plano e histórico auditável (LGPD).",
      chips: ["Triagem", "Checklist por etapa", "Histórico auditável"],
    },
    cadunico: {
      title: "CadÚnico",
      subtitle: "Pré-cadastro, agendamentos, pendências e histórico — uma tela por vez.",
      chips: [],
    },
    encaminhamentos: {
      title: "Encaminhamentos",
      subtitle: "Fluxo CRAS/CREAS/PopRua: envio, recebimento e prazos.",
      chips: ["Filtros","Novo","Sem devolutiva","Encaminhamento SUAS","Todos"] /* ENC_CHIPS_V1 */,
    },
    casos: {
      title: "Casos",
      subtitle: "Linha do metrô (etapas + SLA), evidências e contrarreferência — use as subtelas para criar, filtrar e operar a lista.",
      chips: [],
    },
    tarefas: {
      title: "Tarefas",
      subtitle: "Equipe, prazos, vencidas e concluídas (SLA).",
      chips: ["Por técnico","Vencidas","Metas","Concluir em lote"],
    },
    automacoes: {
      title: "Automações",
      subtitle: "Rotinas e notificações para garantir prazos e padronização.",
      chips: ["Modelos", "Regras", "Disparo", "Logs"],
    },
    cadastros: {
      title: "Cadastros",
      subtitle: "Pessoas, famílias e vínculos — use as subtelas para operar uma tela por vez.",
      chips: [],
    },
    programas: {
      title: "Programas",
      subtitle: "Gestão de ofertas e presença por programa.",
      chips: ["Programas", "Presença", "Indicadores"],
    },
    scfv: {
      title: "SCFV",
      subtitle: "Turmas, frequência, evasão e exportação.",
      chips: [],
    },
    ficha: {
      title: "Ficha",
      subtitle: "Ficha única com visão 360 — use as subtelas para navegar por resumo, documentos, histórico e impressão.",
      chips: [],
    },
    documentos: {
      title: "Documentos",
      subtitle: "Geração e biblioteca de modelos com branding.",
      chips: ["Modelos", "Branding", "PDF", "Verificação"],
    },
    relatorios: {
      title: "Relatórios",
      subtitle: "Indicadores, gargalos e visão regional.",
      chips: ["KPIs", "Gargalos", "SLA", "Exportação"],
    },
  }), []);

  const activeMeta = TAB_META[activeTab] || { title: "CRAS", subtitle: "", chips: [] };

  // TAB_SUBTABS_V2 — subtelas do header (1 por vez)
  // TAB_SUBTABS_PAIF_V1
  const TAB_SUBTABS = useMemo(() => ({
    paif: [
      { key: "unidade", label: "Unidade CRAS" },
      { key: "fila", label: "Fila" },
      { key: "pendencias", label: "Pendências" },
      { key: "historico", label: "Histórico" },
      { key: "relatorios", label: "Relatórios" },
    ],
    cadunico: [
      { key: "precadastro", label: "Pré-cadastro" },
      { key: "agendamentos", label: "Agendamentos" },
      { key: "pendencias", label: "Pendências" },
      { key: "historico", label: "Histórico" },
    ],
    casos: [
      { key: "criar", label: "Criar caso" },
      { key: "filtros", label: "Filtros" },
      { key: "lista", label: "Lista de casos" },
    ],


    encaminhamentos: [
      { key: "filtros", label: "Filtros" },
      { key: "novo", label: "Novo" },
      { key: "semdev", label: "Sem devolutiva" },
      { key: "suas", label: "Encaminhamento SUAS" },
      { key: "todos", label: "Todos" },
    ],

    tarefas: [
      { key: "por_tecnico", label: "Por técnico" },
      { key: "vencidas", label: "Vencidas" },
      { key: "metas", label: "Metas" },
      { key: "lote", label: "Concluir em lote" },
    ],

    programas: [
      { key: "lista", label: "Lista" },
      { key: "elegiveis", label: "Elegíveis" },
      { key: "acompanhamento", label: "Acompanhamento" },
      { key: "relatorios", label: "Relatórios" },
    ],
    scfv: [
      { key: "chamada", label: "Chamada" },
      { key: "turmas", label: "Turmas" },
      { key: "alertas", label: "Alertas" },
      { key: "exportar", label: "Exportar" },
    ],
    cadastros: [
      { key: "pessoas", label: "Pessoas" },
      { key: "familias", label: "Famílias" },
      { key: "vinculos", label: "Vínculos" },
      { key: "atualizacao", label: "Atualização" },
    ],
ficha: [
  { key: "resumo", label: "Resumo" },
  { key: "documentos", label: "Documentos" },
  { key: "historico", label: "Histórico" },
  { key: "impressao", label: "Impressão/PDF" },
],
  
    // --- GESTAO_SUBTABS_V1 ---
    automacoes: [
      { key: "ativas", label: "Regras ativas" },
      { key: "criar", label: "Criar automação" },
      { key: "historico", label: "Histórico" },
      { key: "relatorios", label: "Relatórios" },
    ],
    documentos: [
      { key: "modelos", label: "Modelos" },
      { key: "emitir", label: "Emitir documento" },
      { key: "assinaturas", label: "Assinaturas" },
      { key: "historico", label: "Histórico" },
    ],
    relatorios: [
      { key: "painel", label: "Painel" },
      { key: "exportar", label: "Exportar" },
      { key: "indicadores", label: "Indicadores" },
      { key: "metas", label: "Metas" },
    ],
}), []);

  const TAB_SUBTABS_DEFAULT = useMemo(() => ({
    paif: "fila",
    cadunico: "precadastro",
    encaminhamentos: "suas",
    tarefas: "por_tecnico",
    cadastros: "pessoas",
    scfv: "chamada",

    ficha: "resumo",
    programas: "lista",
    // --- GESTAO_SUBTABS_DEFAULT_V1 ---
    automacoes: "ativas",
    documentos: "modelos",
    relatorios: "painel",
}), []);



  const headerSubtabs = TAB_SUBTABS[activeTab] || [];
  const subtabStorageKey = `cras_subtab_${activeTab}`;

  const [activeSubtab, setActiveSubtab] = useState(() => {
    try {
      const def = TAB_SUBTABS_DEFAULT[activeTab] || headerSubtabs[0]?.key || "";
      return localStorage.getItem(subtabStorageKey) || def;
    } catch {
      return headerSubtabs[0]?.key || "";
    }
  });

  useEffect(() => {
    const def = TAB_SUBTABS_DEFAULT[activeTab] || (TAB_SUBTABS[activeTab] || [])[0]?.key || "";
    let saved = "";
    try { saved = localStorage.getItem(`cras_subtab_${activeTab}`) || ""; } catch {}
    setActiveSubtab(saved || def);
    // eslint-disable-next-line
  }, [activeTab]);

  useEffect(() => {
    try {
      localStorage.setItem(`cras_subtab_${activeTab}`, activeSubtab || "");
    } catch {}
  }, [activeTab, activeSubtab]);

  // TAB_HELP_V1 — guia rápido por subtela (recolhido; "Ver como usar")
  const TAB_HELP = useMemo(() => ({
    paif: {
      unidade: {
        title: "Guia rápido",
        summary: "Defina a unidade do CRAS que você está operando agora.",
        what: "Esta tela configura qual unidade (CRAS) estará ativa para a fila, pendências, histórico e relatórios.",
        steps: [
          "Selecione a unidade CRAS (ou crie a unidade padrão, se necessário).",
          "Clique em ‘Atualizar fila’ para sincronizar os números do dia.",
          "Volte para ‘Fila’ para iniciar o atendimento.",
        ],
        after: "A unidade ativa passa a ser usada nas consultas e nos registros de triagem/PAIF.",
      },
      fila: {
        title: "Guia rápido",
        summary: "Gerencie os atendimentos do dia e registre a triagem.",
        what: "A fila organiza os atendimentos de hoje (por unidade), com prioridade, canal e demanda principal.",
        steps: [
          "Confira os atendimentos na lista e identifique prioridade/canal.",
          "Registre uma nova triagem (demanda + observação) e vincule pessoa quando possível.",
          "Quando houver pessoa vinculada, use ‘Converter em PAIF’ para abrir acompanhamento.",
        ],
        after: "Triagens podem ser encerradas ou convertidas em PAIF. O histórico fica auditável.",
      },
      pendencias: {
        title: "Guia rápido",
        summary: "Encontre o que falta resolver para não perder prazo.",
        what: "Pendências reúnem triagens abertas, triagens sem pessoa vinculada (não converte) e pontos que exigem atenção.",
        steps: [
          "Priorize triagens abertas e casos sem pessoa vinculada.",
          "Conclua o que falta (encerrar, converter em PAIF, registrar observações).",
          "Use esta visão como ‘caixa de entrada’ do dia.",
        ],
        after: "Pendências resolvidas reduzem retrabalho e ajudam a cumprir SLA/prazos.",
      },
      historico: {
        title: "Guia rápido",
        summary: "Consulte atendimentos anteriores (consulta e auditoria).",
        what: "O histórico permite buscar triagens por data, mantendo rastreabilidade e continuidade do atendimento.",
        steps: [
          "Escolha uma data e clique em ‘Buscar’.",
          "Abra os registros para conferir demanda, canal, prioridade e desfecho.",
          "Use isso para entender o contexto antes de novas ações.",
        ],
        after: "Você evita retrabalho e garante coerência no acompanhamento.",
      },
      relatorios: {
        title: "Guia rápido",
        summary: "Acompanhe números e exporte evidências de gestão.",
        what: "Relatórios mostram totais do dia por status/prioridade/canal e permitem exportar CSV para prestação de contas.",
        steps: [
          "Confira os indicadores (total, abertas, encerradas, convertidas).",
          "Use o agrupamento por prioridade e canal para identificar gargalos.",
          "Exporte CSV quando precisar de evidência/registro.",
        ],
        after: "Isso apoia coordenação, metas e monitoramento da unidade.",
      },
    },
    cadunico: {
      precadastro: {
        title: "Guia rápido",
        summary: "Crie e organize pré-cadastros do CadÚnico (pendentes).",
        what: "O pré-cadastro registra a demanda de atualização/inclusão no CadÚnico e vincula a um caso, pessoa ou família.",
        steps: [
          "Selecione Caso, Pessoa ou Família (pelo menos um vínculo).",
          "Registre observações quando necessário e clique em ‘Criar pré-cadastro’.",
          "Acompanhe a lista pendente e agende quando a família/pessoa confirmar presença.",
        ],
        after: "O pré-cadastro entra na fila do CadÚnico da unidade, com rastreabilidade e histórico de status.",
      },
      agendamentos: {
        title: "Guia rápido",
        summary: "Gerencie atendimentos agendados (reagendar, finalizar, não compareceu).",
        what: "Aqui ficam os pré-cadastros com data/hora marcada para atendimento do CadÚnico.",
        steps: [
          "Abra um item e confira data/hora e observações.",
          "Use ‘Reagendar’ quando houver necessidade de remarcação.",
          "Após atendimento, marque ‘Finalizar’ ou ‘Não compareceu’.",
        ],
        after: "A lista fica sempre atualizada e evita perda de prazos e retrabalho.",
      },
      pendencias: {
        title: "Guia rápido",
        summary: "Veja o que está pendente ou com ausência registrada.",
        what: "Pendências reúne ‘Pendente’ e ‘Não compareceu’ para priorizar reagendamentos e resolução rápida.",
        steps: [
          "Priorize registros com ‘Não compareceu’ para reagendar.",
          "Agende os pendentes para organizar a agenda da unidade.",
          "Finalize quando o atendimento for concluído.",
        ],
        after: "Você reduz fila invisível e melhora o controle da rotina do CadÚnico.",
      },
      historico: {
        title: "Guia rápido",
        summary: "Consulte registros finalizados para auditoria e continuidade.",
        what: "Histórico mostra os pré-cadastros já finalizados, com vínculo e evidências do atendimento.",
        steps: [
          "Use a lista para localizar um registro pelo vínculo (caso/pessoa/família).",
          "Confira observações e data agendada, quando houver.",
          "Use como evidência e referência em novos atendimentos.",
        ],
        after: "Ajuda coordenação, controle interno e continuidade do acompanhamento.",
      },
    },
    cadastros: {
      pessoas: {
        title: "Guia rápido",
        summary: "Cadastre e localize pessoas para vincular em famílias, casos e CadÚnico.",
        what: "Pessoas são o ponto de partida para atendimento: você encontra CPF/NIS, território e pode vincular em família e em caso.",
        steps: [
          "Cadastre a pessoa (nome; CPF/NIS se houver).",
          "Confira bairro/território para gestão territorial.",
          "Use a pessoa para criar família, abrir caso ou pré-cadastro do CadÚnico.",
        ],
        after: "A pessoa fica disponível para vínculos e para o histórico do atendimento.",
      },
      familias: {
        title: "Guia rápido",
        summary: "Crie famílias e mantenha endereço/território atualizados.",
        what: "Famílias organizam membros sob um mesmo endereço/território e permitem gestão por território e acompanhamento do núcleo familiar.",
        steps: [
          "Preencha endereço/bairro/território (se houver).",
          "Selecione uma pessoa de referência (opcional).",
          "Após cadastrar, vá em ‘Vínculos’ para adicionar os membros.",
        ],
        after: "A família passa a aparecer em CadÚnico, Ficha e Casos quando vinculada.",
      },
      vinculos: {
        title: "Guia rápido",
        summary: "Monte a composição familiar: membros, parentesco e responsável.",
        what: "Vínculos definem quem compõe a família e quem é o responsável — isso melhora a ficha, CadÚnico e encaminhamentos.",
        steps: [
          "Selecione uma família.",
          "Escolha uma pessoa e informe parentesco (opcional).",
          "Marque ‘Responsável’ quando for o caso e adicione.",
        ],
        after: "A composição familiar fica consistente e evita retrabalho em atendimentos futuros.",
      },
      atualizacao: {
        title: "Guia rápido",
        summary: "Atualize a base e confira consistência antes de operar atendimentos.",
        what: "Use esta tela para recarregar pessoas/famílias e validar se não há duplicidade ou cadastro incompleto.",
        steps: [
          "Clique em ‘Atualizar agora’ para recarregar a base.",
          "Se identificar duplicidade (CPF/NIS), corrija em Pessoas.",
          "Se a família estiver incompleta, ajuste em Famílias/Vínculos.",
        ],
        after: "Uma base consistente reduz erros e melhora a qualidade do atendimento.",
      },
    },


    programas: {
      lista: {
        title: "Guia rápido",
        summary: "Organize e consulte programas/projetos do CRAS por unidade.",
        what: "Aqui você visualiza os programas/projetos cadastrados, consulta detalhes e decide o próximo passo (elegíveis ou acompanhamento).",
        steps: [
          "Selecione um programa/projeto na lista para ver detalhes.",
          "Use os atalhos para ir para ‘Elegíveis’ (inscrição) ou ‘Acompanhamento’ (participantes).",
          "Se precisar, crie um novo programa na própria área (subtela ‘Lista’).",
        ],
        after: "O programa fica pronto para inscrição de participantes e registro de acompanhamento.",
      },
      elegiveis: {
        title: "Guia rápido",
        summary: "Inscreva pessoas elegíveis no programa escolhido.",
        what: "A tela mostra pessoas cadastradas e permite inscrever no programa selecionado, respeitando capacidade e evitando duplicidade.",
        steps: [
          "Selecione um programa/projeto.",
          "Escolha a pessoa na lista (a partir do cadastro).",
          "Clique em ‘Inscrever’ e confirme na lista de participantes.",
        ],
        after: "A pessoa passa a constar como participante do programa e entra no acompanhamento.",
      },
      acompanhamento: {
        title: "Guia rápido",
        summary: "Acompanhe participantes e a execução do programa.",
        what: "Consulte participantes por programa, status e dados básicos para manter continuidade do acompanhamento.",
        steps: [
          "Selecione um programa/projeto.",
          "Verifique a lista de participantes e seus status.",
          "Registre evidências/ações na ficha do caso quando necessário.",
        ],
        after: "Você mantém rastreabilidade e consegue demonstrar execução e resultados.",
      },
      relatorios: {
        title: "Guia rápido",
        summary: "Gere indicadores e exporte listas para gestão e prestação de contas.",
        what: "Veja quantitativos por programa (por unidade) e exporte CSV para apoiar gestão, metas e evidências.",
        steps: [
          "Escolha o programa (ou visão geral).",
          "Gere o resumo e valide os números.",
          "Exporte CSV para compartilhar com coordenação/gestão.",
        ],
        after: "Relatórios ajudam em monitoramento, pactuação e auditoria.",
      },
    },

    scfv: {
      chamada: {
        title: "Guia rápido",
        summary: "Registre presença por turma e por data.",
        what: "Use esta tela para marcar presença/ausência e salvar em lote. Tudo fica ligado à turma e à unidade ativa.",
        steps: [
          "Selecione a turma e a data da chamada.",
          "Marque Presente/Ausente (use 'Marcar todos' quando ajudar).",
          "Clique em 'Salvar lote' para gravar e depois 'Recarregar' para conferir.",
        ],
        after: "A presença alimenta alertas, relatório mensal e exportações.",
      },
      turmas: {
        title: "Guia rápido",
        summary: "Crie turmas e gerencie participantes.",
        what: "Nesta tela você cadastra turmas do SCFV e inscreve pessoas (participantes) para aparecerem na chamada.",
        steps: [
          "Crie uma turma (nome, dias/horário e vagas se desejar).",
          "Selecione a turma na lista.",
          "Inscreva participantes usando o cadastro de Pessoas.",
        ],
        after: "Com participantes inscritos, você consegue fazer chamada e gerar relatórios.",
      },
      alertas: {
        title: "Guia rápido",
        summary: "Identifique evasão, baixa presença e dias sem registro.",
        what: "Alertas destacam turmas/participantes com risco (faltas seguidas) ou baixa presença no mês.",
        steps: [
          "Escolha o mês e os limites (faltas seguidas e presença mínima).",
          "Atualize o painel da unidade e selecione a turma com alerta.",
          "Gere o resumo do mês para ver quem precisa de busca ativa.",
        ],
        after: "Você pode abrir o relatório completo na subtela Exportar para evidência/gestão.",
      },
      exportar: {
        title: "Guia rápido",
        summary: "Gere relatório mensal e exporte CSV (resumo ou detalhado).",
        what: "Aqui você consolida o mês por turma, visualiza totais, alertas e exporta para prestação de contas.",
        steps: [
          "Selecione turma e mês.",
          "Clique em 'Gerar' para montar o relatório.",
          "Use 'Exportar CSV' ou 'CSV (datas)' conforme a necessidade.",
        ],
        after: "Relatórios apoiam coordenação, metas e evidências do serviço.",
      },
    },
ficha: {
  resumo: {
    title: "Guia rápido",
    summary: "Veja a ficha única (pessoa ou família) em modo resumo.",
    what: "A ficha consolida informações do usuário/família e aponta pendências e vínculos importantes (CadÚnico, Casos, SCFV).",
    steps: [
      "Escolha se a ficha é de Pessoa ou Família (no bloco de seleção).",
      "Selecione o registro desejado e clique em ‘Atualizar’ quando precisar.",
      "Use esta visão para entender o contexto antes de registrar novos atendimentos.",
    ],
    after: "Com o contexto claro, você evita retrabalho e melhora a continuidade do atendimento.",
  },
  documentos: {
    title: "Guia rápido",
    summary: "Organize documentos e anexos ligados à pessoa/família.",
    what: "Nesta tela você cadastra anexos (links/arquivos) e mantém evidências do atendimento de forma simples e auditável.",
    steps: [
      "Selecione Pessoa ou Família e escolha o registro.",
      "Adicione anexos com título e tipo (ex.: RG, declaração, comprovante).",
      "Use a lista para consultar e abrir rapidamente quando necessário.",
    ],
    after: "Documentos bem organizados reduzem perda de informação e facilitam prestação de contas.",
  },
  historico: {
    title: "Guia rápido",
    summary: "Consulte a timeline e eventos registrados (auditoria).",
    what: "Histórico mostra eventos e movimentações relevantes no período, ajudando a entender a trajetória do usuário/família.",
    steps: [
      "Selecione Pessoa ou Família e o registro desejado.",
      "Use a timeline para localizar os eventos mais recentes.",
      "Abra casos/serviços relacionados quando precisar atuar.",
    ],
    after: "Isso garante rastreabilidade e melhora a tomada de decisão da equipe.",
  },
  impressao: {
    title: "Guia rápido",
    summary: "Gere PDF/CSV da ficha para evidência e impressão.",
    what: "A impressão consolida resumo, pendências e histórico do período selecionado e permite exportar em PDF/CSV.",
    steps: [
      "Selecione Pessoa ou Família e o registro desejado.",
      "Clique em ‘PDF’ para imprimir/salvar em PDF (abre janela de impressão).",
      "Use CSV quando precisar trabalhar em planilhas ou enviar dados para gestão.",
    ],
    after: "Você produz evidências padronizadas para coordenação, auditoria e prestação de contas.",
  },
},


    // --- GESTAO_HELP_V1 ---
    automacoes: {
      ativas: {
        title: "Guia rápido",
        summary: "Regras automáticas de prazos, alertas e execução por SLA.",
        what: "Use para padronizar cobranças, prazos e rotinas sem depender de planilhas.",
        steps: ["Revise as regras ativas.", "Simule (dry-run) antes de executar.", "Execute e acompanhe o histórico."],
        after: "O sistema registra execuções e reduz pendências por esquecimento.",
      },
      criar: {
        title: "Guia rápido",
        summary: "Crie ou ajuste automações conforme a rotina do CRAS.",
        what: "Você define regra, frequência e alvo (unidade/município).",
        steps: ["Escolha um modelo (seed) ou ajuste uma regra existente.", "Defina frequência e ativação.", "Teste com simulação."],
        after: "As regras passam a rodar e gerar tarefas/alertas automaticamente.",
      },
      historico: {
        title: "Guia rápido",
        summary: "Audite o que foi executado e o que foi gerado.",
        what: "Histórico ajuda coordenação e prestação de contas.",
        steps: ["Abra a última execução.", "Confira itens gerados e falhas.", "Ajuste regras se necessário."],
        after: "Você melhora a qualidade e reduz re-trabalho.",
      },
      relatorios: {
        title: "Guia rápido",
        summary: "Consolide resultado das automações por período.",
        what: "Use para enxergar impacto: vencidas, concluídas, tempo médio.",
        steps: ["Selecione período.", "Compare unidades.", "Exporte CSV para gestão."],
        after: "Gestor ganha visão objetiva de gargalos.",
      },
    },
    documentos: {
      modelos: {
        title: "Guia rápido",
        summary: "Gerencie modelos oficiais (ofício, memorando, relatório etc.).",
        what: "Modelos padronizam a escrita e evitam erro de formatação.",
        steps: ["Escolha um modelo.", "Revise campos obrigatórios.", "Gere uma prévia."],
        after: "A emissão fica rápida e consistente entre equipes.",
      },
      emitir: {
        title: "Guia rápido",
        summary: "Preencha campos e emita o PDF com numeração e histórico.",
        what: "Você garante rastreabilidade e prova documental do atendimento/gestão.",
        steps: ["Selecione o modelo.", "Preencha campos.", "Gere PDF e salve."],
        after: "O documento entra no histórico e pode ser conferido depois.",
      },
      assinaturas: {
        title: "Guia rápido",
        summary: "Assinaturas são campos do documento (cargo, nome e data).",
        what: "Use para padronizar quem assina e como aparece no PDF.",
        steps: ["Selecione o modelo.", "Preencha assinatura.", "Gere prévia para conferir."],
        after: "Evita documento sem responsável ou com cargo errado.",
      },
      historico: {
        title: "Guia rápido",
        summary: "Consulte documentos emitidos e baixe novamente quando precisar.",
        what: "Histórico serve para auditoria e reimpressão rápida.",
        steps: ["Filtre por tipo/período.", "Abra/baixe o PDF.", "Valide número e assunto."],
        after: "Você reduz retrabalho e mantém evidência documental.",
      },
    },
    relatorios: {
      painel: {
        title: "Guia rápido",
        summary: "Visão consolidada de gargalos e volume por área.",
        what: "Painel é a primeira tela para gestor enxergar onde travou.",
        steps: ["Selecione período/unidade.", "Atualize dados.", "Leia alertas."],
        after: "Decisões de equipe e prazo ficam baseadas em dado.",
      },
      exportar: {
        title: "Guia rápido",
        summary: "Exporte dados em CSV/PDF para prestação de contas.",
        what: "Use para planilhas, apresentações e controle interno.",
        steps: ["Atualize a base.", "Escolha o conjunto de dados.", "Exporte."],
        after: "Você compartilha resultados sem depender de prints.",
      },
      indicadores: {
        title: "Guia rápido",
        summary: "Acompanhe série histórica e tendências.",
        what: "Indicadores mostram aumento de demanda e efeito de ações.",
        steps: ["Selecione período maior.", "Compare mês a mês.", "Identifique tendência."],
        after: "Você antecipa problemas e planeja equipe.",
      },
      metas: {
        title: "Guia rápido",
        summary: "Metas organizam foco e SLA por área.",
        what: "Defina metas simples (ex.: reduzir vencidas em X%).",
        steps: ["Defina meta.", "Acompanhe semanalmente.", "Ajuste rotinas."],
        after: "Equipe trabalha com objetivo claro.",
      },
    },
}), []);

  const activeHelp = (TAB_HELP[activeTab] || {})[activeSubtab] || null;



  const pageActions = useMemo(() => ([
    { key: "tarefas", label: "Tarefas", variant: "ghost" },
    { key: "relatorios", label: "Relatórios", variant: "primary" },
  ]), []);

  function sair() {
    localStorage.removeItem("poprua_token");
    localStorage.removeItem("poprua_usuario");
    window.location.reload();
  }

  function portal() {
    window.location.href = "/app";
  }

  // Compat: algumas telas antigas chamam onNavigate('tab', params)
  const onNavigate = (x, params) => {
    if (!x) return;
    if (typeof x === "string") {
      const tab = x;
      setActiveTab(tab);
      if (tab === "scfv" && params) setScfvFocus(params);
      return;
    }
    if (x?.tab) setActiveTab(x.tab);
    if (x?.tab === "scfv" && x?.focus) setScfvFocus(x.focus);
  };

  function renderBody() {
    switch (activeTab) {
      case "inicio":
        return (
          <ErrorBoundary label="CRAS · Início">
            <TelaCrasInicioDashboard
              apiBase={API_BASE}
              apiFetch={apiFetch}
              onNavigate={onNavigate}
              unidadeId={unidadeAtivaId || null}
              municipioId={municipioAtivoId || null}
            />
          </ErrorBoundary>
        );

      case "paif":
        return (
          <ErrorBoundary label="CRAS · Triagem + PAIF">
            <TelaCras
              apiBase={API_BASE}
              apiFetch={apiFetch}
              usuarioLogado={usuarioLogado}
              view={activeSubtab || "fila"}
              onSetView={setActiveSubtab}
            />
          </ErrorBoundary>
        );

      case "cadunico":
        return (
          <ErrorBoundary label="CRAS · CadÚnico">
            <TelaCrasCadUnico
              apiBase={API_BASE}
              apiFetch={apiFetch}
              view={activeSubtab || "precadastro"}
              onSetView={setActiveSubtab}
              unidadeAtivaId={unidadeAtivaId}
            />
          </ErrorBoundary>
        );

      case "encaminhamentos":
        return (
          <ErrorBoundary label="CRAS · Encaminhamentos">
            <TelaCrasEncaminhamentos
              apiBase={API_BASE}
              apiFetch={apiFetch}
              usuarioLogado={usuarioLogado}
              onNavigate={onNavigate}
              municipioId={municipioAtivoId || null}
              unidadeId={unidadeAtivaId || null}
              // compat: alguns arquivos usam subView/onSubViewChange
              subView={activeSubtab || "suas"}
              onSubViewChange={setActiveSubtab}
              // compat: outros arquivos usam view/onSetView
              view={activeSubtab || "suas"}
              onSetView={setActiveSubtab}
            />
          </ErrorBoundary>
        );
case "casos":
        return (
          <ErrorBoundary label="CRAS · Casos">
            <TelaCrasCasos
              apiBase={API_BASE}
              apiFetch={apiFetch}
              usuarioLogado={usuarioLogado}
              view={activeSubtab || "lista"}
              onSetView={setActiveSubtab} onNavigate={onNavigate} />
          </ErrorBoundary>
        );

      case "tarefas":
        return (
          <ErrorBoundary label="CRAS · Tarefas">
            <TelaCrasTarefas
              apiBase={API_BASE}
              apiFetch={apiFetch}
              usuarioLogado={usuarioLogado}
              onNavigate={onNavigate}
              onChanged={loadTarefasResumo}
              municipioId={municipioAtivoId || null}
              unidadeId={unidadeAtivaId || null}
              // compat: subView/onSubViewChange (padrão antigo)
              subView={activeSubtab || "por_tecnico"}
              onSubViewChange={setActiveSubtab}
              // compat: view/onSetView (padrão novo)
              view={activeSubtab || "por_tecnico"}
              onSetView={setActiveSubtab}
            />
          </ErrorBoundary>
        );
case "automacoes":
        return (
          <ErrorBoundary label="CRAS · Automações">
            <TelaCrasAutomacoes
              apiBase={API_BASE}
              apiFetch={apiFetch}
              usuarioLogado={usuarioLogado}
              onNavigate={onNavigate}
            
              view={activeSubtab || "ativas"}
              onSetView={setActiveSubtab}
            />
          </ErrorBoundary>
        );

      case "cadastros":
        return (
          <ErrorBoundary label="CRAS · Cadastros">
            <TelaCrasCadastros
              apiBase={API_BASE}
              apiFetch={apiFetch}
              usuarioLogado={usuarioLogado}
              view={activeSubtab || "pessoas"}
              onSetView={setActiveSubtab}
            />
          </ErrorBoundary>
        );

      case "programas":
        return (
          <ErrorBoundary label="CRAS · Programas">
            <TelaCrasProgramas
              apiBase={API_BASE}
              apiFetch={apiFetch}
              usuarioLogado={usuarioLogado}
              view={activeSubtab || "lista"}
              onSetView={setActiveSubtab}
              onNavigate={onNavigate}
            />
          </ErrorBoundary>
        );

      // PROGRAMAS_SUBTABS_HELP_V1
// SCFV_SUBTABS_HELP_V1
case "scfv":
        return (
          <ErrorBoundary label="CRAS · SCFV">
            <TelaCrasScfv
              apiBase={API_BASE}
              apiFetch={apiFetch}
              onNavigate={onNavigate}
              focus={scfvFocus}
              onFocusConsumed={() => setScfvFocus(null)}
              view={activeSubtab || "chamada"}
              onSetView={setActiveSubtab}
            />
          </ErrorBoundary>
        );

      case "ficha":
        return (
          <ErrorBoundary label="CRAS · Ficha">
            <TelaCrasFicha apiBase={API_BASE} apiFetch={apiFetch} onNavigate={onNavigate} view={activeSubtab || "resumo"} />
          </ErrorBoundary>
        );

      case "documentos":
        return (
          <ErrorBoundary label="CRAS · Documentos">
            <TelaCrasDocumentos apiBase={API_BASE} apiFetch={apiFetch} usuarioLogado={usuarioLogado} 
              view={activeSubtab || "modelos"}
              onSetView={setActiveSubtab}
            />
          </ErrorBoundary>
        );

      case "relatorios":
        return (
          <ErrorBoundary label="CRAS · Relatórios">
            <TelaCrasRelatorios apiBase={API_BASE} apiFetch={apiFetch} onNavigate={onNavigate} 
              view={activeSubtab || "painel"}
              onSetView={setActiveSubtab}
            />
          </ErrorBoundary>
        );

      default:
        return null;
    }
  }

  const handleTab = (key) => {
    if (!key) return;
    setActiveTab(key);
    // pequena ajuda: ao trocar de seção, rola para o topo da área principal
    try {
      const el = document.querySelector(".cras-stage-v2");
      if (el) el.scrollIntoView({ behavior: "smooth", block: "start" });
    } catch {}
  };

  return (
    <div className="app-root cras-ui-v2">
      <CrasTopHeader
        usuarioLogado={usuarioLogado}
        municipios={municipios}
        municipioAtivoId={municipioAtivoId}
        setMunicipioAtivoId={setMunicipioAtivoId}
        unidades={unidades}
        unidadeAtivaId={unidadeAtivaId}
        setUnidadeAtivaId={setUnidadeAtivaId}
        tabs={[]}
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        onPortal={portal}
        onSair={sair}
      />

      <main className="app-main">
        <div className={"cras-shell-v2" + (navCollapsed ? " is-nav-collapsed" : "")}>
<CrasSidebarNav
            groups={TAB_GROUPS}
            activeKey={activeTab}
            onChange={handleTab}
            collapsed={navCollapsed}
            onToggleCollapsed={() => setNavCollapsed((v) => !v)}
            query={navQuery}
            setQuery={setNavQuery}
            municipioNome={municipioAtivoNome || "Município"}
            unidadeNome={unidadeAtivaNome || "CRAS"}
          />

          <section className="cras-stage-v2">
            <CrasPageHeader
              eyebrow="Você está em"
              title={activeMeta.title}
              subtitle={activeMeta.subtitle}
              bullets={activeMeta.chips}
              subtabs={headerSubtabs}
              activeSubtabKey={activeSubtab}
              onSubtab={(k) => setActiveSubtab(k)}
              help={activeHelp}
              actions={pageActions}
              onAction={(a) => handleTab(a?.key)}
            />

            <div className="cras-stage-body">
              {renderBody()}
            </div>
          </section>
        </div>
      </main>
    </div>
  );
}

// CRAS_HEADER_SUBTABS_V1
