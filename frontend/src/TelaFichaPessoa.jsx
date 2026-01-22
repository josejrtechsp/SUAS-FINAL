import React, { useEffect, useMemo, useState } from "react";
import { API_BASE } from "./config";

import {
  getAtendimentoTipoLabel,
  getAtendimentoResultadoLabel,
} from "./domain/statuses.js";

/* =====================
   Helpers
   ===================== */
function normalizarTexto(valor) {
  return (valor || "")
    .toString()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .trim();
}

function apenasDigitos(valor) {
  return (valor || "").toString().replace(/\D/g, "");
}

function formatarCPF(cpf) {
  const d = apenasDigitos(cpf);
  if (d.length !== 11) return cpf || "—";
  return `${d.slice(0, 3)}.${d.slice(3, 6)}.${d.slice(6, 9)}-${d.slice(9, 11)}`;
}

function formatarDataBR(data) {
  if (!data) return "—";
  try {
    if (/^\d{4}-\d{2}-\d{2}$/.test(data)) {
      const [y, m, d] = data.split("-");
      return `${d}/${m}/${y}`;
    }
    const dt = new Date(data);
    if (isNaN(dt.getTime())) return data;
    const dia = String(dt.getDate()).padStart(2, "0");
    const mes = String(dt.getMonth() + 1).padStart(2, "0");
    const ano = dt.getFullYear();
    return `${dia}/${mes}/${ano}`;
  } catch {
    return data;
  }
}

function formatarDataHora(isoString) {
  if (!isoString) return "Data não informada";
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

async function copiarTexto(texto) {
  try {
    if (navigator?.clipboard?.writeText) {
      await navigator.clipboard.writeText(texto);
      return true;
    }
  } catch (_) {}
  return false;
}

function iniciaisDoNome(nome) {
  const n = (nome || "").trim();
  return (n?.[0] || "P").toUpperCase();
}

function safeStr(v) {
  if (v == null) return "";
  return String(v);
}

/* =====================
   Componente
   ===================== */
const TelaFichaPessoa = ({
  pessoas = [],
  casos = [],
  municipios = [],
  apiBase = API_BASE,
  apiFetch,
  municipioAtivoId,
  municipioAtivoNome,
  usuarioLogado,
  pessoaIdInicial = "",
}) => {
  const [busca, setBusca] = useState("");
  const [filtroMunicipioId, setFiltroMunicipioId] = useState("todos");
  const [pagina, setPagina] = useState(1);
  const [pessoaSelecionadaId, setPessoaSelecionadaId] = useState(null);

  const [atendimentos, setAtendimentos] = useState([]);
  const [loadingAtend, setLoadingAtend] = useState(false);
  const [erroAtend, setErroAtend] = useState("");
  const [mostrarTodosAtend, setMostrarTodosAtend] = useState(false);

  // edição
  const [modoEdicao, setModoEdicao] = useState(false);
  const [salvando, setSalvando] = useState(false);
  const [erroEdicao, setErroEdicao] = useState("");
  const [form, setForm] = useState({
    nome_social: "",
    genero: "",
    estado_civil: "",
    tempo_rua: "",
    local_referencia: "",
    observacoes_gerais: "",

    // complementos
    apelido: "",
    telefone: "",
    whatsapp: "",
    contato_referencia_nome: "",
    contato_referencia_telefone: "",
    permanencia_rua: "",
    pontos_circulacao: "",
    horario_mais_encontrado: "",
    motivo_rua: "",
    escolaridade: "",
    ocupacao: "",
    interesses_reinsercao: "",
    cadunico_status: "",
    documentos_pendentes: "",
    fonte_renda: "",
    violencia_risco: "",
    ameaca_territorio: "",
    gestante_status: "",
    protecao_imediata: "",
    interesse_acolhimento: "",
    moradia_recente: "",
    tentativas_saida_rua: "",
	    dependencia_quimica: "",
    // sensíveis (admin/consórcio)
    nome_civil: "",
    cpf: "",
    data_nascimento: "",
    municipio_origem_id: "",
    nis: "",
  });

  // cache local para refletir edição imediatamente na lista
  const [pessoasEditadas, setPessoasEditadas] = useState(() => new Map());

  const PAGE_SIZE = 10;

  const perfil = (usuarioLogado?.perfil || "").toLowerCase();
  const podeEditarSensiveis = perfil === "admin" || perfil === "gestor_consorcio";

  // estilos (mantém padrão roxo do sistema)
  const avatarStyle = useMemo(
    () => ({
      width: 42,
      height: 42,
      borderRadius: 999,
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      fontWeight: 800,
      color: "#ffffff",
      background: "linear-gradient(135deg, #7c3aed 0%, #6366f1 100%)",
      boxShadow: "0 10px 30px rgba(124, 58, 237, .22)",
      border: "1px solid rgba(124, 58, 237, .45)",
      flex: "0 0 auto",
    }),
    []
  );

  const blockGap = 12;

  // pré-seleção ao abrir a aba
  useEffect(() => {
    const pid = pessoaIdInicial != null ? String(pessoaIdInicial).trim() : "";
    if (!pid) return;
    if (pessoaSelecionadaId) return;

    const num = Number(pid);
    if (!isNaN(num)) setPessoaSelecionadaId(num);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pessoaIdInicial]);

  async function fetchComAuth(url, options = {}) {
    if (typeof apiFetch === "function") {
      return apiFetch(url, options);
    }
    const token =
      localStorage.getItem("poprua_token") ||
      localStorage.getItem("access_token") ||
      localStorage.getItem("token") ||
      "";
    const merged = {
      ...options,
      headers: {
        ...(options.headers || {}),
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
    };
    return fetch(url, merged);
  }

  const municipiosOrdenados = useMemo(() => {
    const arr = Array.isArray(municipios) ? [...municipios] : [];
    arr.sort((a, b) =>
      (a?.nome || a?.nome_municipio || "").localeCompare(
        b?.nome || b?.nome_municipio || ""
      )
    );
    return arr;
  }, [municipios]);

  const mapaMunicipios = useMemo(() => {
    const m = new Map();
    municipiosOrdenados.forEach((x) => {
      const idNum = Number(x?.id);
      if (!isNaN(idNum)) {
        m.set(idNum, x?.nome || x?.nome_municipio || `Município #${idNum}`);
      }
    });
    return m;
  }, [municipiosOrdenados]);

  function nomeMunicipioPorId(id) {
    const n = Number(id);
    if (isNaN(n)) return "—";
    return mapaMunicipios.get(n) || `Município #${n}`;
  }

  // merge das pessoas editadas
  const pessoasMerge = useMemo(() => {
    const lista = Array.isArray(pessoas) ? pessoas : [];
    if (!pessoasEditadas || pessoasEditadas.size === 0) return lista;
    return lista.map((p) => pessoasEditadas.get(Number(p?.id)) || p);
  }, [pessoas, pessoasEditadas]);

  const pessoasFiltradas = useMemo(() => {
    const lista = pessoasMerge;
    const termo = normalizarTexto(busca);
    const digitosBusca = apenasDigitos(busca);

    const filtrada = lista
      .filter((p) => {
        if (filtroMunicipioId !== "todos") {
          const mid =
            p?.municipio_origem_id ??
            p?.municipioOrigemId ??
            p?.municipio_id ??
            p?.municipioId ??
            null;

          if (mid != null && Number(mid) !== Number(filtroMunicipioId)) {
            return false;
          }
        }

        if (!termo && !digitosBusca) return true;

        const nome = normalizarTexto(
          `${p?.nome_social || ""} ${p?.nome_civil || ""}`
        );
        const cpfDig = apenasDigitos(p?.cpf || "");
        const idStr = String(p?.id ?? "");

        if (digitosBusca) {
          if (cpfDig.includes(digitosBusca)) return true;
          if (idStr.includes(digitosBusca)) return true;
        }

        return nome.includes(termo);
      })
      .sort((a, b) => {
        const na = (a?.nome_social || a?.nome_civil || "").toString();
        const nb = (b?.nome_social || b?.nome_civil || "").toString();
        return na.localeCompare(nb);
      });

    return filtrada;
  }, [pessoasMerge, busca, filtroMunicipioId]);

  useEffect(() => {
    setPagina(1);
  }, [busca, filtroMunicipioId]);

  const totalPaginas = useMemo(() => {
    const t = Math.ceil(pessoasFiltradas.length / PAGE_SIZE);
    return Math.max(1, t || 1);
  }, [pessoasFiltradas.length]);

  useEffect(() => {
    if (pagina > totalPaginas) setPagina(totalPaginas);
  }, [pagina, totalPaginas]);

  const pessoasPagina = useMemo(() => {
    const ini = (pagina - 1) * PAGE_SIZE;
    return pessoasFiltradas.slice(ini, ini + PAGE_SIZE);
  }, [pessoasFiltradas, pagina]);

  const pessoaSelecionada = useMemo(() => {
    if (!pessoaSelecionadaId) return null;

    const idNum = Number(pessoaSelecionadaId);
    if (isNaN(idNum)) return null;

    return (
      pessoasFiltradas.find((p) => Number(p?.id) === idNum) ||
      (Array.isArray(pessoasMerge)
        ? pessoasMerge.find((p) => Number(p?.id) === idNum)
        : null) ||
      null
    );
  }, [pessoaSelecionadaId, pessoasFiltradas, pessoasMerge]);

  const casosDaPessoa = useMemo(() => {
    if (!pessoaSelecionadaId) return [];
    const pid = Number(pessoaSelecionadaId);
    if (isNaN(pid)) return [];

    const lista = Array.isArray(casos) ? casos : [];
    return lista
      .filter((c) => Number(c?.pessoa_id) === pid)
      .sort((a, b) => (b?.id ?? 0) - (a?.id ?? 0));
  }, [casos, pessoaSelecionadaId]);

  function getNomePessoa(p) {
    return p?.nome_social || p?.nome_civil || `Pessoa #${p?.id ?? "—"}`;
  }

  function getMunicipioOrigemId(p) {
    return (
      p?.municipio_origem_id ??
      p?.municipioOrigemId ??
      p?.municipio_id ??
      p?.municipioId ??
      null
    );
  }

  async function carregarAtendimentos(pessoaId) {
    if (!pessoaId) return;

    setErroAtend("");
    setLoadingAtend(true);

    try {
      const res = await fetchComAuth(`${apiBase}/pessoas/${pessoaId}/atendimentos`);
      if (!res.ok) {
        let msg = "Não foi possível carregar os atendimentos dessa pessoa.";
        try {
          const errJson = await res.json();
          if (errJson?.detail) {
            msg =
              typeof errJson.detail === "string"
                ? errJson.detail
                : JSON.stringify(errJson.detail);
          }
        } catch (_) {}
        throw new Error(msg);
      }

      const data = await res.json();
      setAtendimentos(Array.isArray(data) ? data : []);
    } catch (e) {
      console.error(e);
      setAtendimentos([]);
      setErroAtend(e?.message || "Erro ao carregar atendimentos.");
    } finally {
      setLoadingAtend(false);
    }
  }

  useEffect(() => {
    setAtendimentos([]);
    setErroAtend("");
    setMostrarTodosAtend(false);

    if (!pessoaSelecionadaId) return;

    const pid = Number(pessoaSelecionadaId);
    if (!isNaN(pid)) {
      carregarAtendimentos(pid);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pessoaSelecionadaId, apiBase, apiFetch]);

  const atendimentosOrdenados = useMemo(() => {
    const arr = Array.isArray(atendimentos) ? [...atendimentos] : [];
    arr.sort((a, b) => {
      const da = a?.data_atendimento ? new Date(a.data_atendimento).getTime() : 0;
      const db = b?.data_atendimento ? new Date(b.data_atendimento).getTime() : 0;
      return db - da;
    });
    return arr;
  }, [atendimentos]);

  const atendimentosParaMostrar = useMemo(() => {
    if (mostrarTodosAtend) return atendimentosOrdenados;
    return atendimentosOrdenados.slice(0, 6);
  }, [atendimentosOrdenados, mostrarTodosAtend]);

  // preparar form ao selecionar pessoa
  useEffect(() => {
    setErroEdicao("");
    if (!pessoaSelecionada) {
      setModoEdicao(false);
      return;
    }

    setForm({
      nome_social: safeStr(pessoaSelecionada?.nome_social),
      genero: safeStr(pessoaSelecionada?.genero),
      estado_civil: safeStr(pessoaSelecionada?.estado_civil),
      tempo_rua: safeStr(pessoaSelecionada?.tempo_rua),
      local_referencia: safeStr(pessoaSelecionada?.local_referencia),
      observacoes_gerais: safeStr(pessoaSelecionada?.observacoes_gerais),

      apelido: safeStr(pessoaSelecionada?.apelido),
      telefone: safeStr(pessoaSelecionada?.telefone),
      whatsapp: safeStr(pessoaSelecionada?.whatsapp),
      contato_referencia_nome: safeStr(pessoaSelecionada?.contato_referencia_nome),
      contato_referencia_telefone: safeStr(pessoaSelecionada?.contato_referencia_telefone),
      permanencia_rua: safeStr(pessoaSelecionada?.permanencia_rua),
      pontos_circulacao: safeStr(pessoaSelecionada?.pontos_circulacao),
      horario_mais_encontrado: safeStr(pessoaSelecionada?.horario_mais_encontrado),
      motivo_rua: safeStr(pessoaSelecionada?.motivo_rua),
      escolaridade: safeStr(pessoaSelecionada?.escolaridade),
      ocupacao: safeStr(pessoaSelecionada?.ocupacao),
      interesses_reinsercao: safeStr(pessoaSelecionada?.interesses_reinsercao),
      cadunico_status: safeStr(pessoaSelecionada?.cadunico_status),
      documentos_pendentes: safeStr(pessoaSelecionada?.documentos_pendentes),
      fonte_renda: safeStr(pessoaSelecionada?.fonte_renda),
      violencia_risco: safeStr(pessoaSelecionada?.violencia_risco),
      ameaca_territorio: safeStr(pessoaSelecionada?.ameaca_territorio),
      gestante_status: safeStr(pessoaSelecionada?.gestante_status),
      protecao_imediata: safeStr(pessoaSelecionada?.protecao_imediata),
      interesse_acolhimento: safeStr(pessoaSelecionada?.interesse_acolhimento),
      moradia_recente: safeStr(pessoaSelecionada?.moradia_recente),
      tentativas_saida_rua: safeStr(pessoaSelecionada?.tentativas_saida_rua),
	      dependencia_quimica: safeStr(pessoaSelecionada?.dependencia_quimica),
      nome_civil: safeStr(pessoaSelecionada?.nome_civil),
      cpf: safeStr(pessoaSelecionada?.cpf),
      data_nascimento: safeStr(pessoaSelecionada?.data_nascimento),
      municipio_origem_id:
        pessoaSelecionada?.municipio_origem_id == null
          ? ""
          : String(pessoaSelecionada?.municipio_origem_id),
      nis: safeStr(pessoaSelecionada?.nis),
    });
  }, [pessoaSelecionadaId]); // eslint-disable-line react-hooks/exhaustive-deps

  async function salvarEdicao() {
    if (!pessoaSelecionada?.id) return;

    setErroEdicao("");

    const payload = {
      nome_social: form.nome_social || null,
      genero: form.genero || null,
      estado_civil: form.estado_civil || null,
      tempo_rua: form.tempo_rua || null,
      local_referencia: form.local_referencia || null,
      observacoes_gerais: form.observacoes_gerais || null,

      // complementos
      apelido: form.apelido || null,
      telefone: form.telefone || null,
      whatsapp: form.whatsapp || null,
      contato_referencia_nome: form.contato_referencia_nome || null,
      contato_referencia_telefone: form.contato_referencia_telefone || null,
      permanencia_rua: form.permanencia_rua || null,
      pontos_circulacao: form.pontos_circulacao || null,
      horario_mais_encontrado: form.horario_mais_encontrado || null,
      motivo_rua: form.motivo_rua || null,
      escolaridade: form.escolaridade || null,
      ocupacao: form.ocupacao || null,
      interesses_reinsercao: form.interesses_reinsercao || null,
      cadunico_status: form.cadunico_status || null,
      documentos_pendentes: form.documentos_pendentes || null,
      fonte_renda: form.fonte_renda || null,
      violencia_risco: form.violencia_risco || null,
      ameaca_territorio: form.ameaca_territorio || null,
      gestante_status: form.gestante_status || null,
      protecao_imediata: form.protecao_imediata || null,
      interesse_acolhimento: form.interesse_acolhimento || null,
      moradia_recente: form.moradia_recente || null,
      tentativas_saida_rua: form.tentativas_saida_rua || null,
	      dependencia_quimica: form.dependencia_quimica || null,
    };

    if (podeEditarSensiveis) {
      payload.nome_civil = form.nome_civil || null;
      payload.cpf = apenasDigitos(form.cpf) || null;
      payload.nis = apenasDigitos(form.nis) || null;
      payload.data_nascimento = form.data_nascimento || null;
      payload.municipio_origem_id = form.municipio_origem_id
        ? Number(form.municipio_origem_id)
        : null;
    }

    try {
      setSalvando(true);

      const res = await fetchComAuth(`${apiBase}/pessoas/${pessoaSelecionada.id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        let msg = `Erro HTTP ${res.status}`;
        try {
          const errJson = await res.json();
          msg = errJson?.detail ? JSON.stringify(errJson.detail) : msg;
        } catch {
          const txt = await res.text().catch(() => "");
          if (txt) msg = txt;
        }
        throw new Error(msg);
      }

      const atualizada = await res.json();

      setPessoasEditadas((prev) => {
        const m = new Map(prev);
        m.set(Number(atualizada?.id), atualizada);
        return m;
      });

      setPessoaSelecionadaId(Number(atualizada.id));
      setModoEdicao(false);
      setErroEdicao("");
      alert("Ficha atualizada com sucesso!");
    } catch (e) {
      console.error(e);
      setErroEdicao(e?.message || "Erro ao salvar alterações.");
    } finally {
      setSalvando(false);
    }
  }

  return (
    <section className="card card-wide ficha-pessoa">
      {/* HEADER PADRÃO DO SITE */}
      <div className="card-header-row">
        <div> 
          <h2 style={{ margin: 0 }}>Ficha da pessoa</h2>
          <p className="card-subtitle" style={{ marginTop: 6 }}>
            Busque por <strong>nome</strong>, <strong>CPF</strong> ou <strong>ID</strong> e veja os dados e o histórico de atendimentos.
          </p>

          {municipioAtivoNome ? (
            <p className="texto-suave" style={{ marginTop: 6 }}>
              Município ativo: <strong>{municipioAtivoNome}</strong>
              {usuarioLogado?.nome ? (
                <>
                  {" "}
                  · Usuário: <strong>{usuarioLogado.nome}</strong>
                </>
              ) : null}
            </p>
          ) : null}
        </div>
      </div>

      {erroEdicao && <p className="erro-global">{erroEdicao}</p>}

      <div className="grid-2cols" style={{ marginTop: 12 }}>
        {/* COLUNA ESQUERDA */}
        <div>
          <label className="form-label">
            Buscar pessoa (nome, CPF ou ID)
            <input
              className="input"
              placeholder="Ex.: Maria, 123.456.789-00, 15..."
              value={busca}
              onChange={(e) => setBusca(e.target.value)}
            />
          </label>

          {Array.isArray(municipiosOrdenados) && municipiosOrdenados.length > 0 && (
            <label className="form-label" style={{ marginTop: 10 }}>
              Filtrar por município de origem (opcional)
              <select
                className="input"
                value={filtroMunicipioId}
                onChange={(e) => setFiltroMunicipioId(e.target.value)}
              >
                <option value="todos">Todos os municípios</option>
                {municipiosOrdenados.map((m) => (
                  <option key={m.id} value={m.id}>
                    {m.nome || m.nome_municipio}
                  </option>
                ))}
              </select>
            </label>
          )}

          <div style={{ marginTop: 10 }} className="texto-suave">
            {pessoasFiltradas.length} pessoa{pessoasFiltradas.length === 1 ? "" : "s"} encontrada{pessoasFiltradas.length === 1 ? "" : "s"}.
          </div>

          {/* Paginação */}
          <div style={{ marginTop: 10, display: "flex", gap: 8, alignItems: "center" }}>
            <button
              type="button"
              className="btn btn-secundario btn-secundario-mini"
              onClick={() => setPagina((p) => Math.max(1, p - 1))}
              disabled={pagina <= 1}
            >
              Anterior
            </button>

            <div className="texto-suave">
              Página <strong>{pagina}</strong> de <strong>{totalPaginas}</strong>
            </div>

            <button
              type="button"
              className="btn btn-secundario btn-secundario-mini"
              onClick={() => setPagina((p) => Math.min(totalPaginas, p + 1))}
              disabled={pagina >= totalPaginas}
            >
              Próxima
            </button>
          </div>

          {/* Lista */}
          <ul className="lista-atendimentos" style={{ marginTop: 12 }}>
            {pessoasPagina.length === 0 ? (
              <li className="item-atendimento">
                <div className="item-atendimento-titulo">Nenhuma pessoa para exibir</div>
                <div className="item-atendimento-sub">
                  Ajuste a busca/filtros para encontrar registros.
                </div>
              </li>
            ) : (
              pessoasPagina.map((p) => {
                const selecionada = Number(p?.id) === Number(pessoaSelecionadaId);
                const municipioId = getMunicipioOrigemId(p);
                const municipioNome = municipioId ? nomeMunicipioPorId(municipioId) : "—";

                return (
                  <li
                    key={p.id}
                    className="item-atendimento"
                    style={
                      selecionada
                        ? {
                            borderColor: "#7c3aed",
                            boxShadow: "0 12px 32px rgba(124, 58, 237, 0.20)",
                          }
                        : undefined
                    }
                    onClick={() => {
                      setPessoaSelecionadaId(p.id);
                      setErroEdicao("");
                    }}
                  >
                    <div className="item-atendimento-header">
                      <div>
                        <div className="item-atendimento-titulo">{getNomePessoa(p)}</div>
                        <div className="item-atendimento-sub">
                          ID {p.id} · CPF: {formatarCPF(p.cpf)} · {municipioNome}
                        </div>
                      </div>

                      <span className="badge-info badge-pequena">
                        {pessoaSelecionadaId && selecionada ? "Selecionada" : "Ver"}
                      </span>
                    </div>
                  </li>
                );
              })
            )}
          </ul>
        </div>

        {/* COLUNA DIREITA */}
        <div>
          {!pessoaSelecionada ? (
            <div className="item-atendimento" style={{ marginTop: 0 }}>
              <div className="item-atendimento-titulo">Selecione uma pessoa</div>
              <div className="item-atendimento-sub">
                Clique em uma pessoa na lista para ver os dados completos e os atendimentos.
              </div>
            </div>
          ) : (
            <>
              {/* RESUMO */}
              <div className="item-atendimento" style={{ marginTop: 0 }}>
                <div className="item-atendimento-header">
                  <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                    <div style={avatarStyle} aria-hidden="true">
                      {iniciaisDoNome(getNomePessoa(pessoaSelecionada))}
                    </div>

                    <div>
                      <div className="item-atendimento-titulo">{getNomePessoa(pessoaSelecionada)}</div>
                      <div className="item-atendimento-sub">
                        ID {pessoaSelecionada.id} · CPF: {formatarCPF(pessoaSelecionada.cpf)}
                      </div>
                    </div>
                  </div>

                  <div style={{ display: "flex", gap: 8, flexWrap: "wrap", justifyContent: "flex-end" }}>
	                    <button
	                      type="button"
	                      className="btn btn-secundario btn-secundario-mini"
	                      onClick={() => setModoEdicao((v) => !v)}
	                      disabled={!pessoaSelecionada}
	                      title={!pessoaSelecionada ? "Selecione uma pessoa para editar" : ""}
	                    >
	                      {modoEdicao ? "Fechar edição" : "Editar ficha"}
	                    </button>

                    <button
                      type="button"
                      className="btn btn-secundario btn-secundario-mini"
                      onClick={async () => {
                        const ok = await copiarTexto(String(pessoaSelecionada.id));
                        if (ok) alert("ID copiado!");
                      }}
                    >
                      Copiar ID
                    </button>

                    <button
                      type="button"
                      className="btn btn-secundario btn-secundario-mini"
                      onClick={async () => {
                        const cpf = pessoaSelecionada.cpf ? String(pessoaSelecionada.cpf) : "";
                        const ok = await copiarTexto(cpf);
                        if (ok) alert("CPF copiado!");
                      }}
                      disabled={!pessoaSelecionada.cpf}
                    >
                      Copiar CPF
                    </button>
                  </div>
                </div>

                <div className="item-atendimento-detalhes">
                  <span>
                    Nascimento: <strong>{formatarDataBR(pessoaSelecionada.data_nascimento)}</strong>
                  </span>
                  <span>
                    Gênero: <strong>{pessoaSelecionada.genero || "—"}</strong>
                  </span>
                  <span>
                    Estado civil: <strong>{pessoaSelecionada.estado_civil || "—"}</strong>
                  </span>
                </div>

                <div className="item-atendimento-detalhes" style={{ marginTop: 6 }}>
                  <span>
                    Município de origem:{" "}
                    <strong>
                      {(() => {
                        const mid = getMunicipioOrigemId(pessoaSelecionada);
                        if (!mid) return "—";
                        return `${nomeMunicipioPorId(mid)}`;
                      })()}
                    </strong>
                  </span>
                </div>

                <div className="item-atendimento-detalhes" style={{ marginTop: 6 }}>
                  <span>
                    Tempo de rua: <strong>{pessoaSelecionada.tempo_rua || "—"}</strong>
                  </span>
                  <span>
                    Local de referência: <strong>{pessoaSelecionada.local_referencia || "—"}</strong>
                  </span>
                </div>

                <div className="item-atendimento-detalhes" style={{ marginTop: 6 }}>
                  <span>
                    Permanência: <strong>{pessoaSelecionada.permanencia_rua || "—"}</strong>
                  </span>
                  <span>
                    CadÚnico: <strong>{pessoaSelecionada.cadunico_status || "—"}</strong>
                  </span>
                  <span>
                    Acolhimento: <strong>{pessoaSelecionada.interesse_acolhimento || "—"}</strong>
                  </span>
                </div>

                {pessoaSelecionada.observacoes_gerais ? (
                  <p className="item-atendimento-texto" style={{ marginTop: 8 }}>
                    <strong>Observações:</strong> {pessoaSelecionada.observacoes_gerais}
                  </p>
                ) : null}
              </div>

              {/* EDIÇÃO */}
              {modoEdicao && (
                <div className="item-atendimento" style={{ marginTop: blockGap }}>
                  <div className="item-atendimento-header">
                    <div>
                      <div className="item-atendimento-titulo">Editar ficha</div>
                      <div className="item-atendimento-sub">
                        {podeEditarSensiveis
                          ? "Admin/Gestor pode editar também campos sensíveis."
                          : "Edite apenas campos operacionais (LGPD)."}
                      </div>
                    </div>

                    <span className="badge-info badge-pequena">Edição</span>
                  </div>

                  <div className="grid-2cols" style={{ marginTop: 10 }}>
                    <label className="form-label">
                      Nome social
                      <input
                        className="input"
                        value={form.nome_social}
                        onChange={(e) => setForm({ ...form, nome_social: e.target.value })}
                      />
                    </label>

                    <label className="form-label">
                      Gênero
                      <input
                        className="input"
                        value={form.genero}
                        onChange={(e) => setForm({ ...form, genero: e.target.value })}
                      />
                    </label>

                    <label className="form-label">
                      Estado civil
                      <input
                        className="input"
                        value={form.estado_civil}
                        onChange={(e) => setForm({ ...form, estado_civil: e.target.value })}
                      />
                    </label>

                    <label className="form-label">
                      Tempo de rua
                      <input
                        className="input"
                        value={form.tempo_rua}
                        onChange={(e) => setForm({ ...form, tempo_rua: e.target.value })}
                      />
                    </label>

                    <label className="form-label" style={{ gridColumn: "1 / -1" }}>
                      Local de referência
                      <input
                        className="input"
                        value={form.local_referencia}
                        onChange={(e) => setForm({ ...form, local_referencia: e.target.value })}
                      />
                    </label>

                    <label className="form-label" style={{ gridColumn: "1 / -1" }}>
                      Observações gerais
                      <textarea
                        className="input"
                        rows={3}
                        value={form.observacoes_gerais}
                        onChange={(e) => setForm({ ...form, observacoes_gerais: e.target.value })}
                      />
                    </label>

                    {/* =========================
                        Complementos (questionário mais completo)
                        ========================= */}
                    <div style={{ gridColumn: "1 / -1" }}>
                      <details open>
                        <summary style={{ cursor: "pointer", fontWeight: 800 }}>
                          Complementos do cadastro (clique para recolher/abrir)
                        </summary>

                        <div className="grid-2cols" style={{ marginTop: 10 }}>
                          {/* Contato */}
                          <div style={{ gridColumn: "1 / -1" }}>
                            <div className="texto-suave" style={{ fontWeight: 800 }}>
                              Contato e referência
                            </div>
                          </div>

                          <label className="form-label">
                            Apelido
                            <input
                              className="input"
                              value={form.apelido}
                              onChange={(e) => setForm({ ...form, apelido: e.target.value })}
                            />
                          </label>

                          <label className="form-label">
                            Telefone
                            <input
                              className="input"
                              value={form.telefone}
                              onChange={(e) => setForm({ ...form, telefone: e.target.value })}
                            />
                          </label>

                          <label className="form-label">
                            WhatsApp
                            <input
                              className="input"
                              value={form.whatsapp}
                              onChange={(e) => setForm({ ...form, whatsapp: e.target.value })}
                            />
                          </label>

                          <label className="form-label">
                            Contato de referência (nome)
                            <input
                              className="input"
                              value={form.contato_referencia_nome}
                              onChange={(e) =>
                                setForm({ ...form, contato_referencia_nome: e.target.value })
                              }
                            />
                          </label>

                          <label className="form-label">
                            Contato de referência (telefone)
                            <input
                              className="input"
                              value={form.contato_referencia_telefone}
                              onChange={(e) =>
                                setForm({ ...form, contato_referencia_telefone: e.target.value })
                              }
                            />
                          </label>

                          <div style={{ gridColumn: "1 / -1", marginTop: 8 }}>
                            <div className="texto-suave" style={{ fontWeight: 800 }}>
                              Situação de rua e território
                            </div>
                          </div>

                          <label className="form-label">
                            Permanência
                            <select
                              className="input"
                              value={form.permanencia_rua}
                              onChange={(e) => setForm({ ...form, permanencia_rua: e.target.value })}
                            >
                              <option value="">—</option>
                              <option value="fixa">Fixa</option>
                              <option value="itinerante">Itinerante</option>
                              <option value="nao_informado">Não informado</option>
                            </select>
                          </label>

                          <label className="form-label">
                            Horário mais encontrado
                            <input
                              className="input"
                              value={form.horario_mais_encontrado}
                              onChange={(e) =>
                                setForm({ ...form, horario_mais_encontrado: e.target.value })
                              }
                            />
                          </label>

                          <label className="form-label" style={{ gridColumn: "1 / -1" }}>
                            Pontos de circulação
                            <textarea
                              className="input"
                              rows={2}
                              value={form.pontos_circulacao}
                              onChange={(e) => setForm({ ...form, pontos_circulacao: e.target.value })}
                            />
                          </label>

                          <label className="form-label" style={{ gridColumn: "1 / -1" }}>
                            Motivo predominante (sem detalhamento)
                            <input
                              className="input"
                              value={form.motivo_rua}
                              onChange={(e) => setForm({ ...form, motivo_rua: e.target.value })}
                            />
                          </label>

                          <div style={{ gridColumn: "1 / -1", marginTop: 8 }}>
                            <div className="texto-suave" style={{ fontWeight: 800 }}>
                              Rede, trabalho e reinserção
                            </div>
                          </div>

                          <label className="form-label">
                            Escolaridade
                            <input
                              className="input"
                              value={form.escolaridade}
                              onChange={(e) => setForm({ ...form, escolaridade: e.target.value })}
                            />
                          </label>

                          <label className="form-label">
                            Ocupação/Trabalho
                            <input
                              className="input"
                              value={form.ocupacao}
                              onChange={(e) => setForm({ ...form, ocupacao: e.target.value })}
                            />
                          </label>

                          <label className="form-label" style={{ gridColumn: "1 / -1" }}>
                            Interesses (curso/emprego/moradia etc.)
                            <textarea
                              className="input"
                              rows={2}
                              value={form.interesses_reinsercao}
                              onChange={(e) =>
                                setForm({ ...form, interesses_reinsercao: e.target.value })
                              }
                            />
                          </label>

                          <div style={{ gridColumn: "1 / -1", marginTop: 8 }}>
                            <div className="texto-suave" style={{ fontWeight: 800 }}>
                              Renda, benefícios e documentação (resumo)
                            </div>
                          </div>

                          <label className="form-label">
                            CadÚnico
                            <select
                              className="input"
                              value={form.cadunico_status}
                              onChange={(e) => setForm({ ...form, cadunico_status: e.target.value })}
                            >
                              <option value="">—</option>
                              <option value="sim">Sim</option>
                              <option value="nao">Não</option>
                              <option value="nao_sabe">Não sabe</option>
                            </select>
                          </label>

                          <label className="form-label">
                            Fonte de renda (se houver)
                            <input
                              className="input"
                              value={form.fonte_renda}
                              onChange={(e) => setForm({ ...form, fonte_renda: e.target.value })}
                            />
                          </label>

                          <label className="form-label" style={{ gridColumn: "1 / -1" }}>
                            Documentos pendentes (checklist)
                            <textarea
                              className="input"
                              rows={2}
                              value={form.documentos_pendentes}
                              onChange={(e) =>
                                setForm({ ...form, documentos_pendentes: e.target.value })
                              }
                            />
                          </label>

                          <div style={{ gridColumn: "1 / -1", marginTop: 8 }}>
                            <div className="texto-suave" style={{ fontWeight: 800 }}>
                              Proteção e vulnerabilidades (sem detalhar)
                            </div>
                          </div>

                          <label className="form-label">
                            Violência/risco
                            <select
                              className="input"
                              value={form.violencia_risco}
                              onChange={(e) => setForm({ ...form, violencia_risco: e.target.value })}
                            >
                              <option value="">—</option>
                              <option value="sim">Sim</option>
                              <option value="nao">Não</option>
                              <option value="nao_informa">Não quer informar</option>
                            </select>
                          </label>

                          <label className="form-label">
                            Ameaça no território
                            <select
                              className="input"
                              value={form.ameaca_territorio}
                              onChange={(e) => setForm({ ...form, ameaca_territorio: e.target.value })}
                            >
                              <option value="">—</option>
                              <option value="sim">Sim</option>
                              <option value="nao">Não</option>
                              <option value="nao_informa">Não quer informar</option>
                            </select>
                          </label>

	                          <label className="form-label">
	                            Dependência química
	                            <select
	                              className="input"
	                              value={form.dependencia_quimica}
	                              onChange={(e) =>
	                                setForm({ ...form, dependencia_quimica: e.target.value })
	                              }
	                            >
	                              <option value="">—</option>
	                              <option value="sim">Sim</option>
	                              <option value="nao">Não</option>
	                              <option value="nao_informa">Não quer informar</option>
	                            </select>
	                          </label>

                          <label className="form-label">
                            Gestante (se aplicável)
                            <select
                              className="input"
                              value={form.gestante_status}
                              onChange={(e) => setForm({ ...form, gestante_status: e.target.value })}
                            >
                              <option value="">—</option>
                              <option value="sim">Sim</option>
                              <option value="nao">Não</option>
                              <option value="nao_sabe">Não sabe</option>
                              <option value="nao_informa">Não quer informar</option>
                            </select>
                          </label>

                          <label className="form-label">
                            Proteção imediata
                            <select
                              className="input"
                              value={form.protecao_imediata}
                              onChange={(e) => setForm({ ...form, protecao_imediata: e.target.value })}
                            >
                              <option value="">—</option>
                              <option value="sim">Sim</option>
                              <option value="nao">Não</option>
                              <option value="avaliar">Avaliar</option>
                            </select>
                          </label>

                          <div style={{ gridColumn: "1 / -1", marginTop: 8 }}>
                            <div className="texto-suave" style={{ fontWeight: 800 }}>
                              Moradia e acolhimento
                            </div>
                          </div>

                          <label className="form-label">
                            Interesse em acolhimento
                            <select
                              className="input"
                              value={form.interesse_acolhimento}
                              onChange={(e) =>
                                setForm({ ...form, interesse_acolhimento: e.target.value })
                              }
                            >
                              <option value="">—</option>
                              <option value="sim">Sim</option>
                              <option value="nao">Não</option>
                              <option value="avaliar">Avaliar</option>
                            </select>
                          </label>

                          <label className="form-label">
                            Teve moradia recente
                            <select
                              className="input"
                              value={form.moradia_recente}
                              onChange={(e) => setForm({ ...form, moradia_recente: e.target.value })}
                            >
                              <option value="">—</option>
                              <option value="sim">Sim</option>
                              <option value="nao">Não</option>
                              <option value="nao_sabe">Não sabe</option>
                            </select>
                          </label>

                          <label className="form-label" style={{ gridColumn: "1 / -1" }}>
                            Tentativas anteriores de saída das ruas
                            <textarea
                              className="input"
                              rows={2}
                              value={form.tentativas_saida_rua}
                              onChange={(e) =>
                                setForm({ ...form, tentativas_saida_rua: e.target.value })
                              }
                            />
                          </label>
                        </div>
                      </details>
                    </div>

                    {podeEditarSensiveis && (
                      <>
                        <div style={{ gridColumn: "1 / -1", marginTop: 2 }}>
                          <div className="texto-suave" style={{ fontWeight: 700 }}>
                            Campos sensíveis (Admin/Gestor)
                          </div>
                        </div>

                        <label className="form-label">
                          Nome civil
                          <input
                            className="input"
                            value={form.nome_civil}
                            onChange={(e) => setForm({ ...form, nome_civil: e.target.value })}
                          />
                        </label>

                        <label className="form-label">
                          CPF
                          <input
                            className="input"
                            value={form.cpf}
                            onChange={(e) => setForm({ ...form, cpf: e.target.value })}
                          />
                        </label>

                        <label className="form-label">
                          Data de nascimento (AAAA-MM-DD)
                          <input
                            className="input"
                            value={form.data_nascimento}
                            onChange={(e) => setForm({ ...form, data_nascimento: e.target.value })}
                          />
                        </label>

                        <label className="form-label">
                          Município de origem (ID)
                          <input
                            className="input"
                            value={form.municipio_origem_id}
                            onChange={(e) => setForm({ ...form, municipio_origem_id: e.target.value })}
                          />
                        </label>
                      </>
                    )}

                    {/* FOOTER (botões menores e alinhados) */}
                    <div style={{ gridColumn: "1 / -1", marginTop: 6 }}>
                      <div style={{ display: "flex", justifyContent: "flex-end", gap: 10, flexWrap: "wrap" }}>
                        <button
                          type="button"
                          className="btn btn-secundario btn-secundario-mini"
                          onClick={() => setModoEdicao(false)}
                          disabled={salvando}
                        >
                          Cancelar
                        </button>

                        <button
                          type="button"
                          className="btn btn-primario btn-primario-mini"
                          onClick={salvarEdicao}
                          disabled={salvando}
                          style={{ minWidth: 180 }}
                        >
                          {salvando ? "Salvando..." : "Salvar alterações"}
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Casos */}
              <div className="item-atendimento" style={{ marginTop: blockGap }}>
                <div className="item-atendimento-header">
                  <div>
                    <div className="item-atendimento-titulo">Casos Pop Rua</div>
                    <div className="item-atendimento-sub">
                      {casosDaPessoa.length} caso{casosDaPessoa.length === 1 ? "" : "s"} vinculado{casosDaPessoa.length === 1 ? "" : "s"}.
                    </div>
                  </div>
                </div>

                {casosDaPessoa.length === 0 ? (
                  <p className="texto-suave" style={{ marginTop: 8 }}>
                    Nenhum caso encontrado para esta pessoa.
                  </p>
                ) : (
                  <ul className="lista-atendimentos" style={{ marginTop: 8 }}>
                    {casosDaPessoa.slice(0, 6).map((c) => (
                      <li key={c.id} className="item-atendimento">
                        <div className="item-atendimento-header">
                          <div>
                            <div className="item-atendimento-titulo">Caso #{c.id}</div>
                            <div className="item-atendimento-sub">
                              Etapa: {c.etapa_atual || "—"} · Status: {c.status || "—"}
                            </div>
                          </div>
                          <span className="badge-status badge-pequena">
                            {c.status === "encerrado" ? "Encerrado" : "Em andamento"}
                          </span>
                        </div>
                      </li>
                    ))}
                  </ul>
                )}

                {casosDaPessoa.length > 6 ? (
                  <p className="texto-suave" style={{ marginTop: 8 }}>
                    Mostrando os 6 mais recentes.
                  </p>
                ) : null}
              </div>

              {/* Atendimentos */}
              <div className="item-atendimento" style={{ marginTop: blockGap }}>
                <div className="item-atendimento-header">
                  <div>
                    <div className="item-atendimento-titulo">Atendimentos</div>
                    <div className="item-atendimento-sub">
                      Histórico de atendimentos da pessoa (carregado da API).
                    </div>
                  </div>

                  <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
                    <button
                      type="button"
                      className="btn btn-secundario btn-secundario-mini"
                      onClick={() => carregarAtendimentos(pessoaSelecionada.id)}
                      disabled={loadingAtend}
                    >
                      {loadingAtend ? "Carregando..." : "Recarregar"}
                    </button>

                    {atendimentosOrdenados.length > 6 && (
                      <button
                        type="button"
                        className="btn btn-secundario btn-secundario-mini"
                        onClick={() => setMostrarTodosAtend((v) => !v)}
                        disabled={loadingAtend}
                      >
                        {mostrarTodosAtend ? "Ver menos" : "Ver todos"}
                      </button>
                    )}
                  </div>
                </div>

                {erroAtend ? (
                  <p className="erro-global" style={{ marginTop: 8 }}>
                    {erroAtend}
                  </p>
                ) : loadingAtend ? (
                  <p className="texto-suave" style={{ marginTop: 8 }}>
                    Carregando atendimentos...
                  </p>
                ) : atendimentosOrdenados.length === 0 ? (
                  <p className="texto-suave" style={{ marginTop: 8 }}>
                    Nenhum atendimento encontrado para esta pessoa.
                  </p>
                ) : (
                  <ul className="lista-atendimentos" style={{ marginTop: 8 }}>
                    {atendimentosParaMostrar.map((at) => (
                      <li key={at.id} className="item-atendimento">
                        <div className="item-atendimento-header">
                          <div>
                            <div className="item-atendimento-titulo">
                              {getAtendimentoTipoLabel(at?.tipo_atendimento || at?.tipo)}
                            </div>
                            <div className="item-atendimento-sub">
                              {formatarDataHora(at?.data_atendimento)} ·{" "}
                              {at?.local_atendimento || at?.equipamento || "Local não informado"}
                            </div>
                          </div>

                          <span className="badge-status badge-pequena">
                            {getAtendimentoResultadoLabel(at?.resultado, at?.foi_realizado)}
                          </span>
                        </div>

                        {at?.descricao_resumida ? (
                          <p className="item-atendimento-texto">{at.descricao_resumida}</p>
                        ) : at?.descricao ? (
                          <p className="item-atendimento-texto">
                            {String(at.descricao).slice(0, 160)}
                            {String(at.descricao).length > 160 ? "..." : ""}
                          </p>
                        ) : null}
                      </li>
                    ))}
                  </ul>
                )}
              </div>

              <div style={{ marginTop: blockGap }}>
                <button
                  type="button"
                  className="btn btn-secundario"
                  onClick={() => {
                    setPessoaSelecionadaId(null);
                    setModoEdicao(false);
                    setErroEdicao("");
                  }}
                >
                  Limpar seleção
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </section>
  );
};

export default TelaFichaPessoa;