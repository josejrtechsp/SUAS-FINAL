// Atualizações oficiais (modelo de dados)
//
// 🔁 Como atualizar:
// 1) Adicione novos itens no topo (mais recentes primeiro).
// 2) Use data no formato YYYY-MM-DD.
// 3) `url` deve apontar para a fonte oficial (gov.br, in.gov.br, FNDE, FNAS etc.).
//
// ⚠️ Observação: este arquivo é um repositório simples (curadoria). Depois, pode virar API.

export const ATUALIZACOES_OFICIAIS = [
  // =====================
  // ASSISTÊNCIA SOCIAL
  // =====================
  {
    id: "as-2025-11-25-cnas-220",
    area: "assistencia",
    tipo: "Resolução",
    data: "2025-11-25",
    orgao: "CNAS / MDS",
    tag: "CNAS",
    titulo: "Resolução CNAS/MDS nº 220 — Diretrizes do Prontuário Eletrônico do SUAS",
    resumo: "Diretrizes para prontuário eletrônico no SUAS (base para padronização e qualidade do registro).",
    url: "https://blog.mds.gov.br/redesuas/resolucao-cnas-mds-no-220-de-25-de-novembro-de-2025/",
  },
  {
    id: "as-2025-12-04-mds-1136",
    area: "assistencia",
    tipo: "Portaria",
    data: "2025-12-04",
    orgao: "MDS",
    tag: "MDS",
    titulo: "Portaria MDS nº 1.136 — atualização normativa (SUAS)",
    resumo: "Ato normativo recente do MDS. Use como referência para atualização regulatória no SUAS.",
    url: "https://www.gov.br/mds/pt-br/acesso-a-informacao/legislacao/portaria/portaria-mds-no-1-136-de-4-de-dezembro-de-2025",
  },
  {
    id: "as-2025-fnas-selo",
    area: "assistencia",
    tipo: "Comunicado",
    data: "2025-12-01",
    orgao: "FNAS",
    tag: "FNAS",
    titulo: "FNAS — prazos e verificação (Selo FNAS / AgilizaSUAS)",
    resumo: "Atualização de prazos e critérios: verificação e concessão do Selo e exigências associadas.",
    url: "https://fnas.mds.gov.br/fnas-divulga-novos-prazos-para-apuracao-e-concessao-do-selo-fnas/",
  },
  {
    id: "as-2025-10-09-bpc-portaria-conjunta-34",
    area: "assistencia",
    tipo: "Portaria",
    data: "2025-10-09",
    orgao: "MDS / INSS",
    tag: "BPC",
    titulo: "Portaria Conjunta MDS/INSS nº 34 — regras do BPC",
    resumo: "Regras e procedimentos para requerimento, concessão, manutenção e revisão do BPC.",
    url: "https://www.gov.br/inss/pt-br/centrais-de-conteudo/legislacao/portarias-conjuntas/2025/ptcj34mds-inss.pdf",
  },
  {
    id: "as-2025-04-25-snas-47-itens-financiaveis",
    area: "assistencia",
    tipo: "Portaria",
    data: "2025-04-25",
    orgao: "SNAS / MDS",
    tag: "FNAS",
    titulo: "Portaria SNAS/MDS nº 47 — itens financiáveis com recursos SUAS",
    resumo: "Lista padronizada de itens aptos à aquisição com recursos do SUAS.",
    url: "https://fnas.mds.gov.br/nova-portaria-atualiza-lista-de-itens-que-podem-ser-adquiridos-com-recursos-do-suas/",
  },
];

// Atalhos úteis (fontes oficiais) — exibidos na página para orientar a equipe.
// Mantém o portal autoexplicativo mesmo quando uma área ainda não tem itens cadastrados.
export const FONTES_OFICIAIS = {
  assistencia: [
    { nome: "Diário Oficial da União (DOU)", url: "https://www.in.gov.br" },
    { nome: "Ministério do Desenvolvimento e Assistência Social (MDS)", url: "https://www.gov.br/mds/pt-br" },
    { nome: "FNAS — Fundo Nacional de Assistência Social", url: "https://fnas.mds.gov.br" },
    { nome: "Rede SUAS (publicações)", url: "https://blog.mds.gov.br/redesuas" },
  ],
  saude: [
    { nome: "Diário Oficial da União (DOU)", url: "https://www.in.gov.br" },
    { nome: "Ministério da Saúde", url: "https://www.gov.br/saude/pt-br" },
    { nome: "FNS — Fundo Nacional de Saúde", url: "https://www.gov.br/saude/pt-br/composicao/saes/fundo-nacional-de-saude" },
  ],
  educacao: [
    { nome: "Diário Oficial da União (DOU)", url: "https://www.in.gov.br" },
    { nome: "Ministério da Educação (MEC)", url: "https://www.gov.br/mec/pt-br" },
    { nome: "FNDE — Fundo Nacional de Desenvolvimento da Educação", url: "https://www.fnde.gov.br" },
  ],
};
