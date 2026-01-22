import { useEffect, useState } from "react";

const API_BASE = "http://localhost:8000";

/**
 * TelaAcolhimentosPessoa
 *
 * Mostra o histórico de acolhimentos de uma pessoa em situação de rua
 * e permite:
 * - registrar uma nova entrada em acolhimento
 * - registrar a saída do acolhimento atual (em aberto)
 *
 * Props:
 * - pessoaId (number) -> obrigatório
 * - casoId   (number) -> opcional (não usado no backend ainda, só guardado no body)
 */
export default function TelaAcolhimentosPessoa({ pessoaId, casoId = null }) {
  const [acolhimentos, setAcolhimentos] = useState([]);
  const [carregando, setCarregando] = useState(false);
  const [enviandoEntrada, setEnviandoEntrada] = useState(false);
  const [enviandoSaida, setEnviandoSaida] = useState(false);
  const [erroLocal, setErroLocal] = useState("");

  // formulário de ENTRADA
  const [tipoServico, setTipoServico] = useState("acolhimento_institucional");
  const [tipoVaga, setTipoVaga] = useState("pernoite");
  const [municipioId, setMunicipioId] = useState("");
  const [unidadeNome, setUnidadeNome] = useState("");
  const [dataEntrada, setDataEntrada] = useState("");
  const [observacoesEntrada, setObservacoesEntrada] = useState("");

  // formulário de SAÍDA (apenas para acolhimento em aberto)
  const [saidaData, setSaidaData] = useState("");
  const [saidaMotivo, setSaidaMotivo] = useState("");
  const [saidaDestino, setSaidaDestino] = useState("");
  const [saidaObs, setSaidaObs] = useState("");

  // carregar histórico
  useEffect(() => {
    async function carregar() {
      if (!pessoaId) {
        setAcolhimentos([]);
        return;
      }

      setCarregando(true);
      setErroLocal("");

      try {
        const res = await fetch(
          `${API_BASE}/pessoas/${pessoaId}/acolhimentos`
        );
        if (!res.ok) {
          throw new Error("Não foi possível carregar os acolhimentos.");
        }
        const data = await res.json();
        const lista = Array.isArray(data) ? data : [];
        // ordena por data_entrada (mais recente primeiro)
        lista.sort((a, b) => {
          const ad = a.data_entrada ? new Date(a.data_entrada).getTime() : 0;
          const bd = b.data_entrada ? new Date(b.data_entrada).getTime() : 0;
          return bd - ad;
        });
        setAcolhimentos(lista);
      } catch (e) {
        console.error(e);
        setErroLocal(e.message);
        setAcolhimentos([]);
      } finally {
        setCarregando(false);
      }
    }

    carregar();
  }, [pessoaId]);

  // acolhimento em aberto (sem data_saida)
  const acolhimentoAberto = acolhimentos.find((a) => !a.data_saida);

  async function handleSalvarEntrada(e) {
    e.preventDefault();
    setErroLocal("");

    if (!pessoaId) {
      setErroLocal("Selecione uma pessoa para registrar o acolhimento.");
      return;
    }
    if (!unidadeNome.trim()) {
      setErroLocal("Informe o nome do serviço de acolhimento.");
      return;
    }

    const body = {
      caso_id: casoId || null,
      municipio_id: municipioId ? Number(municipioId) : null,
      unidade_nome: unidadeNome || null,
      tipo_servico: tipoServico || null,
      tipo_vaga: tipoVaga || null,
      data_entrada: dataEntrada ? new Date(dataEntrada).toISOString() : null,
      data_saida: null,
      motivo_saida: null,
      destino_pos_saida: null,
      observacoes: observacoesEntrada || null,
    };

    try {
      setEnviandoEntrada(true);

      const res = await fetch(
        `${API_BASE}/pessoas/${pessoaId}/acolhimentos`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body),
        }
      );

      if (!res.ok) {
        let msg = "Erro ao salvar acolhimento.";
        try {
          const errJson = await res.json();
          if (errJson.detail) msg = JSON.stringify(errJson.detail);
        } catch (_) {}
        throw new Error(msg);
      }

      const novo = await res.json();

      setAcolhimentos((lista) => {
        const novaLista = [novo, ...lista];
        novaLista.sort((a, b) => {
          const ad = a.data_entrada ? new Date(a.data_entrada).getTime() : 0;
          const bd = b.data_entrada ? new Date(b.data_entrada).getTime() : 0;
          return bd - ad;
        });
        return novaLista;
      });

      // limpa form de entrada
      setTipoServico("acolhimento_institucional");
      setTipoVaga("pernoite");
      setMunicipioId("");
      setUnidadeNome("");
      setDataEntrada("");
      setObservacoesEntrada("");

      alert("Acolhimento registrado com sucesso!");
    } catch (e) {
      console.error(e);
      setErroLocal(e.message);
    } finally {
      setEnviandoEntrada(false);
    }
  }

  async function handleSalvarSaida(e) {
    e.preventDefault();
    setErroLocal("");

    if (!pessoaId || !acolhimentoAberto) {
      setErroLocal("Não há acolhimento em aberto para registrar saída.");
      return;
    }

    if (!saidaData) {
      setErroLocal("Informe a data da saída do acolhimento.");
      return;
    }

    const body = {
      data_saida: new Date(saidaData).toISOString(),
      motivo_saida: saídaOuNulo(saidaMotivo),
      destino_pos_saida: saídaOuNulo(saidaDestino),
      // se quiser, podemos concatenar observações
      observacoes: saídaOuNulo(saidaObs) ?? acolhimentoAberto.observacoes,
    };

    try {
      setEnviandoSaida(true);

      const res = await fetch(
        `${API_BASE}/pessoas/${pessoaId}/acolhimentos/${acolhimentoAberto.id}`,
        {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body),
        }
      );

      if (!res.ok) {
        let msg = "Erro ao salvar saída do acolhimento.";
        try {
          const errJson = await res.json();
          if (errJson.detail) msg = JSON.stringify(errJson.detail);
        } catch (_) {}
        throw new Error(msg);
      }

      const atualizado = await res.json();

      setAcolhimentos((lista) =>
        lista
          .map((a) => (a.id === atualizado.id ? atualizado : a))
          .sort((a, b) => {
            const ad = a.data_entrada
              ? new Date(a.data_entrada).getTime()
              : 0;
            const bd = b.data_entrada
              ? new Date(b.data_entrada).getTime()
              : 0;
            return bd - ad;
          })
      );

      // limpa form de saída
      setSaidaData("");
      setSaidaMotivo("");
      setSaidaDestino("");
      setSaidaObs("");

      alert("Saída do acolhimento registrada com sucesso!");
    } catch (e) {
      console.error(e);
      setErroLocal(e.message);
    } finally {
      setEnviandoSaida(false);
    }
  }

  if (!pessoaId) {
    return null;
  }

  return (
    <section className="card">
      <div className="card-header-row">
        <h2>Histórico de acolhimentos</h2>
      </div>

      {erroLocal && (
        <p className="erro-global" style={{ marginBottom: 8 }}>
          {erroLocal}
        </p>
      )}

      {carregando && (
        <p className="texto-suave">Carregando acolhimentos...</p>
      )}

      {!carregando && acolhimentos.length === 0 && (
        <p className="texto-suave">
          Ainda não há acolhimentos cadastrados para esta pessoa.
        </p>
      )}

      {!carregando && acolhimentos.length > 0 && (
        <ul className="lista-atendimentos">
          {acolhimentos.map((a) => (
            <li key={a.id} className="item-atendimento">
              <div className="item-atendimento-header">
                <div>
                  <div className="item-atendimento-titulo">
                    {a.unidade_nome || "Serviço de acolhimento"}
                  </div>
                  <div className="item-atendimento-sub">
                    {formatarIntervaloDatas(a.data_entrada, a.data_saida)} ·{" "}
                    {rotuloTipoServico(a.tipo_servico)}{" "}
                    {a.tipo_vaga && `· ${rotuloTipoVaga(a.tipo_vaga)}`}
                  </div>
                </div>
                {!a.data_saida && (
                  <span className="badge-status badge-pequena">
                    Em acolhimento
                  </span>
                )}
              </div>

              {a.motivo_saida && (
                <p className="item-atendimento-texto">
                  <strong>Motivo da saída:</strong> {a.motivo_saida}
                </p>
              )}

              {a.destino_pos_saida && (
                <p className="item-atendimento-texto">
                  <strong>Destino após saída:</strong> {a.destino_pos_saida}
                </p>
              )}

              {a.observacoes && (
                <p className="item-atendimento-texto">
                  <strong>Observações:</strong> {a.observacoes}
                </p>
              )}
            </li>
          ))}
        </ul>
      )}

      {/* Se existir acolhimento em aberto, mostra form de saída */}
      {acolhimentoAberto && (
        <form onSubmit={handleSalvarSaida} className="canal-form" style={{ marginTop: 16 }}>
          <h3 className="protocolo-step-title">
            Registrar saída do acolhimento atual
          </h3>

          <div className="grid-2cols">
            <div>
              <label className="form-label">
                Data da saída
                <input
                  type="datetime-local"
                  className="input"
                  value={saidaData}
                  onChange={(e) => setSaidaData(e.target.value)}
                />
              </label>

              <label className="form-label">
                Motivo da saída
                <select
                  className="input"
                  value={saidaMotivo}
                  onChange={(e) => setSaidaMotivo(e.target.value)}
                >
                  <option value="">Selecione...</option>
                  <option value="alta_planejada">Alta planejada</option>
                  <option value="desistencia">Desistência</option>
                  <option value="descumprimento_regras">
                    Descumprimento de regras
                  </option>
                  <option value="transferencia">Transferência</option>
                  <option value="obito">Óbito</option>
                  <option value="outro">Outro</option>
                </select>
              </label>
            </div>

            <div>
              <label className="form-label">
                Destino após saída
                <select
                  className="input"
                  value={saidaDestino}
                  onChange={(e) => setSaidaDestino(e.target.value)}
                >
                  <option value="">Selecione...</option>
                  <option value="retorno_familia">Retorno à família</option>
                  <option value="outro_servico">
                    Encaminhado para outro serviço
                  </option>
                  <option value="rua">Retorno à rua</option>
                  <option value="moradia">Moradia / aluguel social</option>
                  <option value="outro">Outro</option>
                </select>
              </label>

              <label className="form-label">
                Observações sobre a saída (opcional)
                <textarea
                  className="input"
                  rows={3}
                  value={saidaObs}
                  onChange={(e) => setSaidaObs(e.target.value)}
                  placeholder="Informações adicionais sobre a saída do acolhimento."
                />
              </label>
            </div>
          </div>

          <div className="card-footer-right">
            <button
              type="submit"
              className="btn btn-primario"
              disabled={enviandoSaida}
            >
              {enviandoSaida ? "Salvando..." : "Registrar saída"}
            </button>
          </div>
        </form>
      )}

      {/* Formulário de ENTRADA (sempre disponível) */}
      <form onSubmit={handleSalvarEntrada} className="canal-form" style={{ marginTop: 16 }}>
        <h3 className="protocolo-step-title">
          Registrar novo acolhimento
        </h3>
        <div className="grid-2cols">
          <div>
            <label className="form-label">
              Tipo de serviço de acolhimento
              <select
                className="input"
                value={tipoServico}
                onChange={(e) => setTipoServico(e.target.value)}
              >
                <option value="acolhimento_institucional">
                  Acolhimento institucional
                </option>
                <option value="casa_passagem">Casa de passagem</option>
                <option value="republica">República</option>
                <option value="outro">Outro</option>
              </select>
            </label>

            <label className="form-label">
              Tipo de vaga
              <select
                className="input"
                value={tipoVaga}
                onChange={(e) => setTipoVaga(e.target.value)}
              >
                <option value="pernoite">Pernoite</option>
                <option value="24h">24 horas</option>
                <option value="emergencia">Emergencial</option>
              </select>
            </label>

            <label className="form-label">
              Município (ID)
              <input
                className="input"
                value={municipioId}
                onChange={(e) => setMunicipioId(e.target.value)}
                placeholder="ID do município onde está o serviço"
              />
            </label>

            <label className="form-label">
              Data de entrada
              <input
                type="datetime-local"
                className="input"
                value={dataEntrada}
                onChange={(e) => setDataEntrada(e.target.value)}
              />
            </label>
          </div>

          <div>
            <label className="form-label">
              Nome do serviço de acolhimento
              <input
                className="input"
                value={unidadeNome}
                onChange={(e) => setUnidadeNome(e.target.value)}
                placeholder="Casa de Passagem X, Abrigo Y, etc."
              />
            </label>

            <label className="form-label">
              Observações sobre o acolhimento (opcional)
              <textarea
                className="input"
                rows={4}
                value={observacoesEntrada}
                onChange={(e) => setObservacoesEntrada(e.target.value)}
                placeholder="Informações adicionais sobre o acolhimento."
              />
            </label>
          </div>
        </div>

        <div className="card-footer-right">
          <button
            type="submit"
            className="btn btn-primario"
            disabled={enviandoEntrada}
          >
            {enviandoEntrada ? "Salvando..." : "Registrar acolhimento"}
          </button>
        </div>
      </form>
    </section>
  );
}

/* ===================== */
/*   FUNÇÕES AUXILIARES  */
/* ===================== */

function formatarData(isoString) {
  if (!isoString) return "";
  try {
    const d = new Date(isoString);
    const dia = String(d.getDate()).padStart(2, "0");
    const mes = String(d.getMonth() + 1).padStart(2, "0");
    const ano = d.getFullYear();
    return `${dia}/${mes}/${ano}`;
  } catch {
    return isoString;
  }
}

function formatarIntervaloDatas(entrada, saida) {
  const ini = formatarData(entrada) || "Data de entrada não informada";
  if (!saida) {
    return `${ini} · em acolhimento`;
  }
  const fim = formatarData(saida);
  return `${ini} – ${fim}`;
}

function rotuloTipoServico(tipo) {
  const mapa = {
    acolhimento_institucional: "Acolhimento institucional",
    casa_passagem: "Casa de passagem",
    republica: "República",
    outro: "Outro tipo de acolhimento",
  };
  return mapa[tipo] || "Tipo de acolhimento não informado";
}

function rotuloTipoVaga(tipo) {
  const mapa = {
    pernoite: "Pernoite",
    "24h": "24 horas",
    emergencia: "Emergencial",
  };
  return mapa[tipo] || tipo;
}

function saídaOuNulo(valor) {
  if (!valor) return null;
  if (typeof valor === "string" && valor.trim() === "") return null;
  return valor;
}