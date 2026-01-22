import React, { useState } from "react";

export default function TelaCreasDocumentos() {
  const [msg, setMsg] = useState("");

  function flash(m) {
    setMsg(m || "");
    if (!m) return;
    setTimeout(() => setMsg(""), 2600);
  }

  return (
    <div className="layout-1col">
      <div className="card">
        <div style={{ fontWeight: 950, fontSize: 18 }}>Documentos (CREAS)</div>
        <div className="texto-suave" style={{ marginTop: 6 }}>
          MVP: esta tela vai listar anexos por caso e permitir upload. Por enquanto, o fluxo de caso já está pronto.
        </div>

        {msg ? (
          <div
            className="card"
            style={{ marginTop: 10, padding: 10, boxShadow: "none", border: "1px solid rgba(59,130,246,.25)", background: "rgba(59,130,246,.08)" }}
            role="alert"
          >
            <b>{msg}</b>
          </div>
        ) : null}

        <div style={{ marginTop: 12 }}>
          <button className="btn btn-secundario" type="button" onClick={() => flash("Upload MVP em breve.")}>
            + Anexar documento
          </button>
        </div>
      </div>
    </div>
  );
}
