// Guia SUAS — Conteúdo robusto (v1)
// Estrutura pronta para migrar para backend futuramente (B3).

export const GUIA_SUAS_CATEGORIAS = [
  {
    key: "financiamento",
    label: "Financiamento (SUAS)",
    icon: "💰",
    desc: "Fontes, custeio x investimento, execução segura e prestação de contas sem dor.",
  },
  {
    key: "gestao",
    label: "Gestão",
    icon: "🧭",
    desc: "Organização do serviço, equipe, registros e indicadores simples para gestão.",
  },
  {
    key: "equipamentos",
    label: "Equipamentos",
    icon: "🏢",
    desc: "CRAS, CREAS, Centro POP, Acolhimento e outros: custos, indicadores e checklists.",
  },
  {
    key: "modelos",
    label: "Modelos e Checklists",
    icon: "🧾",
    desc: "Modelos prontos para copiar/colar: justificativas, relatórios e checklists.",
  },
  {
    key: "faq",
    label: "Perguntas rápidas",
    icon: "❓",
    desc: "Respostas curtas para dúvidas do dia a dia (custeio x investimento, documentos etc.).",
  },
  {
    key: "glossario",
    label: "Glossário",
    icon: "📚",
    desc: "Termos do SUAS em linguagem simples.",
  },
];

export const GUIA_SUAS_START_5MIN = {
  title: "Começar por aqui (5 min)",
  subtitle: "Um caminho rápido para quem chegou agora — sem jargão e com foco em execução.",
  cards: [
    {
      title: "SUAS em 30 segundos",
      text:
        "SUAS é o sistema da Assistência Social. Ele organiza serviços, benefícios e ações para proteger famílias e indivíduos em situação de vulnerabilidade.",
    },
    {
      title: "De onde vem o recurso",
      text:
        "O recurso pode ser federal, estadual e municipal. O importante é registrar: fonte, serviço/equipamento e o que foi entregue (resultado).",
    },
    {
      title: "Custeio x investimento",
      text:
        "Custeio é o dia a dia do serviço (rotina, materiais, serviços, capacitação). Investimento é estrutura (equipamentos, reformas, melhorias permanentes).",
    },
    {
      title: "Regra de ouro",
      text:
        "Sem registro = risco. Todo gasto precisa de vínculo com o serviço e documentação básica (processo, nota, comprovação e registro do resultado).",
    },
  ],
  cta: { label: "Ir para Financiamento (SUAS)", targetCategoria: "financiamento" },
};

// Blocos por categoria (organização e UX)
export const GUIA_SUAS_BLOCOS = {
  financiamento: [
    {
      key: "entender",
      title: "Entender o recurso",
      desc: "De onde vem, como separar por serviço e como evitar erros clássicos.",
      temaIds: [
        "fin_fontes_recurso",
        "fin_fundo_a_fundo",
        "fin_custeio_investimento",
        "fin_organizar_por_servico",
        "fin_erros_comuns_execucao",
      ],
    },
    {
      key: "posso_gastar",
      title: "Posso gastar com isso?",
      desc: "Passo a passo para decidir, justificar e comprovar (sem achismo).",
      temaIds: [
        "fin_capacitacao_cursos",
        "fin_materiais_consumo",
        "fin_servicos_terceiros",
        "fin_beneficio_eventual",
        "fin_equipamentos_reformas",
        "fin_diarias_deslocamentos",
      
        "fin_internet_telefonia",
        "fin_combustivel_transporte",
        "fin_termo_referencia_servico",
        "fin_suprimento_fundos",
        "fin_publicidade_divulgacao",],
    },
    {
      key: "prestacao",
      title: "Prestação de contas sem dor",
      desc: "Checklists e modelos para relatório mensal e organização de anexos.",
      temaIds: [
        "fin_documentos_minimos",
        "fin_relatorio_mensal_recurso",
        "fin_pendencias_riscos",
        "fin_padrao_pastas_anexos",
        "fin_mapa_execucao_mensal",
      
        "fin_conciliacao_saldos",
        "fin_empenho_liquidacao_pagamento",
        "fin_planejamento_orcamentario",],
    },
  ],
  gestao: [
    {
      key: "organizacao",
      title: "Organização do serviço",
      desc: "Centro de custos, plano mensal e rotina de gestão (sem burocracia inútil).",
      temaIds: [
        "ges_centro_custos",
        "ges_plano_mensal_servico",
        "ges_reuniao_semanal_pauta",
        "ges_fluxo_documentos",
        "ges_metas_minimas",
      
        "ges_controle_social_conselho",
        "ges_plano_contingencia",
        "ges_fluxo_cadunico",],
    },
    {
      key: "atendimento",
      title: "Gestão do atendimento",
      desc: "Registro mínimo, sigilo e indicadores para justificar ações e recursos.",
      temaIds: [
        "ges_registro_minimo",
        "ges_sigilo_lgpd",
        "ges_indicadores_simples",
        "ges_relatorio_mensal_equipamento",
        "ges_articulacao_rede",
      
        "ges_prontuario_suas",
        "ges_vigilancia_socioassistencial",
        "ges_reuniao_rede_intersetorial",],
    },
    {
      key: "equipe",
      title: "Equipe",
      desc: "Integração de novos servidores e padrões de qualidade do serviço.",
      temaIds: [
        "ges_integracao_7dias",
        "ges_boas_praticas_registro",
        "ges_capacitacao_continua",
        "ges_padronizacao_fluxos",
      
        "ges_capacitacao_plano",
        "ges_comunicacao_registros",],
    },
  ],
  equipamentos: [
    { key: "cras", title: "CRAS", desc: "PAIF, SCFV e gestão do território.", temaIds: ["eq_cras"] },
    { key: "creas", title: "CREAS", desc: "Proteção Especial, PAEFI e violações.", temaIds: ["eq_creas"] },
    { key: "centropop", title: "Centro POP", desc: "Atendimento à população em situação de rua.", temaIds: ["eq_centropop"] },
    { key: "acolhimento", title: "Acolhimento", desc: "Fluxo, rotinas e indicadores do acolhimento.", temaIds: ["eq_acolhimento"] },
    { key: "abordagem", title: "Abordagem Social / Pop Rua", desc: "Busca ativa, registro e encaminhamentos.", temaIds: ["eq_abordagem"] },
    { key: "mulheres", title: "Mulheres (violência)", desc: "Proteção e rede de atendimento.", temaIds: ["eq_mulheres"] },
    { key: "crianca", title: "Criança e Adolescente", desc: "Proteção e articulação com rede.", temaIds: ["eq_crianca_adolescente"] },
    { key: "residencia", title: "Residência Inclusiva", desc: "Cuidados, rotina e indicadores.", temaIds: ["eq_residencia_inclusiva"] },
    { key: "orgaogestor", title: "Órgão Gestor", desc: "Gestão do SUAS, planejamento e monitoramento.", temaIds: ["eq_orgao_gestor"] },
  ],
  modelos: [
    { key: "checklists", title: "Checklists", desc: "Documentos mínimos e conferências rápidas.", temaIds: ["mod_docs_por_gasto", "mod_checklist_mensal_servico"] },
    { key: "justificativas", title: "Justificativas prontas", desc: "Textos para curso, material, serviço e benefício eventual.", temaIds: ["mod_just_curso", "mod_just_material", "mod_just_servico", "mod_just_beneficio_eventual"] },
    { key: "relatorios", title: "Relatórios e planos", desc: "Relatório mensal e plano mensal do serviço.", temaIds: ["mod_relatorio_mensal_servico", "mod_plano_mensal_servico"] },
    { key: "rotinas", title: "Rotinas", desc: "Pauta semanal e roteiro de integração.", temaIds: ["mod_pauta_semanal", "mod_integracao_7dias"] },
  
        "mod_just_combustivel",
        "mod_just_internet",
        "mod_relatorio_capacitacao",
        "mod_ata_reuniao",
        "mod_modelo_pia_acoes",],
  faq: [
    { key: "rapidas", title: "Perguntas rápidas", desc: "Respostas curtas para dúvidas comuns.", temaIds: [
      "faq_custeio_investimento",
      "faq_docs_guardar",
      "faq_justificar_gasto",
      "faq_centro_custo",
      "faq_mais_dá_problema",
      "faq_beneficio_eventual_quando",
      "faq_servico_terceiros",
      "faq_capacitacao_comprovar",
    ] },
  
        "faq_pagar_internet",
        "faq_pagar_combustivel",
        "faq_pagar_alimentacao",],
  glossario: [
    { key: "termos", title: "Termos do SUAS", desc: "Definições em linguagem simples.", temaIds: [
      "glo_fundo_a_fundo",
      "glo_custeio",
      "glo_investimento",
      "glo_centro_custo",
      "glo_execucao",
      "glo_prestacao_contas",
      "glo_beneficio_eventual",
      "glo_pia",
      "glo_paif",
      "glo_paefi",
      "glo_scfv",
      "glo_cadastro_unico",
    ] },
  
        "glo_nob_suas",
        "glo_nob_rh",
        "glo_pnas",
        "glo_tipificacao",],
};

// ========================
// TEMAS (páginas padrão)
// ========================
export const GUIA_SUAS_TEMAS = [
  // ---------- FINANCIAMENTO ----------
  {
    id: "fin_fontes_recurso",
    categoria: "financiamento",
    bloco: "entender",
    title: "Fontes de recurso no SUAS (federal/estadual/municipal)",
    keywords: ["fonte", "recurso", "cofinanciamento", "federal", "estadual", "municipal"],
    sections: {
      oque:
        "As fontes são as origens do dinheiro (federal, estadual, municipal). A regra prática: sempre registrar fonte + serviço/equipamento + resultado.",
      quando:
        "Sempre que for planejar ou executar gasto. Ajuda a evitar mistura indevida e facilita prestação de contas.",
      como: [
        "Identifique a fonte (federal/estadual/municipal) e a finalidade.",
        "Vincule ao serviço (CRAS, CREAS, Centro POP, Acolhimento etc.).",
        "Registre no processo e no relatório mensal: o que foi feito e para quem.",
        "Mantenha pastas/arquivos padronizados por mês e por fonte.",
      ],
      erros: [
        "Misturar gastos de fontes diferentes sem controle.",
        "Não registrar o serviço vinculado (descritivo genérico).",
        "Não produzir relatório mensal simples (o que foi entregue).",
      ],
      checklist: [
        "Fonte identificada",
        "Serviço/equipamento vinculado",
        "Processo/contratação (quando houver)",
        "NF/recibo",
        "Registro do resultado (relatório curto)",
      ],
      texto:
        "O gasto foi executado com recurso de fonte ____________, vinculado ao serviço ____________, visando ____________. Documentos e registros de execução foram anexados ao processo e ao relatório mensal.",
    },
  },
  {
    id: "fin_fundo_a_fundo",
    categoria: "financiamento",
    bloco: "entender",
    title: "O que é “fundo a fundo” e por que isso importa",
    keywords: ["fundo a fundo", "repasse", "fundo municipal", "gestão financeira"],
    sections: {
      oque:
        "É o repasse direto para o Fundo Municipal, com regras de aplicação e registro. Importa porque exige organização clara do gasto e do resultado.",
      quando:
        "Sempre que você receber/usar recursos do fundo. Ajuda a organizar execução e prestação de contas.",
      como: [
        "Registre o recebimento e o saldo por fonte.",
        "Planeje execução por mês (mínimo: previsão de custos e entregas).",
        "Execute com documentação mínima e registro do resultado.",
      ],
      erros: [
        "Executar sem plano mínimo (o que será feito no mês).",
        "Não separar pastas/arquivos por mês e tipo de gasto.",
      ],
      checklist: ["Plano mensal simples", "Processo/compra", "NF", "Registro de entrega/resultado", "Conferência mensal de pendências"],
      texto:
        "A execução do repasse fundo a fundo foi organizada por mês e por serviço, com documentação mínima e registro do resultado em relatório mensal, conforme rotina do Fundo Municipal.",
    },
  },
  {
    id: "fin_custeio_investimento",
    categoria: "financiamento",
    bloco: "entender",
    title: "Custeio x investimento (exemplos do SUAS)",
    keywords: ["custeio", "investimento", "diferença", "exemplos"],
    sections: {
      oque:
        "Custeio é manutenção do serviço (rotina). Investimento é melhoria/estrutura permanente. A dúvida mais comum é classificar corretamente.",
      quando:
        "Antes de qualquer compra/contratação. Evita erro de classificação e questionamentos.",
      como: [
        "Pergunta rápida: é consumido no dia a dia? (custeio) ou vira patrimônio/melhoria permanente? (investimento).",
        "Registre no processo a justificativa e a classificação.",
        "Vincule ao serviço/equipamento.",
      ],
      erros: [
        "Tratar reforma/equipamento como custeio.",
        "Comprar item permanente sem registro patrimonial.",
      ],
      checklist: ["Classificação registrada", "Justificativa do serviço", "NF", "Patrimônio (se investimento)", "Foto/registro de entrega (se aplicável)"],
      texto:
        "O gasto foi classificado como ____________ (custeio/investimento) por se tratar de ____________. Vincula-se ao serviço ____________ e possui comprovação documental anexada.",
    },
  },
  {
    id: "fin_organizar_por_servico",
    categoria: "financiamento",
    bloco: "entender",
    title: "Como organizar por serviço (CRAS, CREAS, Acolhimento etc.)",
    keywords: ["organização", "serviço", "centro de custo", "equipamento"],
    sections: {
      oque:
        "Organizar por serviço é separar execução e documentos por equipamento/atividade. Isso deixa claro onde o recurso foi aplicado.",
      quando:
        "Sempre: compras, serviços, capacitações e benefícios eventuais precisam ter destino claro.",
      como: [
        "Defina uma estrutura simples: Pasta do mês → Serviço → Tipo de gasto.",
        "No processo, descreva: qual serviço, para qual público, qual resultado.",
        "Use sempre o mesmo padrão de nomes de arquivos.",
      ],
      erros: ["Arquivos soltos sem padrão", "Não indicar serviço/público", "Relatórios genéricos"],
      checklist: ["Pasta do mês", "Subpasta do serviço", "Subpasta do tipo de gasto", "NF e comprovantes", "Relatório curto"],
      texto:
        "Os documentos foram organizados por mês e por serviço (__________), assegurando rastreabilidade do gasto e facilidade na prestação de contas.",
    },
  },
  {
    id: "fin_erros_comuns_execucao",
    categoria: "financiamento",
    bloco: "entender",
    title: "Erros mais comuns na execução (e como evitar)",
    keywords: ["erro", "execução", "prestação", "risco"],
    sections: {
      oque:
        "Erros recorrentes são quase sempre de documentação e vínculo com serviço (não é só valor ou compra).",
      quando: "Use como checklist antes de fechar o mês e antes de enviar prestação de contas.",
      como: [
        "Sempre vincule o gasto a um serviço/equipamento.",
        "Guarde evidências: presença, fotos do item entregue, relatório curto.",
        "Padronize nomes e pastas.",
        "Feche o mês com uma conferência de pendências.",
      ],
      erros: ["Sem justificativa do serviço", "Sem evidência", "Sem relatório mensal", "Arquivos desorganizados"],
      checklist: ["Vínculo com serviço", "Documentos mínimos", "Evidência", "Relatório mensal", "Pendências resolvidas"],
      texto:
        "Antes do fechamento mensal, foi realizada conferência de pendências e consolidação dos registros por serviço, garantindo rastreabilidade e segurança na prestação de contas.",
    },
  },

  // Posso gastar
  {
    id: "fin_capacitacao_cursos",
    categoria: "financiamento",
    bloco: "posso_gastar",
    title: "Capacitação e cursos",
    keywords: ["capacitação", "curso", "treinamento", "justificativa", "presença"],
    sections: {
      oque:
        "Gasto para treinar equipe e padronizar o atendimento do serviço. Precisa estar ligado a uma necessidade real do equipamento e do público.",
      quando:
        "Quando a equipe precisa aprender fluxo, protocolo, preenchimento correto, abordagem, encaminhamentos e registro.",
      como: [
        "Defina qual problema do serviço a capacitação vai resolver.",
        "Defina quem participa e qual conteúdo.",
        "Registre carga horária, local, data e instrutor/empresa.",
        "Execute e colete presença.",
        "Produza relatório curto (1 página) do que foi aplicado no serviço.",
        "Guarde tudo no processo e no sistema (anexos).",
      ],
      erros: [
        "Curso sem justificativa do serviço.",
        "Não ter lista de presença.",
        "Não ter relatório do resultado aplicado no serviço.",
      ],
      checklist: [
        "Descrição do curso (objetivo + conteúdo)",
        "Processo/contratação (quando houver)",
        "Lista de presença assinada",
        "Certificados (se houver)",
        "Relatório de execução (1 página)",
      ],
      texto:
        "A capacitação foi realizada para qualificar e padronizar o atendimento do serviço ____________. Participaram ______ servidores, com carga horária de ____ horas. O conteúdo abordou ____________. Como resultado, foram implementadas as melhorias ____________ (ex.: novo fluxo, padronização de registro, melhoria de encaminhamentos).",
    },
  },
  {
    id: "fin_materiais_consumo",
    categoria: "financiamento",
    bloco: "posso_gastar",
    title: "Materiais de consumo (como registrar corretamente)",
    keywords: ["materiais", "consumo", "rotina", "registro"],
    sections: {
      oque:
        "Gasto com materiais usados no dia a dia do serviço para manter atendimento e rotina.",
      quando:
        "Quando o material é necessário para execução do serviço (atendimento, registro, acolhimento, higiene do espaço, atividades).",
      como: [
        "Relacione o material ao serviço/equipamento (CRAS/CREAS/Acolhimento…).",
        "Escreva justificativa simples (por que precisa).",
        "Compre/registre conforme regra local.",
        "Registre destino no sistema: o que comprou, quanto, onde será usado.",
        "Guarde NF e comprovação.",
      ],
      erros: [
        "Comprar sem dizer em qual serviço será usado.",
        "Descrição genérica dos itens.",
        "Falta de justificativa.",
      ],
      checklist: [
        "Lista do material e quantitativo",
        "Justificativa (1 parágrafo)",
        "NF/recibo",
        "Registro do destino (qual serviço)",
      ],
      texto:
        "A aquisição de materiais de consumo destina-se à manutenção das rotinas e atendimentos do serviço ____________. Os itens serão utilizados em ____________ (ex.: atendimento, registro, atividades, manutenção do espaço), garantindo continuidade e qualidade do serviço prestado.",
    },
  },
  {
    id: "fin_servicos_terceiros",
    categoria: "financiamento",
    bloco: "posso_gastar",
    title: "Serviços de terceiros (o que sempre exigir no processo)",
    keywords: ["serviço", "terceiros", "contratação", "comprovação"],
    sections: {
      oque:
        "Contratação de serviço (pessoa física/jurídica) para apoiar rotinas do equipamento (ex.: oficina, manutenção, consultoria, instrutoria).",
      quando:
        "Quando a equipe não consegue executar internamente ou quando há necessidade técnica específica.",
      como: [
        "Descreva o serviço com entregas claras (o que será entregue).",
        "Exija comprovação/relatório da execução (lista de presença, fotos, relatório).",
        "Vincule ao serviço/equipamento e ao público atendido.",
        "Guarde nota/recibo e comprovante de pagamento conforme regra local.",
      ],
      erros: [
        "Contratar sem descrever entregas.",
        "Não comprovar a execução.",
        "Não vincular ao serviço.",
      ],
      checklist: [
        "Termo de referência/descrição",
        "Contrato/ordem de serviço (se aplicável)",
        "Relatório de execução",
        "NF/recibo",
        "Registro do resultado",
      ],
      texto:
        "O serviço de ____________ foi contratado para atender necessidade do equipamento ____________. Entregas previstas: ____________. A execução foi comprovada por ____________ (relatório, presença, fotos), com documentação anexada ao processo.",
    },
  },
  {
    id: "fin_beneficio_eventual",
    categoria: "financiamento",
    bloco: "posso_gastar",
    title: "Benefícios eventuais (LOAS): quando usar e como registrar",
    keywords: ["benefício eventual", "loas", "registro", "urgência"],
    sections: {
      oque:
        "Ajuda temporária para situações de vulnerabilidade e urgência. Deve seguir critério municipal e registro completo da concessão.",
      quando:
        "Quando há situação pontual e urgente, dentro dos critérios definidos pelo município.",
      como: [
        "Registrar o pedido e a situação (em atendimento).",
        "Aplicar critério municipal + justificativa objetiva.",
        "Autorizar conforme fluxo local.",
        "Registrar entrega/concessão (com comprovante).",
        "Registrar no atendimento e arquivar documentos.",
      ],
      erros: [
        "Conceder sem critério claro.",
        "Não registrar e não comprovar entrega.",
      ],
      checklist: [
        "Registro do pedido",
        "Critério aplicado + justificativa",
        "Autorização conforme fluxo",
        "Comprovante de entrega",
        "Registro no atendimento",
      ],
      texto:
        "O benefício eventual foi concedido devido à situação de vulnerabilidade/urgência identificada em atendimento, conforme critério municipal ____________. A concessão visa atender necessidade imediata de ____________. A entrega/concessão foi registrada e documentada.",
    },
  },
  {
    id: "fin_equipamentos_reformas",
    categoria: "financiamento",
    bloco: "posso_gastar",
    title: "Equipamentos e reformas (cuidados antes de comprar)",
    keywords: ["equipamento", "reforma", "investimento", "patrimônio"],
    sections: {
      oque:
        "Compra de itens permanentes ou melhorias estruturais. Exige planejamento e atenção a patrimônio e justificativa.",
      quando:
        "Quando a estrutura do equipamento limita a qualidade do atendimento (ex.: falta de computador, mobiliário, adequação).",
      como: [
        "Justifique a necessidade ligada ao serviço e ao público.",
        "Classifique corretamente (investimento).",
        "Garanta registro patrimonial e localização do bem.",
        "Registre entrega/instalação (foto/termo).",
      ],
      erros: [
        "Comprar sem planejamento ou sem vínculo claro ao serviço.",
        "Não registrar patrimônio.",
      ],
      checklist: [
        "Justificativa do serviço",
        "Classificação (investimento)",
        "NF",
        "Patrimônio",
        "Registro de entrega/instalação",
      ],
      texto:
        "A aquisição/obra foi realizada para adequar a estrutura do equipamento ____________, garantindo melhores condições de atendimento. O item/serviço foi registrado como investimento e incorporado ao patrimônio, com comprovantes anexados.",
    },
  },
  {
    id: "fin_diarias_deslocamentos",
    categoria: "financiamento",
    bloco: "posso_gastar",
    title: "Diárias e deslocamentos (quando fazem sentido no SUAS)",
    keywords: ["diária", "deslocamento", "viagem", "capacitação"],
    sections: {
      oque:
        "Custos de deslocamento podem existir em capacitações, reuniões regionais e ações externas. Precisa de justificativa e comprovação.",
      quando:
        "Quando houver necessidade formal (capacitação, reunião, visita técnica) e autorização conforme regra local.",
      como: [
        "Justifique: objetivo do deslocamento e relação com o serviço.",
        "Registre autorização e participantes.",
        "Guarde comprovantes e relatório breve do resultado.",
      ],
      erros: ["Deslocamento sem objetivo claro", "Sem relatório/resultado", "Sem comprovação"],
      checklist: ["Autorização", "Lista de participantes", "Comprovantes", "Relatório breve"],
      texto:
        "O deslocamento foi autorizado para ____________ (objetivo), relacionado ao serviço ____________. Participaram ______ servidores. Foi produzido relatório breve com encaminhamentos e aplicação no serviço.",
    },
  },

  // Prestação
  {
    id: "fin_documentos_minimos",
    categoria: "financiamento",
    bloco: "prestacao",
    title: "Documentos mínimos por tipo de gasto",
    keywords: ["documentos", "mínimos", "nota", "comprovação"],
    sections: {
      oque:
        "Lista curta do que não pode faltar para cada tipo de gasto (curso, material, serviço, benefício eventual).",
      quando: "Use antes de fechar o mês e antes de enviar prestação.",
      como: [
        "Monte um checklist padrão no município.",
        "Use o mesmo padrão em todos os equipamentos.",
        "Feche o mês conferindo pendências.",
      ],
      erros: ["Falta de NF/recibo", "Sem relatório de execução", "Sem evidência", "Arquivos soltos"],
      checklist: [
        "Curso: descrição + presença + relatório + comprovantes",
        "Material: lista + justificativa + NF + destino",
        "Serviço: entregas + relatório + NF + registro do resultado",
        "Benefício eventual: critério + autorização + comprovante de entrega + registro de atendimento",
      ],
      texto:
        "Documentação mínima conferida conforme tipo de gasto. Itens faltantes foram registrados como pendência e resolvidos antes do fechamento do mês.",
    },
  },
  {
    id: "fin_relatorio_mensal_recurso",
    categoria: "financiamento",
    bloco: "prestacao",
    title: "Relatório mensal do recurso (modelo pronto)",
    keywords: ["relatório mensal", "modelo", "prestação", "mês"],
    sections: {
      oque:
        "Um relatório curto (1–2 páginas) com o que foi executado no mês, por serviço, e qual resultado.",
      quando: "No fechamento de cada mês.",
      como: [
        "Liste execuções por serviço/equipamento.",
        "Inclua 3 itens: o que foi feito, para quem, e qual resultado.",
        "Anexe evidências e documentos mínimos.",
      ],
      erros: ["Relatório genérico", "Não vincular ao serviço", "Não mostrar resultado"],
      checklist: ["Execuções por serviço", "Resultados", "Pendências", "Anexos organizados"],
      texto:
        "No mês de ______, o recurso foi executado nos serviços ______. Principais ações: ______. Resultados: ______. Documentação e evidências anexadas em padrão municipal.",
    },
  },
  {
    id: "fin_pendencias_riscos",
    categoria: "financiamento",
    bloco: "prestacao",
    title: "Pendências e riscos (o que mais dá problema)",
    keywords: ["pendência", "risco", "problema", "auditoria"],
    sections: {
      oque:
        "Principais riscos: gasto sem vínculo com serviço, sem evidência, sem relatório e sem organização de anexos.",
      quando: "Antes de enviar prestação e em auditorias internas.",
      como: [
        "Faça conferência mensal com checklist.",
        "Padronize nomes de pastas e arquivos.",
        "Exija evidência mínima por tipo de gasto.",
      ],
      erros: ["Sem evidência", "Sem relatório", "Arquivos desorganizados"],
      checklist: ["Checklist mensal", "Pendências registradas", "Correção antes do envio"],
      texto:
        "Foi realizada conferência mensal de pendências e riscos, com correção dos itens críticos antes do envio/arquivamento do mês.",
    },
  },
  {
    id: "fin_padrao_pastas_anexos",
    categoria: "financiamento",
    bloco: "prestacao",
    title: "Organização de pastas e anexos (padrão do município)",
    keywords: ["pastas", "anexos", "padrão", "organização"],
    sections: {
      oque:
        "Padrão simples de organização reduz erro e tempo de prestação de contas.",
      quando: "Implemente uma vez e use todo mês.",
      como: [
        "Crie padrão: Ano/Mês → Serviço → Tipo de gasto.",
        "Nomeie arquivos: DATA_TIPO_SERVIÇO_FORNECEDOR.",
        "Guarde evidências junto do gasto.",
      ],
      erros: ["Sem padrão", "Arquivos misturados", "Dificuldade de rastrear"],
      checklist: ["Padrão aprovado", "Pasta por mês", "Nomeação", "Evidências"],
      texto:
        "Os anexos foram organizados conforme padrão municipal: Ano/Mês → Serviço → Tipo de gasto, com nomeação padronizada e evidências junto do respectivo processo.",
    },
  },
  {
    id: "fin_mapa_execucao_mensal",
    categoria: "financiamento",
    bloco: "prestacao",
    title: "Mapa de execução mensal (planilha simples)",
    keywords: ["planilha", "mapa", "execução", "controle"],
    sections: {
      oque:
        "Uma planilha simples (mês a mês) com: serviço, tipo de gasto, valor, evidência e status (ok/pendente).",
      quando: "Use para acompanhar o mês e fechar pendências.",
      como: [
        "Abra planilha do mês com linhas por gasto.",
        "Campos: serviço, tipo, fornecedor, valor, documento, evidência, status.",
        "Feche o mês com status 100% OK.",
      ],
      erros: ["Não acompanhar pendências", "Planilha sem evidência", "Não vincular ao serviço"],
      checklist: ["Planilha do mês", "Evidência", "Status OK", "Arquivo salvo"],
      texto:
        "Foi utilizado mapa de execução mensal com rastreabilidade por serviço, permitindo controle de documentos, evidências e pendências até o fechamento do mês.",
    },
  },

  // ---------- GESTÃO ----------
  {
    id: "ges_centro_custos",
    categoria: "gestao",
    bloco: "organizacao",
    title: "Como montar centro de custos por equipamento",
    keywords: ["centro de custo", "equipamento", "organização"],
    sections: {
      oque:
        "Centro de custos é uma forma simples de saber quanto cada equipamento custa e justificar execução.",
      quando: "Quando você precisa organizar orçamento e prestação de contas por serviço.",
      como: [
        "Defina centros: CRAS, CREAS, Centro POP, Acolhimento…",
        "Registre cada gasto no centro correspondente.",
        "Feche o mês com um resumo por centro.",
      ],
      erros: ["Misturar gastos", "Não consolidar mês a mês"],
      checklist: ["Centros definidos", "Gastos classificados", "Resumo mensal"],
      texto:
        "Os gastos foram organizados por centro de custos (equipamentos), permitindo rastreabilidade e consolidação mensal para gestão e prestação de contas.",
    },
  },
  {
    id: "ges_plano_mensal_servico",
    categoria: "gestao",
    bloco: "organizacao",
    title: "Plano mensal do serviço (metas + custos)",
    keywords: ["plano mensal", "metas", "custos"],
    sections: {
      oque:
        "Plano mensal é o mínimo para sair do improviso: o que vamos fazer e quanto custa.",
      quando: "No início de cada mês ou quando há mudanças de demanda.",
      como: [
        "Defina 3–5 metas do mês (ações/atendimentos).",
        "Liste custos previstos por tipo (material, serviço, capacitação).",
        "Feche o mês comparando previsto x executado.",
      ],
      erros: ["Plano genérico", "Sem custo", "Sem comparação no fechamento"],
      checklist: ["Metas", "Custos previstos", "Responsáveis", "Fechamento mensal"],
      texto:
        "No mês de ______, o serviço ______ planejou metas e custos previstos. Ao final do mês, foi realizada comparação previsto x executado, com registro de resultados e ajustes para o próximo ciclo.",
    },
  },
  {
    id: "ges_reuniao_semanal_pauta",
    categoria: "gestao",
    bloco: "organizacao",
    title: "Reunião semanal (pauta pronta)",
    keywords: ["reunião", "semanal", "pauta", "gestão"],
    sections: {
      oque:
        "Reunião semanal curta (30–45 min) para alinhar casos, pendências e rede.",
      quando: "Em equipes do CRAS/CREAS/Centro POP/Acolhimento.",
      como: [
        "1) Pendências da semana anterior",
        "2) Casos prioritários",
        "3) Encaminhamentos e rede",
        "4) Registros e documentação",
        "5) Próximas ações",
      ],
      erros: ["Reunião sem pauta", "Não registrar encaminhamentos", "Não fechar pendências"],
      checklist: ["Pauta", "Lista de encaminhamentos", "Responsáveis", "Registro de decisões"],
      texto:
        "Reunião semanal realizada com pauta padrão. Encaminhamentos e pendências foram atribuídos a responsáveis e registrados para acompanhamento.",
    },
  },
  {
    id: "ges_fluxo_documentos",
    categoria: "gestao",
    bloco: "organizacao",
    title: "Organização de documentos e anexos (rotina do serviço)",
    keywords: ["documentos", "anexos", "rotina", "pasta"],
    sections: {
      oque:
        "Rotina de documentos é o que sustenta prestação de contas e continuidade do caso.",
      quando: "Diariamente e no fechamento semanal/mensal.",
      como: [
        "Defina onde salvar: mês → equipamento → tipo.",
        "Padronize nomes de arquivos.",
        "Faça conferência semanal de pendências.",
      ],
      erros: ["Documento espalhado", "Sem padrão de nomes", "Pendências acumuladas"],
      checklist: ["Padrão definido", "Pasta do mês", "Conferência semanal"],
      texto:
        "O serviço adotou rotina de organização documental por mês/equipamento/tipo de gasto, com conferência semanal de pendências e rastreabilidade.",
    },
  },
  {
    id: "ges_metas_minimas",
    categoria: "gestao",
    bloco: "organizacao",
    title: "Metas mínimas do mês (modelo simples)",
    keywords: ["metas", "mínimas", "mês"],
    sections: {
      oque:
        "Metas mínimas são um conjunto pequeno de entregas que garantem continuidade do serviço.",
      quando: "Quando a equipe precisa de foco e previsibilidade.",
      como: [
        "Defina metas de atendimento/ações por semana.",
        "Defina metas de registros (cadastros/atualizações).",
        "Defina metas de rede (reuniões/contatos).",
      ],
      erros: ["Metas irrealistas", "Sem acompanhamento", "Sem registro"],
      checklist: ["Metas por semana", "Acompanhamento", "Registro de resultados"],
      texto:
        "Foram definidas metas mínimas mensais por semana para atendimento, registros e articulação com rede, com acompanhamento e registro de resultados.",
    },
  },

  // Gestão atendimento
  {
    id: "ges_registro_minimo",
    categoria: "gestao",
    bloco: "atendimento",
    title: "Registro mínimo do atendimento (sem dado sensível desnecessário)",
    keywords: ["registro", "mínimo", "sigilo", "lgpd"],
    sections: {
      oque:
        "Registro mínimo é o essencial para continuidade do caso, sem coletar informação desnecessária ou sensível.",
      quando: "Em todo atendimento e encaminhamento.",
      como: [
        "Registre: data, local, demanda, orientação/encaminhamento e retorno previsto.",
        "Evite detalhes clínicos: o sistema deve registrar fluxo, não prontuário de saúde.",
        "Use linguagem objetiva e curta.",
      ],
      erros: ["Texto longo e sensível", "Diagnóstico/medicação em registro social", "Falta de encaminhamento claro"],
      checklist: ["Data/local", "Demanda", "Encaminhamento", "Retorno previsto", "Sem dados sensíveis"],
      texto:
        "Atendimento registrado com informações essenciais: demanda apresentada, orientações e encaminhamentos realizados, com retorno previsto e registro objetivo, preservando sigilo.",
    },
  },
  {
    id: "ges_sigilo_lgpd",
    categoria: "gestao",
    bloco: "atendimento",
    title: "Boas práticas de sigilo e LGPD no SUAS",
    keywords: ["lgpd", "sigilo", "dados", "acesso"],
    sections: {
      oque:
        "LGPD é prática: coletar o necessário, restringir acesso e registrar quem fez o quê.",
      quando: "Sempre — principalmente em dados de saúde, violência, dependência, crianças.",
      como: [
        "Colete apenas o necessário para o serviço.",
        "Restrinja campos sensíveis por perfil.",
        "Registre acessos/alterações (auditabilidade).",
        "Evite texto livre com conteúdo clínico.",
      ],
      erros: ["Excesso de dados sensíveis", "Compartilhar sem necessidade", "Campo aberto sem restrição"],
      checklist: ["Necessidade", "Restrição por perfil", "Registro de alteração", "Treinamento da equipe"],
      texto:
        "O registro foi realizado com dados necessários ao serviço, observando sigilo e LGPD, com restrição de campos sensíveis e linguagem objetiva.",
    },
  },
  {
    id: "ges_indicadores_simples",
    categoria: "gestao",
    bloco: "atendimento",
    title: "Indicadores simples do serviço (para gestão)",
    keywords: ["indicadores", "dashboard", "gestão", "mensal"],
    sections: {
      oque:
        "Indicadores simples ajudam a mostrar demanda e justificar recursos: atendimentos, encaminhamentos, retornos, público.",
      quando: "Mensalmente (e semanalmente em serviços de maior demanda).",
      como: [
        "Defina 5 indicadores: atendimentos, encaminhamentos, benefícios, acolhimentos, retornos.",
        "Apresente em 1 página para gestão.",
        "Use para planejar o mês seguinte.",
      ],
      erros: ["Indicadores demais", "Sem periodicidade", "Sem uso na gestão"],
      checklist: ["5 indicadores", "Apresentação mensal", "Uso no planejamento"],
      texto:
        "Indicadores mensais foram consolidados para apoiar gestão do serviço, planejamento e justificativa de recursos, com foco em atendimentos, encaminhamentos e resultados.",
    },
  },
  {
    id: "ges_relatorio_mensal_equipamento",
    categoria: "gestao",
    bloco: "atendimento",
    title: "Relatório mensal do equipamento (modelo pronto)",
    keywords: ["relatório mensal", "equipamento", "modelo"],
    sections: {
      oque:
        "Relatório de 1 página do equipamento: atendimentos, demandas, rede e necessidades.",
      quando: "No fechamento do mês.",
      como: [
        "Informe número de atendimentos/ações.",
        "Principais demandas (3–5).",
        "Articulação com rede (quem e por quê).",
        "Desafios e necessidades do próximo mês.",
      ],
      erros: ["Relatório genérico", "Não citar demandas", "Não indicar necessidades"],
      checklist: ["Atendimentos", "Demandas", "Rede", "Desafios", "Necessidades"],
      texto:
        "No mês de ______, o equipamento ______ realizou ______ atendimentos/ações. As principais demandas foram ______. Houve articulação com ______ (rede). Principais desafios: ______. Necessidades para o próximo mês: ______.",
    },
  },
  {
    id: "ges_articulacao_rede",
    categoria: "gestao",
    bloco: "atendimento",
    title: "Articulação com a rede (roteiro prático)",
    keywords: ["rede", "articulação", "encaminhamento", "intersetorial"],
    sections: {
      oque:
        "Articular rede é garantir fluxo: quem faz o quê, em quanto tempo e como registrar retorno.",
      quando: "Em casos complexos e em encaminhamentos intersetoriais.",
      como: [
        "Defina ponto focal por setor (saúde, habitação, justiça).",
        "Registre encaminhamento e retorno esperado.",
        "Acompanhe pendências semanalmente.",
      ],
      erros: ["Encaminhar sem retorno esperado", "Não registrar retorno", "Sem ponto focal"],
      checklist: ["Ponto focal", "Encaminhamento registrado", "Retorno esperado", "Acompanhamento"],
      texto:
        "Foi realizada articulação com a rede ____________, com encaminhamento registrado e retorno esperado em ____ dias, acompanhado em rotina semanal.",
    },
  },

  // Equipe
  {
    id: "ges_integracao_7dias",
    categoria: "gestao",
    bloco: "equipe",
    title: "Roteiro de integração de equipe nova (7 dias)",
    keywords: ["integração", "equipe", "novo servidor"],
    sections: {
      oque:
        "Um roteiro simples para que o servidor novo aprenda fluxo, registro e rotina em 7 dias.",
      quando: "Quando entra servidor novo ou muda equipe.",
      como: [
        "Dia 1: apresentação do serviço e público",
        "Dia 2: fluxos e encaminhamentos",
        "Dia 3: registro no sistema",
        "Dia 4: documentos e rotinas",
        "Dia 5: indicadores e relatório",
        "Dia 6: rede e território",
        "Dia 7: simulação de caso + feedback",
      ],
      erros: ["Sem roteiro", "Aprender só por improviso", "Não treinar registro"],
      checklist: ["Roteiro", "Acompanhamento", "Simulação", "Feedback"],
      texto:
        "Integração realizada em 7 dias com roteiro padrão, incluindo fluxos, registros, documentos e simulação de caso, garantindo padronização do atendimento.",
    },
  },
  {
    id: "ges_boas_praticas_registro",
    categoria: "gestao",
    bloco: "equipe",
    title: "Boas práticas de registro (qualidade e sigilo)",
    keywords: ["boas práticas", "registro", "qualidade"],
    sections: {
      oque: "Padrão de escrita: objetivo, curto e sem sensível desnecessário.",
      quando: "Em todo atendimento/encaminhamento.",
      como: [
        "Use frases curtas e objetivas.",
        "Evite julgamento e termos clínicos.",
        "Registre encaminhamento e retorno.",
      ],
      erros: ["Textão", "Detalhe clínico", "Sem retorno"],
      checklist: ["Objetivo", "Encaminhamento", "Retorno", "Sigilo"],
      texto:
        "Registro realizado em linguagem objetiva, com encaminhamento e retorno previstos, preservando sigilo e evitando informação sensível desnecessária.",
    },
  },
  {
    id: "ges_capacitacao_continua",
    categoria: "gestao",
    bloco: "equipe",
    title: "Capacitação contínua (ciclo mensal)",
    keywords: ["capacitação", "ciclo", "mensal"],
    sections: {
      oque: "Ciclo mensal de 1 tema prático para manter padrão e reduzir erros.",
      quando: "Mensalmente (30–60 min).",
      como: [
        "Escolha tema do mês (registro, benefício, rede, acolhimento).",
        "Faça checklist e exercício rápido.",
        "Registre presença e melhoria aplicada.",
      ],
      erros: ["Treino sem aplicação", "Sem registro", "Sem continuidade"],
      checklist: ["Tema", "Presença", "Exercício", "Melhoria aplicada"],
      texto:
        "Capacitação mensal realizada com tema prático, com exercício e melhoria aplicada ao fluxo do serviço, com registro de presença.",
    },
  },
  {
    id: "ges_padronizacao_fluxos",
    categoria: "gestao",
    bloco: "equipe",
    title: "Padronização de fluxos (1 página por processo)",
    keywords: ["padronização", "fluxo", "1 página"],
    sections: {
      oque: "Fluxos simples de 1 página reduzem erro e aceleram atendimento.",
      quando: "Quando há troca de equipe ou muita variação na rotina.",
      como: [
        "Desenhe o fluxo em 5 passos.",
        "Defina responsável em cada passo.",
        "Defina prazos e registro no sistema.",
      ],
      erros: ["Fluxo longo", "Sem responsável", "Sem prazo"],
      checklist: ["5 passos", "Responsáveis", "Registro", "Revisão mensal"],
      texto:
        "Fluxos do serviço foram padronizados em 1 página por processo, com responsáveis, prazos e registro no sistema, reduzindo variação e erros.",
    },
  },

  // ---------- EQUIPAMENTOS (cada um como tema) ----------
  {
    id: "eq_cras",
    categoria: "equipamentos",
    bloco: "cras",
    title: "CRAS — O que faz, custos e checklist mensal",
    keywords: ["cras", "paif", "scfv", "território"],
    sections: {
      oque: "CRAS organiza a Proteção Social Básica no território. Foco em prevenção, PAIF, SCFV e encaminhamentos.",
      quando: "Para planejar rotina, custos e relatórios do CRAS.",
      como: [
        "Atendimentos comuns: acolhida, PAIF, orientações, encaminhamentos.",
        "Principais custos: material de consumo, atividades, capacitação, manutenção do espaço.",
        "Indicadores: atendimentos, famílias acompanhadas, encaminhamentos, retornos.",
      ],
      checklist: [
        "Relatório mensal do CRAS",
        "Conferência de documentos do mês",
        "Acompanhamento de pendências e rede",
        "Planejamento do próximo mês",
      ],
      texto:
        "No mês de ______, o CRAS ______ realizou ______ atendimentos e ______ acompanhamentos. Demandas principais: ______. Articulação de rede: ______. Desafios: ______. Necessidades do próximo mês: ______.",
    },
  },
  {
    id: "eq_creas",
    categoria: "equipamentos",
    bloco: "creas",
    title: "CREAS — O que faz, custos e checklist mensal",
    keywords: ["creas", "paefi", "violação", "proteção especial"],
    sections: {
      oque: "CREAS executa Proteção Social Especial, com foco em violações de direitos e acompanhamento especializado (PAEFI).",
      quando: "Para planejar rotina, custos e relatórios do CREAS.",
      como: [
        "Atendimentos comuns: acolhida, estudo de caso, articulação de rede, visitas.",
        "Principais custos: deslocamentos, capacitação, material de registro, apoio a ações em rede.",
        "Indicadores: casos acompanhados, encaminhamentos, retornos, rede articulada.",
      ],
      checklist: ["Relatório mensal do CREAS", "Revisão de casos prioritários", "Pendências de rede", "Registro completo"],
      texto:
        "No mês de ______, o CREAS ______ acompanhou ______ casos. Demandas principais: ______. Rede articulada: ______. Desafios: ______. Necessidades do próximo mês: ______.",
    },
  },
  {
    id: "eq_centropop",
    categoria: "equipamentos",
    bloco: "centropop",
    title: "Centro POP — Rotina, registro e indicadores",
    keywords: ["centro pop", "pop rua", "situação de rua"],
    sections: {
      oque: "Centro POP atende população em situação de rua, com acolhida, higiene, alimentação (quando houver), orientação e encaminhamentos.",
      quando: "Para organizar o registro e os encaminhamentos do Centro POP.",
      como: [
        "Atendimentos comuns: abordagem, cadastro, encaminhamentos, rede.",
        "Indicadores: pessoas atendidas, retornos, encaminhamentos efetivos, ações com rede.",
      ],
      checklist: ["Registro de atendimentos", "Encaminhamentos com retorno", "Relatório mensal", "Pendências de rede"],
      texto:
        "No mês de ______, o Centro POP ______ atendeu ______ pessoas. Principais demandas: ______. Encaminhamentos: ______. Resultados: ______.",
    },
  },
  {
    id: "eq_acolhimento",
    categoria: "equipamentos",
    bloco: "acolhimento",
    title: "Acolhimento — Fluxo, rotinas e indicadores",
    keywords: ["acolhimento", "abrigo", "rotina"],
    sections: {
      oque: "Serviço de acolhimento é proteção temporária, com regras claras, plano de acompanhamento e registro de entradas/saídas.",
      quando: "Para organizar rotina, custos e relatório do acolhimento.",
      como: [
        "Rotina: entradas/saídas, regras, acompanhamento, articulação.",
        "Indicadores: ocupação, permanência média, saídas qualificadas, retornos.",
      ],
      checklist: ["Lista de residentes", "Plano de acompanhamento", "Registro de entradas/saídas", "Relatório mensal"],
      texto:
        "No mês de ______, o acolhimento ______ manteve ocupação média de ____%. Entradas: ___. Saídas qualificadas: ___. Desafios: ______. Necessidades: ______.",
    },
  },
  {
    id: "eq_abordagem",
    categoria: "equipamentos",
    bloco: "abordagem",
    title: "Abordagem Social / Pop Rua — Busca ativa e registro",
    keywords: ["abordagem", "busca ativa", "pop rua"],
    sections: {
      oque: "Abordagem Social atua no território com busca ativa, escuta, orientação e encaminhamentos, registrando retorno.",
      quando: "Para padronizar abordagem e evitar registro incompleto.",
      como: [
        "Registre local/data, demanda, encaminhamento e retorno esperado.",
        "Evite conteúdo clínico; registre fluxo.",
      ],
      checklist: ["Registro mínimo", "Encaminhamento", "Retorno", "Relatório mensal"],
      texto:
        "Abordagem realizada em ______ (local), com orientação e encaminhamentos para ______. Retorno previsto em ____ dias, com registro no sistema.",
    },
  },
  {
    id: "eq_mulheres",
    categoria: "equipamentos",
    bloco: "mulheres",
    title: "Mulheres (violência) — Proteção e rede",
    keywords: ["mulheres", "violência", "rede", "proteção"],
    sections: {
      oque: "Atendimento a mulheres em situação de violência requer sigilo, acolhida e fluxo de rede bem definido.",
      quando: "Para organizar procedimentos e registro mínimo.",
      como: [
        "Registro objetivo e restrição de acesso.",
        "Encaminhamentos com retorno (rede).",
      ],
      checklist: ["Sigilo/LGPD", "Encaminhamento rede", "Retorno", "Relatório"],
      texto:
        "Atendimento realizado com registro mínimo e restrição de acesso. Encaminhamento para ______ com retorno previsto em ____ dias.",
    },
  },
  {
    id: "eq_crianca_adolescente",
    categoria: "equipamentos",
    bloco: "crianca",
    title: "Criança e Adolescente — Proteção e articulação",
    keywords: ["criança", "adolescente", "proteção", "rede"],
    sections: {
      oque: "Atuação em proteção requer registro cuidadoso, articulação e monitoramento.",
      quando: "Para padronizar registro e ações de rede.",
      como: ["Registro mínimo, sem exposição", "Encaminhamento com retorno", "Monitoramento periódico"],
      checklist: ["Sigilo", "Encaminhamento", "Retorno", "Monitoramento"],
      texto:
        "Caso acompanhado com registro mínimo e sigilo. Encaminhamentos realizados para ______ com retorno previsto em ____ dias, monitorado em rotina semanal.",
    },
  },
  {
    id: "eq_residencia_inclusiva",
    categoria: "equipamentos",
    bloco: "residencia",
    title: "Residência Inclusiva — Rotina e indicadores",
    keywords: ["residência inclusiva", "pcd", "rotina"],
    sections: {
      oque: "Serviço de moradia assistida, com rotina e apoio, exigindo registro e acompanhamento.",
      quando: "Para organizar custos, rotina e relatório.",
      como: ["Rotina diária registrada", "Acompanhamento de plano individual", "Articulação com rede"],
      checklist: ["Rotina", "Plano individual", "Relatório mensal", "Pendências rede"],
      texto:
        "No mês de ______, a Residência Inclusiva ______ realizou acompanhamento de ____ residentes, com articulação de rede ______ e registro de rotinas e ações.",
    },
  },
  {
    id: "eq_orgao_gestor",
    categoria: "equipamentos",
    bloco: "orgaogestor",
    title: "Órgão gestor — Planejamento e monitoramento",
    keywords: ["órgão gestor", "planejamento", "monitoramento", "suas"],
    sections: {
      oque: "Órgão gestor coordena planejamento, execução, monitoramento e prestação de contas do SUAS no município.",
      quando: "Para organizar ciclos de gestão e controle.",
      como: ["Plano mensal e anual", "Monitoramento de indicadores", "Rotina de pendências e prestação"],
      checklist: ["Plano", "Indicadores", "Relatórios", "Pendências"],
      texto:
        "O órgão gestor consolidou planejamento e monitoramento do SUAS, com controle de execução por serviço e conferência de pendências e relatórios mensais.",
    },
  },

  // ---------- MODELOS ----------
  {
    id: "mod_docs_por_gasto",
    categoria: "modelos",
    bloco: "checklists",
    title: "Checklist de documentos por tipo de gasto",
    keywords: ["checklist", "documentos", "gasto"],
    sections: {
      oque: "Checklist para fechar mês sem pendência.",
      quando: "No dia a dia e no fechamento mensal.",
      como: ["Use para curso, material, serviço, benefício eventual."],
      checklist: [
        "Curso: descrição + presença + relatório + NF",
        "Material: lista + justificativa + NF + destino",
        "Serviço: entregas + relatório + NF + evidência",
        "Benefício eventual: critério + autorização + entrega + registro atendimento",
      ],
      texto: "Checklist conferido e anexado ao fechamento do mês.",
    },
  },
  {
    id: "mod_checklist_mensal_servico",
    categoria: "modelos",
    bloco: "checklists",
    title: "Checklist mensal do serviço (1 página)",
    keywords: ["checklist mensal", "rotina", "serviço"],
    sections: {
      oque: "Uma rotina mensal para fechar pendências e consolidar resultados.",
      quando: "No último dia útil do mês.",
      checklist: [
        "Conferir registros de atendimentos/encaminhamentos",
        "Conferir documentos de gastos",
        "Produzir relatório mensal (1 página)",
        "Planejar próximo mês (metas + custos)",
      ],
      texto: "Checklist mensal executado e arquivado.",
    },
  },
  {
    id: "mod_just_curso",
    categoria: "modelos",
    bloco: "justificativas",
    title: "Modelo de justificativa — Capacitação/Curso",
    keywords: ["modelo", "justificativa", "curso"],
    sections: {
      texto:
        "A capacitação foi realizada para qualificar e padronizar o atendimento do serviço ____________. Participaram ______ servidores, com carga horária de ____ horas. O conteúdo abordou ____________. Como resultado, foram implementadas as melhorias ____________.",
    },
  },
  {
    id: "mod_just_material",
    categoria: "modelos",
    bloco: "justificativas",
    title: "Modelo de justificativa — Material de consumo",
    keywords: ["modelo", "justificativa", "material"],
    sections: {
      texto:
        "A aquisição de materiais de consumo destina-se à manutenção das rotinas e atendimentos do serviço ____________. Os itens serão utilizados em ____________, garantindo continuidade e qualidade do serviço prestado.",
    },
  },
  {
    id: "mod_just_servico",
    categoria: "modelos",
    bloco: "justificativas",
    title: "Modelo de justificativa — Serviço de terceiros",
    keywords: ["modelo", "justificativa", "serviço"],
    sections: {
      texto:
        "O serviço de ____________ foi contratado para atender necessidade do equipamento ____________. Entregas previstas: ____________. A execução foi comprovada por ____________, com documentação anexada ao processo.",
    },
  },
  {
    id: "mod_just_beneficio_eventual",
    categoria: "modelos",
    bloco: "justificativas",
    title: "Modelo de justificativa — Benefício eventual",
    keywords: ["modelo", "benefício eventual", "justificativa"],
    sections: {
      texto:
        "O benefício eventual foi concedido devido à situação de vulnerabilidade/urgência, conforme critério municipal ____________. Visa atender necessidade imediata de ____________. A entrega/concessão foi registrada e documentada.",
    },
  },
  {
    id: "mod_relatorio_mensal_servico",
    categoria: "modelos",
    bloco: "relatorios",
    title: "Modelo de relatório mensal do serviço (copiar e colar)",
    keywords: ["modelo", "relatório mensal", "serviço"],
    sections: {
      texto:
        "No mês de ______, o equipamento ______ realizou ______ atendimentos/ações. As principais demandas foram ______. Houve articulação com ______ (rede). Principais desafios: ______. Necessidades para o próximo mês: ______.",
    },
  },
  {
    id: "mod_plano_mensal_servico",
    categoria: "modelos",
    bloco: "relatorios",
    title: "Modelo de plano mensal do serviço (metas + custos)",
    keywords: ["plano mensal", "modelo", "metas"],
    sections: {
      texto:
        "Plano mensal do serviço ______ (mês ____): Metas: (1) ____ (2) ____ (3) ____. Custos previstos: materiais ____; serviços ____; capacitação ____. Responsáveis: ____. Observações: ____.",
    },
  },
  {
    id: "mod_pauta_semanal",
    categoria: "modelos",
    bloco: "rotinas",
    title: "Pauta semanal pronta (30–45 min)",
    keywords: ["pauta", "reunião semanal", "modelo"],
    sections: {
      texto:
        "Pauta semanal: (1) Pendências anteriores (2) Casos prioritários (3) Encaminhamentos e retorno (4) Registros/documentos (5) Próximas ações (responsáveis e prazos).",
    },
  },
  {
    id: "mod_integracao_7dias",
    categoria: "modelos",
    bloco: "rotinas",
    title: "Roteiro de integração (7 dias) — versão copiável",
    keywords: ["integração", "7 dias", "modelo"],
    sections: {
      texto:
        "Integração 7 dias: D1 serviço/público; D2 fluxos/encaminhamentos; D3 registro no sistema; D4 documentos/rotinas; D5 indicadores/relatório; D6 rede/território; D7 simulação + feedback.",
    },
  },

  // ---------- FAQ ----------
  {
    id: "faq_custeio_investimento",
    categoria: "faq",
    bloco: "rapidas",
    title: "Isso é custeio ou investimento?",
    keywords: ["custeio", "investimento"],
    sections: {
      oque:
        "Regra rápida: é consumido no dia a dia? (custeio). Vira patrimônio/melhoria permanente? (investimento).",
    },
  },
  {
    id: "faq_docs_guardar",
    categoria: "faq",
    bloco: "rapidas",
    title: "Que documentos eu preciso guardar?",
    keywords: ["documentos", "guardar"],
    sections: {
      oque:
        "Sempre: justificativa do serviço + NF/recibo + evidência de execução + registro do resultado (relatório curto).",
    },
  },
  {
    id: "faq_justificar_gasto",
    categoria: "faq",
    bloco: "rapidas",
    title: "Como justifico esse gasto?",
    keywords: ["justificar", "gasto"],
    sections: {
      oque:
        "Vincule ao serviço/equipamento e ao público. Responda: por que precisa, para quem é e qual resultado esperado.",
    },
  },
  {
    id: "faq_centro_custo",
    categoria: "faq",
    bloco: "rapidas",
    title: "Em qual serviço/centro de custo eu marco?",
    keywords: ["centro de custo", "serviço"],
    sections: {
      oque:
        "Marque sempre no equipamento onde o gasto será usado (CRAS/CREAS/Centro POP/Acolhimento).",
    },
  },
  {
    id: "faq_mais_dá_problema",
    categoria: "faq",
    bloco: "rapidas",
    title: "O que mais dá problema na prestação de contas?",
    keywords: ["problema", "prestação"],
    sections: {
      oque:
        "Gasto sem vínculo com serviço, sem evidência e sem relatório mensal. Organização ruim de anexos também pesa muito.",
    },
  },
  {
    id: "faq_beneficio_eventual_quando",
    categoria: "faq",
    bloco: "rapidas",
    title: "Benefício eventual: quando posso conceder?",
    keywords: ["benefício eventual", "conceder"],
    sections: {
      oque:
        "Quando houver situação pontual/urgente e dentro do critério municipal. Sempre registrar critério, autorização e entrega.",
    },
  },
  {
    id: "faq_servico_terceiros",
    categoria: "faq",
    bloco: "rapidas",
    title: "Serviço de terceiros: como comprovar?",
    keywords: ["serviço de terceiros", "comprovar"],
    sections: {
      oque:
        "Com entregas claras + evidência (lista de presença, fotos, relatório) + NF/recibo. Sem evidência, vira risco.",
    },
  },
  {
    id: "faq_capacitacao_comprovar",
    categoria: "faq",
    bloco: "rapidas",
    title: "Capacitação: o que comprova?",
    keywords: ["capacitação", "comprovar", "presença"],
    sections: {
      oque:
        "Descrição do curso + lista de presença + relatório do que foi aplicado no serviço. Certificados ajudam, mas não substituem relatório.",
    },
  },

  // ---------- GLOSSÁRIO ----------
  { id: "glo_fundo_a_fundo", categoria: "glossario", bloco: "termos", title: "Fundo a fundo", keywords: ["repasse"], sections: { oque: "Repasse direto para o Fundo Municipal, com regras de aplicação e registro." } },
  { id: "glo_custeio", categoria: "glossario", bloco: "termos", title: "Custeio", keywords: ["rotina"], sections: { oque: "Gasto do dia a dia do serviço: materiais, serviços, capacitação, manutenção." } },
  { id: "glo_investimento", categoria: "glossario", bloco: "termos", title: "Investimento", keywords: ["patrimônio"], sections: { oque: "Gasto permanente: equipamentos, reformas, melhorias estruturais." } },
  { id: "glo_centro_custo", categoria: "glossario", bloco: "termos", title: "Centro de custo", keywords: ["equipamento"], sections: { oque: "Forma de separar gastos por equipamento/serviço para gestão e prestação de contas." } },
  { id: "glo_execucao", categoria: "glossario", bloco: "termos", title: "Execução", keywords: ["gasto"], sections: { oque: "Realização do gasto com documentação e registro do resultado." } },
  { id: "glo_prestacao_contas", categoria: "glossario", bloco: "termos", title: "Prestação de contas", keywords: ["relatório"], sections: { oque: "Conjunto de documentos e relatórios que comprovam uso correto do recurso." } },
  { id: "glo_beneficio_eventual", categoria: "glossario", bloco: "termos", title: "Benefício eventual", keywords: ["loas"], sections: { oque: "Ajuda temporária para urgência/vulnerabilidade, com critérios e registro." } },
  { id: "glo_pia", categoria: "glossario", bloco: "termos", title: "PIA / Plano do caso", keywords: ["plano"], sections: { oque: "Plano de objetivos e ações com responsáveis, prazos e monitoramento." } },
  { id: "glo_paif", categoria: "glossario", bloco: "termos", title: "PAIF", keywords: ["cras"], sections: { oque: "Serviço de Proteção e Atendimento Integral à Família (CRAS)." } },
  { id: "glo_paefi", categoria: "glossario", bloco: "termos", title: "PAEFI", keywords: ["creas"], sections: { oque: "Serviço de Proteção e Atendimento Especializado a Famílias e Indivíduos (CREAS)." } },
  { id: "glo_scfv", categoria: "glossario", bloco: "termos", title: "SCFV", keywords: ["convivência"], sections: { oque: "Serviço de Convivência e Fortalecimento de Vínculos." } },
  { id: "glo_cadastro_unico", categoria: "glossario", bloco: "termos", title: "Cadastro Único", keywords: ["cadúnico"], sections: { oque: "Instrumento de identificação e caracterização socioeconômica para acesso a programas." } },

  // === NOVOS TEMAS (v2) ===
  {
    id: "fin_internet_telefonia",
    categoria: "financiamento",
    bloco: "posso_gastar",
    title: "Internet/telefonia e comunicação do serviço",
    keywords: ["internet", "telefonia", "comunicação", "custeio", "serviço"],
    sections: {
      oque: "Gasto de custeio para manter comunicação e funcionamento do serviço (internet, telefonia, chips/planos), desde que vinculado ao equipamento e ao atendimento.",
      quando: "Quando o serviço depende de internet/telefone para agendar, registrar atendimentos, articular rede e manter rotina administrativa do equipamento.",
      como: [
        "Vincule ao equipamento (CRAS/CREAS/Centro POP/Acolhimento).",
        "Justifique a necessidade (rotina do atendimento/registro/contato com rede).",
        "Defina escopo: plano/fornecedor/valor/mês e quem utiliza.",
        "Guarde fatura/nota, comprovante de pagamento e relatório mensal simples (uso e finalidade)."
      ],
      erros: [
        "Contratar sem vincular ao equipamento/serviço.",
        "Faturas sem identificação do uso no serviço.",
        "Misturar linhas pessoais com serviço."
      ],
      checklist: [
        "Justificativa do serviço (1 parágrafo).",
        "Contrato/plano ou termo do fornecedor.",
        "Fatura/nota do período.",
        "Comprovante de pagamento.",
        "Registro no relatório mensal do equipamento."
      ],
      texto: "A despesa com internet/telefonia destina-se à manutenção da rotina do serviço ____________, permitindo registro de atendimentos, contato com usuários e articulação com a rede. Documentos do período foram anexados.",
    },
  },
  {
    id: "fin_combustivel_transporte",
    categoria: "financiamento",
    bloco: "posso_gastar",
    title: "Combustível e transporte para ações do serviço",
    keywords: ["combustível", "transporte", "veículo", "deslocamento", "custeio"],
    sections: {
      oque: "Custeio para viabilizar deslocamentos de equipe/ações do serviço (visita domiciliar, abordagem, articulação de rede), com controle e registro de finalidade.",
      quando: "Quando há deslocamentos necessários à execução do serviço (território, visitas, reuniões de rede, busca ativa).",
      como: [
        "Defina a finalidade e o tipo de deslocamento (território/visita/abordagem).",
        "Estabeleça controle mínimo (data, rota/objetivo, equipe, km/abastecimento).",
        "Vincule ao equipamento responsável pela ação.",
        "Guarde NF do combustível e relatório mensal de rotas/ações."
      ],
      erros: [
        "Abastecer sem controle de finalidade.",
        "Não vincular a ação ao equipamento.",
        "Não registrar rota/atividade (risco na prestação de contas)."
      ],
      checklist: [
        "Plano/rotina de uso do veículo.",
        "Controle de deslocamentos (planilha simples).",
        "NF do combustível.",
        "Registro das ações realizadas (relatório mensal)."
      ],
      texto: "Combustível/deslocamentos utilizados para execução de ações do serviço ____________ (visitas/abordagens/articulação de rede), conforme controle de rotas e relatório mensal anexados.",
    },
  },
  {
    id: "fin_termo_referencia_servico",
    categoria: "financiamento",
    bloco: "posso_gastar",
    title: "Serviços de terceiros: termo de referência simples",
    keywords: ["terceiros", "contratação", "termo de referência", "escopo", "entrega"],
    sections: {
      oque: "Documento curto que define o que será contratado, para quê, como medir entrega e quais documentos serão exigidos. Reduz risco e dá clareza ao processo.",
      quando: "Antes de contratar qualquer serviço (capacitação, manutenção, consultoria, apoio técnico, eventos).",
      como: [
        "Defina objetivo (qual problema do serviço será resolvido).",
        "Liste entregas (o que deve ser entregue, em itens).",
        "Defina prazo, local e público/equipe envolvida.",
        "Defina comprovação: relatório, lista de presença, fotos, produto final, etc.",
        "Inclua critérios mínimos de habilitação do fornecedor (quando aplicável)."
      ],
      erros: [
        "Escopo genérico ('prestação de serviços') sem entregas.",
        "Não definir como comprovar execução.",
        "Não vincular ao serviço/equipamento."
      ],
      checklist: [
        "Objetivo e justificativa.",
        "Entregas/itens do serviço.",
        "Prazos e responsáveis.",
        "Forma de comprovação.",
        "Checklist de documentos do fornecedor."
      ],
      texto: "Contrata-se o serviço ____________ para atender necessidade do equipamento ____________. Entregas esperadas: ____________. Comprovação: ____________. Prazo: ____.",
    },
  },
  {
    id: "fin_suprimento_fundos",
    categoria: "financiamento",
    bloco: "posso_gastar",
    title: "Suprimento de fundos/pequenas despesas: cuidados",
    keywords: ["suprimento de fundos", "pequenas despesas", "adiantamento", "controle"],
    sections: {
      oque: "Mecanismo para pequenas despesas urgentes, com regras rígidas de controle e comprovação. Use só quando o fluxo normal não atende a tempo.",
      quando: "Quando há necessidade imediata e de baixo valor (itens urgentes) e o município prevê esse procedimento.",
      como: [
        "Verifique se o município permite e qual o limite/forma.",
        "Registre a finalidade e o vínculo com o serviço.",
        "Exija comprovantes válidos e detalhados.",
        "Faça prestação de contas do adiantamento com relatório simples."
      ],
      erros: [
        "Virar 'caixinha' sem controle.",
        "Comprovantes inválidos ou genéricos.",
        "Uso repetido para compras que deveriam seguir processo regular."
      ],
      checklist: [
        "Norma municipal aplicável.",
        "Autorização formal.",
        "Comprovantes detalhados.",
        "Relatório de prestação do adiantamento.",
        "Vínculo com o serviço/equipamento."
      ],
      texto: "A despesa foi realizada via procedimento de pequenas despesas/suprimento de fundos, por urgência do serviço ____________. Comprovantes e relatório de prestação foram anexados.",
    },
  },
  {
    id: "fin_publicidade_divulgacao",
    categoria: "financiamento",
    bloco: "posso_gastar",
    title: "Divulgação/Comunicação institucional do serviço",
    keywords: ["divulgação", "comunicação", "material gráfico", "campanha", "orientação"],
    sections: {
      oque: "Ações de comunicação para orientar usuários e divulgar serviços (materiais informativos, sinalização do equipamento), desde que ligadas ao atendimento e à função socioassistencial.",
      quando: "Quando é necessário orientar a população sobre serviços, horários, fluxos e direitos, ou sinalizar o equipamento para facilitar acesso.",
      como: [
        "Defina objetivo (orientar acesso/fluxo).",
        "Aprove o conteúdo (mensagem simples, sem expor dados pessoais).",
        "Registre quantitativo, local de distribuição e público-alvo.",
        "Guarde arte final, NF e registro do resultado (ex.: alcance/entrega)."
      ],
      erros: [
        "Transformar em marketing sem vínculo com o serviço.",
        "Conteúdo com dados pessoais/sensíveis.",
        "Não registrar onde/como foi distribuído."
      ],
      checklist: [
        "Justificativa e objetivo.",
        "Arte final/aprovação.",
        "NF e comprovante.",
        "Registro de distribuição/uso.",
        "Relatório curto do resultado."
      ],
      texto: "Materiais de comunicação foram produzidos para orientar acesso ao serviço ____________, informando ____________. A distribuição/uso foi registrada e documentada.",
    },
  },
  {
    id: "fin_conciliacao_saldos",
    categoria: "financiamento",
    bloco: "prestacao",
    title: "Conciliação de saldos e conferência mensal",
    keywords: ["saldo", "conciliação", "conferência", "prestação de contas", "pendências"],
    sections: {
      oque: "Rotina mensal para conferir saldo, despesas do mês e pendências (documentos faltantes). Evita acumular problemas no fim do ano.",
      quando: "No fechamento de cada mês (ou quinzenalmente em meses de muita execução).",
      como: [
        "Liste despesas do mês por tipo (material/serviço/benefício).",
        "Conferir NF/recibos e comprovantes de pagamento.",
        "Marcar pendências e responsáveis para resolver.",
        "Atualizar relatório mensal do recurso e do equipamento."
      ],
      erros: [
        "Deixar para conferir só no fim do ano.",
        "Perder comprovantes/faturas.",
        "Não registrar pendências e responsáveis."
      ],
      checklist: [
        "Extrato/saldo do período.",
        "Planilha simples de despesas.",
        "Pasta com NFs e comprovantes.",
        "Lista de pendências + responsável + prazo.",
        "Relatório mensal atualizado."
      ],
      texto: "Foi realizada conciliação mensal do recurso do serviço ____________, conferindo saldo, despesas e documentação. Pendências foram registradas e encaminhadas para regularização.",
    },
  },
  {
    id: "fin_empenho_liquidacao_pagamento",
    categoria: "financiamento",
    bloco: "prestacao",
    title: "Empenho, liquidação e pagamento (visão prática)",
    keywords: ["empenho", "liquidação", "pagamento", "processo", "nota fiscal"],
    sections: {
      oque: "Três etapas básicas da despesa pública: empenho (reserva), liquidação (comprovação do serviço/entrega) e pagamento. Na prática, serve para organizar o processo e anexos.",
      quando: "Sempre que executar despesa (material/serviço). Ajuda a entender por que precisa de documentos e comprovação.",
      como: [
        "Empenho: verificar dotação e registrar a despesa no processo.",
        "Liquidação: comprovar que foi entregue/realizado (NF + atesto + evidência).",
        "Pagamento: comprovar pagamento e arquivar no processo.",
        "Registre no relatório mensal o que foi entregue (resultado)."
      ],
      erros: [
        "Pular etapa de comprovação (liquidação fraca).",
        "Atestar sem evidência mínima.",
        "Processo sem registro do resultado."
      ],
      checklist: [
        "Empenho/registro equivalente.",
        "NF/recibo + atesto.",
        "Evidência (relatório/foto/lista/presença).",
        "Comprovante de pagamento.",
        "Registro no relatório mensal."
      ],
      texto: "A despesa do serviço ____________ seguiu as etapas de empenho, liquidação (com comprovação da entrega/execução) e pagamento, com documentação completa anexada.",
    },
  },
  {
    id: "fin_planejamento_orcamentario",
    categoria: "financiamento",
    bloco: "prestacao",
    title: "Planejamento orçamentário do serviço (mês/trimestre)",
    keywords: ["planejamento", "orçamento", "previsão", "centro de custos", "execução"],
    sections: {
      oque: "Organização simples do que o serviço pretende executar e quanto custará no mês/trimestre. Ajuda a não gastar no improviso e melhora a prestação de contas.",
      quando: "Antes do mês começar (ou no início do trimestre), principalmente em serviços com alta demanda.",
      como: [
        "Liste rotinas fixas (materiais, contratos recorrentes).",
        "Liste ações previstas (capacitacao, atividades, reparos).",
        "Estime custos e vincule ao equipamento.",
        "No fim do período, compare previsto x executado e registre ajustes."
      ],
      erros: [
        "Executar sem previsão mínima.",
        "Não vincular custos ao serviço.",
        "Não registrar comparação previsto x executado."
      ],
      checklist: [
        "Lista de rotinas e ações.",
        "Estimativa de custos.",
        "Vínculo com equipamento.",
        "Comparativo previsto x executado.",
        "Relatório curto de ajustes."
      ],
      texto: "Foi elaborado planejamento orçamentário do equipamento ____________ para o período ____________, com previsão de rotinas e ações, estimativa de custos e registro de execução/ajustes.",
    },
  },
  {
    id: "ges_controle_social_conselho",
    categoria: "gestao",
    bloco: "organizacao",
    title: "Controle social e Conselho: o que registrar",
    keywords: ["controle social", "conselho", "atas", "deliberação", "transparência"],
    sections: {
      oque: "Controle social é participação e fiscalização da política. Na prática: registrar decisões, encaminhamentos e evidências de discussão/validação no conselho quando aplicável.",
      quando: "Quando houver deliberações, pactuações, aprovação de planos/relatórios e temas relevantes de gestão do SUAS.",
      como: [
        "Manter pauta e ata objetiva (decisão + responsável + prazo).",
        "Anexar documentos discutidos (planos/relatórios).",
        "Registrar encaminhamentos e acompanhar cumprimento.",
        "Guardar arquivo digital padronizado por data."
      ],
      erros: [
        "Ata genérica sem decisão.",
        "Sem lista de presença.",
        "Não acompanhar encaminhamentos."
      ],
      checklist: [
        "Pauta.",
        "Lista de presença.",
        "Ata (decisões e encaminhamentos).",
        "Documentos anexos.",
        "Acompanhamento de pendências."
      ],
      texto: "Em reunião de controle social/conselho, foi deliberado ____________. Encaminhamentos: ____________ (responsável/prazo). Documentos e ata anexados.",
    },
  },
  {
    id: "ges_plano_contingencia",
    categoria: "gestao",
    bloco: "organizacao",
    title: "Plano de contingência do serviço (emergências)",
    keywords: ["contingência", "emergência", "enchente", "calamidade", "fluxo"],
    sections: {
      oque: "Plano simples para manter atendimento em situações de emergência (enchentes, ondas de frio, calamidade). Define fluxo, responsáveis e registros mínimos.",
      quando: "Quando o município enfrenta eventos que aumentam vulnerabilidade e demanda do serviço.",
      como: [
        "Defina cenários (frio, enchente, desabrigados).",
        "Defina equipe de plantão e contatos da rede.",
        "Defina registros mínimos (sem excessos de dados sensíveis).",
        "Defina logística (insumos, acolhimento, encaminhamentos)."
      ],
      erros: [
        "Não ter lista de contatos e responsáveis.",
        "Não registrar entregas/atendimentos.",
        "Confundir assistência social com saúde (dados clínicos indevidos)."
      ],
      checklist: [
        "Cenários e medidas.",
        "Responsáveis e contatos.",
        "Fluxo e registros mínimos.",
        "Logística/estoques.",
        "Relatório pós-evento (lições aprendidas)."
      ],
      texto: "Foi ativado plano de contingência do serviço ____________ para o cenário ____________. Equipe responsável: ____________. Atendimentos e entregas foram registrados conforme fluxo.",
    },
  },
  {
    id: "ges_fluxo_cadunico",
    categoria: "gestao",
    bloco: "organizacao",
    title: "Fluxo CadÚnico: integração com o atendimento do SUAS",
    keywords: ["cadúnico", "cadastro único", "fluxo", "atendimento", "encaminhamento"],
    sections: {
      oque: "Rotina para identificar se a família/pessoa está no CadÚnico, orientar regularização e registrar encaminhamento, sem travar o atendimento.",
      quando: "Quando o usuário precisa acessar benefícios e programas e o CadÚnico é requisito ou facilita a análise.",
      como: [
        "No atendimento, checar situação (sim/não/não sabe).",
        "Se necessário, orientar documentos e agendar/encaminhar ao setor responsável.",
        "Registrar no caso/atendimento o encaminhamento e status.",
        "Acompanhar retorno (concluído/pendente)."
      ],
      erros: [
        "Exigir CadÚnico para qualquer atendimento (barreira).",
        "Não registrar encaminhamento/retorno.",
        "Guardar documentos pessoais indevidos no sistema."
      ],
      checklist: [
        "Registro da situação CadÚnico.",
        "Orientação de documentos.",
        "Encaminhamento/agendamento.",
        "Status/retorno registrado."
      ],
      texto: "No atendimento do serviço ____________, foi verificada situação CadÚnico e, quando necessário, realizado encaminhamento para regularização, com registro de status.",
    },
  },
  {
    id: "ges_prontuario_suas",
    categoria: "gestao",
    bloco: "atendimento",
    title: "Prontuário SUAS: uso prático (sem excesso)",
    keywords: ["prontuário suas", "registro", "atendimento", "sigilo", "cadastro"],
    sections: {
      oque: "Registro padronizado do atendimento socioassistencial. A regra prática: registrar o necessário para continuidade do caso, evitando dados sensíveis desnecessários.",
      quando: "Sempre que houver acompanhamento e necessidade de histórico para equipe/gestão.",
      como: [
        "Defina campos mínimos (demanda, encaminhamento, providência).",
        "Evite informações clínicas; registre apenas fluxo e necessidade operacional.",
        "Use linguagem objetiva e respeitosa.",
        "Garanta controle de acesso por perfil."
      ],
      erros: [
        "Transformar em prontuário clínico.",
        "Textos longos e opinativos.",
        "Registrar dados sensíveis sem necessidade."
      ],
      checklist: [
        "Demanda registrada.",
        "Providência tomada.",
        "Encaminhamentos com status.",
        "Próximo passo definido.",
        "Acesso controlado."
      ],
      texto: "Registro do atendimento realizado no serviço ____________: demanda ____________, providências ____________, encaminhamentos ____________ (status) e próximo passo ____________.",
    },
  },
  {
    id: "ges_vigilancia_socioassistencial",
    categoria: "gestao",
    bloco: "atendimento",
    title: "Vigilância socioassistencial: indicadores úteis",
    keywords: ["vigilância", "indicadores", "território", "demanda", "monitoramento"],
    sections: {
      oque: "Uso de dados do serviço para entender demandas do território e ajustar prioridades. Em B1: indicadores simples e acionáveis.",
      quando: "Para relatório mensal, planejamento e justificativa de recursos.",
      como: [
        "Defina 5 indicadores simples (ex.: atendimentos, encaminhamentos, retornos, benefícios, acolhimentos).",
        "Registre por período e, quando possível, por território/bairro.",
        "Use no planejamento do mês seguinte (metas e ações)."
      ],
      erros: [
        "Medir tudo e não usar nada.",
        "Indicadores sem periodicidade.",
        "Não transformar dados em decisão."
      ],
      checklist: [
        "Indicadores definidos.",
        "Planilha/registro mensal.",
        "Leitura rápida (o que aumentou/diminuiu).",
        "Ajuste de ações do mês seguinte."
      ],
      texto: "Indicadores do período apontaram ____________. Com base nisso, o serviço ajustará ____________ (ações/fluxos) no próximo mês.",
    },
  },
  {
    id: "ges_reuniao_rede_intersetorial",
    categoria: "gestao",
    bloco: "atendimento",
    title: "Reunião de rede/intersetorial: pauta e registro",
    keywords: ["rede", "intersetorial", "reunião", "encaminhamento", "fluxo"],
    sections: {
      oque: "Rotina de articulação com rede (saúde, educação, justiça, habitação). Precisa de pauta, encaminhamentos e responsáveis.",
      quando: "Quando há casos complexos e necessidade de alinhar fluxos/serviços entre setores.",
      como: [
        "Defina pauta (casos e temas).",
        "Registre decisões por caso: responsável + prazo + serviço.",
        "Registre pendências e retorno na próxima reunião.",
        "Evite expor dados sensíveis além do necessário."
      ],
      erros: [
        "Reunião sem encaminhamentos claros.",
        "Sem registro de responsável/prazo.",
        "Excesso de dados sensíveis compartilhados."
      ],
      checklist: [
        "Pauta.",
        "Lista de presença.",
        "Encaminhamentos por caso (responsável/prazo).",
        "Registro de retorno.",
        "Controle de sigilo."
      ],
      texto: "Em reunião de rede, foram definidos encaminhamentos para o caso ____________: ____________ (responsável/prazo). Registro anexado e acompanhamento programado.",
    },
  },
  {
    id: "ges_capacitacao_plano",
    categoria: "gestao",
    bloco: "equipe",
    title: "Plano de capacitação contínua (trimestral)",
    keywords: ["capacitação", "plano", "equipe", "treinamento", "padronização"],
    sections: {
      oque: "Planejamento simples de temas e treinamentos para reduzir erro e padronizar atendimento (ex.: registro, benefícios, acolhimento, rede).",
      quando: "Quando há rotatividade de equipe, mudanças de fluxo ou erros recorrentes em registro/execução.",
      como: [
        "Liste 3–5 temas prioritários do trimestre.",
        "Defina público (CRAS/CREAS/Centro POP).",
        "Defina formato (reunião interna, curso, estudo de caso).",
        "Registre presença e resultado (o que mudou na rotina)."
      ],
      erros: [
        "Treinar sem objetivo prático.",
        "Não registrar presença/resultado.",
        "Não implementar mudanças pós-treinamento."
      ],
      checklist: [
        "Lista de temas.",
        "Cronograma.",
        "Público e instrutor.",
        "Lista de presença.",
        "Relatório de aplicação."
      ],
      texto: "Plano de capacitação trimestral do serviço ____________: temas ____________. Objetivo: padronizar ____________. Participantes: _____. Resultados implementados: ____________.",
    },
  },
  {
    id: "ges_comunicacao_registros",
    categoria: "gestao",
    bloco: "equipe",
    title: "Boas práticas de comunicação e registros (equipe)",
    keywords: ["comunicação", "registro", "padrão", "qualidade", "sigilo"],
    sections: {
      oque: "Padrões simples para comunicação interna e registros: linguagem objetiva, foco em providência e respeito ao usuário.",
      quando: "Para reduzir ruído entre turnos/equipes e melhorar continuidade do caso.",
      como: [
        "Use linguagem objetiva (o que aconteceu, o que foi feito, próximo passo).",
        "Evite adjetivos/opiniões; registre fatos e providências.",
        "Padronize campos e siglas.",
        "Defina revisão semanal de registros (amostra)."
      ],
      erros: [
        "Registros longos e opinativos.",
        "Siglas sem padronização.",
        "Exposição desnecessária de dados sensíveis."
      ],
      checklist: [
        "Padrão de campos.",
        "Lista de siglas.",
        "Revisão semanal (amostra).",
        "Orientação de sigilo.",
        "Feedback para equipe."
      ],
      texto: "Padroniza-se o registro no serviço ____________ com foco em fatos, providências e próximo passo, evitando dados sensíveis desnecessários.",
    },
  },
  {
    id: "mod_just_combustivel",
    categoria: "modelos",
    bloco: "justificativas",
    title: "Modelo: justificativa de combustível/deslocamentos",
    keywords: ["modelo", "justificativa", "combustível", "deslocamento"],
    sections: {
      oque: "Texto pronto para justificar combustível/transportes vinculados ao serviço.",
      quando: "Quando houver deslocamentos para execução de ações do equipamento.",
      como: [
        "Preencha serviço, objetivo e tipo de ação.",
        "Anexe controle de rotas e NFs.",
        "Registre resultado (ações realizadas)."
      ],
      erros: [
        "Texto genérico sem ação.",
        "Sem controle de rotas.",
        "Sem vínculo com serviço."
      ],
      checklist: [
        "Justificativa preenchida.",
        "Controle de rotas.",
        "NF combustível.",
        "Relatório mensal com ações."
      ],
      texto: "A despesa com combustível/deslocamentos destina-se à execução de ações do serviço ____________ (visitas/abordagens/articulação de rede), conforme controle de rotas e registros anexados.",
    },
  },
  {
    id: "mod_just_internet",
    categoria: "modelos",
    bloco: "justificativas",
    title: "Modelo: justificativa de internet/telefonia",
    keywords: ["modelo", "justificativa", "internet", "telefonia"],
    sections: {
      oque: "Texto pronto para justificar internet/telefonia do equipamento.",
      quando: "Para contratos/faturas mensais de comunicação do serviço.",
      como: [
        "Preencha equipamento e finalidade.",
        "Anexe fatura/nota e comprovante.",
        "Registre no relatório mensal."
      ],
      erros: [
        "Sem finalidade clara.",
        "Misturar uso pessoal.",
        "Sem comprovação do período."
      ],
      checklist: [
        "Justificativa.",
        "Contrato/plano.",
        "Fatura/nota.",
        "Comprovante de pagamento.",
        "Registro no relatório mensal."
      ],
      texto: "A despesa com internet/telefonia do equipamento ____________ é necessária para registro e acompanhamento de atendimentos, contato com usuários e articulação com a rede, conforme documentação do período anexada.",
    },
  },
  {
    id: "mod_relatorio_capacitacao",
    categoria: "modelos",
    bloco: "justificativas",
    title: "Modelo: relatório curto de capacitação (1 página)",
    keywords: ["modelo", "relatório", "capacitação", "presença", "resultado"],
    sections: {
      oque: "Modelo enxuto para registrar capacitação executada e o que foi aplicado na rotina.",
      quando: "Após capacitação/treinamento interno ou externo.",
      como: [
        "Registre objetivo e público.",
        "Anexe presença.",
        "Liste 3 aprendizados.",
        "Liste 3 mudanças aplicadas."
      ],
      erros: [
        "Sem lista de presença.",
        "Sem evidência de aplicação.",
        "Relatório longo e sem foco."
      ],
      checklist: [
        "Objetivo.",
        "Participantes.",
        "Conteúdo.",
        "Presença.",
        "Mudanças implementadas."
      ],
      texto: "Capacitação realizada em __/__/____ para equipe ____________. Conteúdo: ____________. Participantes: ____. Mudanças aplicadas: (1)____ (2)____ (3)____.",
    },
  },
  {
    id: "mod_ata_reuniao",
    categoria: "modelos",
    bloco: "rotinas",
    title: "Modelo: ata simples de reunião (decisão + responsável)",
    keywords: ["modelo", "ata", "reunião", "encaminhamento"],
    sections: {
      oque: "Ata curta e operacional: decisões, responsáveis e prazos.",
      quando: "Reuniões de equipe, rede ou gestão do equipamento.",
      como: [
        "Liste pauta.",
        "Registre decisões em tópicos.",
        "Atribua responsável e prazo.",
        "Anexe lista de presença."
      ],
      erros: [
        "Ata sem decisão.",
        "Sem responsável/prazo.",
        "Sem presença."
      ],
      checklist: [
        "Pauta.",
        "Decisões.",
        "Responsáveis e prazos.",
        "Presença.",
        "Pendências para próxima reunião."
      ],
      texto: "Ata da reunião do dia __/__/____. Pauta: ____. Decisões: (1)____ (resp: __, prazo: __) (2)____. Presença: ____.",
    },
  },
  {
    id: "mod_modelo_pia_acoes",
    categoria: "modelos",
    bloco: "relatorios",
    title: "Modelo: Plano do Caso (PIA) — ações e prazos",
    keywords: ["modelo", "pia", "plano", "ações", "prazo"],
    sections: {
      oque: "Modelo de plano simples: objetivo, ação, responsável, prazo e status.",
      quando: "Quando iniciar acompanhamento/PIA no caso.",
      como: [
        "Defina 1–3 objetivos.",
        "Quebre em ações concretas.",
        "Defina responsável e prazo.",
        "Atualize status mensalmente."
      ],
      erros: [
        "Objetivo genérico.",
        "Ações sem responsável.",
        "Sem prazos."
      ],
      checklist: [
        "Objetivos claros.",
        "Ações concretas.",
        "Responsável definido.",
        "Prazo definido.",
        "Status atualizado."
      ],
      texto: "Objetivo: ____ | Ação: ____ | Responsável: ____ | Prazo: ____ | Status: ____ | Observação: ____",
    },
  },
  {
    id: "faq_pagar_internet",
    categoria: "faq",
    bloco: "rapidas",
    title: "Posso pagar internet/telefonia com recurso do SUAS?",
    keywords: ["faq", "internet", "telefonia", "custeio"],
    sections: {
      oque: "Sim, quando for custeio do equipamento/serviço e houver justificativa e comprovação de uso no serviço.",
      quando: "Quando o serviço depende de comunicação para registro, contato e articulação de rede.",
      como: [
        "Vincule ao equipamento.",
        "Justifique finalidade.",
        "Guarde fatura/nota e comprovante.",
        "Registre no relatório mensal."
      ],
      erros: [
        "Misturar uso pessoal.",
        "Sem justificativa.",
        "Fatura sem identificação."
      ],
      checklist: [
        "Justificativa",
        "Fatura/nota",
        "Comprovante",
        "Registro no relatório"
      ],
      texto: "Justifica-se internet/telefonia para manter rotina do serviço ____________ (registro e contato com rede/usuários), com documentação do período anexada.",
    },
  },
  {
    id: "faq_pagar_combustivel",
    categoria: "faq",
    bloco: "rapidas",
    title: "Posso pagar combustível/deslocamento com recurso do SUAS?",
    keywords: ["faq", "combustível", "deslocamento", "visita", "abordagem"],
    sections: {
      oque: "Depende do regramento local, mas em regra é possível como custeio vinculado a ações do serviço, com controle de finalidade.",
      quando: "Quando há deslocamentos para visita, abordagem, articulação de rede e execução do serviço.",
      como: [
        "Vincule ao serviço.",
        "Controle de rotas/objetivo.",
        "Guarde NF.",
        "Registre ações no relatório mensal."
      ],
      erros: [
        "Sem controle.",
        "Sem vínculo com serviço.",
        "Uso recorrente sem planejamento."
      ],
      checklist: [
        "Controle de rotas",
        "NF combustível",
        "Registro de ações"
      ],
      texto: "Combustível/deslocamentos vinculados às ações do serviço ____________, conforme controle de rotas e documentação anexada.",
    },
  },
  {
    id: "faq_pagar_alimentacao",
    categoria: "faq",
    bloco: "rapidas",
    title: "Posso comprar alimentação para atividade/reunião?",
    keywords: ["faq", "alimentação", "reunião", "atividade", "custeio"],
    sections: {
      oque: "Em geral, só se houver justificativa clara ligada à ação do serviço e previsão/aceite no regramento local. Evite quando não for essencial.",
      quando: "Em atividades do serviço com público-alvo ou reuniões essenciais de execução, quando permitido.",
      como: [
        "Verifique regra local.",
        "Justifique a ação e o público.",
        "Registre lista/atividade.",
        "Guarde NF e registro do resultado."
      ],
      erros: [
        "Virar gasto sem vínculo.",
        "Sem registro da atividade.",
        "Sem regra local."
      ],
      checklist: [
        "Regra local",
        "Justificativa",
        "Registro da atividade",
        "NF"
      ],
      texto: "Aquisição vinculada à atividade do serviço ____________ em __/__/____, com público ____________ e registro do resultado anexado.",
    },
  },
  {
    id: "glo_nob_suas",
    categoria: "glossario",
    bloco: "termos",
    title: "NOB/SUAS",
    keywords: ["nob", "norma operacional básica", "suas"],
    sections: {
      oque: "Norma Operacional Básica do SUAS: orienta gestão, responsabilidades e organização da política no município.",
      quando: "Quando precisar entender papéis de gestão, financiamento e organização do SUAS.",
      como: [
        "Use como referência de gestão.",
        "Consulte para definir responsabilidades e estrutura.",
        "Padronize rotinas conforme orientação."
      ],
      erros: [
        "Usar sem adaptar à realidade local.",
        "Confundir com norma da saúde."
      ],
      checklist: [
        "Referência correta",
        "Aplicação na gestão",
        "Registro de decisões"
      ],
      texto: "NOB/SUAS: norma que orienta organização e responsabilidades na gestão do SUAS.",
    },
  },
  {
    id: "glo_nob_rh",
    categoria: "glossario",
    bloco: "termos",
    title: "NOB-RH/SUAS",
    keywords: ["nob-rh", "recursos humanos", "suas"],
    sections: {
      oque: "Norma Operacional Básica de Recursos Humanos do SUAS: orienta composição e organização das equipes.",
      quando: "Para organizar equipe e justificar necessidades de RH do serviço.",
      como: [
        "Use para planejar equipe.",
        "Base para capacitação e perfis.",
        "Orientar lotação e atribuições."
      ],
      erros: [
        "Equipe sem atribuições claras.",
        "Rotatividade sem integração."
      ],
      checklist: [
        "Perfis definidos",
        "Atribuições",
        "Plano de capacitação"
      ],
      texto: "NOB-RH/SUAS: norma que orienta gestão de pessoas e composição das equipes do SUAS.",
    },
  },
  {
    id: "glo_pnas",
    categoria: "glossario",
    bloco: "termos",
    title: "PNAS",
    keywords: ["pnas", "política nacional de assistência social"],
    sections: {
      oque: "Política Nacional de Assistência Social: diretrizes e bases da assistência social no Brasil.",
      quando: "Para alinhar planejamento municipal às diretrizes nacionais.",
      como: [
        "Use como referência de princípios e objetivos.",
        "Alinhe serviços e benefícios.",
        "Use em relatórios e planejamento."
      ],
      erros: [
        "Tratar como documento só teórico.",
        "Não aplicar na rotina."
      ],
      checklist: [
        "Diretriz",
        "Aplicação",
        "Registro"
      ],
      texto: "PNAS: define diretrizes e objetivos da assistência social no Brasil.",
    },
  },
  {
    id: "glo_tipificacao",
    categoria: "glossario",
    bloco: "termos",
    title: "Tipificação Nacional de Serviços Socioassistenciais",
    keywords: ["tipificação", "serviços", "suas", "proteção social"],
    sections: {
      oque: "Documento que define e padroniza os serviços socioassistenciais (o que cada serviço é e faz).",
      quando: "Para padronizar oferta e organizar serviços/equipamentos.",
      como: [
        "Use para descrever serviços no planejamento.",
        "Alinhe registros e relatórios.",
        "Padronize fluxos e indicadores."
      ],
      erros: [
        "Confundir serviço com benefício.",
        "Criar serviços fora do padrão sem justificativa."
      ],
      checklist: [
        "Serviço identificado",
        "Descrição correta",
        "Registro padronizado"
      ],
      texto: "Tipificação: padroniza os serviços socioassistenciais do SUAS (definição e organização).",
    },
  },
];
