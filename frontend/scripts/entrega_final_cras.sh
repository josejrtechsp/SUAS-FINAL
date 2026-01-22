#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "== 1) Diagnóstico rápido do repositório =="
test -d backend && test -d frontend && echo "OK: backend/ e frontend/ encontrados."

echo "== 2) Atualizar/Padronizar Cabeçalho (modelo do print, compacto, full width) =="
cat > frontend/src/components/CrasPageHeader.jsx <<'EOF'
import React from "react";

/**
 * Cabeçalho padrão CRAS (modelo do print) — compacto e full width.
 * Compatível com props antigas: tips, badge, rightText
 * e novas: bullets, rightTag, rightMetaLabel/rightMetaValue
 */
export default function CrasPageHeader({
  kicker = "MÓDULO SUAS · INTELIGÊNCIA SOCIAL",
  title,
  subtitle,
  bullets,
  tips,
  rightTag,
  badge,
  rightMetaLabel = "Usuário",
  rightMetaValue = "—",
  rightText,
}) {
  const lista = (bullets && bullets.length ? bullets : tips) || [];
  const tag = rightTag || badge || "CRAS";

  return (
    <div
      className="card"
      style={{
        width: "100%",
        maxWidth: "100%",
        padding: 14,
        borderRadius: 18,
        border: "1px solid rgba(2,6,23,.08)",
        background:
          "radial-gradient(1200px 420px at 25% 0%, rgba(99,102,241,.12), rgba(255,255,255,.70))",
        boxShadow: "0 10px 30px rgba(2,6,23,.07)",
      }}
    >
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "1fr 280px",
          gap: 14,
          alignItems: "start",
        }}
      >
        <div>
          <div
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: 8,
              padding: "5px 10px",
              borderRadius: 999,
              border: "1px solid rgba(99,102,241,.25)",
              background: "rgba(99,102,241,.08)",
              color: "rgb(79,70,229)",
              fontWeight: 900,
              letterSpacing: ".10em",
              textTransform: "uppercase",
              fontSize: 11,
            }}
          >
            {kicker}
          </div>

          <div style={{ marginTop: 8, fontSize: 30, fontWeight: 950, color: "rgb(2,6,23)", lineHeight: 1.08 }}>
            {title}
          </div>

          {subtitle ? (
            <div style={{ marginTop: 6, fontSize: 16, color: "rgba(2,6,23,.65)", lineHeight: 1.35 }}>
              {subtitle}
            </div>
          ) : null}

          {lista.length ? (
            <div style={{ marginTop: 10 }}>
              {lista.map((t, idx) => (
                <div key={idx} style={{ display: "flex", gap: 10, alignItems: "flex-start", marginTop: 6, fontSize: 16 }}>
                  <span aria-hidden style={{ lineHeight: "20px" }}>✅</span>
                  <div style={{ color: "rgba(2,6,23,.85)" }}>{t}</div>
                </div>
              ))}
            </div>
          ) : null}
        </div>

        <div>
          <div
            style={{
              height: 24,
              borderRadius: 999,
              background: "rgba(14,165,233,.12)",
              border: "1px solid rgba(14,165,233,.18)",
              display: "flex",
              alignItems: "center",
              padding: "0 10px",
            }}
          >
            <span style={{ fontSize: 12, fontWeight: 900, color: "rgb(3,105,161)" }}>{tag}</span>
          </div>

          <div style={{ marginTop: 8, color: "rgba(2,6,23,.65)", fontSize: 14 }}>
            {rightText ? (
              rightText
            ) : (
              <>
                {rightMetaLabel}: <strong style={{ color: "rgba(2,6,23,.9)" }}>{rightMetaValue}</strong>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
EOF

echo "== 3) Garantir full width (remover max-width do container) =="
# Ajusta App.css de forma segura (não quebra se não encontrar)
python3 - <<'PY'
from pathlib import Path
import re
from datetime import datetime

css = Path("frontend/src/App.css")
if not css.exists():
    print("WARN: frontend/src/App.css não encontrado; pulando.")
    raise SystemExit(0)

ts = datetime.now().strftime("%Y%m%d_%H%M%S")
orig = css.read_text(encoding="utf-8")
bak = css.with_suffix(css.suffix + f".bak_{ts}")
bak.write_text(orig, encoding="utf-8")

def patch_block(selector: str, text: str):
    pat = re.compile(rf"({re.escape(selector)}\s*\{{)([\s\S]*?)(\}})", re.M)
    m = pat.search(text)
    if not m:
        return text
    head, body, tail = m.group(1), m.group(2), m.group(3)
    body = re.sub(r"max-width\s*:\s*[^;]+;\s*", "", body)
    if "max-width" not in body:
        body = "  max-width: none;\n" + body
    if "width:" not in body:
        body = "  width: 100%;\n" + body
    return text[:m.start()] + head + "\n" + body + tail + text[m.end():]

txt = orig
for sel in [".layout-1col", ".app-main", ".app-main-1col"]:
    txt2 = patch_block(sel, txt)
    txt = txt2

css.write_text(txt, encoding="utf-8")
print("OK: App.css ajustado. Backup:", bak)
PY

echo "== 4) Dashboard do Gestor (frontend) =="
cat > frontend/src/TelaCrasInicioDashboard.jsx <<'EOF'
import React, { useEffect, useMemo, useState } from "react";

export default function TelaCrasInicioDashboard({ apiBase, apiFetch, onNavigate }) {
  const [data, setData] = useState(null);
  const [erro, setErro] = useState(null);
  const [loading, setLoading] = useState(false);

  async function load() {
    setLoading(true);
    setErro(null);
    try {
      // tenta endpoint novo, cai no overview existente
      let d = null;
      try {
        d = await apiFetch(`${apiBase}/cras/dashboard/overview`);
      } catch {
        d = await apiFetch(`${apiBase}/cras/relatorios/overview`);
      }
      setData(d);
    } catch (e) {
      setErro(String(e));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, []);

  const cards = useMemo(() => {
    const d = data || {};
    return [
      { k: "Usuários", v: d.pessoas_total ?? d.total_pessoas ?? "—", hint: "Pessoas cadastradas/atendidas" },
      { k: "Famílias", v: d.familias_total ?? d.total_familias ?? "—", hint: "Famílias cadastradas" },
      { k: "Casos abertos", v: d.casos_abertos ?? d.total_casos_abertos ?? "—", hint: "Casos em andamento" },
      { k: "Pendências (SLA)", v: d.pendencias_sla ?? d.total_pendencias ?? "—", hint: "Itens vencendo/vencidos" },
      { k: "SCFV presença (mês)", v: d.scfv_presencas_mes ?? "—", hint: "Presenças registradas no mês" },
      { k: "SCFV ausências (mês)", v: d.scfv_ausencias_mes ?? "—", hint: "Ausências no mês" },
      { k: "Programas presença (mês)", v: d.programas_presencas_mes ?? "—", hint: "Presenças em encontros" },
      { k: "CadÚnico pendente", v: d.cadunico_pendentes ?? "—", hint: "Pré-cadastro/agendamento/atrasos" },
    ];
  }, [data]);

  return (
    <div>
      {erro ? (
        <div className="card" style={{ padding: 12, borderRadius: 14 }}>
          <strong>Erro:</strong> {erro}
        </div>
      ) : null}

      <div style={{ display: "flex", justifyContent: "space-between", gap: 10, flexWrap: "wrap", alignItems: "center" }}>
        <div className="texto-suave">Painel operacional do CRAS (gestão por dados e ações)</div>
        <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
          <button className="btn btn-secundario" type="button" onClick={load} disabled={loading}>
            {loading ? "Atualizando..." : "Atualizar"}
          </button>
          <button className="btn btn-primario" type="button" onClick={() => onNavigate?.({ tab: "relatorios" })}>
            Ir para Relatórios
          </button>
        </div>
      </div>

      <div style={{ marginTop: 12, display: "grid", gridTemplateColumns: "repeat(4, minmax(220px, 1fr))", gap: 12 }}>
        {cards.map((c) => (
          <div key={c.k} className="card" style={{ padding: 12, borderRadius: 16 }}>
            <div className="texto-suave" style={{ fontSize: 13 }}>{c.k}</div>
            <div style={{ fontSize: 28, fontWeight: 950, marginTop: 6 }}>{c.v}</div>
            <div className="texto-suave" style={{ marginTop: 4 }}>{c.hint}</div>
          </div>
        ))}
      </div>

      {/* Ações rápidas */}
      <div className="card" style={{ padding: 12, borderRadius: 16, marginTop: 12 }}>
        <div style={{ fontWeight: 950 }}>Ações rápidas</div>
        <div style={{ display: "flex", gap: 10, flexWrap: "wrap", marginTop: 10 }}>
          <button className="btn btn-secundario" type="button" onClick={() => onNavigate?.({ tab: "casos" })}>Casos</button>
          <button className="btn btn-secundario" type="button" onClick={() => onNavigate?.({ tab: "cadunico" })}>CadÚnico</button>
          <button className="btn btn-secundario" type="button" onClick={() => onNavigate?.({ tab: "scfv" })}>SCFV</button>
          <button className="btn btn-secundario" type="button" onClick={() => onNavigate?.({ tab: "programas" })}>Programas</button>
          <button className="btn btn-secundario" type="button" onClick={() => onNavigate?.({ tab: "ficha" })}>Ficha 360°</button>
        </div>
      </div>
    </div>
  );
}
EOF

echo "== 5) Documento mercado + diferenciais (com fontes) =="
cat > docs/mercado_diferenciais.md <<'EOF'
# Pesquisa de mercado e diferenciais — SUAS Inteligência Social

## Panorama (o que o mercado promete)
- Sistemas como SociÁgil, ProSUAS, W3Social e SUASnet normalmente vendem: prontuário digital, integração de unidades, relatórios/dashboards e automação genérica.
  - SociÁgil: sistema de gestão SUAS integrado (CRAS/CREAS/POP etc.) e rotinas administrativas/relatórios. Fonte: https://www.sociagil.com.br/
  - ProSUAS: prontuário digital, diagnóstico familiar, monitoramento e “RMA em um clique”. Fonte: https://prosuas.com.br/
  - W3Social: automação de fluxos, gestão de grupos/atividades e dashboards. Fonte: https://w3sistemas.tec.br/w3social/
  - SUASnet: software + treinamentos; foco em reduzir burocracia e integrar unidades. Fonte: https://www.suasnet.com.br/

## Movimento do Governo (impacto estratégico)
- Novo Prontuário Eletrônico do SUAS com abertura em 18/12/2025 e referência normativa (CNAS/MDS nº 220/2025). Fonte: https://blog.mds.gov.br/redesuas/comunicado-de-abertura-do-novo-prontuario-eletronico-do-suas/
- Integração/modernização com CadÚnico é tema recorrente nas comunicações. Ex.: notícia regional citando Portaria 1.804 e integração com CadÚnico. Fonte: https://mpmt.mp.br/portalcao/news/1181/159186/prontuario-eletronico-da-assistencia-social-sera-integrado-ao-cadastro-unico/20

## Onde os sistemas geralmente falham (oportunidade)
1) Muito “registro” e pouca “ação”: dados ficam armazenados, mas não viram rotinas práticas.
2) Gestor não enxerga SLA por técnico e backlog por tipo (visita, contato, atualização, devolutiva).
3) “Ficha” não agrega tudo com contexto (usuário participa de vários serviços e vira caça ao tesouro).
4) Evasão/presença costuma ser relatório, não gatilho operacional com sugestão de ação.

## Diferenciais pro SUAS Inteligência Social (para ganhar mercado)
- **Gestão por SLA**: tudo vira pendência rastreável, com prazo, responsável e auditoria.
- **Ações embutidas**: Cobrar, Agendar, Criar encaminhamento, Abrir caso/PIA/PAIF, Registrar contato.
- **Ficha 360° real**: agrega SCFV + Programas + Casos + CadÚnico + Condicionalidades + anexos + timeline.
- **Painel do gestor do CRAS**: usuários por perfil/território, pendências por SLA, presença/ausência por serviço, produtividade por técnico.
- **Evidência e compliance**: histórico auditável, trilha por usuário/família/caso e relatórios prontos para gestão/controle social.

## Próximos passos (produto)
- Consolidar entidade “Tarefa” (assign + SLA + status) ligada a: Caso, CadÚnico, SCFV, Programa, Encaminhamento.
- Criar “Regra de alerta” configurável (ex.: 3 faltas/30 dias → ação sugerida).
- Melhorar diferencial com UX: “1 clique” do painel abre a ficha já filtrada com highlight da pendência.
EOF

echo "== 6) Diagnóstico automático (frontend) — procurar erros comuns antes do build =="
python3 - <<'PY'
import re
from pathlib import Path

SRC = Path("frontend/src")
issues = []

# 1) linha solta "}" dentro de layout-1col
for p in SRC.rglob("TelaCras*.jsx"):
    txt = p.read_text(encoding="utf-8", errors="ignore").splitlines()
    for i, ln in enumerate(txt, 1):
        if re.match(r"^\s*\}\s*$", ln):
            # só marca se estiver perto de return e layout-1col
            if any("layout-1col" in x for x in txt[max(0,i-15):i+5]):
                issues.append((str(p), i, "Linha '}' solta perto de layout-1col"))

# 2) <input ...> sem fechamento (muito comum em JSX quebrado)
for p in SRC.rglob("*.jsx"):
    txt = p.read_text(encoding="utf-8", errors="ignore").splitlines()
    for i, ln in enumerate(txt, 1):
        if "<input" in ln and "/>" not in ln and "</input>" not in ln:
            # ignora se for linha de abertura e fecha depois na próxima linha
            if i < len(txt) and "/>" in txt[i]:
                continue
            issues.append((str(p), i, "<input possivelmente sem fechamento />"))

print("DIAGNÓSTICO FRONTEND:")
if not issues:
    print("OK: nenhum padrão crítico detectado.")
else:
    for it in issues[:80]:
        print(" -", it[0], "linha", it[1], ":", it[2])
    if len(issues) > 80:
        print(" ... (mais itens)")
PY

echo "== 7) Build frontend (limpo) =="
cd frontend
npm install >/dev/null
npm run build
cd ..

echo "== 8) Checagem backend (compileall) =="
python3 - <<'PY'
import compileall
ok = compileall.compile_dir("backend/app", quiet=1)
print("Backend compileall:", "OK" if ok else "FALHOU")
if not ok:
    raise SystemExit(1)
PY

echo "== 9) Empacotar ZIP FINAL (sem node_modules e sem .venv) =="
ZIP="SUAS_CRAS_ENTREGA_FINAL.zip"
rm -f "$ZIP"
zip -r "$ZIP" backend frontend docs scripts \
  -x "backend/.venv/*" \
  -x "frontend/node_modules/*" \
  -x "**/.DS_Store" \
  -x "__MACOSX/*" >/dev/null

echo "OK: ZIP gerado -> $ROOT/$ZIP"
ls -lah "$ZIP"
