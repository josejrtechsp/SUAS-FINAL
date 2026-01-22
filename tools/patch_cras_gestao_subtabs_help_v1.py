#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PATCH_CRAS_GESTAO_SUBTABS_HELP_V1
- Adiciona subtelas (subtabs) para: automacoes, documentos, relatorios
- Define defaults por aba (se mapa existir)
- Garante que TelaCrasAutomacoes/Documentos/Relatorios recebam view + onSetView (se possível)
- Injeta help texts (se mapa existir)
"""

from __future__ import annotations
import sys
from pathlib import Path
import re

def die(msg: str, code: int = 1):
    print(msg, file=sys.stderr)
    sys.exit(code)

def read(p: Path) -> str:
    return p.read_text(encoding="utf-8")

def write(p: Path, s: str):
    p.write_text(s, encoding="utf-8")

def find_object_literal(src: str, name: str):
    """
    Finds the first object literal associated with a variable/const named `name`.
    Returns (start_idx_of_open_brace, end_idx_inclusive_of_close_brace) or None.
    Supports patterns:
      const NAME = { ... };
      const NAME = useMemo(() => ({ ... }), [...]);
    """
    idx = src.find(name)
    if idx < 0:
        return None
    # find first '{' after idx
    brace = src.find("{", idx)
    if brace < 0:
        return None
    depth = 0
    i = brace
    while i < len(src):
        c = src[i]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return (brace, i)
        i += 1
    return None

def add_keys_to_object(src: str, name: str, additions: str) -> str:
    loc = find_object_literal(src, name)
    if not loc:
        return src
    a, b = loc
    body = src[a:b+1]
    # if already has automacoes/documentos/relatorios keys, skip
    if "automacoes:" in body and "documentos:" in body and "relatorios:" in body:
        return src
    # insert before closing }
    ins = b
    # Ensure we don't duplicate each key separately
    add = additions.rstrip()
    # If body already ends with '{\n', handle comma logic simply by prefixing with '\n'
    new = src[:ins] + "\n" + add + "\n" + src[ins:]
    return new

def ensure_component_props(src: str, component: str, view_default: str) -> str:
    """
    Ensure JSX component call includes:
      view={activeSubtab || "<default>"}
      onSetView={setActiveSubtab}
    Only inserts if component call exists and doesn't already include view=.
    """
    # Find occurrences of <Component ... />
    pattern = re.compile(rf"<{component}\b[^>]*\/>", re.M)
    m = pattern.search(src)
    if not m:
        return src
    block = m.group(0)
    if "view=" in block:
        return src
    # Try to insert before '/>'
    insert = f'\n              view={{activeSubtab || "{view_default}"}}\n              onSetView={{setActiveSubtab}}\n'
    new_block = block.replace("/>", insert + "            />")
    return src[:m.start()] + new_block + src[m.end():]

def main():
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    f = root / "frontend" / "src" / "CrasApp.jsx"
    if not f.exists():
        die(f"ERRO: não achei {f}")

    src = read(f)

    # --- 1) Subtabs map: try common names ---
    subtabs_add = """    // --- GESTAO_SUBTABS_V1 ---
    automacoes: [
      { key: "ativas", label: "Regras ativas" },
      { key: "criar", label: "Criar automação" },
      { key: "historico", label: "Histórico" },
      { key: "relatorios", label: "Relatórios" },
    ],
    documentos: [
      { key: "modelos", label: "Modelos" },
      { key: "emitir", label: "Emitir documento" },
      { key: "assinaturas", label: "Assinaturas" },
      { key: "historico", label: "Histórico" },
    ],
    relatorios: [
      { key: "painel", label: "Painel" },
      { key: "exportar", label: "Exportar" },
      { key: "indicadores", label: "Indicadores" },
      { key: "metas", label: "Metas" },
    ],"""

    for name in ["TAB_SUBTABS", "SUBTABS_BY_TAB", "TAB_SUBTABS_MAP", "TAB_VIEWS"]:
        if name in src:
            src2 = add_keys_to_object(src, name, subtabs_add)
            src = src2

    # --- 2) Defaults map (optional) ---
    defaults_add = """    // --- GESTAO_SUBTABS_DEFAULT_V1 ---
    automacoes: "ativas",
    documentos: "modelos",
    relatorios: "painel","""
    for name in ["TAB_SUBTABS_DEFAULT", "SUBTABS_DEFAULT", "DEFAULT_SUBTAB_BY_TAB"]:
        if name in src:
            src = add_keys_to_object(src, name, defaults_add)

    # --- 3) Help map (optional) ---
    help_add = """    // --- GESTAO_HELP_V1 ---
    automacoes: {
      ativas: {
        title: "Guia rápido",
        summary: "Regras automáticas de prazos, alertas e execução por SLA.",
        what: "Use para padronizar cobranças, prazos e rotinas sem depender de planilhas.",
        steps: ["Revise as regras ativas.", "Simule (dry-run) antes de executar.", "Execute e acompanhe o histórico."],
        after: "O sistema registra execuções e reduz pendências por esquecimento.",
      },
      criar: {
        title: "Guia rápido",
        summary: "Crie ou ajuste automações conforme a rotina do CRAS.",
        what: "Você define regra, frequência e alvo (unidade/município).",
        steps: ["Escolha um modelo (seed) ou ajuste uma regra existente.", "Defina frequência e ativação.", "Teste com simulação."],
        after: "As regras passam a rodar e gerar tarefas/alertas automaticamente.",
      },
      historico: {
        title: "Guia rápido",
        summary: "Audite o que foi executado e o que foi gerado.",
        what: "Histórico ajuda coordenação e prestação de contas.",
        steps: ["Abra a última execução.", "Confira itens gerados e falhas.", "Ajuste regras se necessário."],
        after: "Você melhora a qualidade e reduz re-trabalho.",
      },
      relatorios: {
        title: "Guia rápido",
        summary: "Consolide resultado das automações por período.",
        what: "Use para enxergar impacto: vencidas, concluídas, tempo médio.",
        steps: ["Selecione período.", "Compare unidades.", "Exporte CSV para gestão."],
        after: "Gestor ganha visão objetiva de gargalos.",
      },
    },
    documentos: {
      modelos: {
        title: "Guia rápido",
        summary: "Gerencie modelos oficiais (ofício, memorando, relatório etc.).",
        what: "Modelos padronizam a escrita e evitam erro de formatação.",
        steps: ["Escolha um modelo.", "Revise campos obrigatórios.", "Gere uma prévia."],
        after: "A emissão fica rápida e consistente entre equipes.",
      },
      emitir: {
        title: "Guia rápido",
        summary: "Preencha campos e emita o PDF com numeração e histórico.",
        what: "Você garante rastreabilidade e prova documental do atendimento/gestão.",
        steps: ["Selecione o modelo.", "Preencha campos.", "Gere PDF e salve."],
        after: "O documento entra no histórico e pode ser conferido depois.",
      },
      assinaturas: {
        title: "Guia rápido",
        summary: "Assinaturas são campos do documento (cargo, nome e data).",
        what: "Use para padronizar quem assina e como aparece no PDF.",
        steps: ["Selecione o modelo.", "Preencha assinatura.", "Gere prévia para conferir."],
        after: "Evita documento sem responsável ou com cargo errado.",
      },
      historico: {
        title: "Guia rápido",
        summary: "Consulte documentos emitidos e baixe novamente quando precisar.",
        what: "Histórico serve para auditoria e reimpressão rápida.",
        steps: ["Filtre por tipo/período.", "Abra/baixe o PDF.", "Valide número e assunto."],
        after: "Você reduz retrabalho e mantém evidência documental.",
      },
    },
    relatorios: {
      painel: {
        title: "Guia rápido",
        summary: "Visão consolidada de gargalos e volume por área.",
        what: "Painel é a primeira tela para gestor enxergar onde travou.",
        steps: ["Selecione período/unidade.", "Atualize dados.", "Leia alertas."],
        after: "Decisões de equipe e prazo ficam baseadas em dado.",
      },
      exportar: {
        title: "Guia rápido",
        summary: "Exporte dados em CSV/PDF para prestação de contas.",
        what: "Use para planilhas, apresentações e controle interno.",
        steps: ["Atualize a base.", "Escolha o conjunto de dados.", "Exporte."],
        after: "Você compartilha resultados sem depender de prints.",
      },
      indicadores: {
        title: "Guia rápido",
        summary: "Acompanhe série histórica e tendências.",
        what: "Indicadores mostram aumento de demanda e efeito de ações.",
        steps: ["Selecione período maior.", "Compare mês a mês.", "Identifique tendência."],
        after: "Você antecipa problemas e planeja equipe.",
      },
      metas: {
        title: "Guia rápido",
        summary: "Metas organizam foco e SLA por área.",
        what: "Defina metas simples (ex.: reduzir vencidas em X%).",
        steps: ["Defina meta.", "Acompanhe semanalmente.", "Ajuste rotinas."],
        after: "Equipe trabalha com objetivo claro.",
      },
    },"""
    for name in ["TAB_HELP", "TAB_HELP_MAP", "HELP_BY_TAB", "TAB_HELP_TEXTS"]:
        if name in src:
            src = add_keys_to_object(src, name, help_add)

    # --- 4) Ensure view/onSetView props in rendered components ---
    # Only if activeSubtab exists
    if "activeSubtab" in src and "setActiveSubtab" in src:
        src = ensure_component_props(src, "TelaCrasAutomacoes", "ativas")
        src = ensure_component_props(src, "TelaCrasDocumentos", "modelos")
        src = ensure_component_props(src, "TelaCrasRelatorios", "painel")

    write(f, src)

if __name__ == "__main__":
    main()
