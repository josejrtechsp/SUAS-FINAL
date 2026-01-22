import React, { useMemo, useState } from "react";
import { createCreasCase,
  setCreasSelectedCaseId } from "./domain/creasStore.js";
import { isRecepcao } from "./domain/acl.js";

const TEMAS = [
  { tema: "Violência/Ameaça", detalhes: ["violência física", "violência psicológica", "violência sexual", "ameaça"] },
  { tema: "Criança e adolescente", detalhes: ["negligência", "abuso", "trabalho infantil", "evasão escolar"] },
  { tema: "Mulher/Família", detalhes: ["violência contra a mulher", "conflitos familiares", "dependência química (família)"] },
  { tema: "Idoso/PcD", detalhes: ["maus-tratos", "exploração financeira", "violação PcD"] },
  { tema: "Direitos/Vulnerabilidade grave", detalhes: ["situação de rua", "desaparecimento", "exploração", "violação geral"] },
  { tema: "Encaminhamento de órgão/rede", detalhes: ["Conselho Tutelar", "Judiciário", "CRAS", "Escola", "Saúde", "Segurança", "Denúncia"] },
  { tema: "Outro", detalhes: ["outro"] },
];

export default function TelaCreasNovoCaso({ usuarioLogado, onNavigate }) {
  const [msg, setMsg] = useState("");
  function flash(m) {
    setMsg(m || "");
    if (!m) return;
    setTimeout(() => setMsg(""), 2600);
  }
  const [nome, setNome] = useState("");
  const [origem, setOrigem] = useState("CRAS");
  const [risco, setRisco] = useState("medio");
  const [tema, setTema] = useState("Violência/Ameaça");
  const [detalhe, setDetalhe] = useState("violência psicológica");
  const [proximoPasso, setProximoPasso] = useState("Registrar triagem");
  const [proximoData, setProximoData] = useState(() => {
    const d = new Date();
    d.setDate(d.getDate() + 1);
    return d.toISOString().slice(0, 16);
  });

  const recepcao = useMemo(() => isRecepcao(usuarioLogado), [usuarioLogado]);

  const detalhes = useMemo(() => {
    const x = TEMAS.find((t) => t.tema === tema);
    return x?.detalhes || ["—"];
  }, [tema]);

  function salvar(irParaTriagem) {
    if (!nome.trim()) return flash("Informe o nome (ou identificação) da pessoa/família.");
    if (!proximoPasso.trim()) return flash("Faltou informar o próximo passo.");
    if (!proximoData) return flash("Faltou marcar a data do próximo passo.");

    const created = createCreasCase({
      nome: nome.trim(),
      origem,
      usuario: usuarioLogado || null,
      risco,
      motivo_tema: tema,
      motivo_detalhe: detalhe,
      proximo_passo: proximoPasso,
      proximo_passo_em: new Date(proximoData).toISOString(),
      usuario_nome: usuarioLogado?.nome || "—",
    });

    try {
      setCreasSelectedCaseId(String(created.id));
    } catch {}

    flash(
      recepcao
        ? "Caso salvo ✅\n\nDica: este caso ficou SEM responsável para um técnico ASSUMIR."
        : "Caso salvo ✅"
    );

    if (irParaTriagem) {
      onNavigate?.({ tab: "casos" });
    } else {
      onNavigate?.({ tab: "painel" });
    }
  }

  return (
    <div className="layout-1col">
      <div className="card">
        <div className="card-header-row">
          <div>
            <div style={{ fontSize: 18, fontWeight: 950 }}>Entrada rápida (CREAS)</div>
      {msg ? (
        <div className="card" style={{ marginTop: 10, padding: 10, boxShadow: "none", border: "1px solid rgba(59,130,246,.25)", background: "rgba(59,130,246,.08)" }} role="alert">
          <b>{msg}</b>
        </div>
      ) : null}
            <div className="texto-suave">Preencha o básico. O resto pode ser completado depois.</div>
            {recepcao ? (
              <div className="texto-suave" style={{ marginTop: 6 }}>
                Seu perfil é <b>Recepção</b>: o caso será salvo <b>sem responsável</b> para um técnico <b>ASSUMIR</b>.
              </div>
            ) : null}
          </div>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
          <div>
            <div className="texto-suave" style={{ fontWeight: 900, marginBottom: 6 }}>Pessoa/Família</div>
            <input className="input" value={nome} onChange={(e) => setNome(e.target.value)} placeholder="Ex.: Maria da Silva / Família Souza" />
          </div>

          <div>
            <div className="texto-suave" style={{ fontWeight: 900, marginBottom: 6 }}>Origem</div>
            <select className="input" value={origem} onChange={(e) => setOrigem(e.target.value)}>
              <option>CRAS</option>
              <option>Conselho Tutelar</option>
              <option>Judiciário</option>
              <option>MP</option>
              <option>Escola</option>
              <option>Saúde</option>
              <option>Segurança</option>
              <option>Denúncia</option>
              <option>Outro</option>
            </select>
          </div>

          <div>
            <div className="texto-suave" style={{ fontWeight: 900, marginBottom: 6 }}>Motivo (tema)</div>
            <select
              className="input"
              value={tema}
              onChange={(e) => {
                setTema(e.target.value);
                const nx = TEMAS.find((t) => t.tema === e.target.value);
                setDetalhe(nx?.detalhes?.[0] || "—");
              }}
            >
              {TEMAS.map((t) => (
                <option key={t.tema} value={t.tema}>
                  {t.tema}
                </option>
              ))}
            </select>
          </div>

          <div>
            <div className="texto-suave" style={{ fontWeight: 900, marginBottom: 6 }}>Motivo (detalhe)</div>
            <select className="input" value={detalhe} onChange={(e) => setDetalhe(e.target.value)}>
              {detalhes.map((d) => (
                <option key={d} value={d}>
                  {d}
                </option>
              ))}
            </select>
          </div>

          <div>
            <div className="texto-suave" style={{ fontWeight: 900, marginBottom: 6 }}>Risco</div>
            <select className="input" value={risco} onChange={(e) => setRisco(e.target.value)}>
              <option value="baixo">Baixo</option>
              <option value="medio">Médio</option>
              <option value="alto">Alto</option>
            </select>
          </div>

          <div>
            <div className="texto-suave" style={{ fontWeight: 900, marginBottom: 6 }}>Próximo passo (obrigatório)</div>
            <input className="input" value={proximoPasso} onChange={(e) => setProximoPasso(e.target.value)} placeholder="Ex.: Registrar triagem" />
          </div>

          <div>
            <div className="texto-suave" style={{ fontWeight: 900, marginBottom: 6 }}>Data do próximo passo (obrigatório)</div>
            <input className="input" type="datetime-local" value={proximoData} onChange={(e) => setProximoData(e.target.value)} />
          </div>
        </div>

        <div className="card-footer-right">
          <button className="btn btn-secundario" type="button" onClick={() => salvar(false)}>
            Salvar e sair
          </button>
          <button className="btn btn-primario" type="button" onClick={() => salvar(true)}>
            Salvar e ir para triagem
          </button>
        </div>
      </div>
    </div>
  );
}