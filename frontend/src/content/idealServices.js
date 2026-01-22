export const IDEAL_SERVICES = [
  {
    slug: "plataforma-municipal",
    icon: "🧩",
    badge: "GovTech",
    title: "Plataforma Municipal Integrada",
    subtitle: "Uma base única para operar serviços, fluxos, LGPD e indicadores.",
    excerpt:
      "Padronize registros, acompanhe pendências por etapa (SLA) e gere evidências para auditoria e prestação de contas — com visão por cidadão/família/caso e operação em rede.",
    sections: {
      oQueE:
        "Uma plataforma para organizar o trabalho real da prefeitura, com fluxo por etapas, pendências e responsabilidade definida. A base é modular: começa no SUAS e evolui para Saúde e Educação mantendo a mesma experiência e governança.",
      paraQuemE:
        "Prefeituras e consórcios que precisam padronizar rotinas, reduzir retrabalho, proteger a gestão (auditoria/LGPD) e dar previsibilidade à execução.",
      oQueResolve: [
        "Fim do atendimento 'solto' (cada equipe do seu jeito).",
        "Trilha contínua de caso/atendimento (histórico preservado).",
        "Pendências, prazos e devolutivas visíveis (SLA).",
        "Indicadores e evidências para gestão, auditoria e controle social.",
      ],
      entregas: [
        "Mapeamento de fluxo e configuração por município.",
        "Perfis e permissões (LGPD por perfil).",
        "Trilha de auditoria e histórico contínuo.",
        "Dashboards operacionais e gerenciais.",
        "Implantação e treinamento por papel.",
      ],
      comoFunciona:
        "A IDEAL mapeia o processo real (como a rede trabalha), define etapas e responsabilidades, configura o sistema e acompanha a implantação. A gestão passa a operar por fluxo (etapas, pendências, devolutivas) com rastreabilidade.",
      indicadores: [
        "Tempo médio por etapa (SLA).",
        "Casos/atendimentos ativos e concluídos.",
        "Pendências por equipe/unidade.",
        "Devolutivas/encaminhamentos concluídos.",
        "Produtividade por perfil (sem expor dados sensíveis).",
      ],
    },
  },

  {
    slug: "suas-assistencia-social",
    icon: "🧑‍🤝‍🧑",
    badge: "SUAS",
    title: "Assistência Social (SUAS)",
    subtitle: "CRAS, CREAS, Pop Rua e serviços com padrão e rastreabilidade.",
    excerpt:
      "Gestão por fluxo com etapas e devolutivas, histórico contínuo, LGPD por perfil e indicadores para prestação de contas e controle social.",
    sections: {
      oQueE:
        "Conjunto de módulos e rotinas para operar a rede SUAS com padrão: triagem, acompanhamento, atendimentos, encaminhamentos, devolutivas e evidências.",
      paraQuemE:
        "Secretarias municipais, unidades (CRAS/CREAS/POP) e consórcios que precisam organizar atendimento, rede e indicadores.",
      oQueResolve: [
        "Registro padronizado e histórico contínuo.",
        "Encaminhamentos com devolutiva (a rede responde).",
        "Controle de pendências por etapa.",
        "Relatórios e evidências para CMAS, auditoria e prestação de contas.",
      ],
      entregas: [
        "Módulos SUAS (por implantação gradual).",
        "Modelos de registro em linguagem simples.",
        "Perfis LGPD (mínimo necessário) + auditoria.",
        "Indicadores e painéis para gestão.",
      ],
      comoFunciona:
        "A implantação começa com um módulo prioritário (ex.: Pop Rua ou CRAS), ajusta campos e etapas, treina equipes e escala para o restante da rede mantendo o mesmo padrão.",
      indicadores: [
        "Tempo de resposta da rede (devolutiva).",
        "Casos por status/etapa.",
        "Atendimentos por unidade/perfil.",
        "Encaminhamentos concluídos vs. pendentes.",
      ],
    },
  },

  {
    slug: "saude-sus",
    icon: "🩺",
    badge: "SUS",
    title: "Saúde (SUS)",
    subtitle: "Governança operacional, fluxos e indicadores — sem perder o histórico.",
    excerpt:
      "Estruture processos e trilhas de execução (SLA), organize evidências e dashboards e conecte serviços com rastreabilidade.",
    sections: {
      oQueE:
        "Camada de governança e operação para processos de saúde, conectando solicitações, encaminhamentos e devolutivas com trilha auditável.",
      paraQuemE:
        "Gestores municipais e regionais que precisam acompanhar execução, gargalos e evidências com clareza.",
      oQueResolve: [
        "Gargalos invisíveis passam a aparecer.",
        "Responsabilidades por etapa (SLA) ficam claras.",
        "Histórico preservado para auditoria.",
      ],
      entregas: [
        "Modelagem de fluxos prioritários (por município).",
        "Dashboards de execução e gargalos.",
        "Padrões de registro e trilha de evidências.",
      ],
      comoFunciona:
        "Selecionamos processos-chave (ex.: regulação/encaminhamentos), desenhamos o fluxo por etapas e implantamos com treinamento e acompanhamento.",
      indicadores: [
        "Tempo por etapa (SLA).",
        "Fila por status/prioridade.",
        "Taxa de conclusão de devolutivas.",
      ],
    },
  },

  {
    slug: "educacao",
    icon: "📚",
    badge: "Educação",
    title: "Educação",
    subtitle: "Fluxos e evidências para acompanhamento, prioridades e resultado.",
    excerpt:
      "Organize processos e acompanhamento com registro padronizado, indicadores e trilha de execução por etapa.",
    sections: {
      oQueE:
        "Camada de gestão por fluxo e indicadores para processos educacionais municipais, com foco em execução e evidências.",
      paraQuemE:
        "Secretarias e equipes que precisam acompanhar ações, prioridades e entregas com clareza.",
      oQueResolve: [
        "Ações deixam de ser 'soltas' e passam a ter trilha e responsáveis.",
        "Indicadores organizados para decisão e prestação de contas.",
      ],
      entregas: [
        "Desenho de fluxos prioritários.",
        "Dashboards e relatórios.",
        "Padrões de registro e evidências.",
      ],
      comoFunciona:
        "Começamos por um fluxo prioritário (ex.: acompanhamento de programas), implantamos e expandimos.",
      indicadores: [
        "Tempo por etapa.",
        "Ações concluídas vs. pendentes.",
        "Prioridades por território/unidade.",
      ],
    },
  },

  {
    slug: "pesquisa-eleitoral",
    icon: "🗳️",
    badge: "Pesquisa",
    title: "Pesquisa eleitoral e tracking",
    subtitle: "Intenção de voto, imagem, tracking e testes de mensagem.",
    excerpt:
      "Do diagnóstico à estratégia: leitura do território, segmentação e acompanhamento contínuo para decisões rápidas e seguras.",
    sections: {
      oQueE:
        "Pesquisas quantitativas e qualitativas para campanhas, com desenho amostral, coleta, análise e relatórios claros para tomada de decisão.",
      paraQuemE:
        "Campanhas, partidos e lideranças que precisam de informação confiável e acionável.",
      oQueResolve: [
        "Reduz achismo e define prioridades.",
        "Identifica segmentos e temas críticos.",
        "Testa mensagens e melhora comunicação.",
      ],
      entregas: [
        "Questionário e metodologia (amostra/estratificação).",
        "Coleta (presencial/telefone/online, conforme projeto).",
        "Relatório com síntese visual e recomendações.",
        "Tracking (rodadas) quando necessário.",
      ],
      comoFunciona:
        "Definimos objetivo, amostra e questionário; coletamos; analisamos por território/segmento e entregamos recomendações práticas.",
      indicadores: [
        "Intenção de voto/avaliação por segmento.",
        "Rejeição, conhecimento e imagem.",
        "Temas prioritários por território.",
      ],
    },
  },

  {
    slug: "pesquisa-mercado",
    icon: "📈",
    badge: "Mercado",
    title: "Pesquisa de mercado",
    subtitle: "Marca, posicionamento, hábitos e concorrência.",
    excerpt:
      "Entenda seu público, ajuste oferta e comunicação e encontre oportunidades reais — com análise clara e recomendações.",
    sections: {
      oQueE:
        "Pesquisas para decisões empresariais: marca, satisfação, hábitos, concorrência e potencial de mercado.",
      paraQuemE:
        "Empresas e marcas que precisam reduzir risco e priorizar investimentos.",
      oQueResolve: [
        "Mostra onde agir primeiro.",
        "Revela diferenciais percebidos e gargalos.",
        "Ajuda a ajustar preço, oferta e comunicação.",
      ],
      entregas: [
        "Diagnóstico e desenho do estudo.",
        "Coleta e análise por segmentos.",
        "Relatório com recomendações e plano de ação.",
      ],
      comoFunciona:
        "Mapeamos a pergunta de negócio, desenhamos o método e entregamos leitura segmentada + recomendações práticas.",
      indicadores: [
        "NPS/satisfação.",
        "Brand awareness e preferência.",
        "Segmentos com maior potencial.",
      ],
    },
  },

  {
    slug: "diagnostico-politicas-publicas",
    icon: "🧭",
    badge: "Governo",
    title: "Diagnóstico e avaliação de governo",
    subtitle: "Prioridades, leitura territorial e plano de ação.",
    excerpt:
      "Traduza dados em decisões: o que fazer, onde agir primeiro, quais metas e como medir.",
    sections: {
      oQueE:
        "Diagnóstico sob medida para gestão pública: opinião, prioridades, territorialização e desenho de plano de ação com indicadores.",
      paraQuemE:
        "Prefeituras, consórcios e órgãos públicos que precisam planejar e executar com evidências.",
      oQueResolve: [
        "Define prioridades reais (não só percepção interna).",
        "Organiza metas, responsáveis e prazos.",
        "Cria indicadores para acompanhar execução.",
      ],
      entregas: [
        "Pesquisa/diagnóstico + leitura territorial.",
        "Ranking de prioridades e recomendações.",
        "Plano de ação com metas e indicadores.",
      ],
      comoFunciona:
        "Combinamos pesquisa, dados do território e entrevistas; sintetizamos e transformamos em plano de ação e indicadores.",
      indicadores: [
        "Prioridades por bairro/região.",
        "Satisfação e percepção de serviços.",
        "Metas e entregas por eixo.",
      ],
    },
  },

  {
    slug: "monitoramento-avaliacao",
    icon: "🧪",
    badge: "M&A",
    title: "Monitoramento e avaliação",
    subtitle: "Acompanhe execução, gargalos e resultado com método.",
    excerpt:
      "Transforme plano em execução: rotina de acompanhamento, painéis, evidências e alertas de risco.",
    sections: {
      oQueE:
        "Metodologia e ferramentas para acompanhar políticas e projetos: metas, indicadores, responsáveis, prazos e evidências.",
      paraQuemE:
        "Gestores que precisam garantir entrega e mostrar resultado com clareza.",
      oQueResolve: [
        "Evita que projetos 'sumam' depois do anúncio.",
        "Mostra gargalos e risco de atraso.",
        "Organiza evidências para prestação de contas.",
      ],
      entregas: [
        "Modelo de indicadores e painel.",
        "Ritos de acompanhamento (cadência).",
        "Relatórios executivos e alertas.",
      ],
      comoFunciona:
        "Definimos indicadores e cadência (mensal/quinzenal), padronizamos evidências e acompanhamos a execução com plano de correção.",
      indicadores: [
        "Percentual de metas no prazo.",
        "Atrasos por área/etapa.",
        "Evidências entregues vs. pendentes.",
      ],
    },
  },

  {
    slug: "governanca-dados-lgpd",
    icon: "🛡️",
    badge: "LGPD",
    title: "Governança de dados e LGPD",
    subtitle: "Mínimo necessário, acesso por perfil e trilha de auditoria.",
    excerpt:
      "Proteja o poder público: padronize campos sensíveis, permissões e evidências sem travar a operação.",
    sections: {
      oQueE:
        "Conjunto de práticas para reduzir risco institucional: definição de perfis, campos sensíveis, logs/auditoria e padrão de registro.",
      paraQuemE:
        "Órgãos públicos que precisam de segurança jurídica e operacional.",
      oQueResolve: [
        "Evita exposição indevida de dados.",
        "Garante rastreabilidade de acesso e alterações.",
        "Mantém operação ágil com o mínimo necessário.",
      ],
      entregas: [
        "Matriz de perfis e permissões.",
        "Padrão de campos sensíveis.",
        "Trilha de auditoria e relatórios.",
      ],
      comoFunciona:
        "Definimos perfis e regras de acesso, configuramos permissões e padronizamos evidências. O foco é reduzir risco sem burocratizar.",
      indicadores: [
        "Acessos por perfil (monitoramento).",
        "Eventos auditáveis (logs).",
        "Conformidade de preenchimento mínimo.",
      ],
    },
  },
];
