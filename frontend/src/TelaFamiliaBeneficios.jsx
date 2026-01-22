import { useEffect, useState } from "react";
import PageHero from "./components/PageHero";

const API_BASE = "http://localhost:8000";

/**
 * TelaFamiliaBeneficios
 *
 * Abinha para o servidor escolher uma pessoa e editar:
 * - Família de referência
 * - Benefícios da pessoa (BPC, Bolsa Família, etc.)
 *
 * Props:
 * - pessoas: array de pessoas (do App)
 */
export default function TelaFamiliaBeneficios({ pessoas }) {
  const [pessoaId, setPessoaId] = useState("");
  const [familia, setFamilia] = useState(null);
  const [beneficios, setBeneficios] = useState([]);

  const [carregandoFamilia, setCarregandoFamilia] = useState(false);
  const [carregandoBeneficios, setCarregandoBeneficios] = useState(false);
  const [salvandoFamilia, setSalvandoFamilia] = useState(false);
  const [salvandoBeneficio, setSalvandoBeneficio] = useState(false);

  const [erroFamilia, setErroFamilia] = useState("");
  const [erroBeneficios, setErroBeneficios] = useState("");

  // Form família
  const [nomeReferencia, setNomeReferencia] = useState("");
  const [parentesco, setParentesco] = useState("");
  const [telefone, setTelefone] = useState("");
  const [familiaMunicipioId, setFamiliaMunicipioId] = useState("");
  const [familiaObs, setFamiliaObs] = useState("");

  // Form benefício
  const [benefTipo, setBenefTipo] = useState("BPC");
  const [benefSituacao, setBenefSituacao] = useState("ativo");
  const [benefDescricao, setBenefDescricao] = useState("");
  const [benefDataInicio, setBenefDataInicio] = useState("");
  const [benefNIS, setBenefNIS] = useState("");
  const [benefOrgao, setBenefOrgao] = useState("");

  // flags de UI (controlam quando mostrar formulários)
  const [mostrarFormFamilia, setMostrarFormFamilia] = useState(false);
  const [mostrarFormBeneficio, setMostrarFormBeneficio] = useState(false);

  // sempre que mudar a pessoa, recarrega família e benefícios
  useEffect(() => {
    if (!pessoaId) {
      setFamilia(null);
      setBeneficios([]);
      return;
    }

    carregarFamilia();
    carregarBeneficios();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pessoaId]);

  async function carregarFamilia() {
    setCarregandoFamilia(true);
    setErroFamilia("");

    try {
      const res = await fetch(
        `${API_BASE}/pessoas/${pessoaId}/familia-referencia`
      );
      if (!res.ok) {
        throw new Error("Erro ao carregar família de referência.");
      }

      const data = await res.json();
      if (data) {
        setFamilia(data);
        setNomeReferencia(data.nome_referencia || "");
        setParentesco(data.parentesco || "");
        setTelefone(data.telefone || "");
        setFamiliaMunicipioId(data.municipio_id || "");
        setFamiliaObs(data.observacoes || "");
        setMostrarFormFamilia(false);
      } else {
        setFamilia(null);
        setNomeReferencia("");
        setParentesco("");
        setTelefone("");
        setFamiliaMunicipioId("");
        setFamiliaObs("");
        setMostrarFormFamilia(true);
      }
    } catch (e) {
      console.error(e);
      setErroFamilia(e.message);
      setFamilia(null);
    } finally {
      setCarregandoFamilia(false);
    }
  }

  async function carregarBeneficios() {
    setCarregandoBeneficios(true);
    setErroBeneficios("");

    try {
      const res = await fetch(
        `${API_BASE}/pessoas/${pessoaId}/beneficios`
      );
      if (!res.ok) {
        throw new Error("Erro ao carregar benefícios da pessoa.");
      }

      const data = await res.json();
      setBeneficios(Array.isArray(data) ? data : []);
    } catch (e) {
      console.error(e);
      setErroBeneficios(e.message);
      setBeneficios([]);
    } finally {
      setCarregandoBeneficios(false);
    }
  }

  async function handleSalvarFamilia(e) {
    e.preventDefault();
    if (!pessoaId) return;

    setSalvandoFamilia(true);
    setErroFamilia("");

    const body = {
      nome_referencia: nomeReferencia || null,
      parentesco: parentesco || null,
      telefone: telefone || null,
      municipio_id: familiaMunicipioId
        ? Number(familiaMunicipioId)
        : null,
      observacoes: familiaObs || null,
    };

    try {
      const res = await fetch(
        `${API_BASE}/pessoas/${pessoaId}/familia-referencia`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body),
        }
      );

      if (!res.ok) {
        let msg = "Erro ao salvar família de referência.";
        try {
          const errJson = await res.json();
          if (errJson.detail) msg = JSON.stringify(errJson.detail);
        } catch (_) {}
        throw new Error(msg);
      }

      const data = await res.json();
      setFamilia(data);
      setMostrarFormFamilia(false);
      alert("Família de referência salva com sucesso!");
    } catch (e) {
      console.error(e);
      setErroFamilia(e.message);
    } finally {
      setSalvandoFamilia(false);
    }
  }

  async function handleSalvarBeneficio(e) {
    e.preventDefault();
    if (!pessoaId) return;

    setSalvandoBeneficio(true);
    setErroBeneficios("");

    const body = {
      tipo: benefTipo || "Outro",
      situacao: benefSituacao || "ativo",
      descricao: benefDescricao || null,
      data_inicio: benefDataInicio
        ? new Date(benefDataInicio).toISOString().slice(0, 10)
        : null,
      data_fim: null,
      orgao_gestor: benefOrgao || null,
      numero_nis: benefNIS || null,
    };

    try {
      const res = await fetch(
        `${API_BASE}/pessoas/${pessoaId}/beneficios`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body),
        }
      );

      if (!res.ok) {
        let msg = "Erro ao salvar benefício.";
        try {
          const errJson = await res.json();
          if (errJson.detail) msg = JSON.stringify(errJson.detail);
        } catch (_) {}
        throw new Error(msg);
      }

      const novo = await res.json();
      setBeneficios((lista) => [novo, ...lista]);
      setBenefTipo("BPC");
      setBenefSituacao("ativo");
      setBenefDescricao("");
      setBenefDataInicio("");
      setBenefNIS("");
      setBenefOrgao("");
      setMostrarFormBeneficio(false);

      alert("Benefício registrado com sucesso!");
    } catch (e) {
      console.error(e);
      setErroBeneficios(e.message);
    } finally {
      setSalvandoBeneficio(false);
    }
  }

  return (
    <div className="layout-1col">
      <PageHero
  kicker="MÓDULO SUAS · POP RUA EM REDE"
  title="Pop Rua — Família & Benefícios"
  subtitle="Registre família de referência e benefícios (BPC, Bolsa Família, benefícios eventuais), com rastreabilidade."
  tips={[
    "Vincule benefícios à pessoa e ao caso quando aplicável.",
    "Mantenha histórico e evidências.",
    "Base para relatórios e gestão de demandas.",
  ]}
  badge="POP RUA"
/>
<section className="card card-wide">
        <div className="card-header-row">
          <div>
          </div>
        </div>

        {/* Seleção de pessoa */}
        <div style={{ marginBottom: 16 }}>
          <label className="form-label">
            Pessoa em situação de rua
            <select
              className="input"
              value={pessoaId}
              onChange={(e) => {
                setPessoaId(e.target.value);
                setErroFamilia("");
                setErroBeneficios("");
              }}
            >
              <option value="">Selecione...</option>
              {pessoas.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.id} — {p.nome_social || p.nome_civil}
                </option>
              ))}
            </select>
          </label>
        </div>

        {!pessoaId && (
          <p className="texto-suave">
            Selecione uma pessoa acima para exibir e editar família de referência e
            benefícios.
          </p>
        )}

        {pessoaId && (
          <>
            {/* BLOCO FAMÍLIA */}
            <div className="card card-familia">
              <div className="card-header-row">
                <div className="familia-header-titulo">
                  <span className="familia-icone">👨‍👩‍👧</span>
                  <div>
                    <h3>Família de referência</h3>
                    <p className="familia-subtitulo">
                      Contato principal e vínculos familiares para apoio ao
                      acompanhamento.
                    </p>
                  </div>
                </div>

                {familia && !mostrarFormFamilia && (
                  <button
                    type="button"
                    className="btn btn-secundario btn-secundario-mini"
                    onClick={() => setMostrarFormFamilia(true)}
                  >
                    Editar família
                  </button>
                )}
              </div>

              {erroFamilia && (
                <p className="erro-global" style={{ marginBottom: 8 }}>
                  {erroFamilia}
                </p>
              )}

              {carregandoFamilia && (
                <p className="texto-suave">Carregando família...</p>
              )}

              {/* Resumo quando já existe família e não está editando */}
              {familia && !mostrarFormFamilia && !carregandoFamilia && (
                <div className="familia-resumo">
                  <div className="familia-resumo-linha">
                    <span className="familia-resumo-label">Referência</span>
                    <span className="familia-resumo-valor">
                      {familia.nome_referencia || "Não informado"}
                      {familia.parentesco && ` (${familia.parentesco})`}
                    </span>
                  </div>
                  <div className="familia-resumo-linha">
                    <span className="familia-resumo-label">Telefone</span>
                    <span className="familia-resumo-valor">
                      {familia.telefone || "Não informado"}
                    </span>
                  </div>
                  <div className="familia-resumo-linha">
                    <span className="familia-resumo-label">Município (ID)</span>
                    <span className="familia-resumo-valor">
                      {familia.municipio_id || "Não informado"}
                    </span>
                  </div>
                  {familia.observacoes && (
                    <div className="familia-resumo-linha familia-resumo-observacoes">
                      <span className="familia-resumo-label">Observações</span>
                      <span className="familia-resumo-valor">
                        {familia.observacoes}
                      </span>
                    </div>
                  )}
                </div>
              )}

              {/* Formulário de edição/criação de família */}
              {mostrarFormFamilia && !carregandoFamilia && (
                <>
                  <form onSubmit={handleSalvarFamilia} className="grid-2cols">
                    <div>
                      <label className="form-label">
                        Nome da pessoa de referência
                        <input
                          className="input"
                          value={nomeReferencia}
                          onChange={(e) => setNomeReferencia(e.target.value)}
                          placeholder="Ex.: Maria de Souza (mãe)"
                        />
                      </label>

                      <label className="form-label">
                        Parentesco
                        <input
                          className="input"
                          value={parentesco}
                          onChange={(e) => setParentesco(e.target.value)}
                          placeholder="Ex.: mãe, pai, irmã, companheiro..."
                        />
                      </label>

                      <label className="form-label">
                        Telefone
                        <input
                          className="input"
                          value={telefone}
                          onChange={(e) => setTelefone(e.target.value)}
                          placeholder="(xx) xxxxx-xxxx"
                        />
                      </label>
                    </div>

                    <div>
                      <label className="form-label">
                        Município (ID) da família
                        <input
                          className="input"
                          value={familiaMunicipioId}
                          onChange={(e) =>
                            setFamiliaMunicipioId(e.target.value)
                          }
                          placeholder="ID do município de residência da família"
                        />
                      </label>

                      <label className="form-label">
                        Observações sobre os vínculos
                        <textarea
                          className="input"
                          rows={4}
                          value={familiaObs}
                          onChange={(e) => setFamiliaObs(e.target.value)}
                          placeholder="Resumo dos vínculos, contatos mantidos, possibilidades de retorno, conflitos, etc."
                        />
                      </label>
                    </div>
                  </form>

                  <div className="card-footer-right" style={{ marginTop: 8 }}>
                    <button
                      type="button"
                      className="btn btn-secundario btn-secundario-mini"
                      onClick={() => setMostrarFormFamilia(false)}
                      disabled={salvandoFamilia}
                      style={{ marginRight: 8 }}
                    >
                      Cancelar
                    </button>
                    <button
                      type="submit"
                      className="btn btn-primario"
                      onClick={handleSalvarFamilia}
                      disabled={salvandoFamilia}
                    >
                      {salvandoFamilia
                        ? "Salvando..."
                        : "Salvar família de referência"}
                    </button>
                  </div>
                </>
              )}

              {!familia && !carregandoFamilia && !mostrarFormFamilia && (
                <p className="texto-suave">
                  Ainda não há família de referência cadastrada para esta pessoa.
                  Clique em <strong>“Editar família”</strong> para incluir os dados.
                </p>
              )}
            </div>

            {/* BLOCO BENEFÍCIOS */}
            <div className="card card-beneficios">
              <div className="card-header-row">
                <div className="beneficios-header">
                  <span className="beneficios-icone">💳</span>
                  <div>
                    <h3>Benefícios da pessoa</h3>
                    <p className="beneficios-subtitulo">
                      Benefícios em andamento, suspensos ou em análise (BPC, Bolsa
                      Família, benefícios eventuais, etc.).
                    </p>
                  </div>
                </div>

                <button
                  type="button"
                  className="btn btn-secundario btn-secundario-mini"
                  onClick={() => setMostrarFormBeneficio((v) => !v)}
                >
                  {mostrarFormBeneficio
                    ? "Fechar formulário"
                    : "Registrar novo benefício"}
                </button>
              </div>

              {erroBeneficios && (
                <p className="erro-global" style={{ marginBottom: 8 }}>
                  {erroBeneficios}
                </p>
              )}

              {carregandoBeneficios && (
                <p className="texto-suave">Carregando benefícios...</p>
              )}

              {!carregandoBeneficios && beneficios.length === 0 && (
                <p className="texto-suave">
                  Ainda não há benefícios cadastrados para esta pessoa.
                </p>
              )}

              {!carregandoBeneficios && beneficios.length > 0 && (
                <ul className="lista-beneficios">
                  {beneficios.map((b) => (
                    <li key={b.id} className="beneficio-item">
                      <div className="beneficio-header">
                        <span className="beneficio-tipo">{b.tipo}</span>
                        <span
                          className={
                            "beneficio-situacao beneficio-situacao-" +
                            (b.situacao || "ativo")
                          }
                        >
                          {rotuloSituacaoBeneficio(b.situacao)}
                        </span>
                      </div>
                      <div className="beneficio-info-linha">
                        <span>
                          {formatarPeriodoBeneficio(
                            b.data_inicio,
                            b.data_fim
                          )}
                        </span>
                      </div>
                      <div className="beneficio-info-linha">
                        {b.numero_nis && (
                          <span>
                            NIS: <strong>{b.numero_nis}</strong>
                          </span>
                        )}
                        {b.orgao_gestor && (
                          <span>
                            Órgão: <strong>{b.orgao_gestor}</strong>
                          </span>
                        )}
                      </div>
                      {b.descricao && (
                        <p className="beneficio-descricao">{b.descricao}</p>
                      )}
                    </li>
                  ))}
                </ul>
              )}

              {/* Form novo benefício (mostrado sob demanda) */}
              {mostrarFormBeneficio && (
                <form
                  onSubmit={handleSalvarBeneficio}
                  className="canal-form"
                  style={{ marginTop: 16 }}
                >
                  <h4 className="protocolo-step-title">
                    Registrar novo benefício
                  </h4>

                  <div className="grid-2cols">
                    <div>
                      <label className="form-label">
                        Tipo de benefício
                        <select
                          className="input"
                          value={benefTipo}
                          onChange={(e) => setBenefTipo(e.target.value)}
                        >
                          <option value="BPC">
                            BPC (Benefício de Prestação Continuada)
                          </option>
                          <option value="Bolsa Família">Bolsa Família</option>
                          <option value="Benefício eventual">
                            Benefício eventual
                          </option>
                          <option value="Outro">Outro</option>
                        </select>
                      </label>

                      <label className="form-label">
                        Situação
                        <select
                          className="input"
                          value={benefSituacao}
                          onChange={(e) => setBenefSituacao(e.target.value)}
                        >
                          <option value="ativo">Ativo</option>
                          <option value="suspenso">Suspenso</option>
                          <option value="encerrado">Encerrado</option>
                          <option value="em_analise">Em análise</option>
                        </select>
                      </label>

                      <label className="form-label">
                        Data de início
                        <input
                          type="date"
                          className="input"
                          value={benefDataInicio}
                          onChange={(e) =>
                            setBenefDataInicio(e.target.value)
                          }
                        />
                      </label>
                    </div>

                    <div>
                      <label className="form-label">
                        NIS (se aplicável)
                        <input
                          className="input"
                          value={benefNIS}
                          onChange={(e) => setBenefNIS(e.target.value)}
                          placeholder="Número do NIS relacionado ao benefício"
                        />
                      </label>

                      <label className="form-label">
                        Órgão gestor / responsável
                        <input
                          className="input"
                          value={benefOrgao}
                          onChange={(e) => setBenefOrgao(e.target.value)}
                          placeholder="INSS, Prefeitura, Estado, etc."
                        />
                      </label>

                      <label className="form-label">
                        Descrição / observações
                        <textarea
                          className="input"
                          rows={3}
                          value={benefDescricao}
                          onChange={(e) =>
                            setBenefDescricao(e.target.value)
                          }
                          placeholder="Qualquer informação adicional importante sobre o benefício."
                        />
                      </label>
                    </div>
                  </div>

                  <div className="card-footer-right">
                    <button
                      type="submit"
                      className="btn btn-primario"
                      disabled={salvandoBeneficio}
                    >
                      {salvandoBeneficio
                        ? "Salvando..."
                        : "Registrar benefício"}
                    </button>
                  </div>
                </form>
              )}
            </div>
          </>
        )}
      </section>
    </div>
  );
}

/* ===================== */
/*   FUNÇÕES AUXILIARES  */
/* ===================== */

function formatarPeriodoBeneficio(inicio, fim) {
  const ini = inicio || "";
  const fimTxt = fim || "";
  if (!ini && !fimTxt) return "Período não informado";
  if (ini && !fimTxt) return `Início em ${ini}`;
  return `${ini} até ${fimTxt}`;
}

function rotuloSituacaoBeneficio(situacao) {
  const mapa = {
    ativo: "Ativo",
    suspenso: "Suspenso",
    encerrado: "Encerrado",
    em_analise: "Em análise",
  };
  return mapa[situacao] || situacao;
}
