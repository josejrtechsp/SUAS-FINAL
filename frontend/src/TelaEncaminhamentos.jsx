import React, { useEffect, useMemo, useState, useRef } from "react";
import "./App.css";
import { API_BASE } from "./config";
import EncaminhamentosSuas from "./components/EncaminhamentosSuas.jsx";

function toIntIdEnc(v) {
  const n = Number(v);
  return Number.isFinite(n) ? n : null;
}

function getPessoaIdFromEnc(item) {
  return (
    toIntIdEnc(item?.pessoa_id) ??
    toIntIdEnc(item?.pessoaId) ??
    toIntIdEnc(item?.pessoa?.id) ??
    toIntIdEnc(item?.pessoa?.pessoa_id) ??
    null
  );
}

function getNomePessoaFromEnc(item, pessoas = []) {
  // 1) se o backend já mandar nome direto
  const direto =
    item?.pessoa_nome ||
    item?.pessoaNome ||
    item?.nome_pessoa ||
    item?.nomePessoa ||
    item?.pessoa?.nome_social ||
    item?.pessoa?.nome_civil ||
    null;

  if (direto && String(direto).trim()) {
const s = String(direto).trim();
const up = s.toUpperCase();
if (up !== "EDITADO AGORA" && up !== "EDITAR AGORA") return s; // evita placeholder
  }

  // 2) resolve via pessoa_id usando a lista de pessoas carregada no app
  const pid = getPessoaIdFromEnc(item);
  if (pid && Array.isArray(pessoas)) {
    const p = pessoas.find((x) => Number(x?.id) === Number(pid)) || null;
    const nome = p?.nome_social || p?.nome_civil || null;
    if (nome) return String(nome).trim();
    return `Pessoa #${pid}`;
  }

  return "Pessoa";
}

function iniciaisPessoa(nome) {
  const n = (nome || "").trim();
  return n ? n.charAt(0).toUpperCase() : "P";
}

function formatarDataHoraEnc(isoString) {
  if (!isoString) return "—";
  try {
    const d = new Date(isoString);
    if (isNaN(d.getTime())) return String(isoString);
    const dia = String(d.getDate()).padStart(2, "0");
    const mes = String(d.getMonth() + 1).padStart(2, "0");
    const ano = d.getFullYear();
    const hora = String(d.getHours()).padStart(2, "0");
    const min = String(d.getMinutes()).padStart(2, "0");
    return `${dia}/${mes}/${ano} ${hora}:${min}`;
  } catch {
    return String(isoString);
  }
}

function formatarDataHora(isoString) {
  if (!isoString) return "—";
  try {
    const d = new Date(isoString);
    if (isNaN(d.getTime())) return isoString;
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

function labelStatusCurto(s) {
  const mapa = {
    solicitado: "Solicitação",
    contato: "Contato",
    aceito: "Aceite",
    agendado: "Agendado",
    passagem: "Passagem",
    contrarreferencia: "Contrarreferência",
    concluido: "Concluído",
    cancelado: "Cancelado",
  };
  return mapa[s] || (s ? String(s).replace(/_/g, " ") : "—");
}

function sideDoPasso(statusKey) {
  const mapa = {
    solicitado: "ORIGEM",
    contato: "ORIGEM",
    aceito: "DESTINO",
    agendado: "DESTINO",
    passagem: "ORIGEM",
    contrarreferencia: "DESTINO",
    concluido: "ORIGEM",
  };
  return mapa[statusKey] || "—";
}

function nextStatusFrom(current) {
  const ordem = [
    "solicitado",
    "contato",
    "aceito",
    "agendado",
    "passagem",
    "contrarreferencia",
    "concluido",
  ];
  const idx = ordem.indexOf(current);
  if (idx < 0) return "contato";
  if (idx >= ordem.length - 1) return null;
  return ordem[idx + 1];
}

function stepIndex(status) {
  const ordem = [
    "solicitado",
    "contato",
    "aceito",
    "agendado",
    "passagem",
    "contrarreferencia",
    "concluido",
  ];
  const idx = ordem.indexOf(status);
  return idx < 0 ? 0 : idx;
}

export default function TelaEncaminhamentos({
  apiBase = API_BASE,
  apiFetch,
  usuarioLogado,
  municipios = [],
  pessoas = [],
  municipioAtivoId,
  municipioAtivoNome,
  onNovoEncaminhamento,
}) {
  const [busca, setBusca] = useState("");
  const [statusFiltro, setStatusFiltro] = useState("todos");

  const [itens, setItens] = useState([]);
  const [loading, setLoading] = useState(false);
  const [erro, setErro] = useState("");

  // selecionado
  const [selecionadoId, setSelecionadoId] = useState(null);
  const [detalhe, setDetalhe] = useState(null);
  const [loadingDetalhe, setLoadingDetalhe] = useState(false);

  // linha do metrô (detalhe por etapa)
  const [openCodigo, setOpenCodigo] = useState(null);
  const acoesRef = useRef(null);

  // dossiê + evidências (intermunicipal)
  const [dossie, setDossie] = useState(null);
  const [anexos, setAnexos] = useState([]);
  const [loadingDossie, setLoadingDossie] = useState(false);

  // admin/consórcio pode “atuar como”
  const [atuandoComo, setAtuandoComo] = useState("AUTO"); // AUTO | ORIGEM | DESTINO

  // campos de ação guiada
  const [textoEtapa, setTextoEtapa] = useState("");

  // contato (origem)
  const [contatoCanal, setContatoCanal] = useState("E-mail institucional");
  const [contatoPara, setContatoPara] = useState("");

  // agendamento (destino)
  const [agDataHora, setAgDataHora] = useState("");
  const [agLocal, setAgLocal] = useState("");

  // passagem (origem)
  const [pasNumero, setPasNumero] = useState("");
  const [pasEmpresa, setPasEmpresa] = useState("");
  const [pasDataViagem, setPasDataViagem] = useState("");
  const [kitLanche, setKitLanche] = useState(false);
  const [kitHigiene, setKitHigiene] = useState(false);
  const [kitMapa, setKitMapa] = useState(false);

  async function fetchComAuth(url, options = {}) {
    if (typeof apiFetch === "function") return apiFetch(url, options);

    const token =
      localStorage.getItem("poprua_token") ||
      localStorage.getItem("access_token") ||
      "";

    return fetch(url, {
      ...options,
      headers: {
        ...(options.headers || {}),
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
    });
  }

  const mapaMunicipios = useMemo(() => {
    const m = new Map();
    (municipios || []).forEach((x) => {
      const id = Number(x?.id);
      if (!isNaN(id)) m.set(id, x?.nome || x?.nome_municipio || "Município");
    });
    return m;
  }, [municipios]);

  const mapaPessoas = useMemo(() => {
    const m = new Map();
    (pessoas || []).forEach((p) => {
      m.set(Number(p.id), p.nome_social || p.nome_civil || "Pessoa");
    });
    return m;
  }, [pessoas]);

  const pessoasOptionsSuas = useMemo(() => {
    return (pessoas || [])
      .map((p) => ({
        id: Number(p?.id),
        nome: p?.nome_social || p?.nome_civil || p?.nome || `Pessoa #${p?.id}`,
      }))
      .filter((x) => x.id && !Number.isNaN(x.id));
  }, [pessoas]);

  function nomeMunicipio(id) {
    if (id == null) return "Município";
    return mapaMunicipios.get(Number(id)) || "Município";
  }

  function nomePessoa(id) {
    if (id == null) return "Pessoa";
    return mapaPessoas.get(Number(id)) || "Pessoa";
  }

  function limparCampos() {
    setTextoEtapa("");
    setContatoCanal("E-mail institucional");
    setContatoPara("");
    setAgDataHora("");
    setAgLocal("");
    setPasNumero("");
    setPasEmpresa("");
    setPasDataViagem("");
    setKitLanche(false);
    setKitHigiene(false);
    setKitMapa(false);
  }

  // Encaminhamentos SUAS (internos): ao RECEBER, podemos criar um caso PopRua automaticamente.
  async function createPopRuaCaseFromSuasEncaminhamento(item) {
    try {
      const pid = Number(item?.pessoa_id);
      if (!pid || Number.isNaN(pid)) return null;
      if (!municipioAtivoId) {
        alert('Selecione o Município ativo no topo antes de receber.');
        return null;
      }

      const obs = `(Encaminhamento SUAS) Origem: ${String(item?.origem_modulo || '-')} · Motivo: ${String(item?.motivo || '-')}`;
      const body = {
        pessoa_id: pid,
        municipio_id: Number(municipioAtivoId),
        observacoes_iniciais: obs,
        observacoes_gerais: null,
      };

      const res = await fetchComAuth(`${apiBase}/casos/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });

      if (!res.ok) {
        const txt = await res.text().catch(() => '');
        throw new Error(txt || `Erro ao criar caso PopRua (${res.status})`);
      }

      const data = await res.json().catch(() => ({}));
      const novoId = toIntIdEnc(data?.id ?? data?.caso_id ?? data?.casoId);
      if (!novoId) return null;
      return novoId;
    } catch (e) {
      console.error(e);
      alert(e?.message || 'Não foi possível criar o caso automaticamente.');
      return null;
    }
  }

  function orientarAbrirCasoPopRua(item) {
    if (!item?.destino_caso_id) return;
    const caseId = Number(item.destino_caso_id);
    const pessoaId = Number(item?.pessoa_id);

    // ✅ 1 clique: abre o caso direto no HUB Atendimento → Casos
    try {
      window.dispatchEvent(
        new CustomEvent('poprua_open_caso', {
          detail: {
            caseId: Number.isFinite(caseId) ? caseId : null,
            pessoaId: Number.isFinite(pessoaId) ? pessoaId : null,
          },
        })
      );
      return;
    } catch (e) {
      console.error(e);
    }

    // Fallback (se o CustomEvent falhar)
    alert(`Caso PopRua #${item.destino_caso_id} pronto. Vá em Atendimento → Casos e selecione o caso.`);
  }

  async function carregar() {
    setErro("");
    setLoading(true);
    try {
      const qs = [];
      if (statusFiltro !== "todos") {
        qs.push(`status_filtro=${encodeURIComponent(statusFiltro)}`);
      }
      const url =
        qs.length > 0
          ? `${apiBase}/encaminhamentos/?${qs.join("&")}`
          : `${apiBase}/encaminhamentos/`;

      const res = await fetchComAuth(url);
      if (!res.ok) {
        const txt = await res.text().catch(() => "");
        throw new Error(`Falha ao carregar (HTTP ${res.status}). ${txt}`);
      }

      const data = await res.json();
      const arr = Array.isArray(data) ? data : [];
      setItens(arr);

      if (arr.length > 0) {
        setSelecionadoId((prev) => prev ?? arr[0].id);
      } else {
        setSelecionadoId(null);
        setDetalhe(null);
      }
    } catch (e) {
      setErro(e.message || "Erro ao carregar encaminhamentos.");
      setItens([]);
      setSelecionadoId(null);
      setDetalhe(null);
    } finally {
      setLoading(false);
    }
  }

  async function carregarDetalhe(id) {
    if (!id) return;
    setErro("");
    setLoadingDetalhe(true);
    try {
      const res = await fetchComAuth(`${apiBase}/encaminhamentos/${id}`);
      if (!res.ok) {
        const txt = await res.text().catch(() => "");
        throw new Error(`Falha ao abrir detalhe (HTTP ${res.status}). ${txt}`);
      }
      const data = await res.json();
      setDetalhe(data);
    } catch (e) {
      setErro(e.message || "Erro ao carregar detalhe.");
      setDetalhe(null);
    } finally {
      setLoadingDetalhe(false);
    }
  }

async function carregarDossie(encId) {
  if (!encId) return;
  setLoadingDossie(true);
  try {
    // dossiê LGPD-safe (origem/destino)
    const res = await fetchComAuth(`${apiBase}/encaminhamentos/intermunicipal/${encId}/dossie`);
    if (res.ok) {
      const data = await res.json().catch(() => null);
      setDossie(data);
    } else {
      setDossie(null);
    }

    // anexos/evidências (se existir)
    const ra = await fetchComAuth(`${apiBase}/encaminhamentos/intermunicipal/${encId}/anexos`);
    if (ra.ok) {
      const a = await ra.json().catch(() => []);
      const arr = Array.isArray(a) ? a : Array.isArray(a?.items) ? a.items : [];
      setAnexos(arr);
    } else {
      setAnexos([]);
    }
  } catch (e) {
    console.error(e);
    setDossie(null);
    setAnexos([]);
  } finally {
    setLoadingDossie(false);
  }
}

  useEffect(() => {
    carregar();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    carregar();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [statusFiltro]);

  useEffect(() => {
    if (selecionadoId != null) {
      limparCampos();
      carregarDetalhe(selecionadoId);
      carregarDossie(selecionadoId);
    } else {
      setDossie(null);
      setAnexos([]);
    }
    setOpenCodigo(null);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selecionadoId]);

  const filtrados = useMemo(() => {
    const q = (busca || "").trim().toLowerCase();
    if (!q) return itens;

    return (itens || []).filter((x) => {
      const pessoaNome = nomePessoa(x.pessoa_id);
      const origemNome = nomeMunicipio(x.municipio_origem_id);
      const destinoNome = nomeMunicipio(x.municipio_destino_id);
      const texto = `${pessoaNome} ${origemNome} ${destinoNome} ${x.motivo || ""} ${x.status || ""}`.toLowerCase();
      return texto.includes(q);
    });
  }, [itens, busca]);

  const selecionadoResumo = useMemo(() => {
    if (!selecionadoId) return null;
    return (itens || []).find((x) => x.id === selecionadoId) || null;
  }, [itens, selecionadoId]);

  const perfil = (usuarioLogado?.perfil || "").toLowerCase();
  const isAdminConsorcio = perfil === "admin" || perfil === "gestor_consorcio";

  const statusAtual = detalhe?.status || selecionadoResumo?.status || "solicitado";
  const isFinal = statusAtual === "concluido" || statusAtual === "cancelado";
  const proximoStatus = isFinal ? null : nextStatusFrom(statusAtual);

const destinoCasoId =
  detalhe?.destino_caso_id ??
  dossie?.destino_caso_id ??
  selecionadoResumo?.destino_caso_id ??
  null;

const linksDocs = useMemo(() => {
  const abs = (u) => {
    if (!u) return null;
    const s = String(u);
    if (s.startsWith("http://") || s.startsWith("https://")) return s;
    if (s.startsWith("/")) return `${apiBase}${s}`;
    return s;
  };

  const temContra =
    Boolean(detalhe?.contrarreferencia_em) ||
    Boolean(dossie?.contrarreferencia) ||
    Boolean(dossie?.contrarreferencia_pdf) ||
    (stepIndex(statusAtual) >= stepIndex("contrarreferencia") && statusAtual !== "cancelado");

  const temRec =
    Boolean(dossie?.recebimento) ||
    Boolean(dossie?.recebimento_pdf) ||
    (stepIndex(statusAtual) >= stepIndex("concluido") && statusAtual !== "cancelado");

  const contraUrl =
    dossie?.contrarreferencia_pdf ||
    dossie?.contrarreferencia?.download_pdf ||
    (temContra && selecionadoId
      ? `${apiBase}/encaminhamentos/intermunicipal/${selecionadoId}/contrarreferencia/pdf`
      : null);

  const recebUrl =
    dossie?.recebimento_pdf ||
    dossie?.recebimento?.download_pdf ||
    (temRec && selecionadoId
      ? `${apiBase}/encaminhamentos/intermunicipal/${selecionadoId}/recebimento/pdf`
      : null);

  return {
    contrarreferencia_pdf: abs(contraUrl),
    recebimento_pdf: abs(recebUrl),
  };
}, [apiBase, detalhe, dossie, selecionadoId, statusAtual]);

function abrirCasoDestino() {
  if (!destinoCasoId) return;
  orientarAbrirCasoPopRua({
    destino_caso_id: destinoCasoId,
    pessoa_id: detalhe?.pessoa_id ?? selecionadoResumo?.pessoa_id ?? null,
  });
}

  const papelMunicipal = useMemo(() => {
    const myMuni = municipioAtivoId != null ? Number(municipioAtivoId) : null;
    const orig = detalhe?.municipio_origem_id ?? selecionadoResumo?.municipio_origem_id ?? null;
    const dest = detalhe?.municipio_destino_id ?? selecionadoResumo?.municipio_destino_id ?? null;

    if (!myMuni) return null;
    if (orig != null && Number(orig) === myMuni) return "ORIGEM";
    if (dest != null && Number(dest) === myMuni) return "DESTINO";
    return "FORA";
  }, [municipioAtivoId, detalhe, selecionadoResumo]);

  const papelAtuando = useMemo(() => {
    if (isAdminConsorcio) {
      if (atuandoComo === "ORIGEM" || atuandoComo === "DESTINO") return atuandoComo;
      if (!proximoStatus) return "—";
      return sideDoPasso(proximoStatus);
    }
    return papelMunicipal || "—";
  }, [isAdminConsorcio, atuandoComo, papelMunicipal, proximoStatus]);

  const podeExecutar = useMemo(() => {
    if (!proximoStatus) return false;
    const ladoNecessario = sideDoPasso(proximoStatus);
    if (isAdminConsorcio) return true;
    return papelAtuando === ladoNecessario;
  }, [proximoStatus, isAdminConsorcio, papelAtuando]);

  // --- fluxo (linha do metrô) usando EXACT as classes do App.css ---
  const steps = useMemo(
    () => [
      { codigo: "solicitado", ordem: 1, nome: "Solicitação", descricao: "Origem registra a solicitação (com consentimento).", lado: "ORIGEM" },
      { codigo: "contato", ordem: 2, nome: "Contato formal", descricao: "Origem contata o destino formalmente (canal + mensagem).", lado: "ORIGEM" },
      { codigo: "aceito", ordem: 3, nome: "Aceite", descricao: "Destino confirma que aceita receber a pessoa.", lado: "DESTINO" },
      { codigo: "agendado", ordem: 4, nome: "Agendamento", descricao: "Destino informa data/hora/local de recepção.", lado: "DESTINO" },
      { codigo: "passagem", ordem: 5, nome: "Passagem", descricao: "Origem registra benefício eventual (se houver) + kits.", lado: "ORIGEM" },
      { codigo: "contrarreferencia", ordem: 6, nome: "Contrarreferência", descricao: "Destino confirma recepção e próximos passos.", lado: "DESTINO" },
      { codigo: "concluido", ordem: 7, nome: "Conclusão", descricao: "Origem encerra o encaminhamento (saída qualificada).", lado: "ORIGEM" },
    ],
    []
  );

  function etapaStatusParaUI(stepIdx) {
    const idxAtual = stepIndex(statusAtual);
    if (statusAtual === "cancelado") return "nao_iniciada";
    if (statusAtual === "concluido") return "concluida";
    if (stepIdx < idxAtual) return "concluida";
    if (stepIdx === idxAtual) return "em_andamento";
    return "nao_iniciada";
  }

  async function postarStatus(novoStatus, detalheTxt) {
    if (!selecionadoId) return;

    setErro("");
    try {
      const res = await fetchComAuth(`${apiBase}/encaminhamentos/${selecionadoId}/status`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: novoStatus, detalhe: detalheTxt || "" }),
      });

      if (!res.ok) {
        const txt = await res.text().catch(() => "");
        throw new Error(`Falha ao registrar etapa (HTTP ${res.status}). ${txt}`);
      }

      const atualizado = await res.json();
      setDetalhe(atualizado);
      setItens((prev) =>
        prev.map((x) => (x.id === atualizado.id ? { ...x, status: atualizado.status } : x))
      );
      limparCampos();
    } catch (e) {
      setErro(e.message || "Erro ao registrar etapa.");
    }
  }

  async function postarPassagem() {
    if (!selecionadoId) return;

    if (!textoEtapa.trim() && !pasNumero.trim() && !pasEmpresa.trim() && !pasDataViagem) {
      setErro("Registre pelo menos um texto explicando a passagem (obrigatório) ou preencha os dados.");
      return;
    }

    setErro("");
    try {
      const body = {
        passagem_numero: pasNumero.trim() || null,
        passagem_empresa: pasEmpresa.trim() || null,
        passagem_data_viagem: pasDataViagem ? new Date(pasDataViagem).toISOString() : null,
        kit_lanche: kitLanche,
        kit_higiene: kitHigiene,
        kit_mapa_info: kitMapa,
        justificativa_passagem: textoEtapa.trim() || null,
      };

      const res = await fetchComAuth(`${apiBase}/encaminhamentos/${selecionadoId}/passagem`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });

      if (!res.ok) {
        const txt = await res.text().catch(() => "");
        throw new Error(`Falha ao registrar passagem (HTTP ${res.status}). ${txt}`);
      }

      const atualizado = await res.json();
      setDetalhe(atualizado);
      setItens((prev) =>
        prev.map((x) => (x.id === atualizado.id ? { ...x, status: atualizado.status } : x))
      );
      limparCampos();
    } catch (e) {
      setErro(e.message || "Erro ao registrar passagem.");
    }
  }

  function renderAcoesGuiadas() {
    if (!selecionadoResumo) {
      return (
        <div className="card">
          <div className="card-header-row">
            <h3 style={{ margin: 0 }}>Ações guiadas</h3>
          </div>
          <p className="texto-suave">Selecione um encaminhamento na fila.</p>
        </div>
      );
    }

    const pessoaNome = nomePessoa(selecionadoResumo.pessoa_id);
    const origemNome = nomeMunicipio(selecionadoResumo.municipio_origem_id);
    const destinoNome = nomeMunicipio(selecionadoResumo.municipio_destino_id);

    if (!proximoStatus) {
      return (
        <div className="card">
          <div className="card-header-row">
            <h3 style={{ margin: 0 }}>Ações guiadas</h3>
          </div>
          <p className="texto-suave">Nenhum passo disponível (fluxo finalizado).</p>
        </div>
      );
    }

    const ladoNecessario = sideDoPasso(proximoStatus);

    const tituloAcao = {
      contato: "Registrar contato formal com o destino (ORIGEM)",
      aceito: "Registrar aceite do destino (DESTINO)",
      agendado: "Registrar agendamento de recepção (DESTINO)",
      passagem: "Registrar passagem (ORIGEM) + kits",
      contrarreferencia: "Registrar contrarreferência (DESTINO)",
      concluido: "Concluir encaminhamento (ORIGEM)",
    }[proximoStatus];

    const placeholder = {
      contato: `Ex.: "Entramos em contato com ${destinoNome} por e-mail institucional solicitando aceite e ponto de recepção."`,
      aceito: `Ex.: "O município ${destinoNome} aceita receber ${pessoaNome}. Serviço de referência: Centro POP/CREAS. Vaga confirmada."`,
      agendado: `Ex.: "Recepção agendada em ${destinoNome}. Local: Rodoviária/Centro POP. Data/hora: ... Observações: ..."`,
      contrarreferencia: `Ex.: "${pessoaNome} foi recebido em ${destinoNome}, acolhimento realizado, próximos passos acordados."`,
      concluido: `Ex.: "Fluxo encerrado após contrarreferência. Saída qualificada registrada."`,
      passagem: `Ex.: "Passagem concedida após aceite formal. Benefício eventual conforme norma municipal. Kits registrados."`,
    }[proximoStatus];

    return (
      <div className="card">
        <div className="card-header-row">
          <div>
            <h3 style={{ margin: 0 }}>Ações guiadas</h3>
            <p className="card-subtitle" style={{ marginTop: 6 }}>
              Próximo passo: <strong>{labelStatusCurto(proximoStatus)}</strong> · Quem registra:{" "}
              <strong>{ladoNecessario}</strong>
            </p>
            <p className="texto-suave" style={{ marginTop: 6 }}>
              Pessoa: <strong>{pessoaNome}</strong> · Origem: <strong>{origemNome}</strong> · Destino:{" "}
              <strong>{destinoNome}</strong>
            </p>
          </div>

          {isAdminConsorcio && (
            <div style={{ minWidth: 240 }}>
              <label className="form-label" style={{ marginBottom: 4 }}>
                Admin/Consórcio (atuar como)
              </label>
              <select className="input" value={atuandoComo} onChange={(e) => setAtuandoComo(e.target.value)}>
                <option value="AUTO">AUTO (segue o próximo passo)</option>
                <option value="ORIGEM">ORIGEM</option>
                <option value="DESTINO">DESTINO</option>
              </select>
            </div>
          )}
        </div>

        {!podeExecutar && (
          <p className="erro-global" style={{ marginTop: 10 }}>
            Ação bloqueada: esta etapa deve ser registrada pelo <strong>{ladoNecessario}</strong>.
          </p>
        )}

        {/* Campos específicos por etapa */}
        {proximoStatus === "contato" && (
          <div className="grid-2cols" style={{ marginTop: 10 }}>
            <label className="form-label">
              Canal
              <select className="input" value={contatoCanal} onChange={(e) => setContatoCanal(e.target.value)}>
                <option>E-mail institucional</option>
                <option>Telefone</option>
                <option>Plataforma do consórcio</option>
                <option>Outro</option>
              </select>
            </label>

            <label className="form-label">
              Para (nome/setor/e-mail)
              <input className="input" value={contatoPara} onChange={(e) => setContatoPara(e.target.value)} />
            </label>
          </div>
        )}

        {proximoStatus === "agendado" && (
          <div className="grid-2cols" style={{ marginTop: 10 }}>
            <label className="form-label">
              Data e hora (recepção)
              <input type="datetime-local" className="input" value={agDataHora} onChange={(e) => setAgDataHora(e.target.value)} />
            </label>

            <label className="form-label">
              Local / ponto de recepção
              <input className="input" value={agLocal} onChange={(e) => setAgLocal(e.target.value)} />
            </label>
          </div>
        )}

        {proximoStatus === "passagem" && (
          <div style={{ marginTop: 10 }}>
            <div className="grid-2cols">
              <label className="form-label">
                Número da passagem (opcional)
                <input className="input" value={pasNumero} onChange={(e) => setPasNumero(e.target.value)} />
              </label>
              <label className="form-label">
                Empresa (opcional)
                <input className="input" value={pasEmpresa} onChange={(e) => setPasEmpresa(e.target.value)} />
              </label>
            </div>

            <label className="form-label" style={{ marginTop: 10 }}>
              Data/hora da viagem (opcional)
              <input type="datetime-local" className="input" value={pasDataViagem} onChange={(e) => setPasDataViagem(e.target.value)} />
            </label>

            <div style={{ marginTop: 10, display: "flex", gap: 16, flexWrap: "wrap" }}>
              <label style={{ display: "flex", gap: 8, alignItems: "center", fontSize: 12, color: "#374151" }}>
                <input type="checkbox" checked={kitLanche} onChange={(e) => setKitLanche(e.target.checked)} />
                Kit lanche
              </label>
              <label style={{ display: "flex", gap: 8, alignItems: "center", fontSize: 12, color: "#374151" }}>
                <input type="checkbox" checked={kitHigiene} onChange={(e) => setKitHigiene(e.target.checked)} />
                Kit higiene
              </label>
              <label style={{ display: "flex", gap: 8, alignItems: "center", fontSize: 12, color: "#374151" }}>
                <input type="checkbox" checked={kitMapa} onChange={(e) => setKitMapa(e.target.checked)} />
                Kit mapa/info
              </label>
            </div>
          </div>
        )}

        <label className="form-label" style={{ marginTop: 12 }}>
          Mensagem/registro da etapa (obrigatório)
          <textarea
            className="input"
            rows={4}
            value={textoEtapa}
            onChange={(e) => setTextoEtapa(e.target.value)}
            placeholder={placeholder}
          />
        </label>

        <div className="card-footer-right">
          <button
            type="button"
            className="btn btn-primario"
            disabled={!podeExecutar || loadingDetalhe}
            onClick={() => {
              if (!podeExecutar) return;

              if (!textoEtapa.trim()) {
                setErro("Escreva o registro da etapa (obrigatório).");
                return;
              }

              if (proximoStatus === "contato") {
                const detalheTxt = `Canal: ${contatoCanal}. Para: ${contatoPara || "—"}. Mensagem: ${textoEtapa.trim()}`;
                postarStatus("contato", detalheTxt);
                return;
              }

              if (proximoStatus === "agendado") {
                const dh = agDataHora ? new Date(agDataHora).toISOString() : "—";
                const loc = agLocal || "—";
                const detalheTxt = `Agendamento em ${destinoNome}. Data/hora: ${dh}. Local: ${loc}. Registro: ${textoEtapa.trim()}`;
                postarStatus("agendado", detalheTxt);
                return;
              }

              if (proximoStatus === "passagem") {
                postarPassagem();
                return;
              }

              postarStatus(proximoStatus, textoEtapa.trim());
            }}
          >
            Registrar: {tituloAcao}
          </button>

          <button type="button" className="btn btn-secundario" onClick={limparCampos} disabled={loadingDetalhe}>
            Limpar
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="layout-1col">
      <EncaminhamentosSuas
        modulo="POPRUA"
        usuarioLogado={usuarioLogado}
        allowCreate={true}
        pessoasOptions={pessoasOptionsSuas}
        onAcceptCreateCaso={(item) => createPopRuaCaseFromSuasEncaminhamento(item)}
        onOpenDestinoCaso={(item) => orientarAbrirCasoPopRua(item)}
        title="Encaminhamentos SUAS"
        subtitle="CRAS ⇄ CREAS ⇄ PopRua, com recebimento e contrarreferência."
      />

      <section className="card card-wide">
        <div className="card-header-row">
          <div>
            <h2 style={{ margin: 0 }}>Encaminhamentos</h2>
            <p className="card-subtitle" style={{ marginTop: 6 }}>
              Fluxo intermunicipal com rastreabilidade e etapas dependentes (tipo “linha do metrô”).
            </p>
            <p className="texto-suave" style={{ marginTop: 6 }}>
              Município ativo: <strong>{municipioAtivoNome || "—"}</strong>
              {usuarioLogado?.nome ? (
                <>
                  {" "}
                  · Usuário: <strong>{usuarioLogado.nome}</strong>
                </>
              ) : null}
            </p>
          </div>

          <div style={{ display: "flex", gap: 8 }}>
            <button type="button" className="btn btn-secundario" onClick={carregar} disabled={loading}>
              {loading ? "Carregando..." : "Recarregar"}
            </button>

            <button type="button" className="btn btn-primario" onClick={() => onNovoEncaminhamento?.()}>
              Novo encaminhamento
            </button>
          </div>
        </div>

        {erro && <p className="erro-global">{erro}</p>}

        <div className="grid-2cols" style={{ marginTop: 10 }}>
          <label className="form-label">
            Buscar
            <input
              className="input"
              value={busca}
              onChange={(e) => setBusca(e.target.value)}
              placeholder="Pessoa, município, motivo..."
            />
          </label>

          <label className="form-label">
            Status
            <select className="input" value={statusFiltro} onChange={(e) => setStatusFiltro(e.target.value)}>
              <option value="todos">Todos</option>
              <option value="solicitado">Solicitação</option>
              <option value="contato">Contato</option>
              <option value="aceito">Aceite</option>
              <option value="agendado">Agendamento</option>
              <option value="passagem">Passagem</option>
              <option value="contrarreferencia">Contrarreferência</option>
              <option value="concluido">Concluído</option>
              <option value="cancelado">Cancelado</option>
            </select>
            <div className="texto-suave" style={{ marginTop: 8 }}>
              O filtro recarrega automaticamente.
            </div>
          </label>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "minmax(280px, 420px) minmax(0, 1fr)", gap: 16, marginTop: 14 }}>
          {/* FILA */}
          <div className="card">
            <div className="card-header-row">
              <h3 style={{ margin: 0 }}>Fila</h3>
              <span className="badge-info badge-pequena">{filtrados.length} registro(s)</span>
            </div>

            {filtrados.length === 0 ? (
              <p className="texto-suave">Nenhum encaminhamento encontrado.</p>
            ) : (
              <ul className="lista-casos">
                {filtrados.map((x) => {
                  return (
                    <li
  key={x.id}
  className={"item-caso enc-fila-item" + (x.id === selecionadoId ? " item-caso-ativo" : "")}
  onClick={() => setSelecionadoId(x.id)}
>
  <div className="enc-fila-row">
    <div className="enc-avatar enc-avatar-sm" aria-hidden="true">
      <span style={{ fontSize: 12, lineHeight: 1 }}>
        {(nomePessoa(x.pessoa_id) || "P").trim().charAt(0).toUpperCase()}
      </span>
    </div>

    <div style={{ minWidth: 0 }}>
      <div className="item-caso-nome">{nomePessoa(x.pessoa_id)}</div>
      <div className="item-caso-sub">Destino: {nomeMunicipio(x.municipio_destino_id)}</div>
    </div>
  </div>

  <span className="badge-status">{labelStatusCurto(x.status)}</span>
</li>
                  );
                })}
              </ul>
            )}
          </div>

          {/* DETALHE */}
          <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
            {/* RESUMO (padrão do site) */}
<ResumoEncaminhamento item={detalhe || selecionadoResumo} municipios={municipios} pessoas={pessoas} destinoCasoId={destinoCasoId} onOpenDestinoCaso={abrirCasoDestino} docs={linksDocs} loadingDossie={loadingDossie} anexosCount={(Array.isArray(anexos) ? anexos.length : 0)} />{/* FLUXO (linha do metrô) — padrão do sistema (clicável + dados reais) */}
<div className="card">
  <h3 style={{ marginTop: 0 }}>Fluxo (linha do metrô)</h3>
  <p className="texto-suave" style={{ marginTop: 6 }}>
    Clique em uma etapa para ver o último registro, evidências e histórico. Só libera o próximo passo, conforme ORIGEM/DESTINO.
  </p>

  {(() => {
    const eventos = Array.isArray(detalhe?.eventos) ? detalhe.eventos : [];
    const lower = (v) => String(v || "").toLowerCase();

    function marcoEm(cod) {
      if (!detalhe) return null;
      if (cod === "contato") return detalhe.contato_em;
      if (cod === "aceito") return detalhe.aceite_em;
      if (cod === "agendado") return detalhe.agendado_em;
      if (cod === "passagem") return detalhe.passagem_em;
      if (cod === "contrarreferencia") return detalhe.contrarreferencia_em;
      if (cod === "concluido") return detalhe.concluido_em;
      if (cod === "cancelado") return detalhe.cancelado_em;
      if (cod === "solicitado") return detalhe.criado_em;
      return null;
    }

    function ultimoRegistro(cod) {
      const ev = eventos.find((e) => lower(e?.tipo) === lower(cod)) || null;
      const dt = ev?.em || marcoEm(cod) || null;

      let obs = ev?.detalhe || null;


      const extras = [];
      const rawDetail = String(ev?.detalhe || "");

      if (cod === "contato") {
        const mCanal = rawDetail.match(/Canal:\s*([^\.\n]+)/i);
        const mPara = rawDetail.match(/Para:\s*([^\.\n]+)/i);
        if (mCanal) extras.push({ label: "Canal", value: (mCanal[1] || "").trim() });
        if (mPara) extras.push({ label: "Para", value: (mPara[1] || "").trim() });
      }

      if (cod === "agendado") {
        const mLocal = rawDetail.match(/Local:\s*([^\.\n]+)/i);
        if (mLocal) extras.push({ label: "Local", value: (mLocal[1] || "").trim() });
      }

      // Enriquecimentos (quando existirem campos estruturados no backend)
      if (cod === "passagem" && detalhe) {
        const parts = [];
        if (detalhe.passagem_numero) parts.push(`Passagem: ${detalhe.passagem_numero}`);
        if (detalhe.passagem_empresa) parts.push(`Empresa: ${detalhe.passagem_empresa}`);
        if (detalhe.passagem_data_viagem) parts.push(`Viagem: ${formatarDataHora(detalhe.passagem_data_viagem)}`);
        const kits = [];
        if (detalhe.kit_lanche) kits.push("lanche");
        if (detalhe.kit_higiene) kits.push("higiene");
        if (detalhe.kit_mapa_info) kits.push("mapa/info");
        if (kits.length) parts.push(`Kits: ${kits.join(", ")}`);
        if (detalhe.justificativa_passagem) parts.push(`Obs: ${detalhe.justificativa_passagem}`);
        if (parts.length) obs = (obs ? `${obs}
` : "") + parts.join(" · ");
      }

      return {
        responsavel_nome: ev?.por_nome || "—",
        data_hora: dt,
        obs: obs,
        extras: extras,
      };
    }

    function historicoEtapa(cod) {
      const arr = eventos.filter((e) => lower(e?.tipo) === lower(cod));
      return arr.slice(0, 8).map((e) => ({
        id: e?.id,
        responsavel_nome: e?.por_nome || "—",
        data_hora: e?.em || null,
        obs: e?.detalhe || null,
      }));
    }

    function label(st) {
      if (st === "concluida") return "Concluída";
      if (st === "em_andamento") return "Em andamento";
      return "Não iniciada";
    }

    const nextKey = (proximoStatus || "").toLowerCase();

    return (
      <div className="linha-metro metro-elegante metro-premium" style={{ marginTop: 10 }}>
        {steps.map((s, i) => {
          const codigo = (s.codigo || "").toLowerCase();
          const st = etapaStatusParaUI(i);
          const aberto = openCodigo === codigo;

          const ur = ultimoRegistro(codigo);
          const regs = historicoEtapa(codigo);

          const isNext = nextKey && codigo === nextKey;
          const ladoNec = sideDoPasso(nextKey);
          const podeAqui = isNext && podeExecutar;

          return (
            <div key={codigo} className={`etapa-linha metro-card metro-card-${st}`}>
              <button
                type="button"
                className="metro-click"
                onClick={() => {
                  const next = aberto ? null : codigo;
                  setOpenCodigo(next);
                  if (!aberto && podeAqui) {
                    setTimeout(() => {
                      acoesRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
                    }, 50);
                  }
                }}
              >
                <div className={`etapa-bolinha etapa-bolinha-${st}`} aria-hidden="true" />

                <div className="etapa-conteudo">
                  <div className="etapa-titulo">
                    {s.ordem}. {s.nome}{" "}
                    <span className="texto-suave" style={{ fontSize: 11, fontWeight: 800 }}>
                      ({s.lado})
                    </span>
                  </div>
                  <div className="etapa-descricao">{s.descricao}</div>
                </div>

                <span className={`badge-status badge-pequena badge-${st}`}>{label(st)}</span>
              </button>

              {aberto ? (
                <div className="metro-detalhe">
                  <div className="metro-detalhe-top">
                    <div>
                      <div className="metro-detalhe-titulo">Último registro</div>
                      <div className="texto-suave" style={{ marginTop: 6 }}>
                        <div>
                          <strong>Responsável:</strong> {ur?.responsavel_nome || "—"}
                        </div>
                        <div>
                          <strong>Data/hora:</strong> {formatarDataHoraEnc(ur?.data_hora)}
                        </div>

{Array.isArray(ur?.extras) && ur.extras.length ? (
  <div style={{ marginTop: 6 }}>
    {ur.extras.map((x, ix) => (
      <div key={ix}>
        <strong>{x.label}:</strong> {x.value}
      </div>
    ))}
  </div>
) : null}

                        {ur?.obs ? (
                          <div style={{ marginTop: 6, whiteSpace: "pre-wrap" }}>
                            <strong>Obs:</strong> {ur.obs}
                          </div>
                        ) : (
                          <div style={{ marginTop: 6 }}>Nenhum registro ainda para esta etapa.</div>
                        )}
                      </div>
                    </div>

                    <div style={{ display: "flex", gap: 10, alignItems: "center", flexWrap: "wrap" }}>
                      {isNext ? (
                        <button
                          type="button"
                          className="btn btn-primario btn-primario-mini"
                          disabled={!podeAqui}
                          onClick={() => {
                            if (!podeAqui) return;
                            acoesRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
                          }}
                          title={!podeAqui ? `Bloqueado: deve ser registrado pelo ${ladoNec}` : "Abrir a ação guiada desta etapa"}
                        >
                          Abrir ação desta etapa
                        </button>
                      ) : null}
                    </div>
                  </div>

                  {regs.length ? (
                    <div className="metro-box">
                      <div className="metro-box-title">Histórico da etapa</div>
                      <ul className="metro-list">
                        {regs.map((r) => (
                          <li key={r.id || Math.random()}>
                            <div>
                              <strong>{r.responsavel_nome || "—"}</strong> — {formatarDataHoraEnc(r.data_hora)}
                            </div>
                            {r.obs ? <div className="muted" style={{ whiteSpace: "pre-wrap" }}>{r.obs}</div> : null}
                          </li>
                        ))}
                      </ul>
                    </div>
                  ) : null}


                  {loadingDossie ? (
                    <div className="texto-suave" style={{ marginTop: 10 }}>
                      Carregando dossiê…
                    </div>
                  ) : null}

                  {(() => {
                    const a1 = Array.isArray(dossie?.anexos) ? dossie.anexos : [];
                    const a2 = Array.isArray(anexos) ? anexos : [];
                    const all = [...a1, ...a2];
                    const seen = new Set();
                    const uniq = all.filter((x) => {
                      const k = x?.id ?? x?.url ?? x?.path ?? JSON.stringify(x);
                      if (seen.has(k)) return false;
                      seen.add(k);
                      return true;
                    });

                    const hasDocs = Boolean(linksDocs?.contrarreferencia_pdf || linksDocs?.recebimento_pdf);
                    const hasVinc = Boolean(destinoCasoId);
                    const hasAnex = uniq.length > 0;

                    if (!hasDocs && !hasVinc && !hasAnex) return null;

                    return (
                      <div className="metro-box">
                        <div className="metro-box-title">Evidências e documentos</div>

                        <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 8 }}>
                          {linksDocs?.contrarreferencia_pdf ? (
                            <a
                              className="btn btn-secundario btn-primario-mini"
                              href={linksDocs.contrarreferencia_pdf}
                              target="_blank"
                              rel="noreferrer"
                            >
                              Baixar contrarreferência
                            </a>
                          ) : null}

                          {linksDocs?.recebimento_pdf ? (
                            <a
                              className="btn btn-secundario btn-primario-mini"
                              href={linksDocs.recebimento_pdf}
                              target="_blank"
                              rel="noreferrer"
                            >
                              Baixar recebimento
                            </a>
                          ) : null}

                          {destinoCasoId ? (
                            <button
                              type="button"
                              className="btn btn-primario btn-primario-mini"
                              onClick={abrirCasoDestino}
                            >
                              Abrir caso no destino
                            </button>
                          ) : null}
                        </div>

                        {hasAnex ? (
                          <div className="metro-enc-list">
                            {uniq.slice(0, 20).map((a) => {
                              const href = a?.url || a?.href || a?.link || a?.path || null;
                              const titulo = a?.titulo || a?.nome || a?.filename || "Anexo";
                              const when = a?.criado_em || a?.em || a?.created_at || null;
                              const por = a?.por_nome || a?.usuario_nome || a?.criado_por_nome || null;

                              const absHref =
                                href && (String(href).startsWith("http://") || String(href).startsWith("https://"))
                                  ? href
                                  : href && String(href).startsWith("/")
                                  ? `${apiBase}${href}`
                                  : href;

                              return (
                                <div key={a?.id || absHref || Math.random()} className="metro-enc-item">
                                  <div style={{ minWidth: 0 }}>
                                    <div style={{ fontWeight: 900, fontSize: 12 }}>{titulo}</div>
                                    <div className="texto-suave" style={{ marginTop: 2 }}>
                                      {(por ? `Por: ${por} · ` : "")}
                                      {formatarDataHoraEnc(when)}
                                    </div>
                                    {absHref ? (
                                      <a
                                        href={absHref}
                                        target="_blank"
                                        rel="noreferrer"
                                        className="texto-suave"
                                        style={{ display: "inline-block", marginTop: 4 }}
                                      >
                                        Abrir anexo
                                      </a>
                                    ) : null}
                                  </div>
                                </div>
                              );
                            })}
                          </div>
                        ) : (
                          <div className="texto-suave">Sem anexos registrados.</div>
                        )}
                      </div>
                    );
                  })()}

                  {isNext && !podeAqui ? (
                    <div className="erro-global" style={{ marginTop: 10 }}>
                      Ação bloqueada: esta etapa deve ser registrada pelo <strong>{ladoNec}</strong>.
                    </div>
                  ) : null}
                </div>
              ) : null}
            </div>
          );
        })}
      </div>
    );
  })()}
</div>

            {/* AÇÕES GUIADAS (CORRIGIDO: sem soltar “aceite do quê”) */}
            <div ref={acoesRef}>{renderAcoesGuiadas()}</div>

            {/* HISTÓRICO */}
            <div className="card">
              <h3 style={{ marginTop: 0 }}>Histórico (eventos)</h3>

              {loadingDetalhe ? (
                <p className="texto-suave">Carregando eventos...</p>
              ) : detalhe?.eventos && detalhe.eventos.length > 0 ? (
                <ul className="lista-atendimentos">
                  {detalhe.eventos.slice(0, 12).map((ev) => (
                    <li key={ev.id} className="item-atendimento">
                      <div className="item-atendimento-header">
                        <div className="item-atendimento-titulo">{labelStatusCurto(ev.tipo)}</div>
                        <span className="badge-info badge-pequena">{formatarDataHora(ev.em)}</span>
                      </div>
                      <div className="item-atendimento-sub">Por: {ev.por_nome || "—"}</div>
                      {ev.detalhe ? <div className="item-atendimento-texto">{ev.detalhe}</div> : null}
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="texto-suave">Sem eventos.</p>
              )}
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}

function toIni(txt) {
  const s = String(txt || "").trim();
  return s ? s[0].toUpperCase() : "E";
}

function fmtDH(v) {
  if (!v) return "—";
  const d = new Date(v);
  if (Number.isNaN(d.getTime())) return String(v);
  const dd = String(d.getDate()).padStart(2, "0");
  const mm = String(d.getMonth() + 1).padStart(2, "0");
  const yy = d.getFullYear();
  const hh = String(d.getHours()).padStart(2, "0");
  const mi = String(d.getMinutes()).padStart(2, "0");
  return `${dd}/${mm}/${yy} ${hh}:${mi}`;
}

function ResumoEncaminhamento({ item, municipios = [], pessoas = [], destinoCasoId, onOpenDestinoCaso, docs, loadingDossie, anexosCount = 0 }) {
  if (!item) return null;

  const map = new Map(
    (municipios || []).map((m) => [
      Number(m?.id),
      m?.nome || m?.nome_municipio || `Município #${m?.id}`,
    ])
  );

  const pessoaNome = getNomePessoaFromEnc(item, pessoas);
  const iniciais = iniciaisPessoa(pessoaNome);

  const origemId =
    toIntIdEnc(item?.municipio_origem_id) ??
    toIntIdEnc(item?.origem_municipio_id) ??
    toIntIdEnc(item?.municipioOrigemId) ??
    toIntIdEnc(item?.origem_id) ??
    null;

  const destinoId =
    toIntIdEnc(item?.municipio_destino_id) ??
    toIntIdEnc(item?.destino_municipio_id) ??
    toIntIdEnc(item?.municipioDestinoId) ??
    toIntIdEnc(item?.destino_id) ??
    null;

  const origemNome = origemId != null ? map.get(Number(origemId)) || "—" : "—";
  const destinoNome = destinoId != null ? map.get(Number(destinoId)) || "—" : "—";

  const criadoEm =
    item?.criado_em || item?.criadoEm || item?.created_at || item?.data_criacao || null;

  const motivo = item?.motivo || item?.observacao || item?.descricao || "—";
  const etapa = item?.etapa_atual || item?.etapaAtual || item?.etapa || "—";
  const status = (item?.status || item?.situacao || item?.estado || item?.status_atual || "—").toString();

  return (
    <div className="enc-resumo-card">
      <div className="enc-hero">
        <div className="enc-hero-left">
          <div className="enc-avatar" aria-hidden="true">
            <span>{iniciais}</span>
          </div>

          <div className="enc-hero-main">
            <div className="enc-hero-title">{pessoaNome}</div>
            <div className="enc-hero-meta">
              Origem: <strong>{origemNome}</strong> · Destino: <strong>{destinoNome}</strong>
            </div>
          </div>
        </div>

        <div className="enc-hero-right">
          <span className="badge-status badge-pequena">{status}</span>
        </div>
      </div>

      <div className="enc-resumo-grid">
        <div className="enc-kv">
          <span className="enc-k">Criado</span>
          <span className="enc-v">{formatarDataHoraEnc(criadoEm)}</span>
        </div>

        <div className="enc-kv">
          <span className="enc-k">Motivo</span>
          <span className="enc-v">{String(motivo || "—")}</span>
        </div>

        <div className="enc-kv">
          <span className="enc-k">Etapa</span>
          <span className="enc-v">{String(etapa || "—")}</span>
        </div>

        <div className="enc-kv">
          <span className="enc-k">Status</span>
          <span className="enc-v">{String(status || "—")}</span>
        </div>
      </div>

<div style={{ marginTop: 12, display: "flex", gap: 8, justifyContent: "flex-end", flexWrap: "wrap" }}>
  {loadingDossie ? (
    <span className="texto-suave">Carregando dossiê…</span>
  ) : (
    <>
      {Number(anexosCount) > 0 ? (
        <span className="badge-info badge-pequena">Anexos: {anexosCount}</span>
      ) : null}

      {docs?.contrarreferencia_pdf ? (
        <a className="btn btn-secundario btn-primario-mini" href={docs.contrarreferencia_pdf} target="_blank" rel="noreferrer">
          Baixar contrarreferência
        </a>
      ) : null}

      {docs?.recebimento_pdf ? (
        <a className="btn btn-secundario btn-primario-mini" href={docs.recebimento_pdf} target="_blank" rel="noreferrer">
          Baixar recebimento
        </a>
      ) : null}

      {destinoCasoId ? (
        <button type="button" className="btn btn-primario btn-primario-mini" onClick={onOpenDestinoCaso}>
          Abrir caso no destino
        </button>
      ) : null}
    </>
  )}
</div>
    </div>
  );
}

    