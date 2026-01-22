import re
from pathlib import Path
from datetime import datetime

ROOT = Path.cwd()
CRASAPP = ROOT / "frontend/src/CrasApp.jsx"
HEADER = ROOT / "frontend/src/components/CrasPageHeader.jsx"

ts = datetime.now().strftime("%Y%m%d_%H%M%S")

def backup(p: Path):
    if p.exists():
        b = p.with_suffix(p.suffix + f".bak_{ts}")
        b.write_text(p.read_text(encoding="utf-8"), encoding="utf-8")
        return b
    return None

def ensure_header_component():
    # Sobrescreve o CrasPageHeader para garantir o modelo único (print)
    HEADER.parent.mkdir(parents=True, exist_ok=True)
    backup(HEADER)
    HEADER.write_text(
        """import React from "react";

export default function CrasPageHeader({
  kicker = "MÓDULO SUAS · INTELIGÊNCIA SOCIAL",
  title,
  subtitle,
  bullets = [],
  rightTag = "CRAS",
  rightMetaLabel = "Usuário",
  rightMetaValue = "",
  className = "",
}) {
  return (
    <section className={`rounded-3xl border bg-white/70 shadow-sm ${className}`}>
      <div className="p-6 md:p-7 flex flex-col md:flex-row md:items-start md:justify-between gap-4">
        <div className="min-w-0">
          <div className="inline-flex items-center gap-2 rounded-full border px-3 py-1 text-xs font-semibold tracking-widest text-indigo-700 bg-indigo-50/60">
            {kicker}
          </div>

          <h1 className="mt-3 text-3xl md:text-4xl font-extrabold text-slate-900">
            {title}
          </h1>

          {subtitle ? (
            <p className="mt-2 text-slate-600 text-base md:text-lg">
              {subtitle}
            </p>
          ) : null}

          {bullets?.length ? (
            <ul className="mt-4 space-y-2 text-slate-700">
              {bullets.map((b, idx) => (
                <li key={idx} className="flex items-start gap-2">
                  <span aria-hidden className="mt-0.5">✅</span>
                  <span className="leading-relaxed">{b}</span>
                </li>
              ))}
            </ul>
          ) : null}
        </div>

        <aside className="shrink-0 md:w-[280px]">
          <div className="rounded-full bg-sky-100/70 border px-3 py-2 flex items-center justify-between">
            <span className="text-xs font-semibold text-sky-800">
              {rightTag}
            </span>
          </div>
          <div className="mt-2 text-slate-600">
            <span className="text-sm">{rightMetaLabel}: </span>
            <span className="text-sm font-semibold text-slate-800">
              {rightMetaValue || "—"}
            </span>
          </div>
        </aside>
      </div>
    </section>
  );
}
""",
        encoding="utf-8",
    )

def infer_tabs(text: str):
    # tenta achar { key/id: "x", label/title: "Y" }
    tab_re = re.compile(
        r"(?:key|id)\s*:\s*['\"]([^'\"]+)['\"].{0,500}?(?:label|title)\s*:\s*['\"]([^'\"]+)['\"]",
        re.S,
    )
    tabs = []
    seen = set()
    for m in tab_re.finditer(text):
        k, lbl = m.group(1), m.group(2)
        if k not in seen:
            seen.add(k)
            tabs.append((k, lbl))
    return tabs

def header_for(label: str):
    l = label.lower()

    def pack(title, subtitle, bullets):
        return dict(title=title, subtitle=subtitle, bullets=bullets)

    if "cad" in l and ("único" in l or "unico" in l):
        return pack("CRAS — CadÚnico",
                    "Pré-cadastro, agendamento, finalização e rastreabilidade.",
                    ["Pré-cadastro com status e histórico.",
                     "Agendamento e comparecimento.",
                     "Drill-down por ficha com pendências."])
    if "encamin" in l:
        return pack("CRAS — Encaminhamentos",
                    "Encaminhar, acompanhar retorno e manter trilha auditável.",
                    ["Registro por motivo/serviço.",
                     "Retorno e validação.",
                     "Timeline do caso e anexos."])
    if "caso" in l:
        return pack("CRAS — Casos",
                    "Etapas, validação, SLA e auditoria.",
                    ["Trilho (metrô) por etapas.",
                     "Validação de recebimento.",
                     "Alertas por SLA e histórico completo."])
    if "cadastr" in l:
        return pack("CRAS — Cadastros SUAS",
                    "Pessoa SUAS, Família, membros e vínculos.",
                    ["Pessoa e Família com consistência.",
                     "Membros clicáveis (drill-down).",
                     "Documentos e anexos por ficha."])
    if "program" in l or "projeto" in l:
        return pack("CRAS — Programas e Projetos",
                    "Criar programas/projetos e inscrever participantes.",
                    ["Programas por público e objetivo.",
                     "Inscrições vinculadas à Pessoa SUAS.",
                     "Lista e gestão de participantes."])
    if "scfv" in l:
        return pack("CRAS — SCFV",
                    "Turmas, inscrição, presença, relatório mensal, evasão e exportação.",
                    ["Chamada/presença por turma.",
                     "Relatório mensal e export CSV.",
                     "Alertas de evasão e pendências."])
    if "ficha" in l:
        return pack("CRAS — Ficha 360°",
                    "Resumo, pendências, timeline/auditoria e anexos (Pessoa e Família).",
                    ["Drill-down por pessoa e família.",
                     "Pendências com contexto e prioridade.",
                     "Documentos/anexos por ficha."])
    if "relat" in l:
        return pack("CRAS — Relatórios (Gestão)",
                    "Consolidado, drill-down e priorização por pendência.",
                    ["Consolidado por tipo de pendência.",
                     "Drill-down abre ficha com highlight.",
                     "Visão por SLA e status."])
    if "triagem" in l or "paif" in l:
        return pack("CRAS — Triagem e PAIF",
                    "Triagem, abertura de caso e acompanhamento PAIF.",
                    ["Registre triagem com rastreabilidade.",
                     "Acompanhe etapas e prazos (SLA).",
                     "Histórico auditável por pessoa/família."])
    if "início" in l or "inicio" in l:
        return pack("CRAS — Início",
                    "Visão geral, alertas, SLA e atalhos do CRAS.",
                    ["Pendências e alertas por SLA.",
                     "Acesso rápido aos fluxos.",
                     "Indicadores do território."])

    # fallback
    return pack(f"CRAS — {label}", "Gestão e atendimento no CRAS com rastreabilidade.", ["Fluxos por etapa.", "Histórico auditável.", "SLA e alertas."])

def ensure_crasapp_inject_header():
    if not CRASAPP.exists():
        raise SystemExit(f"ERRO: não achei {CRASAPP}")

    backup(CRASAPP)
    text = CRASAPP.read_text(encoding="utf-8")

    # 1) garante import
    if "CrasPageHeader" not in text:
        imports = list(re.finditer(r"^import .*$", text, flags=re.M))
        if not imports:
            raise SystemExit("ERRO: não achei imports para inserir CrasPageHeader")
        insert_at = imports[-1].end()
        text = text[:insert_at] + "\nimport CrasPageHeader from \"./components/CrasPageHeader\";\n" + text[insert_at:]

    # 2) descobre variável de aba ativa
    # pega primeira useState("algo") com cara de tab
    m = re.search(r"const\s*\[\s*(\w+)\s*,\s*set\w+\s*\]\s*=\s*useState\(\s*['\"]([^'\"]+)['\"]", text)
    active_var = m.group(1) if m else "activeTab"
    default_key = m.group(2) if m else "inicio"

    # 3) extrai tabs para montar headers (se não achar, usa defaults)
    tabs = infer_tabs(text)
    if not tabs:
        tabs = [
            ("inicio", "Início"),
            ("triagem", "Triagem + PAIF"),
            ("cadunico", "CadÚnico"),
            ("encaminhamentos", "Encaminhamentos"),
            ("casos", "Casos"),
            ("cadastros", "Cadastros"),
            ("programas", "Programas"),
            ("scfv", "SCFV"),
            ("ficha", "Ficha"),
            ("relatorios", "Relatórios"),
        ]

    # garante que default_key exista
    if default_key not in {k for k, _ in tabs}:
        tabs = [(default_key, default_key)] + tabs

    # 4) injeta CRAS_HEADERS dentro do componente (apenas se não existir)
    if "const CRAS_HEADERS" not in text:
        fn = re.search(r"(export\s+default\s+function\s+\w+\s*\([^)]*\)\s*\{)", text)
        if not fn:
            fn = re.search(r"(function\s+\w+\s*\([^)]*\)\s*\{)", text)
        if not fn:
            raise SystemExit("ERRO: não achei declaração da função do CrasApp para inserir CRAS_HEADERS")

        insert_pos = fn.end(1)
        headers_lines = []
        headers_lines.append("\n  const userName = \"Admin Pop Rua\";")
        headers_lines.append("\n  const DEFAULT_KICKER = \"MÓDULO SUAS · INTELIGÊNCIA SOCIAL\";")
        headers_lines.append("\n  const CRAS_HEADERS = {")
        for k, lbl in tabs:
            h = header_for(lbl)
            bullets = ", ".join([f"\"{b}\"" for b in h["bullets"]])
            headers_lines.append(
                f"\n    \"{k}\": {{ kicker: DEFAULT_KICKER, title: \"{h['title']}\", subtitle: \"{h['subtitle']}\", bullets: [{bullets}] }},"
            )
        headers_lines.append("\n  };")
        headers_lines.append("\n")

        text = text[:insert_pos] + "".join(headers_lines) + text[insert_pos:]

    # 5) injeta o componente CrasPageHeader no ponto onde a aba é renderizada
    # procura {renderXxx()} primeiro com Tab/Aba/Content
    render_candidates = [
        r"\{\s*(render[A-Za-z0-9_]*(?:Tab|Aba|Content|Conteudo|View)[A-Za-z0-9_]*)\(\)\s*\}",
        r"\{\s*(render[A-Za-z0-9_]+)\(\)\s*\}",
    ]
    replaced = False
    for pat in render_candidates:
        m = re.search(pat, text)
        if m:
            fn_name = m.group(1)
            repl = (
                "{(\n"
                "  <>\n"
                f"    <CrasPageHeader {{...(CRAS_HEADERS[{active_var}] || CRAS_HEADERS[\"{default_key}\"] || {{}})}} rightTag=\"CRAS\" rightMetaLabel=\"Usuário\" rightMetaValue={{userName}} />\n"
                f"    {{{fn_name}()}}\n"
                "  </>\n"
                ")}"
            )
            text = text[:m.start()] + repl + text[m.end():]
            replaced = True
            break

    if not replaced:
        # fallback: tenta inserir logo após <ErrorBoundary>
        eb = re.search(r"<ErrorBoundary[^>]*>", text)
        if eb:
            ins = (
                "\n      <>\n"
                f"        <CrasPageHeader {{...(CRAS_HEADERS[{active_var}] || CRAS_HEADERS[\"{default_key}\"] || {{}})}} rightTag=\"CRAS\" rightMetaLabel=\"Usuário\" rightMetaValue={{userName}} />\n"
                "      </>\n"
            )
            text = text[:eb.end()] + ins + text[eb.end():]
            replaced = True

    if not replaced:
        raise SystemExit("ERRO: não consegui achar onde a aba é renderizada no CrasApp.jsx (nenhum renderXxx() e nenhum <ErrorBoundary>).")

    CRASAPP.write_text(text, encoding="utf-8")
    return active_var, default_key, tabs

def strip_headers_from_screens():
    # remove CrasPageHeader das telas (para não duplicar)
    touched = []
    for p in sorted((ROOT / "frontend/src").glob("TelaCras*.jsx")):
        t = p.read_text(encoding="utf-8")

        if "CrasPageHeader" not in t and "<CrasPageHeader" not in t:
            continue

        b = backup(p)

        # remove import
        t2 = re.sub(r"^.*CrasPageHeader.*\n", "", t, flags=re.M)

        # remove JSX do header (self-closing ou bloco)
        t2 = re.sub(r"<CrasPageHeader\b[\s\S]*?\/>\s*", "", t2)

        if t2 != t:
            p.write_text(t2, encoding="utf-8")
            touched.append(str(p))
    return touched

def main():
    print("== Patch CRAS Headers ==")
    ensure_header_component()
    active_var, default_key, tabs = ensure_crasapp_inject_header()
    touched = strip_headers_from_screens()

    print(f"- OK: CrasPageHeader.jsx padronizado (modelo único).")
    print(f"- OK: CrasApp.jsx injeta header global.")
    print(f"  > variável de aba ativa detectada: {active_var}")
    print(f"  > chave default detectada: {default_key}")
    print(f"  > abas detectadas no CrasApp: {len(tabs)}")
    if touched:
        print(f"- OK: removi headers duplicados em {len(touched)} telas TelaCras*.jsx:")
        for x in touched[:25]:
            print("  -", x)
        if len(touched) > 25:
            print("  ...")
    else:
        print("- INFO: não encontrei CrasPageHeader dentro das telas TelaCras*.jsx (sem duplicados).")

    print("\nPróximo passo: testar build.\n")

if __name__ == "__main__":
    main()
