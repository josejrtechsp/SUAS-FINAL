/**
 * frontend/src/domain/rmaCollector.js
 * Coletor invisível do RMA (zero retrabalho).
 * Usa apiFetch (já autenticado) e falha silenciosamente.
 */
export async function rmaCollect({
  apiBase,
  apiFetch,
  servico,
  acao,
  unidade_id = null,
  pessoa_id = null,
  familia_id = null,
  caso_id = null,
  alvo_tipo = null,
  alvo_id = null,
  meta = null,
  data_evento = null,
}) {
  try {
    if (!apiBase || typeof apiFetch !== "function") return;
    if (!servico || !acao) return;

    const body = {
      servico,
      acao,
      unidade_id,
      pessoa_id,
      familia_id,
      caso_id,
      alvo_tipo,
      alvo_id,
      meta,
      data_evento,
    };

    Object.keys(body).forEach((k) => (body[k] === undefined ? delete body[k] : null));

    const r = await apiFetch(`${apiBase}/cras/rma/evento`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });

    // falha silenciosa
    if (!r.ok) {
      // noop
    }
  } catch (e) {
    // silencioso
  }
}
