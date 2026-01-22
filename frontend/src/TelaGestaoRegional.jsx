import { useMemo } from "react";

export default function TelaGestaoRegional({ perfilAtivo, municipios, casos }) {
  const perfil = String(perfilAtivo || "").toLowerCase();
  const pode = perfil === "admin" || perfil === "gestor_consorcio";

  const getNomeMuni = (id) => {
    const arr = Array.isArray(municipios) ? municipios : [];
    for (let i = 0; i < arr.length; i++) {
      const x = arr[i] || {};
      const mid = Number(x.id);
      if (Number.isFinite(mid) && mid === id) {
        // evita optional chaining / nullish para não dar bug em parsers
        const n = x.nome ? String(x.nome) : (x.nome_municipio ? String(x.nome_municipio) : "Município");
        return n;
      }
    }
    return "Município";
  };

  const rows = useMemo(() => {
    const acc = new Map();
    const arr = Array.isArray(casos) ? casos : [];
    for (let i = 0; i < arr.length; i++) {
      const c = arr[i] || {};
      const mid = Number(c.municipio_id);
      if (!Number.isFinite(mid)) continue;
      const cur = acc.get(mid) || { total: 0, em_andamento: 0, encerrados: 0, arquivados: 0 };
      cur.total += 1;
      const st = String(c.status || c.estado || "").toLowerCase();
      if (st.includes("encerr")) cur.encerrados += 1;
      else if (st.includes("arquiv")) cur.arquivados += 1;
      else cur.em_andamento += 1;
      acc.set(mid, cur);
    }
    // sort por total desc
    const out = [];
    for (const [mid, v] of acc.entries()) {
      out.push({ municipio_id: mid, ...v });
    }
    out.sort((a, b) => (b.total - a.total));
    return out;
  }, [casos]);

  if (!pode) {
    return (
      <div className="card" style={{ padding: 16 }}>
        <div style={{ fontWeight: 900 }}>Acesso restrito</div>
        <div className="texto-suave" style={{ marginTop: 6 }}>
          Esta visão é exclusiva para Admin e Gestor do Consórcio.
        </div>
      </div>
    );
  }

  return (
    <div className="card" style={{ padding: 16 }}>
      <div style={{ fontWeight: 900, fontSize: 22 }}>Gestão Regional (Consórcio)</div>
      <div className="texto-suave" style={{ marginTop: 6 }}>
        Painel agregado por município para coordenação regional.
      </div>

      <div style={{ marginTop: 14, overflowX: "auto" }}>
        <table className="table" style={{ width: "100%", borderCollapse: "separate", borderSpacing: 0 }}>
          <thead>
            <tr>
              <th>Município</th>
              <th>Total</th>
              <th>Em andamento</th>
              <th>Encerrados</th>
              <th>Arquivados</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.municipio_id}>
                <td>{getNomeMuni(r.municipio_id)}</td>
                <td>{r.total}</td>
                <td>{r.em_andamento}</td>
                <td>{r.encerrados}</td>
                <td>{r.arquivados}</td>
              </tr>
            ))}
            {!rows.length ? (
              <tr>
                <td colSpan={5} className="texto-suave">Sem dados.</td>
              </tr>
            ) : null}
          </tbody>
        </table>
      </div>
    </div>
  );
}
