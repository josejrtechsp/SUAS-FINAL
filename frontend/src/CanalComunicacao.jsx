import { useEffect, useState } from "react";
import {
  getComunicacaoTipoIcon,
  getComunicacaoTipoLabel,
} from "./domain/statuses.js";

const API_BASE = "http://localhost:8000";

/**
 * Canal de comunicação entre municípios para uma pessoa/caso Pop Rua.
 *
 * Props:
 * - pessoaId (number)          -> obrigatório
 * - casoId   (number|null)     -> opcional
 * - municipioId (number|null)  -> opcional (quem está escrevendo)
 * - municipioNome (string)     -> opcional ("Araraquara", "São Carlos", etc.)
 * - autorNomeDefault (string)  -> opcional ("Usuário do sistema", "Equipe CRAS", etc.)
 * - onMensagemEnviada (fn)     -> callback opcional após envio bem-sucedido
 */
export default function CanalComunicacao({
  pessoaId,
  casoId = null,
  municipioId = null,
  municipioNome = "",
  autorNomeDefault = "Usuário do sistema",
  onMensagemEnviada,
}) {
  const [mensagens, setMensagens] = useState([]);
  const [tipo, setTipo] = useState("registro");
  const [texto, setTexto] = useState("");
  const [carregandoLista, setCarregandoLista] = useState(false);
  const [enviando, setEnviando] = useState(false);
  const [erroLocal, setErroLocal] = useState("");

  // --------- Carregar mensagens quando muda pessoa/caso ---------
  useEffect(() => {
    async function carregarMensagens() {
      if (!pessoaId) {
        setMensagens([]);
        return;
      }

      setCarregandoLista(true);
      setErroLocal("");

      try {
        let url = `${API_BASE}/pessoas/${pessoaId}/comunicacoes`;
        const params = [];
        if (casoId) params.push(`caso_id=${casoId}`);
        if (params.length > 0) url += `?${params.join("&")}`;

        const res = await fetch(url);
        if (!res.ok) {
          throw new Error("Endpoint de comunicações não disponível.");
        }

        const data = await res.json();
        const lista = Array.isArray(data) ? data : data.itens || [];
        setMensagens(lista);
      } catch (e) {
        console.error(e);
        setErroLocal(
          "Não foi possível carregar as mensagens de comunicação. " +
            "Verifique se o endpoint /pessoas/{id}/comunicacoes já está implementado."
        );
        setMensagens([]);
      } finally {
        setCarregandoLista(false);
      }
    }

    carregarMensagens();
  }, [pessoaId, casoId]);

  // --------- Enviar nova mensagem ---------
  async function handleEnviar(e) {
    e.preventDefault();
    setErroLocal("");

    if (!pessoaId) {
      setErroLocal("Selecione uma pessoa/caso antes de enviar uma mensagem.");
      return;
    }
    if (!texto.trim()) {
      setErroLocal("Digite o conteúdo da mensagem.");
      return;
    }

    const body = {
      texto: texto.trim(),
      tipo: tipo || "registro",
      caso_id: casoId || null,
      municipio_id: municipioId,
      municipio_nome: municipioNome || null,
      autor_nome: autorNomeDefault,
    };

    try {
      setEnviando(true);

      const res = await fetch(`${API_BASE}/pessoas/${pessoaId}/comunicacoes`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });

      if (!res.ok) {
        let msg = "Erro ao enviar mensagem.";
        try {
          const errJson = await res.json();
          if (errJson.detail) msg = JSON.stringify(errJson.detail);
        } catch (_) {}
        throw new Error(msg);
      }

      const novaMensagem = await res.json();

      // Atualiza lista local
      setMensagens((lista) => [novaMensagem, ...lista]);

      setTexto("");
      setTipo("registro");

      if (onMensagemEnviada) onMensagemEnviada(novaMensagem);

      alert("Mensagem enviada com sucesso!");
    } catch (e) {
      console.error(e);
      setErroLocal(e.message);
    } finally {
      setEnviando(false);
    }
  }

  // --------- Preparar dados para exibir ---------
  const totalMensagens = mensagens.length;

  const mensagensOrdenadas = [...mensagens].sort((a, b) => {
    const ad = a.criado_em ? new Date(a.criado_em).getTime() : 0;
    const bd = b.criado_em ? new Date(b.criado_em).getTime() : 0;
    return bd - ad;
  });

  if (!pessoaId) {
    return (
      <section className="card">
        <div className="card-header-row">
          <h2>Comunicação entre municípios</h2>
        </div>
        <p className="texto-suave">
          Selecione um caso ou uma pessoa para visualizar e registrar mensagens
          de comunicação entre os municípios.
        </p>
      </section>
    );
  }

  return (
    <section className="card">
      <div className="card-header-row canal-header-row">
        <div>
          <h2>Comunicação entre municípios</h2>
          {totalMensagens > 0 && (
            <p className="canal-subtitle">
              {totalMensagens}{" "}
              {totalMensagens === 1
                ? "mensagem registrada"
                : "mensagens registradas"}
            </p>
          )}
        </div>

        <div className="canal-header-right">
          {municipioNome && (
            <span className="badge-info">Seu município: {municipioNome}</span>
          )}
        </div>
      </div>

      {erroLocal && (
        <p className="erro-global" style={{ marginBottom: 8 }}>
          {erroLocal}
        </p>
      )}

      {/* Lista de mensagens */}
      <div className="canal-mensagens">
        {carregandoLista && <p className="texto-suave">Carregando mensagens...</p>}

        {!carregandoLista && mensagensOrdenadas.length === 0 && (
          <p className="texto-suave">
            Ainda não há mensagens registradas para esta pessoa/caso. Use o
            formulário abaixo para iniciar a comunicação.
          </p>
        )}

        {!carregandoLista && mensagensOrdenadas.length > 0 && (
          <ul className="canal-mensagens-lista">
            {mensagensOrdenadas.map((m) => {
              const isLocal =
                municipioNome &&
                m.municipio_nome &&
                m.municipio_nome === municipioNome;

              return (
                <li
                  key={m.id}
                  className={
                    "canal-mensagem-item " +
                    (isLocal
                      ? "canal-mensagem-local"
                      : "canal-mensagem-externo")
                  }
                >
                  <div className="canal-mensagem-header">
                    <span className="canal-mensagem-autor">
                      {m.municipio_nome || "Município não informado"} ·{" "}
                      {m.autor_nome || "Autor não informado"}
                    </span>

                    <span className={`canal-tipo canal-tipo-${m.tipo || "registro"}`}>
                      {getComunicacaoTipoIcon(m.tipo)}{" "}
                      {getComunicacaoTipoLabel(m.tipo)}
                    </span>
                  </div>

                  <div className="canal-mensagem-texto">{m.texto}</div>

                  {m.criado_em && (
                    <div className="canal-mensagem-data">
                      {formatarDataHora(m.criado_em)}
                    </div>
                  )}
                </li>
              );
            })}
          </ul>
        )}
      </div>

      {/* Formulário para nova mensagem */}
      <form onSubmit={handleEnviar} className="canal-form">
        <div className="grid-2cols">
          <div>
            <label className="form-label">
              Tipo de mensagem
              <select
                className="input"
                value={tipo}
                onChange={(e) => setTipo(e.target.value)}
              >
                <option value="registro">Registro</option>
                <option value="alerta">Alerta</option>
                <option value="duvida">Dúvida</option>
                <option value="retorno">Retorno / resposta</option>
              </select>
            </label>
          </div>

          <div>
            <label className="form-label">
              Mensagem
              <textarea
                className="input"
                rows={3}
                placeholder="Descreva de forma objetiva o que está acontecendo entre os municípios..."
                value={texto}
                onChange={(e) => setTexto(e.target.value)}
              />
            </label>
          </div>
        </div>

        <div className="card-footer-right">
          <button type="submit" className="btn btn-primario" disabled={enviando}>
            {enviando ? "Enviando..." : "Enviar mensagem"}
          </button>
        </div>
      </form>
    </section>
  );
}

function formatarDataHora(isoString) {
  if (!isoString) return "";
  try {
    const d = new Date(isoString);
    const dia = String(d.getDate()).padStart(2, "0");
    const mes = String(d.getMonth() + 1).padStart(2, "0");
    const ano = d.getFullYear();
    const hora = String(d.getHours()).padStart(2, "0");
    const min = String(d.getMinutes()).padStart(2, "0");
    return `${dia}/${mes}/${ano} ${hora}:${min}`;
  } catch {
    return isoString;
  }
}