import React from "react";
import { useParams, useNavigate } from "react-router-dom";
import { pesquisasFake } from "../data/pesquisasFake";

const azulIdeal = "#050C36";
const douradoIdeal = "#B28316";

// Textos no estilo jornalístico, um por pesquisa
const textosJornalisticos = {
  "br-2025-alcool-alertas": [
    "A maioria absoluta dos brasileiros declara apoiar a adoção de alertas de risco à saúde em bebidas alcoólicas. A pesquisa Ideal Desenvolvimento Estratégico mostra que, para grande parte da população, o consumo de álcool deve vir acompanhado de informações claras sobre danos ao fígado, dependência e outras doenças associadas.",
    "Entre os entrevistados, é comum a percepção de que campanhas públicas e avisos nos rótulos podem ajudar principalmente os mais jovens a entender melhor os efeitos do consumo frequente. Mesmo entre quem consome bebidas alcoólicas com regularidade, prevalece o entendimento de que a transparência sobre riscos é um dever do Estado e da indústria.",
    "O apoio aos alertas é mais intenso entre mulheres e pessoas com filhos, grupos que tendem a mencionar preocupação com exemplos dentro da família e com a formação das novas gerações. Já entre os homens mais jovens, o apoio também é majoritário, mas aparecem com mais força argumentos ligados à liberdade de escolha e à responsabilidade individual.",
    "A pesquisa sugere que eventuais mudanças na legislação ou na regulamentação de rótulos devem encontrar um ambiente social favorável. A disputa tende a se concentrar menos no 'se' e mais no 'como' essas mensagens serão exibidas, quais conteúdos trarão e de que forma dialogarão com campanhas educativas mais amplas."
  ],

  "br-2025-racismo-infancia": [
    "Responsáveis por crianças de até 6 anos relatam, em parcela significativa, episódios de discriminação racial vividos pelos filhos. Segundo o levantamento da Ideal Desenvolvimento Estratégico, as situações citadas envolvem comentários sobre cor da pele, cabelo e traços físicos, muitas vezes em ambientes de convivência diária.",
    "O espaço escolar aparece com frequência como cenário desses relatos, seja em interações entre colegas, seja em falas atribuídas a adultos. Também são mencionados parques, ruas e locais de lazer, o que indica que o problema não se restringe a um ambiente específico, mas atravessa diferentes aspectos da vida social da criança.",
    "Entre os responsáveis que relatam episódios de racismo, é comum a sensação de despreparo para lidar com o tema. Muitos afirmam ter dificuldade em encontrar apoio institucional ou orientação adequada para mediar conflitos e proteger a autoestima das crianças, sobretudo nas idades iniciais, em que a percepção de si ainda está em formação.",
    "Os resultados reforçam a importância de políticas de formação para educadores, protocolos claros de acolhimento e canais de denúncia acessíveis. A pesquisa aponta que, na visão das famílias, o combate ao racismo na infância passa tanto pela punição de comportamentos discriminatórios quanto pela criação de ambientes escolares e comunitários mais inclusivos."
  ],

  "sp-2024-prefeitura-intencao-voto-1": [
    "Levantamento da Ideal Desenvolvimento Estratégico em São Paulo mede a intenção de voto para a disputa pela prefeitura da capital. O cenário estimulado apresenta um grupo reduzido de nomes mais conhecidos à frente, enquanto pré-candidatos menos expostos ainda lutam para se tornar conhecidos do eleitorado.",
    "Na avaliação espontânea, em que o entrevistado cita o nome sem ver a lista de candidatos, o índice de indecisos permanece elevado. A presença de eleitores que não sabem em quem votar ou que respondem 'ninguém' e 'branco/nulo' indica um quadro ainda aberto, típico de períodos anteriores ao início oficial da campanha.",
    "A pesquisa mostra diferenças relevantes entre regiões da cidade e faixas de renda. Em áreas periféricas, temas como transporte público, saúde nos bairros e segurança aparecem como prioridades nas menções espontâneas. Já entre eleitores de renda mais alta, ganham espaço discussões sobre gestão fiscal, inovação e mobilidade urbana.",
    "O estudo também verifica variações por faixa etária. Eleitores mais jovens demonstram maior distância da política institucional e maior uso das redes sociais como fonte de informação, enquanto os mais velhos tendem a citar com mais frequência rádio e televisão. Esses recortes ajudam a explicar por que alguns pré-candidatos se destacam em segmentos específicos do eleitorado."
  ],

  "mg-2024-avaliacao-governo-estadual": [
    "Em Minas Gerais, a pesquisa Ideal Desenvolvimento Estratégico mede a avaliação do governo estadual a partir das categorias ótimo, bom, regular, ruim e péssimo. O resultado revela um quadro de opinião dividido, com parcela do eleitorado avaliando positivamente áreas específicas, enquanto outra parte manifesta insatisfação com temas centrais do cotidiano.",
    "Entre os pontos melhor avaliados aparecem, em alguns segmentos, ações ligadas à infraestrutura e à atração de investimentos. Já na área de serviços públicos, especialmente saúde e transporte, crescem as menções negativas, com destaque para relatos de dificuldade de acesso e demora em atendimentos.",
    "O desempenho do governo varia conforme região do estado. Em polos urbanos e regiões mais industrializadas, a percepção tende a ser diferente daquela registrada em municípios menores, onde a dependência de serviços diretamente ofertados pelo poder público é maior. A distância entre a sede do governo e localidades do interior também é citada em algumas entrevistas como fator de desconexão.",
    "A análise por perfil de eleitor mostra que a avaliação de governo se entrelaça com expectativas econômicas e com o julgamento de gestões anteriores. Eleitores que declaram ver perspectiva de melhora na economia local tendem a ser mais tolerantes com problemas pontuais, enquanto aqueles que relatam piora na renda e no emprego demonstram maior propensão a avaliar a gestão de forma negativa."
  ]
};

export default function PesquisaDetalhe() {
  const { id } = useParams();
  const navigate = useNavigate();

  const pesquisa = pesquisasFake.find((p) => p.id === id);
  const paragrafosMateria = pesquisa ? textosJornalisticos[pesquisa.id] || [] : [];

  if (!pesquisa) {
    return (
      <div style={{ padding: 40 }}>
        <h2 style={{ color: azulIdeal }}>Pesquisa não encontrada</h2>
        <button
          onClick={() => navigate("/pesquisas")}
          style={{
            marginTop: 12,
            padding: "8px 12px",
            borderRadius: 4,
            border: "1px solid #ccc",
            backgroundColor: "#fff",
            cursor: "pointer",
            fontSize: 14
          }}
        >
          Voltar para pesquisas
        </button>
      </div>
    );
  }

  return (
    <div
      style={{
        padding: "32px 40px",
        maxWidth: 900,
        margin: "0 auto",
        fontFamily: "system-ui"
      }}
    >
      {/* Botão voltar */}
      <button
        onClick={() => navigate("/pesquisas")}
        style={{
          border: "none",
          background: "transparent",
          color: azulIdeal,
          fontSize: 14,
          cursor: "pointer",
          marginBottom: 16
        }}
      >
        ← Voltar para todas as pesquisas
      </button>

      {/* Tipo / cargo */}
      <div
        style={{
          fontSize: 12,
          fontWeight: 700,
          color: douradoIdeal,
          textTransform: "uppercase",
          marginBottom: 4
        }}
      >
        {pesquisa.tipo}
        {pesquisa.cargo ? ` · ${pesquisa.cargo}` : ""}
      </div>

      {/* TÍTULO */}
      <h1
        style={{
          fontSize: 32,
          lineHeight: 1.2,
          fontWeight: 700,
          color: azulIdeal,
          marginBottom: 12
        }}
      >
        {pesquisa.titulo}
      </h1>

      {/* SUBTÍTULO (puxado da descrição curta) */}
      <p
        style={{
          fontSize: 18,
          color: "#444",
          lineHeight: 1.4,
          marginBottom: 10
        }}
      >
        {pesquisa.descricaoCurta}
      </p>

      {/* META-INFORMAÇÕES */}
      <div
        style={{
          fontSize: 14,
          color: "#555",
          marginBottom: 24
        }}
      >
        {pesquisa.local} · Coleta em {pesquisa.dataColeta} · Amostra de{" "}
        {pesquisa.amostra} entrevistados · Margem de erro {pesquisa.margemErro}
      </div>

      {/* ÁREA DO GRÁFICO (placeholder por enquanto) */}
      <div
        style={{
          width: "100%",
          height: 320,
          backgroundColor: "#f2f2f2",
          borderRadius: 8,
          border: "1px solid #ddd",
          marginBottom: 24,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          color: "#777",
          fontSize: 14
        }}
      >
        (Gráfico da pesquisa será exibido aqui na próxima etapa)
      </div>

      {/* TEXTO JORNALÍSTICO */}
      {paragrafosMateria.length > 0 ? (
        paragrafosMateria.map((par, idx) => (
          <p
            key={idx}
            style={{
              fontSize: 16,
              color: "#333",
              lineHeight: 1.6,
              marginTop: idx === 0 ? 0 : 12
            }}
          >
            {par}
          </p>
        ))
      ) : (
        <>
          <p
            style={{
              fontSize: 16,
              color: "#333",
              lineHeight: 1.6,
              marginTop: 0
            }}
          >
            Este levantamento foi realizado pela Ideal Desenvolvimento
            Estratégico com o objetivo de medir a percepção pública sobre o
            tema. Em sua versão completa, o relatório inclui cruzamentos por
            sexo, idade, escolaridade, região e renda.
          </p>
          <p
            style={{
              fontSize: 16,
              color: "#333",
              lineHeight: 1.6
            }}
          >
            Os dados completos da pesquisa, incluindo a ficha técnica detalhada
            e o questionário aplicado, estão disponíveis em relatório próprio,
            que poderá ser acessado nesta mesma página quando a integração com o
            painel administrativo estiver concluída.
          </p>
        </>
      )}

      {/* TAGS */}
      <div style={{ marginTop: 16, marginBottom: 20 }}>
        {pesquisa.tags &&
          pesquisa.tags.map((tag) => (
            <span
              key={tag}
              style={{
                display: "inline-block",
                padding: "4px 8px",
                borderRadius: 999,
                border: "1px solid #ddd",
                marginRight: 6,
                backgroundColor: "#fafafa",
                fontSize: 13
              }}
            >
              {tag}
            </span>
          ))}
      </div>

      {/* FICHA TÉCNICA */}
      <div
        style={{
          backgroundColor: "#f9f9f9",
          border: "1px solid #ddd",
          borderRadius: 8,
          padding: 20,
          marginTop: 26
        }}
      >
        <h2
          style={{
            fontSize: 20,
            marginBottom: 10,
            color: azulIdeal,
            borderLeft: `4px solid ${douradoIdeal}`,
            paddingLeft: 8
          }}
        >
          Ficha técnica
        </h2>

        <p style={{ margin: "6px 0" }}>
          <strong>Instituto responsável:</strong> Ideal Desenvolvimento
          Estratégico
        </p>
        <p style={{ margin: "6px 0" }}>
          <strong>Local:</strong> {pesquisa.local}
        </p>
        <p style={{ margin: "6px 0" }}>
          <strong>Data da coleta:</strong> {pesquisa.dataColeta}
        </p>
        <p style={{ margin: "6px 0" }}>
          <strong>Amostra:</strong> {pesquisa.amostra} entrevistas
        </p>
        <p style={{ margin: "6px 0" }}>
          <strong>Margem de erro:</strong> {pesquisa.margemErro}
        </p>
        <p style={{ margin: "6px 0" }}>
          <strong>Metodologia:</strong> Amostra estratificada por sexo, idade,
          escolaridade, região e renda, com aplicação de questionário
          estruturado. Resultados ponderados para refletir a distribuição
          sociodemográfica da população estudada.
        </p>
      </div>

      {/* PDF */}
      <button
        onClick={() => {
          if (pesquisa.pdfUrl && pesquisa.pdfUrl !== "#") {
            window.open(pesquisa.pdfUrl, "_blank", "noopener,noreferrer");
          } else {
            alert("PDF ainda não cadastrado para esta pesquisa.");
          }
        }}
        style={{
          marginTop: 24,
          padding: "10px 16px",
          borderRadius: 4,
          border: "none",
          backgroundColor: azulIdeal,
          color: "white",
          fontSize: 15,
          cursor: "pointer"
        }}
      >
        Baixar relatório completo (PDF)
      </button>
    </div>
  );
}