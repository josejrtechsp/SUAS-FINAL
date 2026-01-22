import React from "react";

export default function ProntuarioQuickExport({ apiBase, apiFetch, pessoaId = null, familiaId = null }) {
  async function download(url, filename) {
    const r = await apiFetch(url);
    if (!r.ok) throw new Error(await r.text());
    const blob = await r.blob();
    const obj = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = obj;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(obj);
  }

  async function baixarPessoa() {
    if (!pessoaId) return;
    try {
      const url = `${apiBase}/cras/prontuario/export.csv?pessoa_id=${encodeURIComponent(String(pessoaId))}&include_suas=1`;
      await download(url, `prontuario_pessoa_${pessoaId}.csv`);
    } catch (e) { console.error(e); alert("Falha ao baixar prontuário da pessoa."); }
  }

  async function baixarFamilia() {
    if (!familiaId) return;
    try {
      const url = `${apiBase}/cras/prontuario/export.csv?familia_id=${encodeURIComponent(String(familiaId))}&include_suas=1`;
      await download(url, `prontuario_familia_${familiaId}.csv`);
    } catch (e) { console.error(e); alert("Falha ao baixar prontuário da família."); }
  }

  if (!apiBase || typeof apiFetch !== "function") return null;

  return (
    <div className="card" style={{ padding: 12, borderRadius: 16, marginBottom: 10 }}>
      <div style={{ display: "flex", justifyContent: "space-between", gap: 10, flexWrap: "wrap", alignItems: "center" }}>
        <div>
          <div style={{ fontWeight: 900 }}>Prontuário (CSV)</div>
          <div className="texto-suave">Exportação rápida da linha do tempo (inclui SUAS quando houver).</div>
        </div>
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
          <button className="btn btn-secundario" type="button" disabled={!pessoaId} onClick={baixarPessoa}>Baixar Pessoa</button>
          <button className="btn btn-secundario" type="button" disabled={!familiaId} onClick={baixarFamilia}>Baixar Família</button>
        </div>
      </div>
    </div>
  );
}

// PRONTUARIO_EXPORT_V1
