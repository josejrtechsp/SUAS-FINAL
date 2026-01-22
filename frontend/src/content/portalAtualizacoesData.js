// Conteúdos internos do Portal (Atualizações)
// Edite este arquivo para adicionar novas atualizações.
// Padrão IDEAL: texto claro + decisão rápida + 3 passos + evidência mínima (3 provas).

export const PORTAL_ATUALIZACOES = [
  {
    id: "as-132",
    area: "assistencia",
    slug: "prestacao-de-contas-suas-2024-prazos-portaria-132-2025",
    tipo: "Portaria",
    data: "2025-12-11",
    titulo: "Prestação de contas do SUAS (2024): novos prazos para gestores e conselhos",
    subtitulo:
      "Portaria SNAS/MDS nº 132/2025 redefine o calendário — a diferença prática é parar de fazer mutirão e transformar prestação de contas em rotina.",
    resumo:
      "Gestores têm até 01/03/2026 para finalizar o preenchimento; Conselhos até 30/04/2026 para emitir parecer. O ganho real é operacional: criar rotina mensal para não virar urgência no fim.",

    em30s: [
      "Mudou: os prazos da prestação de contas do SUAS/2024 foram redefinidos (gestor e conselho).",
      "Afeta: gestão do SUAS/Fundo, financeiro/contabilidade, controle interno e Conselho.",
      "Ação imediata: criar rotina mensal de pendências e revisão — para não estourar no fim.",
    ],

    decisaoRapida: [
      "Precisa agir agora? Sim — organize calendário interno e rotina mensal de fechamento.",
      "Quem assume: gestão SUAS + financeiro/contabilidade (com alinhamento do Conselho).",
      "Risco de ignorar: atraso, retrabalho e risco de apontamentos por falha de registro.",
    ],

    entenda: [
      "Isso não é só 'prazo maior'. É um recado: prestação de contas precisa ser construída durante o ano. Se você deixa para o fim, vira mutirão e aumenta a chance de erro.",
      "O jeito mais simples é trabalhar por pendências: o que falta conciliar, o que falta registrar e o que falta validar. Cada pendência tem responsável e data de revisão.",
    ],

    mudaRotina: [
      "Defina um dia fixo por mês para conciliação + atualização de registros + fechamento de pendências.",
      "Organize por bloco/serviço (do jeito que sua prestação é cobrada).",
      "Combine com o Conselho um prazo interno para parecer (antes do limite final).",
    ],

    passos: [
      {
        t: "Confirmar",
        d: "Quais itens do exercício 2024 estão pendentes (conciliação, registros, anexos e validações).",
      },
      {
        t: "Organizar",
        d: "Criar um quadro simples por bloco: pendência → responsável → data de revisão (rotina, não mutirão).",
      },
      {
        t: "Executar e registrar",
        d: "Fechar pendências mês a mês e deixar tudo pronto para revisão final e parecer do Conselho.",
      },
    ],

    evidenciaMinima: [
      {
        t: "Prova 1 — Base",
        d: "Número da portaria + 1 página (print/PDF) com o trecho dos prazos.",
      },
      {
        t: "Prova 2 — Andamento",
        d: "Conciliação/demonstrativos e o registro do que foi atualizado (o suficiente para mostrar que está sendo feito).",
      },
      {
        t: "Prova 3 — Entrega",
        d: "Prestação finalizada + parecer do Conselho (e um resumo curto do fechamento).",
      },
    ],

    errosComuns: [
      "Deixar para o último mês e tentar 'montar o ano' em uma semana.",
      "Misturar blocos/competências e perder a rastreabilidade.",
      "Não combinar prazo interno com o Conselho e virar corrida no final.",
      "Ter documentos, mas não ter registro (ou vice‑versa).",
    ],

    mensagemPronta: `Prestação de contas SUAS/2024 — rotina a partir de agora

Responsáveis:
• Gestão SUAS: ______
• Financeiro/Contabilidade do Fundo: ______
• Articulação com o Conselho: ______

Ritmo:
• Fechamento mensal (conciliação + pendências): toda ____ (dia) até ____ (data)
• Revisão final antes do prazo oficial

Evidência mínima (3 provas):
1) Base: portaria + trecho com prazos
2) Andamento: conciliação/demonstrativos + registro do que foi atualizado
3) Entrega: prestação finalizada + parecer do Conselho`,

    fontes: [
      "DOU (Imprensa Nacional): Portaria SNAS/MDS nº 132, de 4 de dezembro de 2025 (publicada em 11/12/2025).",
      "FNAS / MDS: comunicados e orientações sobre prazos do AgilizaSUAS.",
    ],
  },

  {
    id: "as-rep-dez",
    area: "assistencia",
    slug: "repasse-de-dezembro-2025-suas-e-regularizacao-crianca-feliz",
    tipo: "Comunicado",
    data: "2025-12-26",
    titulo: "SUAS: repasse de dezembro e regularização do Criança Feliz (out/nov/dez 2025)",
    subtitulo:
      "FNAS informou repasse da competência de dezembro (PSB e PSE) e regularização de parcelas do Criança Feliz de 2025.",
    resumo:
      "O ponto prático: conciliar e separar por competência (out/nov/dez). Se tratar tudo como 'dezembro', a prestação de contas vira confusão.",

    em30s: [
      "Mudou: entrou repasse da competência de dezembro/2025 (PSB/PSE) e regularização de parcelas do Criança Feliz (out/nov/dez).",
      "Afeta: financeiro/contabilidade do Fundo + gestão SUAS.",
      "Ação imediata: conciliar e registrar por competência para não bagunçar saldo e prestação de contas.",
    ],

    decisaoRapida: [
      "Precisa agir agora? Sim — conciliação e classificação correta devem ser feitas logo.",
      "Quem assume: financeiro/contabilidade do Fundo + gestão SUAS.",
      "Risco: tratar tudo como 'dezembro' e perder rastreio de competência/objeto.",
    ],

    entenda: [
      "Quando ocorre regularização de meses anteriores, a entrada pode cair junto no extrato, mas a competência não é a mesma. O registro correto evita erro de saldo e confusão nos relatórios.",
      "O jeito simples é: cada entrada vira uma tarefa interna com competência, destino e responsável. Sem isso, o saldo fica 'solto'.",
    ],

    mudaRotina: [
      "Conferir extrato do Fundo assim que o repasse cair.",
      "Abrir uma pendência interna: conciliação → destinação → registro.",
      "Separar o que é competência atual do que é regularização retroativa (out/nov/dez).",
    ],

    passos: [
      {
        t: "Confirmar",
        d: "Verificar valores e competências (out/nov/dez) no comunicado e no extrato do Fundo.",
      },
      {
        t: "Organizar",
        d: "Criar 1 tarefa por competência: destino do recurso + responsável + prazo.",
      },
      {
        t: "Executar e registrar",
        d: "Usar conforme planejamento e deixar registro objetivo do que foi financiado (para prestação de contas).",
      },
    ],

    evidenciaMinima: [
      {
        t: "Prova 1 — Base",
        d: "Comunicado/nota do FNAS com a descrição do repasse e da regularização.",
      },
      {
        t: "Prova 2 — Entrada",
        d: "Print do extrato do Fundo mostrando a entrada (data e valor).",
      },
      {
        t: "Prova 3 — Entrega",
        d: "Registro do uso: nota/empenho/registro do serviço + resumo curto do que foi financiado.",
      },
    ],

    errosComuns: [
      "Misturar regularização (out/nov) com dezembro e perder referência.",
      "Deixar saldo 'solto' sem destinação e sem registro.",
      "Financeiro vê o repasse, mas a gestão não registra (ou vice‑versa).",
    ],

    mensagemPronta: `SUAS — repasse/regularização Criança Feliz (out/nov/dez)

Ação agora:
1) Financeiro: conciliar extrato do Fundo e separar por competência (out/nov/dez)
2) Gestão SUAS: definir destino do recurso por competência e abrir tarefas internas
3) Registro: anexar evidência mínima e atualizar controle da prestação de contas

Evidência mínima:
• Base (comunicado FNAS)
• Entrada (extrato do Fundo)
• Entrega (registro do que foi financiado + resumo curto)`,

    fontes: [
      "FNAS / MDS: comunicado sobre repasse de dezembro dos serviços socioassistenciais e regularização do Criança Feliz (26/12/2025).",
    ],
  },

  {
    id: "as-res-219",
    area: "assistencia",
    slug: "resolucao-cnas-219-2025-servico-domiciliar-gestantes-criancas-0-6",
    tipo: "Resolução",
    data: "2025-11-26",
    titulo: "Novo serviço no SUAS: PSB no domicílio para gestantes e crianças (0–6)",
    subtitulo:
      "A Resolução CNAS/MDS nº 219/2025 regulamenta o SPSBD‑GC. Na prática: acompanhar no domicílio precisa virar fluxo, não visita solta.",
    resumo:
      "O município precisa identificar público prioritário, referenciar no CRAS/PAIF, organizar visitas e registrar no prontuário. Sem método, não dá para comprovar nem monitorar.",

    em30s: [
      "Mudou: serviço de PSB no domicílio para gestantes e crianças 0–6 foi regulamentado (SPSBD‑GC).",
      "Afeta: CRAS/PAIF + vigilância socioassistencial + rede (saúde/educação).",
      "Ação imediata: desenhar fluxo e padrão de registro para não virar ação solta.",
    ],

    decisaoRapida: [
      "Precisa agir agora? Sim, se o município vai organizar/ofertar o serviço — é rotina, não campanha.",
      "Quem assume: coordenação CRAS/PAIF + gestão SUAS (com articulação intersetorial).",
      "Risco: visitas sem critério e sem registro → impossível comprovar e monitorar resultados.",
    ],

    entenda: [
      "O ponto central é transformar acompanhamento domiciliar em rotina: identificar público, priorizar, planejar visitas, registrar e acompanhar evolução.",
      "Sem registro padronizado, o município perde memória do caso e não consegue gerir fila, cobertura e encaminhamentos.",
    ],

    mudaRotina: [
      "Definir critérios de prioridade (quem entra primeiro na fila).",
      "Criar roteiro simples de visita e registro no prontuário.",
      "Estabelecer periodicidade mínima e indicadores básicos (famílias, visitas, encaminhamentos).",
    ],

    passos: [
      {
        t: "Confirmar",
        d: "Mapear público prioritário (CadÚnico + busca ativa) e capacidade de equipe para iniciar.",
      },
      {
        t: "Organizar",
        d: "Desenhar o fluxo: entrada → priorização → plano → visitas → encaminhamentos → acompanhamento.",
      },
      {
        t: "Executar e registrar",
        d: "Realizar visitas e registrar ações/encaminhamentos de forma padronizada no prontuário.",
      },
    ],

    evidenciaMinima: [
      {
        t: "Prova 1 — Base",
        d: "Resolução + 1 página com o trecho das diretrizes e do público prioritário.",
      },
      {
        t: "Prova 2 — Entrada",
        d: "Registro das famílias priorizadas + agenda/plano de visitas (início do acompanhamento).",
      },
      {
        t: "Prova 3 — Entrega",
        d: "Registros de visitas/encaminhamentos + relatório mensal simples (quantos acompanhados/visitas/encaminhamentos).",
      },
    ],

    errosComuns: [
      "Atender sem critério de prioridade (fila invisível).",
      "Fazer visita sem registro e depois tentar reconstruir o histórico.",
      "Não articular com saúde/educação quando necessário.",
    ],

    mensagemPronta: `SPSBD‑GC (gestantes e crianças 0–6) — organização do fluxo

Ação:
1) Definir critérios de prioridade e lista inicial de famílias
2) Montar agenda de visitas e roteiro padrão de registro
3) Registrar visitas, encaminhamentos e acompanhamento no prontuário

Evidência mínima:
• Base (resolução)
• Entrada (famílias priorizadas + plano/agenda)
• Entrega (registros de visitas + relatório mensal simples)`,

    fontes: [
      "DOU (Imprensa Nacional): Resolução CNAS/MDS nº 219, de 25/11/2025 (publicada em 26/11/2025).",
    ],
  },

  {
    id: "as-res-220",
    area: "assistencia",
    slug: "prontuario-suas-diretrizes-2025-seguranca-transparencia-lgpd",
    tipo: "Resolução",
    data: "2025-11-10",
    titulo: "Prontuário SUAS: diretrizes para padronizar registro e reduzir risco (LGPD na prática)",
    subtitulo:
      "A atualização de diretrizes reforça sigilo, proteção de dados e padronização do registro — para reduzir duplicidade e perda de histórico no atendimento.",
    resumo:
      "O recado é simples: prontuário bem feito vira gestão (continuidade do caso, rede e indicadores). Sem padrão e acesso por perfil, aumenta risco e retrabalho.",

    em30s: [
      "Mudou: diretrizes reforçam padronização, sigilo e proteção de dados no Prontuário SUAS.",
      "Afeta: equipe técnica, coordenação, gestão e (quando houver) TI.",
      "Ação imediata: definir campos mínimos e perfis de acesso + treinar equipe.",
    ],

    decisaoRapida: [
      "Precisa agir agora? Sim — prontuário é base do acompanhamento e da conformidade (LGPD).",
      "Quem assume: gestão SUAS + coordenações (com apoio de TI/administrativo).",
      "Risco: dados sensíveis expostos e perda de continuidade do caso por registro inconsistente.",
    ],

    entenda: [
      "Prontuário não é texto grande. É registro objetivo que permite: continuidade do caso, encaminhamento correto e memória institucional.",
      "Quando cada um registra de um jeito, o município perde tempo e cria duplicidade. Quando padroniza, ganha previsibilidade e segurança.",
    ],

    mudaRotina: [
      "Campos mínimos: motivo, ação, encaminhamento, responsável e próxima ação.",
      "Acesso por perfil: quem vê o quê (e com trilha/auditoria).",
      "Revisão mensal: duplicidades, campos vazios e pendências de registro.",
    ],

    passos: [
      {
        t: "Confirmar",
        d: "Definir campos mínimos por tipo de atendimento e quais perfis terão acesso.",
      },
      {
        t: "Organizar",
        d: "Treinar equipe em registro curto e padronizado + publicar uma norma interna simples.",
      },
      {
        t: "Executar e monitorar",
        d: "Aplicar padrão e rodar revisão mensal com correções (qualidade do dado).",
      },
    ],

    evidenciaMinima: [
      {
        t: "Prova 1 — Base",
        d: "Diretriz/resolução + regra interna de acesso e registro (documento curto).",
      },
      {
        t: "Prova 2 — Entrada",
        d: "Registro do treinamento/adesão (lista/ata) + parametrização de perfis.",
      },
      {
        t: "Prova 3 — Entrega",
        d: "Relatório mensal de qualidade (duplicidades/pendências) + evidência de auditoria/log quando aplicável.",
      },
    ],

    errosComuns: [
      "Todo mundo com acesso total (risco desnecessário).",
      "Registro longo e confuso ou registro vazio (sem próxima ação).",
      "Sem revisão, duplicidade vira normal e ninguém confia no dado.",
    ],

    mensagemPronta: `Prontuário SUAS — padrão mínimo (LGPD na prática)

Ação:
1) Campos mínimos por atendimento: motivo, ação, encaminhamento, responsável, próxima ação
2) Acesso por perfil (técnico/coordenação/gestão) + trilha de auditoria
3) Revisão mensal: duplicidades, campos vazios e pendências

Evidência mínima:
• Base (diretriz + norma interna)
• Entrada (treinamento + perfis)
• Entrega (relatório mensal de qualidade)`,

    fontes: [
      "MDS (gov.br): publicações e orientações sobre diretrizes do Prontuário SUAS (nov/2025).",
    ],
  },

  {
    id: "sa-9569",
    area: "saude",
    slug: "pv-visa-2025-portaria-9569-ultimas-parcelas",
    tipo: "Portaria",
    data: "2025-12-26",
    titulo: "Vigilância Sanitária: PV‑Visa (2025) e o que a prefeitura precisa fazer",
    subtitulo:
      "Portaria GM/MS nº 9.569/2025 institui parcelas de transferência do PV‑Visa para fortalecer ações estratégicas de vigilância sanitária.",
    resumo:
      "O ponto prático: conciliar repasse, definir plano simples de uso e deixar registro para o RAG. Repasse sem rastreio vira risco.",

    em30s: [
      "Mudou: a portaria define parcelas do PV‑Visa 2025 (incentivo para ações de vigilância sanitária).",
      "Afeta: vigilância sanitária + financeiro do Fundo de Saúde.",
      "Ação imediata: conciliar repasse, planejar uso e registrar para o RAG.",
    ],

    decisaoRapida: [
      "Precisa agir agora? Sim — repasse sem plano e sem registro vira risco (auditoria/RAG).",
      "Quem assume: vigilância + financeiro/contabilidade (e compras, se houver aquisição).",
      "Risco: gastar sem vínculo claro com a ação e depois não conseguir comprovar.",
    ],

    entenda: [
      "O problema não é receber. É executar com rastreio: o que foi feito com esse recurso e como isso aparece no RAG.",
      "Quando cada parcela vira uma tarefa com responsável e prazo, o fechamento anual fica simples.",
    ],

    mudaRotina: [
      "Conciliação do repasse no Fundo de Saúde.",
      "Plano simples: ação → responsável → prazo.",
      "Registro de execução e consolidação no RAG.",
    ],

    passos: [
      {
        t: "Confirmar",
        d: "Checar repasse no extrato do Fundo e conciliar valores (data/valor).",
      },
      {
        t: "Organizar",
        d: "Definir plano simples de uso (ações prioritárias, responsável e prazo).",
      },
      {
        t: "Executar e registrar",
        d: "Executar as ações e registrar evidências para consolidar no RAG.",
      },
    ],

    evidenciaMinima: [
      {
        t: "Prova 1 — Base",
        d: "Número da portaria + trecho/print que descreve as parcelas e o objetivo do incentivo.",
      },
      {
        t: "Prova 2 — Entrada",
        d: "Print do extrato do Fundo evidenciando a entrada do PV‑Visa (data e valor).",
      },
      {
        t: "Prova 3 — Entrega",
        d: "Registro da execução + consolidação no RAG (com um resumo curto do que foi feito).",
      },
    ],

    errosComuns: [
      "Conferir o repasse e não criar plano/ação (o recurso fica sem destino claro).",
      "Executar sem registro e tentar montar evidência no fim do ano.",
      "Não integrar financeiro + área técnica (cada um tem um pedaço da história).",
    ],

    mensagemPronta: `PV‑Visa (2025) — rotina rápida

1) Financeiro: conciliar entrada no Fundo (data/valor)
2) Vigilância: definir ações prioritárias + responsável + prazo
3) Registro: guardar base/entrada/entrega e consolidar no RAG

Evidência mínima:
• Base (portaria)
• Entrada (extrato do Fundo)
• Entrega (registro + RAG)`,

    fontes: [
      "Ministério da Saúde: Portaria GM/MS nº 9.569, de 23/12/2025 (publicada no DOU em 26/12/2025).",
    ],
  },

  {
    id: "sa-guia-fim-ano",
    area: "saude",
    slug: "guia-sus-como-nao-perder-repasses-portarias-incremento-equipamentos-mac",
    tipo: "Guia",
    data: "2025-12-29",
    titulo: "Fim de ano no SUS: guia rápido para não perder repasses autorizados por portarias",
    subtitulo:
      "No fim do ano saem várias portarias (incremento, equipamentos, MAC). O risco é o município descobrir tarde, perder prazo interno e faltar documento.",
    resumo:
      "Método simples: portaria → checar anexo (IBGE/CNPJ) → conciliar → abrir tarefa com responsável e prazo → registrar para o RAG.",

    em30s: [
      "Mudou: não é um ato único — é um padrão de fim de ano (muitas portarias autorizando repasses).",
      "Afeta: saúde + financeiro + compras (e a gestão do RAG).",
      "Ação imediata: criar rotina semanal de checagem e transformar cada repasse em tarefa.",
    ],

    decisaoRapida: [
      "Precisa agir agora? Sim — o problema é timing (prazo interno e planejamento).",
      "Quem assume: alguém da saúde/finanças com rotina de checagem (15 min/semana).",
      "Risco: município estar no anexo e ninguém ver; depois vira correria e retrabalho.",
    ],

    entenda: [
      "Portaria autorizando repasse não resolve sozinha. Você precisa checar anexo (código IBGE/CNPJ), conciliar no extrato e abrir uma tarefa interna para execução/registro.",
      "Quando você faz isso toda semana, o RAG deixa de ser 'correria de dezembro' e vira fechamento natural.",
    ],

    mudaRotina: [
      "Rotina semanal (15 min): checar portarias e anexos.",
      "Quando o município aparecer: abrir tarefa com responsável/prazo e destino do recurso.",
      "Conciliação e registro desde o primeiro gasto para facilitar o RAG.",
    ],

    passos: [
      {
        t: "Confirmar",
        d: "Identificar a portaria do dia e checar se o município está no anexo (IBGE/CNPJ).",
      },
      {
        t: "Organizar",
        d: "Abrir tarefa interna: destino do recurso + responsável + prazo + forma de registro.",
      },
      {
        t: "Executar e registrar",
        d: "Conciliação + execução conforme plano + registro para consolidar no RAG.",
      },
    ],

    evidenciaMinima: [
      {
        t: "Prova 1 — Base",
        d: "Portaria + anexo (print do trecho onde o município aparece).",
      },
      {
        t: "Prova 2 — Entrada",
        d: "Extrato do Fundo confirmando entrada (quando ocorrer).",
      },
      {
        t: "Prova 3 — Entrega",
        d: "Registro da execução + resumo do que foi feito (para o RAG).",
      },
    ],

    errosComuns: [
      "Não checar anexos e perder o timing.",
      "Deixar para conciliar/registrar só no fim do ano.",
      "Executar sem combinar com compras/financeiro e criar retrabalho.",
    ],

    mensagemPronta: `SUS — portaria de repasse/incremento (rotina)

1) Checar anexo (IBGE/CNPJ) e confirmar se o município está contemplado
2) Abrir tarefa: destino do recurso + responsável + prazo
3) Conciliação no Fundo + execução + registro para o RAG

Evidência mínima:
• Base (portaria + anexo)
• Entrada (extrato)
• Entrega (registro + resumo)`,

    fontes: [
      "Conasems: compilação diária de legislações nacionais (dez/2025) com portarias de repasse e incrementos.",
    ],
  },

  {
    id: "ed-24",
    area: "educacao",
    slug: "toda-matematica-apoio-financeiro-pdde-resolucao-24-2025",
    tipo: "Resolução",
    data: "2025-12-23",
    titulo: "Toda Matemática: apoio financeiro via PDDE e o que a rede precisa fazer",
    subtitulo:
      "Resolução CD/FNDE nº 24/2025 regulamenta apoio financeiro do Compromisso Nacional Toda Matemática (orientação curricular).",
    resumo:
      "Na prática: escola executa via PDDE, mas o município precisa orientar, acompanhar pendências e garantir evidência para prestação de contas.",

    em30s: [
      "Mudou: apoio financeiro via PDDE para ações do Toda Matemática foi regulamentado (critérios + execução + contas).",
      "Afeta: escolas (execução) e Secretaria (orientação e acompanhamento).",
      "Ação imediata: padronizar orientação e rotina de acompanhamento (para não virar problema na prestação).",
    ],

    decisaoRapida: [
      "Precisa agir agora? Sim — adesão, orientação e acompanhamento evitam erro na ponta.",
      "Quem assume: Secretaria (gestão) + diretores/secretarias escolares (execução).",
      "Risco: escola compra errado ou não registra; depois vira devolução/pendência.",
    ],

    entenda: [
      "O dinheiro é meio. O resultado depende de governança: orientar o que pode comprar/como comprovar e acompanhar pendências por escola.",
      "Se cada escola fizer 'do seu jeito', a Secretaria só descobre o problema na prestação de contas.",
    ],

    mudaRotina: [
      "Padronizar um guia curto: o que pode, o que não pode e como comprovar.",
      "Acompanhar pendências por escola (prazo e registro).",
      "Concentrar evidência em 3 provas: base (resolução), entrada (repasse) e entrega (execução registrada).",
    ],

    passos: [
      {
        t: "Confirmar",
        d: "Checar critérios/adesão e orientar a rede sobre o que pode ser executado via PDDE.",
      },
      {
        t: "Organizar",
        d: "Criar rotina de acompanhamento por escola (pendências, prazos e suporte).",
      },
      {
        t: "Executar e prestar contas",
        d: "Apoiar execução correta e garantir registro/comprovação para prestação de contas.",
      },
    ],

    evidenciaMinima: [
      {
        t: "Prova 1 — Base",
        d: "Resolução + trecho com regras de execução/prestação (1 página).",
      },
      {
        t: "Prova 2 — Entrada",
        d: "Registro do repasse/entrada na conta PDDE (por escola, quando aplicável).",
      },
      {
        t: "Prova 3 — Entrega",
        d: "Execução registrada (nota/processo PDDE) + resumo curto do que foi entregue.",
      },
    ],

    errosComuns: [
      "Secretaria não orienta e cada escola executa de um jeito.",
      "Compra sem vínculo claro com o programa e sem registro adequado.",
      "Só olhar prestação de contas no final, quando já virou pendência.",
    ],

    mensagemPronta: `Toda Matemática (PDDE) — orientação para a rede

1) Confirmar adesão/critério e divulgar o que pode executar
2) Acompanhar pendências por escola (prazo e suporte)
3) Garantir registro para prestação de contas

Evidência mínima:
• Base (resolução)
• Entrada (repasse/conta PDDE)
• Entrega (execução registrada + resumo)`,

    fontes: [
      "MEC (gov.br): publicação sobre regulamentação do apoio financeiro do Toda Matemática (23/12/2025).",
      "FNDE/DOU: Resolução CD/FNDE nº 24, de 19/12/2025 (publicada em 23/12/2025).",
    ],
  },

  {
    id: "ed-18",
    area: "educacao",
    slug: "fnde-resolucao-18-2025-conta-zerada-saldos-fevereiro-2027",
    tipo: "Resolução",
    data: "2025-12-01",
    titulo: "FNDE: regra de saldos e ‘conta zerada’ — como se preparar",
    subtitulo:
      "Resolução CD/FNDE nº 18/2025 ajusta prazos e cria regra prática: novos créditos só em contas com saldo zerado (programas abrangidos).",
    resumo:
      "É mudança operacional: se o município não controla saldos e reprogramação, pode travar recebimento futuro. O caminho é rotina de conciliação e plano de uso.",

    em30s: [
      "Mudou: regra de 'conta zerada' para novos créditos e prazo de uso/reprogramação de saldos (a partir de 2027).",
      "Afeta: finanças/educação (gestão de contas e saldos dos programas).",
      "Ação imediata: preparar rotina mensal de conciliação e plano de uso para evitar saldo residual.",
    ],

    decisaoRapida: [
      "Precisa agir agora? Sim para se preparar — a regra entra em 2027, mas método se constrói antes.",
      "Quem assume: finanças/contabilidade + educação (gestão dos programas).",
      "Risco: saldo residual travar novos créditos e gerar corrida para 'zerar'.",
    ],

    entenda: [
      "'Conta zerada' não é gastar por gastar. É ter planejamento e execução para não deixar saldo parado sem destino e evitar bloqueio de novos créditos.",
      "A prefeitura ganha quando transforma isso em rotina: conciliar → decidir → executar → registrar.",
    ],

    mudaRotina: [
      "Rotina mensal: saldo → itens pendentes → decisão de uso/reprogramação.",
      "Evitar saldo residual antes da janela de novos créditos (quando aplicável).",
      "Tratar PDDE separado (regras próprias).",
    ],

    passos: [
      {
        t: "Confirmar",
        d: "Quais programas/contas entram na regra e qual o saldo atual de cada uma.",
      },
      {
        t: "Organizar",
        d: "Criar rotina mensal de conciliação e um plano de uso/reprogramação do saldo.",
      },
      {
        t: "Executar e registrar",
        d: "Executar o plano e evitar saldo residual que impeça novos créditos.",
      },
    ],

    evidenciaMinima: [
      {
        t: "Prova 1 — Base",
        d: "Resolução + trecho da regra de 'conta zerada' e do prazo de uso/reprogramação.",
      },
      {
        t: "Prova 2 — Entrada",
        d: "Relatório simples de saldos por conta/programa (mensal).",
      },
      {
        t: "Prova 3 — Entrega",
        d: "Plano executado (uso/reprogramação) + registro do fechamento do saldo quando aplicável.",
      },
    ],

    errosComuns: [
      "Só olhar saldo quando o crédito novo não cai.",
      "Deixar saldo residual pequeno e achar que 'não faz diferença'.",
      "Misturar PDDE com outras regras e gerar confusão.",
    ],

    mensagemPronta: `FNDE — conta zerada (preparação)

1) Levantar saldos por conta/programa
2) Rotina mensal: conciliar → decidir → executar
3) Evitar saldo residual antes da janela de novos créditos

Evidência mínima:
• Base (resolução)
• Entrada (relatório mensal de saldos)
• Entrega (plano executado + fechamento quando aplicável)`,

    fontes: [
      "FNDE/DOU: Resolução CD/FNDE nº 18, de 27/11/2025 (publicada em 01/12/2025).",
    ],
  },

  {
    id: "ed-reprog",
    area: "educacao",
    slug: "reprogramacao-de-saldos-par-fnde-como-fazer-sem-travar",
    tipo: "Guia",
    data: "2025-12-10",
    titulo: "Reprogramação de saldos (PAR/FNDE): como ajustar sem travar o município",
    subtitulo:
      "Reprogramar não é gambiarra: é ferramenta oficial para adequar execução à realidade local — desde que registre decisão e justificativa.",
    resumo:
      "Quando preço mudou, item ficou inviável ou necessidade mudou, reprogramar é o caminho. O erro é fazer sem justificativa e sem registro.",

    em30s: [
      "Mudou: não é um ato único — é um procedimento oficial do FNDE para ajustar execução.",
      "Afeta: educação + compras/financeiro (execução e prestação).",
      "Ação imediata: padronizar como justificar e registrar reprogramações.",
    ],

    decisaoRapida: [
      "Precisa agir agora? Sim, quando houver inviabilidade/necessidade diferente — com registro e justificativa.",
      "Quem assume: educação (técnico) + compras/financeiro (execução).",
      "Risco: reprogramar sem evidência e virar problema em auditoria.",
    ],

    entenda: [
      "Reprogramação existe para evitar devolução de recurso quando o item original ficou inviável ou perdeu sentido. Mas precisa deixar rastro: por que mudou e quem decidiu.",
      "O objetivo é transparência: decisão registrada, justificativa clara e execução ajustada.",
    ],

    mudaRotina: [
      "Antes de reprogramar: documentar o motivo (preço/mercado/necessidade).",
      "Registrar a decisão e atualizar plano/itens.",
      "Acompanhar pendências para executar o novo plano (sem perder o timing).",
    ],

    passos: [
      {
        t: "Confirmar",
        d: "Identificar o motivo real (preço, mercado, necessidade) e o que a regra permite ajustar.",
      },
      {
        t: "Organizar",
        d: "Registrar justificativa + decisão formal e atualizar o plano/itens.",
      },
      {
        t: "Executar e registrar",
        d: "Executar o plano ajustado e manter registro para prestação de contas.",
      },
    ],

    evidenciaMinima: [
      {
        t: "Prova 1 — Base",
        d: "Regra/orientação do FNDE sobre reprogramação (print/trecho).",
      },
      {
        t: "Prova 2 — Motivo",
        d: "Evidência do porquê: pesquisa de preço, tentativas, justificativa técnica.",
      },
      {
        t: "Prova 3 — Entrega",
        d: "Decisão registrada + plano atualizado + execução do item reprogramado.",
      },
    ],

    errosComuns: [
      "Reprogramar só 'na conversa' e não registrar a decisão.",
      "Não guardar evidência do motivo (preço/mercado).",
      "Atualizar o plano, mas não acompanhar pendências para executar.",
    ],

    mensagemPronta: `PAR/FNDE — reprogramação

1) Motivo: preço/mercado/necessidade (documentar)
2) Decisão: registrar despacho/ata e atualizar plano
3) Execução: acompanhar pendências e executar o novo plano

Evidência mínima:
• Base (orientação)
• Motivo (prova do porquê)
• Entrega (decisão + plano + execução)`,

    fontes: [
      "FNDE (gov.br): orientações gerais sobre reprogramação de saldos e execução.",
    ],
  },
];
