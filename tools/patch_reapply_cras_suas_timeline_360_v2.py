#!/usr/bin/env python3
# tools/patch_reapply_cras_suas_timeline_360_v2.py
from __future__ import annotations

from pathlib import Path
import re
import sys
from datetime import datetime

NEW_CASOS_BLOCK = """  // ✅ Integração SUAS (BACKEND): devolutivas/cobranças aparecem no caso (histórico + metrô)
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

SUAS_HELPER = """
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

def _bak(path: Path, s: str) -> None:
    tag = datetime.now().strftime("%Y%m%d_%H%M%S")
    path.with_suffix(path.suffix + f".bak_{tag}").write_text(s, encoding="utf-8")

def patch_casos(path: Path) -> bool:
    s0 = path.read_text(encoding="utf-8")
    s = s0
    changed = False

    s2 = re.sub(r'\nimport\s+\{\s*getSuasUpdatesForCase\s*\}\s+from\s+"\.\/domain\/suasEncaminhamentosStore\.js";\s*\n', "\n", s)
    if s2 != s:
        s = s2
        changed = True

    if "Integração SUAS (BACKEND)" in s:
        if changed:
            _bak(path, s0); path.write_text(s, encoding="utf-8")
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

    _bak(path, s0)
    path.write_text(s, encoding="utf-8")
    return changed

def _insert_after(pattern: str, s: str, insert: str) -> tuple[str, bool]:
    m = re.search(pattern, s)
    if not m:
        return s, False
    pos = m.end()
    return s[:pos] + insert + s[pos:], True

def patch_360(path: Path, kind: str) -> bool:
    s0 = path.read_text(encoding="utf-8")
    s = s0
    if "loadSuas360" in s:
        return False

    # state insertion
    if 'const [suas, setSuas]' not in s:
        if 'const [data, setData] = useState(null);' not in s:
            raise RuntimeError(f"Não achei 'const [data, setData] = useState(null);' em {path}")
        s = s.replace(
            '  const [data, setData] = useState(null);\n',
            '  const [data, setData] = useState(null);\n\n  // Encaminhamentos SUAS (banco): pendências e timeline entram no 360\n  const [suas, setSuas] = useState({ pendencias: [], timeline: [] });\n'
        )

    alvo = "pessoaSel" if kind == "pessoa" else "famSel"
    filtro = "pessoa_id" if kind == "pessoa" else "familia_id"

    # insert helper+loader after loadFicha() block
    m = re.search(r"async function loadFicha\(\)[\s\S]*?\n  }\n", s)
    if not m:
        raise RuntimeError(f"Não achei bloco loadFicha() em {path}")
    insert_pos = m.end()

    loader = (
        "\n" + SUAS_HELPER + "\n" +
        "  async function loadSuas360() {\n"
        f"    const alvo = {alvo};\n"
        "    if (!alvo) { setSuas({ pendencias: [], timeline: [] }); return; }\n"
        "    try {\n"
        "      const params = new URLSearchParams();\n"
        "      params.set(\"modulo\", \"CRAS\");\n"
        "      params.set(\"view\", \"all\");\n"
        "      params.set(\"include_events\", \"0\");\n"
        f"      params.set(\"{filtro}\", String(alvo));\n"
        "      try {\n"
        "        const fid = data?.familia?.id;\n"
        f"        if (fid && \"{kind}\" === \"pessoa\") params.set(\"familia_id\", String(fid));\n"
        "      } catch {}\n"
        "      const r = await apiFetch(`${apiBase}/suas/encaminhamentos?${params.toString()}`);\n"
        "      if (!r.ok) throw new Error(await r.text());\n"
        "      const j = await r.json();\n"
        "      const arr = Array.isArray(j) ? j : [];\n"
        "      const vencidos = arr.filter(_isSuasVencido).length;\n"
        "      const abertos = arr.filter(_isSuasAberto).length;\n"
        "      const pend = [];\n"
        "      if (vencidos) {\n"
        "        pend.push({ tipo: \"suas_sem_devolutiva\", gravidade: vencidos >= 2 ? \"alta\" : \"media\", referencia: \"Encaminhamentos SUAS\", detalhe: `${vencidos} encaminhamento(s) com prazo vencido e sem contrarreferência.`, sugerido: \"Cobrar devolutiva, registrar retorno e concluir quando resolvido.\" });\n"
        "      } else if (abertos) {\n"
        "        pend.push({ tipo: \"suas_abertos\", gravidade: \"media\", referencia: \"Encaminhamentos SUAS\", detalhe: `${abertos} encaminhamento(s) SUAS em aberto.`, sugerido: \"Acompanhar status e registrar devolutiva quando houver.\" });\n"
        "      }\n"
        "      const tl = [];\n"
        "      arr.slice(0, 120).forEach((e) => {\n"
        "        const origem = String(e?.origem_modulo || \"\").toUpperCase();\n"
        "        const destino = String(e?.destino_modulo || \"\").toUpperCase();\n"
        "        const other = origem === \"CRAS\" ? (destino || \"SUAS\") : (origem || \"SUAS\");\n"
        "        const when = e?.retorno_em || e?.cobranca_ultimo_em || e?.status_em || e?.atualizado_em || e?.criado_em || null;\n"
        "        const st = String(e?.status || \"\").toUpperCase();\n"
        "        const titulo = `SUAS · ${other} · ${st}`;\n"
        "        const detalhe = [\n"
        "          e?.assunto ? `Assunto: ${e.assunto}` : null,\n"
        "          e?.prazo_retorno ? `Prazo: ${e.prazo_retorno}` : null,\n"
        "          e?.motivo ? `Motivo: ${String(e.motivo).slice(0, 380)}` : null,\n"
        "          e?.retorno_texto ? `Retorno: ${String(e.retorno_texto).slice(0, 380)}` : null,\n"
        "          e?.cobranca_ultimo_texto ? `Cobrança: ${String(e.cobranca_ultimo_texto).slice(0, 240)}` : null,\n"
        "        ].filter(Boolean).join(\" · \");\n"
        "        tl.push({ tipo: \"suas_encaminhamento\", quando: when, titulo, autor: e?.atualizado_por_nome || e?.criado_por_nome || null, detalhe, caso_id: e?.origem_caso_id || e?.destino_caso_id || null });\n"
        "      });\n"
        "      tl.sort((a,b) => (b?.quando ? new Date(b.quando).getTime():0) - (a?.quando ? new Date(a.quando).getTime():0));\n"
        "      setSuas({ pendencias: pend, timeline: tl.slice(0, 260) });\n"
        "    } catch (e) {\n"
        "      console.error(e);\n"
        "      setSuas({ pendencias: [], timeline: [] });\n"
        "    }\n"
        "  }\n"
    )

    s = s[:insert_pos] + loader + s[insert_pos:]

    # hook effect insertion: best effort
    if "loadSuas360();" not in s:
        pass

    # if there is a loadFicha useEffect, append another useEffect after it
    # Try pattern: useEffect(() => { loadFicha(); ... }, [<alvo>]);
    pat = r"useEffect\(\(\)\s*=>\s*\{\s*loadFicha\(\)\s*;\s*.*?\}\s*,\s*\[\s*" + re.escape(alvo) + r".*?\]\s*\)\s*;\s*// eslint-disable-line"
    m2 = re.search(pat, s, flags=re.S)
    if m2 and "loadSuas360();" not in s[m2.end():m2.end()+250]:
        ins = "\n  useEffect(() => { loadSuas360(); }, [" + alvo + (", data?.familia?.id" if kind=="pessoa" else "") + "]); // eslint-disable-line\n"
        s = s[:m2.end()] + ins + s[m2.end():]
    else:
        # fallback: add near top after first useEffect occurrence
        s, _ = _insert_after(r"useEffect\(", s, "")

    # merge pend and tl (replace first occurrences)
    s = re.sub(
        r"\n\s*const\s+pend\s*=\s*data\?\.\s*pendencias\s*\|\|\s*\[\]\s*;\s*\n",
        "\n  const pend = useMemo(() => {\n    const a = Array.isArray(suas?.pendencias) ? suas.pendencias : [];\n    const b = Array.isArray(data?.pendencias) ? data.pendencias : (data?.pendencias || []);\n    return [...a, ...b];\n  }, [suas, data]);\n",
        s,
        count=1
    )
    s = re.sub(
        r"\n\s*const\s+tl\s*=\s*data\?\.\s*timeline\s*\|\|\s*\[\]\s*;\s*\n",
        "\n  const tl = useMemo(() => {\n    const a = Array.isArray(suas?.timeline) ? suas.timeline : [];\n    const b = Array.isArray(data?.timeline) ? data.timeline : (data?.timeline || []);\n    const all = [...a, ...b];\n    all.sort((x,y)=>{\n      const tx = x?.quando ? new Date(x.quando).getTime() : 0;\n      const ty = y?.quando ? new Date(y.quando).getTime() : 0;\n      return ty - tx;\n    });\n    return all;\n  }, [suas, data]);\n",
        s,
        count=1
    )

    _bak(path, s0)
    path.write_text(s, encoding="utf-8")
    return True

def main() -> int:
    root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(".").resolve()

    p_casos = root / "frontend/src/TelaCrasCasos.jsx"
    p_pessoa = root / "frontend/src/TelaCrasFichaPessoa360.jsx"
    p_familia = root / "frontend/src/TelaCrasFichaFamilia360.jsx"

    for p in (p_casos, p_pessoa, p_familia):
        if not p.exists():
            print("ERRO: arquivo não encontrado:", p)
            return 2

    out = {}
    try:
        out["casos"] = patch_casos(p_casos)
        out["pessoa360"] = patch_360(p_pessoa, "pessoa")
        out["familia360"] = patch_360(p_familia, "familia")
    except Exception as e:
        print("ERRO:", str(e))
        return 2

    print("OK:", out)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
