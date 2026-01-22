#!/usr/bin/env python3
# tools/patch_cras_suas_timeline_360_v1.py
# Fix: patcher idempotente (sem regex quebrando com chaves) para:
# - Casos: trocar integração SUAS localStorage por backend /suas/encaminhamentos
# - Ficha Pessoa/Família 360: carregar pendências e timeline SUAS do backend e mesclar no 360

from __future__ import annotations

from pathlib import Path
import re
import sys

NEW_CASOS_BLOCK = r"""
  // ✅ Integração SUAS (BACKEND): devolutivas/cobranças aparecem no caso (histórico + metrô)
  const [suasUI, setSuasUI] = useState({
    timeline: [],
    metroRegistros: [],
    stats: { total: 0, abertos: 0, vencidos: 0 },
  });

  function _ymdToTs(ymd) {
    if (!ymd) return 0;
    try {
      const d = new Date(String(ymd) + "T00:00:00");
      const t = d.getTime();
      return Number.isNaN(t) ? 0 : t;
    } catch {
      return 0;
    }
  }

  function _isEncAberto(enc) {
    const st = String(enc?.status || "").toLowerCase();
    return st && st !== "concluido" && st !== "concluído" && st !== "cancelado";
  }

  function _isEncVencido(enc) {
    if (!_isEncAberto(enc)) return false;
    const st = String(enc?.status || "").toLowerCase();
    if (st === "retorno_enviado") return false;
    const pr = enc?.prazo_retorno || null;
    const ts = _ymdToTs(pr);
    if (!ts) return false;
    const hoje = _ymdToTs(new Date().toISOString().slice(0, 10));
    return ts < hoje;
  }

  function _buildSuasUI(encs) {
    const list = Array.isArray(encs) ? encs : [];

    const timeline = [];
    const metroRegistros = [];

    const total = list.length;
    const abertos = list.filter(_isEncAberto).length;
    const vencidos = list.filter(_isEncVencido).length;

    list.forEach((enc) => {
      const id = enc?.id;
      const origem = String(enc?.origem_modulo || "").toUpperCase();
      const destino = String(enc?.destino_modulo || "").toUpperCase();
      const other = origem === "CRAS" ? (destino || "SUAS") : (origem || "SUAS");

      const assunto = String(enc?.assunto || "Encaminhamento SUAS").trim();
      const pr = enc?.prazo_retorno ? ` · Prazo: ${enc.prazo_retorno}` : "";
      const st = String(enc?.status || "").toLowerCase();
      const stLabel = st ? st.toUpperCase() : "—";

      const evs = Array.isArray(enc?.timeline) ? enc.timeline : [];
      if (evs.length) {
        evs.forEach((ev) => {
          const et = String(ev?.tipo || "").toLowerCase();
          const when = ev?.em || enc?.status_em || enc?.atualizado_em || enc?.criado_em || null;
          const por = ev?.por_nome || enc?.atualizado_por_nome || enc?.criado_por_nome || "—";

          let tipo = "suas_status";
          let texto = `SUAS · ${other} · ${stLabel}`;
          let detalhe = ev?.detalhe || "";

          if (et === "cobranca") {
            tipo = "suas_cobranca";
            texto = `SUAS · Cobrança (${other})`;
            detalhe = ev?.detalhe || enc?.cobranca_ultimo_texto || "";
          } else if (et === "retorno" || et === "retorno_enviado") {
            tipo = "suas_retorno";
            texto = `SUAS · Contrarreferência (${other})`;
            detalhe = ev?.detalhe || enc?.retorno_texto || enc?.retorno_detalhe || "";
          } else if (et) {
            texto = `SUAS · ${other} · ${et.toUpperCase()}`;
          }

          const tlItem = {
            id: `suas_${id || "x"}_${ev?.id || et}_${String(when || "").slice(-12)}`,
            tipo,
            texto: `${texto}${assunto ? ` · ${assunto}` : ""}${pr}`,
            detalhe: detalhe || "",
            por,
            criado_em: when,
          };
          timeline.push(tlItem);

          metroRegistros.push({
            id: tlItem.id,
            responsavel_nome: por,
            data_hora: when,
            obs: `${tlItem.texto}${tlItem.detalhe ? " — " + String(tlItem.detalhe).slice(0, 220) : ""}`,
          });
        });
      } else {
        const when = enc?.status_em || enc?.atualizado_em || enc?.criado_em || null;
        const por = enc?.atualizado_por_nome || enc?.criado_por_nome || "—";
        timeline.push({
          id: `suas_${id || "x"}_${st || "status"}`,
          tipo: "suas_status",
          texto: `SUAS · ${other} · ${stLabel}${assunto ? ` · ${assunto}` : ""}${pr}`,
          detalhe: enc?.motivo || "",
          por,
          criado_em: when,
        });
      }
    });

    timeline.sort((a, b) => {
      const ta = a?.criado_em ? new Date(a.criado_em).getTime() : 0;
      const tb = b?.criado_em ? new Date(b.criado_em).getTime() : 0;
      return tb - ta;
    });

    metroRegistros.sort((a, b) => {
      const ta = a?.data_hora ? new Date(a.data_hora).getTime() : 0;
      const tb = b?.data_hora ? new Date(b.data_hora).getTime() : 0;
      return tb - ta;
    });

    return { timeline: timeline.slice(0, 120), metroRegistros: metroRegistros.slice(0, 80), stats: { total, abertos, vencidos } };
  }

  async function loadSuasForCase(casoId) {
    if (!casoId) return setSuasUI({ timeline: [], metroRegistros: [], stats: { total: 0, abertos: 0, vencidos: 0 } });
    try {
      const params = new URLSearchParams();
      params.set("modulo", "CRAS");
      params.set("view", "all");
      params.set("include_events", "1");
      params.set("caso_id", String(casoId));
      const r = await apiFetch(`${apiBase}/suas/encaminhamentos?${params.toString()}`);
      if (!r.ok) throw new Error(await r.text());
      const j = await r.json();
      setSuasUI(_buildSuasUI(Array.isArray(j) ? j : []));
    } catch (e) {
      console.error(e);
      setSuasUI({ timeline: [], metroRegistros: [], stats: { total: 0, abertos: 0, vencidos: 0 } });
    }
  }

  useEffect(() => {
    if (!sel?.id) {
      setSuasUI({ timeline: [], metroRegistros: [], stats: { total: 0, abertos: 0, vencidos: 0 } });
      return;
    }
    loadSuasForCase(sel.id);
    // eslint-disable-next-line
  }, [sel?.id]);

"""

def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8")

def _write(p: Path, s: str) -> None:
    p.write_text(s, encoding="utf-8")

def patch_casos(p: Path) -> bool:
    s = _read(p)
    changed = False

    # remove store import if present
    s2 = re.sub(r'\nimport\s+\{\s*getSuasUpdatesForCase\s*\}\s+from\s+"\.\/domain\/suasEncaminhamentosStore\.js";\s*\n', "\n", s)
    if s2 != s:
        s = s2
        changed = True

    if "Integração SUAS (BACKEND)" in s:
        # already patched
        _write(p, s)
        return changed

    start = s.find("// ✅ Integração SUAS (localStorage)")
    if start < 0:
        raise RuntimeError("Marker não encontrado em TelaCrasCasos.jsx: // ✅ Integração SUAS (localStorage)")

    m_end = re.search(r"\n\s*async function loadEtapas\(\)", s[start:])
    if not m_end:
        raise RuntimeError("Não encontrei 'async function loadEtapas()' após o marker em TelaCrasCasos.jsx")

    end = start + m_end.start()
    s = s[:start] + NEW_CASOS_BLOCK + s[end:]
    changed = True

    # add badges (best-effort)
    needle = '<div className="texto-suave">Status: <strong>{sel.status}</strong> · Tipo: <strong>{sel.tipo_caso}</strong></div>'
    if needle in s and "SUAS sem devolutiva" not in s:
        s = s.replace(needle, needle + """
                  <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginTop: 6 }}>
                    {suasUI?.stats?.vencidos ? (
                      <span style={badgeStyle("vermelho")}>SUAS sem devolutiva: {suasUI.stats.vencidos}</span>
                    ) : null}
                    {suasUI?.stats?.abertos ? (
                      <span style={badgeStyle("laranja")}>SUAS abertos: {suasUI.stats.abertos}</span>
                    ) : null}
                  </div>""")
        changed = True

    _write(p, s)
    return changed

SUAS_360_HELPER = r"""
  function _isSuasAberto(enc) {
    const st = String(enc?.status || "").toLowerCase();
    return st && st !== "concluido" && st !== "concluído" && st !== "cancelado";
  }
  function _isSuasVencido(enc) {
    if (!_isSuasAberto(enc)) return false;
    const st = String(enc?.status || "").toLowerCase();
    if (st === "retorno_enviado") return false;
    const pr = enc?.prazo_retorno;
    if (!pr) return false;
    try {
      const prazo = new Date(String(pr) + "T00:00:00").getTime();
      const hoje = new Date(new Date().toISOString().slice(0,10) + "T00:00:00").getTime();
      return prazo < hoje;
    } catch { return false; }
  }
"""

def patch_360(p: Path, kind: str) -> bool:
    s = _read(p)
    if "loadSuas360" in s:
        return False

    changed = False

    # ensure state
    if 'const [suas, setSuas]' not in s:
        s2 = s.replace(
            '  const [data, setData] = useState(null);\n',
            '  const [data, setData] = useState(null);\n\n  // Encaminhamentos SUAS (banco): pendências e timeline entram no 360\n  const [suas, setSuas] = useState({ pendencias: [], timeline: [] });\n'
        )
        if s2 == s:
            raise RuntimeError(f"Não achei 'const [data, setData] = useState(null);' em {p}")
        s = s2
        changed = True

    # insert helper + loader after loadFicha()
    m = re.search(r"async function loadFicha\(\)[\s\S]*?\n  }\n", s)
    if not m:
        raise RuntimeError(f"Não achei bloco loadFicha() em {p}")

    insert_pos = m.end()

    alvo = "pessoaSel" if kind == "pessoa" else "famSel"
    filtro = "pessoa_id" if kind == "pessoa" else "familia_id"

    loader = f"""
{SUAS_360_HELPER}
  async function loadSuas360() {{
    const alvo = {alvo};
    if (!alvo) {{ setSuas({{ pendencias: [], timeline: [] }}); return; }}
    try {{
      const params = new URLSearchParams();
      params.set("modulo", "CRAS");
      params.set("view", "all");
      params.set("include_events", "0");
      params.set("{filtro}", String(alvo));
      // no Pessoa360, se tiver familia carregada, soma também
      try {{
        const fid = data?.familia?.id;
        if (fid && "{kind}" === "pessoa") params.set("familia_id", String(fid));
      }} catch {{}}
      const r = await apiFetch(`${{apiBase}}/suas/encaminhamentos?${{params.toString()}}`);
      if (!r.ok) throw new Error(await r.text());
      const j = await r.json();
      const arr = Array.isArray(j) ? j : [];

      const vencidos = arr.filter(_isSuasVencido).length;
      const abertos = arr.filter(_isSuasAberto).length;

      const pend = [];
      if (vencidos) {{
        pend.push({{
          tipo: "suas_sem_devolutiva",
          gravidade: vencidos >= 2 ? "alta" : "media",
          referencia: "Encaminhamentos SUAS",
          detalhe: `${{vencidos}} encaminhamento(s) com prazo vencido e sem contrarreferência.`,
          sugerido: "Cobrar devolutiva, registrar retorno e concluir quando resolvido.",
        }});
      }} else if (abertos) {{
        pend.push({{
          tipo: "suas_abertos",
          gravidade: "media",
          referencia: "Encaminhamentos SUAS",
          detalhe: `${{abertos}} encaminhamento(s) SUAS em aberto.`,
          sugerido: "Acompanhar status e registrar devolutiva quando houver.",
        }});
      }}

      const tl = [];
      arr.slice(0, 80).forEach((e) => {{
        const origem = String(e?.origem_modulo || "").toUpperCase();
        const destino = String(e?.destino_modulo || "").toUpperCase();
        const other = origem === "CRAS" ? (destino || "SUAS") : (origem || "SUAS");
        const when = e?.retorno_em || e?.cobranca_ultimo_em || e?.status_em || e?.atualizado_em || e?.criado_em || null;
        const st = String(e?.status || "").toUpperCase();
        const titulo = `SUAS · ${{other}} · ${{st}}`;
        const detalhe = [
          e?.assunto ? `Assunto: ${{e.assunto}}` : null,
          e?.prazo_retorno ? `Prazo: ${{e.prazo_retorno}}` : null,
          e?.motivo ? `Motivo: ${{String(e.motivo).slice(0, 380)}}` : null,
          e?.retorno_texto ? `Retorno: ${{String(e.retorno_texto).slice(0, 380)}}` : null,
          e?.cobranca_ultimo_texto ? `Cobrança: ${{String(e.cobranca_ultimo_texto).slice(0, 240)}}` : null,
        ].filter(Boolean).join(" · ");
        tl.push({{ tipo: "suas_encaminhamento", quando: when, titulo, autor: e?.atualizado_por_nome || e?.criado_por_nome || null, detalhe, caso_id: e?.origem_caso_id || e?.destino_caso_id || null }});
      }});
      tl.sort((a,b) => (b?.quando ? new Date(b.quando).getTime():0) - (a?.quando ? new Date(a.quando).getTime():0));
      setSuas({{ pendencias: pend, timeline: tl.slice(0, 200) }});
    }} catch (e) {{
      console.error(e);
      setSuas({{ pendencias: [], timeline: [] }});
    }}
  }}
"""

    s = s[:insert_pos] + loader + s[insert_pos:]
    changed = True

    # add useEffect call (best effort)
    if "loadSuas360();" not in s:
        # likely already exists by insertion below, but still
        pass

    # After loadFicha effect, add effect for suas
    s2 = re.sub(
        r'(useEffect\(\(\)\s*=>\s*\{\s*loadFicha\(\);\s*\}\s*,\s*\[\s*' + re.escape(alvo) + r'\s*\]\s*\);\s*// eslint-disable-line\s*\n)',
        r'\1  useEffect(() => { loadSuas360(); }, [' + alvo + r', data?.familia?.id]); // eslint-disable-line\n',
        s,
        count=1
    )
    if s2 == s:
        # fallback: simple insertion after first occurrence of loadFicha effect line
        s2 = s.replace("loadFicha();", "loadFicha();\n    // loadSuas360 será chamado em effect separado", 1)
    s = s2

    # Replace pend/tl definitions with merged memos (minimal invasive)
    # pend:
    s = re.sub(
        r'\n\s*const\s+pend\s*=\s*data\?\.\s*pendencias\s*\|\|\s*\[\]\s*;\s*\n',
        '\n  const pend = useMemo(() => {\n    const a = Array.isArray(suas?.pendencias) ? suas.pendencias : [];\n    const b = Array.isArray(data?.pendencias) ? data.pendencias : (data?.pendencias || []);\n    return [...a, ...b];\n  }, [suas, data]);\n',
        s,
        count=1
    )
    # tl:
    s = re.sub(
        r'\n\s*const\s+tl\s*=\s*data\?\.\s*timeline\s*\|\|\s*\[\]\s*;\s*\n',
        '\n  const tl = useMemo(() => {\n    const a = Array.isArray(suas?.timeline) ? suas.timeline : [];\n    const b = Array.isArray(data?.timeline) ? data.timeline : (data?.timeline || []);\n    const all = [...a, ...b];\n    all.sort((x,y)=>{\n      const tx = x?.quando ? new Date(x.quando).getTime() : 0;\n      const ty = y?.quando ? new Date(y.quando).getTime() : 0;\n      return ty - tx;\n    });\n    return all;\n  }, [suas, data]);\n',
        s,
        count=1
    )

    _write(p, s)
    return changed

def main() -> int:
    root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(".").resolve()

    p_casos = root / "frontend/src/TelaCrasCasos.jsx"
    p_pessoa = root / "frontend/src/TelaCrasFichaPessoa360.jsx"
    p_familia = root / "frontend/src/TelaCrasFichaFamilia360.jsx"

    for p in (p_casos, p_pessoa, p_familia):
        if not p.exists():
            print("ERRO: arquivo não encontrado:", p)
            return 2

    changed = {}
    try:
        changed["casos"] = patch_casos(p_casos)
        changed["pessoa360"] = patch_360(p_pessoa, "pessoa")
        changed["familia360"] = patch_360(p_familia, "familia")
    except Exception as e:
        print("ERRO:", str(e))
        return 2

    print("OK:", changed)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
