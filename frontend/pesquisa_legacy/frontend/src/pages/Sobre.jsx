import React from "react";

const azulIdeal = "#050C36";
const douradoIdeal = "#B28316";

export default function Sobre() {
  return (
    <div
      style={{
        maxWidth: 900,
        margin: "0 auto",
        padding: "32px 20px 60px 20px",
        fontFamily: "system-ui",
      }}
    >
      {/* TÍTULO */}
      <h1
        style={{
          fontSize: 30,
          fontWeight: 700,
          color: azulIdeal,
          marginBottom: 12,
        }}
      >
        Sobre a Ideal Desenvolvimento Estratégico
      </h1>

      {/* SUBTÍTULO */}
      <p
        style={{
          fontSize: 17,
          color: "#444",
          lineHeight: 1.6,
          marginBottom: 22,
          maxWidth: 720,
        }}
      >
        A Ideal Desenvolvimento Estratégico é um instituto dedicado à produção de
        informação qualificada sobre a sociedade brasileira. Atuamos na fronteira
        entre pesquisa de opinião, análise de dados e planejamento estratégico.
      </p>

      {/* BLOCO 1 – QUEM SOMOS */}
      <h2
        style={{
          fontSize: 22,
          color: azulIdeal,
          borderLeft: `4px solid ${douradoIdeal}`,
          paddingLeft: 8,
          marginTop: 18,
          marginBottom: 8,
        }}
      >
        Quem somos
      </h2>

      <p style={{ fontSize: 16, color: "#333", lineHeight: 1.7 }}>
        A Ideal reúne profissionais das áreas de estatística, ciências sociais,
        ciência política, economia e gestão pública. A equipe combina experiência
        em pesquisas eleitorais, estudos de opinião, avaliação de políticas
        públicas e projetos de diagnóstico regional. Cada levantamento é tratado
        como um instrumento de leitura da realidade, e não apenas como um número
        divulgado na imprensa.
      </p>

      <p style={{ fontSize: 16, color: "#333", lineHeight: 1.7, marginTop: 10 }}>
        Nosso trabalho parte de uma premissa simples: decisões melhores exigem
        informações melhores. Por isso, a Ideal opera com metodologia clara,
        critérios rigorosos de qualidade e compromisso com a transparência na
        apresentação dos resultados.
      </p>

      {/* BLOCO 2 – O QUE FAZEMOS */}
      <h2
        style={{
          fontSize: 22,
          color: azulIdeal,
          borderLeft: `4px solid ${douradoIdeal}`,
          paddingLeft: 8,
          marginTop: 26,
          marginBottom: 8,
        }}
      >
        O que fazemos
      </h2>

      <p style={{ fontSize: 16, color: "#333", lineHeight: 1.7 }}>
        A Ideal Desenvolvimento Estratégico atua em três frentes principais:
      </p>

      <ul
        style={{
          marginTop: 10,
          fontSize: 16,
          color: "#333",
          lineHeight: 1.7,
          paddingLeft: 20,
        }}
      >
        <li>
          <strong>Pesquisas eleitorais:</strong> medição de intenção de voto,
          avaliação de governo, análise de cenário e identificação de tendências
          ao longo do tempo.
        </li>
        <li>
          <strong>Opinião pública e comportamento social:</strong> estudos sobre
          temas econômicos, sociais e institucionais, com recortes por região,
          faixa etária, renda, gênero e outros segmentos.
        </li>
        <li>
          <strong>Inteligência para gestão pública e privada:</strong> diagnósticos
          regionais, mapeamento de demandas da população, testes de políticas
          públicas, avaliação de programas e monitoramento de imagem.
        </li>
      </ul>

      <p style={{ fontSize: 16, color: "#333", lineHeight: 1.7, marginTop: 10 }}>
        Em todos os projetos, o foco é entregar análises que conversem com a
        realidade do território e com os desafios concretos de quem toma
        decisões.
      </p>

      {/* BLOCO 3 – MISSÃO, VISÃO, VALORES */}
      <h2
        style={{
          fontSize: 22,
          color: azulIdeal,
          borderLeft: `4px solid ${douradoIdeal}`,
          paddingLeft: 8,
          marginTop: 26,
          marginBottom: 8,
        }}
      >
        Missão, visão e valores
      </h2>

      <p style={{ fontSize: 16, color: "#333", lineHeight: 1.7 }}>
        A atuação da Ideal está ancorada em um conjunto claro de princípios:
      </p>

      <p style={{ marginTop: 10, fontSize: 16, color: "#333", lineHeight: 1.7 }}>
        <strong>Missão:</strong> produzir conhecimento confiável que ajude
        governos, empresas e instituições a tomar decisões mais responsáveis e
        conectadas à realidade da população.
      </p>

      <p style={{ marginTop: 8, fontSize: 16, color: "#333", lineHeight: 1.7 }}>
        <strong>Visão:</strong> consolidar-se como referência em pesquisa de
        opinião e inteligência estratégica, reconhecida pela seriedade
        metodológica, pela independência analítica e pela utilidade prática dos
        estudos realizados.
      </p>

      <p style={{ marginTop: 8, fontSize: 16, color: "#333", lineHeight: 1.7 }}>
        <strong>Valores:</strong> ética, transparência, rigor técnico,
        responsabilidade com o impacto público das informações e compromisso
        com a qualidade em todas as etapas do trabalho.
      </p>

      {/* BLOCO 4 – COMPROMISSO COM A TRANSPARÊNCIA */}
      <h2
        style={{
          fontSize: 22,
          color: azulIdeal,
          borderLeft: `4px solid ${douradoIdeal}`,
          paddingLeft: 8,
          marginTop: 26,
          marginBottom: 8,
        }}
      >
        Compromisso com a transparência
      </h2>

      <p style={{ fontSize: 16, color: "#333", lineHeight: 1.7 }}>
        Em pesquisas eleitorais, a Ideal segue as exigências da legislação
        vigente, com registro formal dos levantamentos quando necessário,
        divulgação de ficha técnica completa e detalhamento de metodologia,
        amostragem e período de realização.
      </p>

      <p style={{ fontSize: 16, color: "#333", lineHeight: 1.7, marginTop: 10 }}>
        O mesmo critério se aplica a estudos contratados por organizações
        privadas ou pelo setor público: sempre que houver divulgação dos dados,
        o público deve ter acesso à forma como a pesquisa foi feita, quais
        perfis foram ouvidos e qual o alcance estatístico daquela amostra.
      </p>

      {/* BLOCO 5 – O PAPEL DAS PESQUISAS */}
      <h2
        style={{
          fontSize: 22,
          color: azulIdeal,
          borderLeft: `4px solid ${douradoIdeal}`,
          paddingLeft: 8,
          marginTop: 26,
          marginBottom: 8,
        }}
      >
        O papel das pesquisas no debate público
      </h2>

      <p style={{ fontSize: 16, color: "#333", lineHeight: 1.7 }}>
        Pesquisas de opinião não são previsões automáticas de futuro, mas
        retratos de um determinado momento. Elas apontam tendências, ajudam a
        identificar demandas reprimidas e oferecem elementos para compreender
        o que está em disputa no debate público.
      </p>

      <p style={{ fontSize: 16, color: "#333", lineHeight: 1.7, marginTop: 10 }}>
        Ao divulgar seus levantamentos, a Ideal busca contribuir para um debate
        mais qualificado, em que dados confiáveis ocupem espaço no lugar de
        boatos, percepções isoladas ou informações distorcidas.
      </p>

      {/* FECHO */}
      <p
        style={{
          fontSize: 15,
          color: "#555",
          lineHeight: 1.7,
          marginTop: 26,
        }}
      >
        A Ideal Desenvolvimento Estratégico entende que conhecer melhor a
        sociedade é condição essencial para planejar políticas públicas,
        desenhar estratégias privadas e fortalecer a democracia. É com esse
        espírito que cada pesquisa é realizada, analisada e apresentada ao
        público.
      </p>
    </div>
  );
}