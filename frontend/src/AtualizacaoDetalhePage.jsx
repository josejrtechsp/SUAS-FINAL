import React, { useMemo } from "react";
import { useNavigate, useParams } from "react-router-dom";
import "./Portal.css";
import PortalHeader from "./PortalHeader.jsx";

import { PORTAL_ATUALIZACOES } from "./content/portalAtualizacoesData.js";

function formatDateBR(iso) {
  if (!iso) return "";
  const parts = String(iso).split("-");
  if (parts.length !== 3) return iso;
  const [y, m, d] = parts;
  if (!y || !m || !d) return iso;
  return `${d}/${m}/${y}`;
}

function labelForArea(key) {
  if (key === "assistencia") return "Assistência Social (SUAS)";
  if (key === "saude") return "Saúde (SUS)";
  if (key === "educacao") return "Educação (MEC/FNDE)";
  return "Atualização";
}

function safeKeydown(e, fn) {
  if (e.key === "Enter" || e.key === " ") {
    e.preventDefault();
    fn?.();
  }
}

function BulletList({ items, icon = "✅" }) {
  if (!Array.isArray(items) || items.length === 0) return null;
  return (
    <div style={{ display: "grid", gap: 8, marginTop: 10, fontSize: 13, color: "#374151", lineHeight: 1.55 }}>
      {items.map((t, i) => (
        <div key={i} style={{ display: "flex", gap: 10, alignItems: "flex-start" }}>
          <span style={{ marginTop: 1 }}>{icon}</span>
          <span>{t}</span>
        </div>
      ))}
    </div>
  );
}

function ParaList({ paragraphs }) {
  if (!Array.isArray(paragraphs) || paragraphs.length === 0) return null;
  return (
    <div style={{ marginTop: 10, display: "grid", gap: 10 }}>
      {paragraphs.map((p, i) => (
        <p key={i} style={{ margin: 0, fontSize: 13, color: "#374151", lineHeight: 1.7 }}>
          {p}
        </p>
      ))}
    </div>
  );
}

function MiniSection({ title, subtitle, children }) {
  return (
    <div style={{ marginTop: 14 }}>
      <div style={{ fontWeight: 950, fontSize: 13, color: "#111827" }}>{title}</div>
      {subtitle ? <div style={{ marginTop: 4, fontSize: 12, color: "#6b7280" }}>{subtitle}</div> : null}
      {children}
    </div>
  );
}

function Steps({ items }) {
  if (!Array.isArray(items) || items.length === 0) return null;
  return (
    <div style={{ marginTop: 10, display: "grid", gap: 10 }}>
      {items.map((s, i) => {
        const title = typeof s === "object" ? s.t : null;
        const desc = typeof s === "object" ? s.d : String(s);
        return (
          <div key={i} className="portal3-step" style={{ alignItems: "flex-start" }}>
            <span className="portal3-step-n">{i + 1}</span>
            <div style={{ display: "grid", gap: 4 }}>
              {title ? <div style={{ fontSize: 13, fontWeight: 950, color: "#111827" }}>{title}</div> : null}
              <div style={{ fontSize: 13, lineHeight: 1.35 }}>{desc}</div>
            </div>
          </div>
        );
      })}
    </div>
  );
}

function Proofs({ items }) {
  if (!Array.isArray(items) || items.length === 0) return null;
  return (
    <div style={{ marginTop: 10, display: "grid", gap: 10 }}>
      {items.map((p, i) => (
        <div
          key={i}
          style={{
            border: "1px solid rgba(0,0,0,0.06)",
            background: "rgba(255,255,255,0.55)",
            borderRadius: 14,
            padding: 12,
          }}
        >
          <div style={{ fontWeight: 950, color: "#111827", fontSize: 13 }}>{p?.t}</div>
          <div style={{ marginTop: 6, fontSize: 12, color: "#4b5563", lineHeight: 1.5 }}>{p?.d}</div>
        </div>
      ))}
    </div>
  );
}

export default function AtualizacaoDetalhePage({ onEntrar }) {
  const navigate = useNavigate();
  const { slug } = useParams();

  const item = useMemo(() => {
    const s = (slug || "").trim();
    if (!s) return null;
    return (PORTAL_ATUALIZACOES || []).find((x) => String(x.slug) === s) || null;
  }, [slug]);

  if (!item) {
    return (
      <div className="portal3-root">
        <PortalHeader onEntrar={onEntrar} backTo="/atualizacoes" backLabel="Atualizações" />

        <main className="portal3-main">
          <section className="portal3-section">
            <div className="portal3-empty">
              Atualização não encontrada. <br />
              Volte para o portal e selecione outro item.
            </div>
          </section>
        </main>
      </div>
    );
  }

  const areaLabel = labelForArea(item.area);
  const tipo = (item.tipo || "Atualização").toUpperCase();

  // novo padrão (com fallback para campos antigos, caso exista conteúdo legado)
  const em30 = item.em30s || item.leituraRapida || [];
  const decisao = item.decisaoRapida || [];
  const entenda = item.entenda || [];
  const mudaRotina = item.mudaRotina || item.impacto || [];
  const passos = item.passos || (item.oQueFazer || []).map((x) => ({ t: null, d: x }));
  const provas = item.provas || item.evidenciaMinima || [];
  const erros = item.errosComuns || [];
  const msg = item.mensagemPronta || "";

  return (
    <div className="portal3-root">
      <PortalHeader onEntrar={onEntrar} backTo="/atualizacoes" backLabel="Atualizações" />

      <main className="portal3-main">
        <section className="portal3-section">
          <div className="portal3-section-head">
            <div className="portal3-proof" style={{ marginBottom: 10 }}>
              <span className="portal3-tag">{tipo}</span>
              <span className="portal3-proof-chip">{areaLabel}</span>
              <span className="portal3-proof-chip">{formatDateBR(item.data)}</span>
            </div>

            <h1 className="portal3-h1" style={{ marginTop: 2 }}>
              {item.titulo}
            </h1>

            <p className="portal3-sub" style={{ maxWidth: 900 }}>
              {item.subtitulo}
            </p>
          </div>

          <div className="portal3-split">
            {/* Conteúdo */}
            <div className="portal3-splitLeft portal3-callout">
              <MiniSection title="Em 30 segundos" subtitle="O que mudou · quem é afetado · qual ação imediata">
                <BulletList items={em30} />
              </MiniSection>

              <MiniSection title="Decisão rápida" subtitle="Vale agir agora? Quem assume? Qual risco se ignorar?">
                <BulletList items={decisao} icon="⚡️" />
              </MiniSection>

              <MiniSection title="Entenda (sem juridiquês)">
                <ParaList paragraphs={entenda} />
              </MiniSection>

              <MiniSection title="O que muda na rotina">
                <BulletList items={mudaRotina} icon="🧭" />
              </MiniSection>

              <div style={{ marginTop: 18, borderTop: "1px solid rgba(0,0,0,0.06)", paddingTop: 14 }}>
                <div style={{ fontWeight: 950, fontSize: 13, color: "#111827" }}>Fonte</div>
                <div style={{ marginTop: 8, fontSize: 12, color: "#6b7280", lineHeight: 1.6 }}>
                  {(item.fontes || []).map((f, i) => (
                    <div key={i}>• {f}</div>
                  ))}
                  <div style={{ marginTop: 8 }}>
                    Observação: este texto é uma síntese operacional. Para aplicação formal, valide sempre no ato oficial e nas orientações do órgão responsável.
                  </div>
                </div>
              </div>
            </div>

            {/* Coluna direita */}
            <div className="portal3-splitRight portal3-callout">
              <div className="portal3-upHead" style={{ padding: 0 }}>
                <div className="portal3-upTitle">3 passos para executar</div>
                <div className="portal3-upSub">confirme · organize · execute e registre (sem complicar)</div>
              </div>

              <Steps items={passos} />

              <MiniSection title="Evidência mínima (3 provas)" subtitle="base → entrada → entrega (o suficiente para gestão e auditoria)">
                <Proofs items={provas} />
              </MiniSection>

              <MiniSection title="Erros comuns" subtitle="o que mais faz município perder prazo e retrabalhar">
                <BulletList items={erros} icon="⚠️" />
              </MiniSection>

              {msg ? (
                <MiniSection title="Mensagem pronta" subtitle="copiar e colar para sua equipe">
                  <pre
                    style={{
                      marginTop: 10,
                      marginBottom: 0,
                      padding: 12,
                      borderRadius: 14,
                      border: "1px solid rgba(0,0,0,0.06)",
                      background: "rgba(255,255,255,0.60)",
                      fontSize: 12,
                      color: "#374151",
                      whiteSpace: "pre-wrap",
                      lineHeight: 1.55,
                    }}
                  >
                    {msg}
                  </pre>
                </MiniSection>
              ) : null}

              <div style={{ marginTop: 14 }}>
                <a
                  href="/atualizacoes"
                  className="portal3-link"
                  onClick={(e) => {
                    e.preventDefault();
                    navigate("/atualizacoes");
                  }}
                  onKeyDown={(e) => safeKeydown(e, () => navigate("/atualizacoes"))}
                >
                  ← Voltar ao Portal
                </a>
              </div>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}
