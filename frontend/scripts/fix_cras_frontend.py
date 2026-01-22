import re
from pathlib import Path
from datetime import datetime

ROOT = Path.cwd()
SRC = ROOT / "frontend/src"
CRASAPP = SRC / "CrasApp.jsx"
HEADER = SRC / "components" / "CrasPageHeader.jsx"
ts = datetime.now().strftime("%Y%m%d_%H%M%S")

def backup(p: Path):
    b = p.with_suffix(p.suffix + f".bak_{ts}")
    b.write_text(p.read_text(encoding="utf-8"), encoding="utf-8")
    return b

def write_header_model():
    # garante que o header único existe (modelo do print)
    HEADER.parent.mkdir(parents=True, exist_ok=True)
    if HEADER.exists():
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

def fix_common_jsx(p: Path) -> int:
    txt = p.read_text(encoding="utf-8").splitlines(True)
    out = []
    changed = 0

    # remove props soltas (kicker/title/subtitle/tips/badge/rightText) que ficaram fora de tag
    prop_re = re.compile(r'^\s*(kicker|title|subtitle|tips|badge|rightText)\s*=')
    i = 0
    while i < len(txt):
        line = txt[i]

        # remove linha solta "/>"
        if line.strip() == "/>":
            changed += 1
            i += 1
            continue

        # remove “bloco de props soltas” até achar um "/>"
        if prop_re.match(line):
            changed += 1
            i += 1
            while i < len(txt) and "/>" not in txt[i]:
                i += 1
            if i < len(txt) and "/>" in txt[i]:
                i += 1
            continue

        out.append(line)
        i += 1

    s = "".join(out)

    # fecha LinhaMetro se estiver aberto e não tiver />
    # padrão que já apareceu no seu caso: "<LinhaMetro ... onRefresh=... ) : ("
    s2 = re.sub(
        r'(<LinhaMetro[\s\S]*?onRefresh=\{\(\)\s*=>\s*carregarLinhaMetro\([^)]*\)\}\s*)\)\s*:\s*\(',
        r'\1/>\n                  ) : (',
        s,
        flags=re.M,
    )
    if s2 != s:
        s = s2
        changed += 1

    # troca ternário simples por && (reduz chance de parser quebrar por : null)
    s2 = re.sub(r'\{(\w+)\s*\?\s*<div\b', r'{\1 && <div', s)
    if s2 != s:
        s = s2
        changed += 1
    # se virou "{erro && <div ... : null}" em algum lugar, remove ": null"
    s2 = re.sub(r'\}\s*:\s*null\}', r'}', s)
    if s2 != s:
        s = s2
        changed += 1

    if changed:
        backup(p)
        p.write_text(s, encoding="utf-8")
    return changed

def normalize_headers_in_screens():
    # remove cabeçalho interno (PageHero/CrasPageHeader) das telas CRAS
    touched = []
    for p in sorted(SRC.glob("TelaCras*.jsx")):
        t = p.read_text(encoding="utf-8")
        original = t

        # remove imports de PageHero ou CrasPageHeader
        t = re.sub(r"^.*\bPageHero\b.*\n", "", t, flags=re.M)
        t = re.sub(r"^.*\bCrasPageHeader\b.*\n", "", t, flags=re.M)

        # remove <PageHero .../> e <PageHero>...</PageHero>
        t = re.sub(r"\n\s*<PageHero\b[\s\S]*?\/>\s*\n", "\n", t)
        t = re.sub(r"\n\s*<PageHero\b[\s\S]*?>[\s\S]*?<\/PageHero>\s*\n", "\n", t)

        # remove <CrasPageHeader .../> se existir
        t = re.sub(r"\n\s*<CrasPageHeader\b[\s\S]*?\/>\s*\n", "\n", t)

        # limpa múltiplas linhas vazias
        t = re.sub(r"\n{3,}", "\n\n", t)

        if t != original:
            backup(p)
            p.write_text(t, encoding="utf-8")
            touched.append(p.name)
    return touched

def inject_header_in_crasapp():
    if not CRASAPP.exists():
        raise SystemExit(f"Não achei {CRASAPP}")

    text = CRASAPP.read_text(encoding="utf-8")
    original = text

    # garante import
    if "CrasPageHeader" not in text:
        text = re.sub(
            r"(\nimport .*?;\n)(?!.*CrasPageHeader)",
            r"\1import CrasPageHeader from \"./components/CrasPageHeader\";\n",
            text,
            count=1,
            flags=re.S,
        )

    # tenta detectar nome do estado da aba
    m = re.search(r"const\s*\[\s*(\w+)\s*,\s*set\w+\s*\]\s*=\s*useState\(", text)
    active_var = m.group(1) if m else "aba"

    # insere mapa de cabeçalhos se não existir
    if "const CRAS_HEADERS" not in text:
        insert = """
  const userName = usuarioLogado?.nome || "—";
  const unidadeAtiva = unidade || unidadeAtiva || "—";
  const DEFAULT_KICKER = "MÓDULO CRAS · INTELIGÊNCIA SOCIAL";
  const CRAS_HEADERS = {
    inicio: { kicker: DEFAULT_KICKER, title: "CRAS — Início", subtitle: "Painel do equipamento, SLA e pendências.", bullets: ["Pendências e alertas por prazo.", "Fluxos críticos do dia.", "Visão por equipe e território."] },
    triagem: { kicker: DEFAULT_KICKER, title: "CRAS — Triagem + PAIF", subtitle: "Triagem, PAIF por etapas e checklist.", bullets: ["Fila do dia por unidade.", "Plano/etapas e prazos.", "Histórico auditável."] },
    cadunico: { kicker: DEFAULT_KICKER, title: "CRAS — CadÚnico", subtitle: "Pré-cadastro, agendamento e finalização.", bullets: ["Status e histórico.", "Não compareceu e reagendamento.", "Pendências por prazo."] },
    encaminhamentos: { kicker: DEFAULT_KICKER, title: "CRAS — Encaminhamentos", subtitle: "Encaminhar e controlar devolutiva.", bullets: ["Sem devolutiva = atraso por prazo.", "Cobrança com evidência.", "Timeline do item."] },
    casos: { kicker: DEFAULT_KICKER, title: "CRAS — Casos", subtitle: "Etapas, validação, SLA e auditoria.", bullets: ["Linha do metrô por etapa.", "Validação de recebimento.", "Alertas e histórico."] },
    cadastros: { kicker: DEFAULT_KICKER, title: "CRAS — Cadastros", subtitle: "Pessoa + Família (base da rede).", bullets: ["Pessoa → família → membros.", "Vínculos para casos e programas.", "Documentos e anexos."] },
    programas: { kicker: DEFAULT_KICKER, title: "CRAS — Programas e Projetos", subtitle: "Cadastro, inscrição e participação.", bullets: ["Público-alvo e critérios.", "Inscrições por unidade.", "Acompanhamento por usuário."] },
    scfv: { kicker: DEFAULT_KICKER, title: "CRAS — SCFV", subtitle: "Turmas, presença, relatório e evasão.", bullets: ["Chamada simples.", "Relatório mensal.", "Alertas automáticos."] },
    ficha: { kicker: DEFAULT_KICKER, title: "CRAS — Ficha 360°", subtitle: "Tudo do usuário/família num lugar só.", bullets: ["Pendências com contexto.", "Timeline/auditoria.", "Programas/SCFV/encaminhamentos."] },
    relatorios: { kicker: DEFAULT_KICKER, title: "CRAS — Relatórios", subtitle: "Consolidado e drill-down por pendência.", bullets: ["Gestão por SLA.", "Priorização.", "Drill-down abre ficha."] },
  };
"""
        text = re.sub(r"(export\s+default\s+function\s+\w+\s*\([^)]*\)\s*\{)", r"\1" + insert, text, count=1)

    # injeta CrasPageHeader no render (um único ponto)
    if "CRAS_HEADERS" in text and "<CrasPageHeader" not in text:
        # tenta achar um {renderXxx()} para envolver
        m = re.search(r"\{\s*(render\w+)\(\)\s*\}", text)
        if m:
            fn = m.group(1)
            wrapped = (
                "{(\n"
                "  <>\n"
                f"    <CrasPageHeader {{...(CRAS_HEADERS[{active_var}] || CRAS_HEADERS.inicio)}} rightTag=\"CRAS\" rightMetaLabel=\"Unidade\" rightMetaValue={unidadeAtiva} />\n"
                f"    {{{fn}()}}\n"
                "  </>\n"
                ")}"
            )
            text = text[:m.start()] + wrapped + text[m.end():]
        else:
            # fallback: insere logo após ErrorBoundary
            eb = re.search(r"<ErrorBoundary[^>]*>", text)
            if eb:
                ins = (
                    "\n      <>\n"
                    f"        <CrasPageHeader {{...(CRAS_HEADERS[{active_var}] || CRAS_HEADERS.inicio)}} rightTag=\"CRAS\" rightMetaLabel=\"Unidade\" rightMetaValue={unidadeAtiva} />\n"
                    "      </>\n"
                )
                text = text[:eb.end()] + ins + text[eb.end():]

    if text != original:
        backup(CRASAPP)
        CRASAPP.write_text(text, encoding="utf-8")

def main():
    print("== Fix CRAS Frontend ==")
    write_header_model()

    changed = 0
    # corrige TelaCras*.jsx + CrasApp.jsx
    for p in sorted(SRC.glob("TelaCras*.jsx")):
        changed += fix_common_jsx(p)
    changed += fix_common_jsx(CRASAPP)

    touched = normalize_headers_in_screens()
    inject_header_in_crasapp()

    print(f"- OK: header model em {HEADER}")
    print(f"- OK: fixes aplicados (arquivos com mudanças): {changed}")
    print(f"- OK: removi headers internos em {len(touched)} telas: {touched[:10]}{'...' if len(touched)>10 else ''}")
    print("Próximo: npm run build / npm run dev")

if __name__ == "__main__":
    main()
