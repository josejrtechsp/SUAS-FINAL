import React from "react";

const azulIdeal = "#050C36";
const douradoIdeal = "#B28316";

export default function Metodologia() {
  return (
    <div
      style={{
        maxWidth: 900,
        margin: "0 auto",
        padding: "32px 20px 60px 20px",
        fontFamily: "system-ui",
      }}
    >
      {/* Título */}
      <h1
        style={{
          fontSize: 30,
          fontWeight: 700,
          color: azulIdeal,
          marginBottom: 12,
        }}
      >
        Metodologia das Pesquisas
      </h1>

      {/* Subtítulo */}
      <p
        style={{
          fontSize: 16,
          color: "#444",
          marginBottom: 24,
          maxWidth: 700,
          lineHeight: 1.6,
        }}
      >
        A Ideal Desenvolvimento Estratégico adota rigor técnico, transparência
        operacional e protocolos reconhecidos nacional e internacionalmente
        para realização de pesquisas de opinião pública, eleitorais e análises
        estratégicas.
      </p>

      {/* Sessão 1 */}
      <h2
        style={{
          fontSize: 22,
          color: azulIdeal,
          marginTop: 20,
          borderLeft: `4px solid ${douradoIdeal}`,
          paddingLeft: 8,
        }}
      >
        1. Desenho amostral
      </h2>

      <p style={{ lineHeight: 1.6, color: "#333", marginTop: 8 }}>
        Os estudos utilizam amostras probabilísticas ou amostras por cotas,
        dependendo do objetivo e da natureza do levantamento. As variáveis
        consideradas incluem:
      </p>

      <ul style={{ marginTop: 10, lineHeight: 1.6, color: "#333" }}>
        <li>Sexo</li>
        <li>Faixa etária</li>
        <li>Escolaridade</li>
        <li>Renda</li>
        <li>Região geográfica ou bairro</li>
        <li>Estrutura demográfica local (IBGE, PNAD, TSE)</li>
      </ul>

      {/* Sessão 2 */}
      <h2
        style={{
          fontSize: 22,
          color: azulIdeal,
          marginTop: 26,
          borderLeft: `4px solid ${douradoIdeal}`,
          paddingLeft: 8,
        }}
      >
        2. Coleta de dados
      </h2>

      <p style={{ lineHeight: 1.6, color: "#333", marginTop: 8 }}>
        A coleta é realizada exclusivamente por entrevistadores treinados,
        utilizando questionários estruturados. Os modos de coleta podem incluir:
      </p>

      <ul style={{ marginTop: 10, lineHeight: 1.6, color: "#333" }}>
        <li>Aplicação presencial (PAPI ou CAPI)</li>
        <li>Entrevistas telefônicas supervisionadas (CATI)</li>
        <li>Levantamentos online com painéis certificados</li>
      </ul>

      <p style={{ marginTop: 10, lineHeight: 1.6, color: "#333" }}>
        Todos os levantamentos contam com checagem de consistência, verificação
        de tempo mínimo, auditoria e monitoramento das rotas de entrevistadores
        quando aplicável.
      </p>

      {/* Sessão 3 */}
      <h2
        style={{
          fontSize: 22,
          color: azulIdeal,
          marginTop: 26,
          borderLeft: `4px solid ${douradoIdeal}`,
          paddingLeft: 8,
        }}
      >
        3. Ponderação e limpeza dos dados
      </h2>

      <p style={{ lineHeight: 1.6, color: "#333", marginTop: 8 }}>
        As bases de dados passam por processos de ponderação (weights) para
        ajustar proporcionalmente a amostra ao perfil populacional real. Isso
        inclui correções baseadas em:
      </p>

      <ul style={{ marginTop: 10, lineHeight: 1.6, color: "#333" }}>
        <li>Distribuição por sexo e idade</li>
        <li>Perfil educacional</li>
        <li>Regiões e zonas geográficas</li>
        <li>Peso populacional de municípios ou bairros</li>
      </ul>

      <p style={{ marginTop: 10, lineHeight: 1.6, color: "#333" }}>
        Antes da análise, respostas inconsistentes são verificadas e casos
        suspeitos ou inválidos são removidos.
      </p>

      {/* Sessão 4 */}
      <h2
        style={{
          fontSize: 22,
          color: azulIdeal,
          marginTop: 26,
          borderLeft: `4px solid ${douradoIdeal}`,
          paddingLeft: 8,
        }}
      >
        4. Margem de erro e intervalo de confiança
      </h2>

      <p style={{ lineHeight: 1.6, color: "#333", marginTop: 8 }}>
        As pesquisas seguem padrões estatísticos amplamente aceitos. Para
        amostras probabilísticas:
      </p>

      <ul style={{ marginTop: 10, lineHeight: 1.6, color: "#333" }}>
        <li>Margem de erro calculada conforme variância binomial</li>
        <li>Nível de confiança de 95%</li>
        <li>Correção para população finita quando aplicável</li>
      </ul>

      <p style={{ marginTop: 10, lineHeight: 1.6, color: "#333" }}>
        Em amostras por cotas, a margem de erro é apresentada como estimativa
        aproximada para fins comparativos.
      </p>

      {/* Sessão 5 */}
      <h2
        style={{
          fontSize: 22,
          color: azulIdeal,
          marginTop: 26,
          borderLeft: `4px solid ${douradoIdeal}`,
          paddingLeft: 8,
        }}
      >
        5. Transparência e registro dos estudos
      </h2>

      <p style={{ lineHeight: 1.6, color: "#333", marginTop: 8 }}>
        Para pesquisas eleitorais, a Ideal segue estritamente as normas da
        legislação vigente, incluindo:
      </p>

      <ul style={{ marginTop: 10, lineHeight: 1.6, color: "#333" }}>
        <li>Registro no TSE quando exigido</li>
        <li>Publicação de ficha técnica completa</li>
        <li>Metodologia clara e auditável</li>
        <li>Arquivamento dos questionários e planilhas brutas</li>
      </ul>

      {/* Sessão 6 */}
      <h2
        style={{
          fontSize: 22,
          color: azulIdeal,
          marginTop: 26,
          borderLeft: `4px solid ${douradoIdeal}`,
          paddingLeft: 8,
        }}
      >
        6. Ética e proteção de dados
      </h2>

      <p style={{ lineHeight: 1.6, color: "#333", marginTop: 8 }}>
        Todas as entrevistas são anônimas, respeitando integralmente as normas
        da LGPD. Nenhuma informação individualizada é coletada com fins de
        identificação pessoal.
      </p>

      <p style={{ marginTop: 10, lineHeight: 1.6, color: "#333" }}>
        Os bancos de dados são armazenados em servidores seguros e acessíveis
        apenas a profissionais autorizados.
      </p>

      {/* Sessão final */}
      <p
        style={{
          marginTop: 30,
          fontSize: 15,
          color: "#555",
          lineHeight: 1.6,
        }}
      >
        A Ideal Desenvolvimento Estratégico combina rigor estatístico,
        experiência acumulada e compromisso com a qualidade da informação para
        entregar diagnósticos sólidos, confiáveis e úteis para gestores públicos,
        organizações privadas, imprensa e sociedade.
      </p>
    </div>
  );
}