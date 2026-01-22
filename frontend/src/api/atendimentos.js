// src/api/atendimentos.js
const API_BASE = "http://localhost:8000";

// GET /pessoas/{pessoa_id}/atendimentos
export async function listarAtendimentosPessoa(pessoaId) {
  if (!pessoaId) return [];
  const resp = await fetch(`${API_BASE}/pessoas/${pessoaId}/atendimentos`);

  if (!resp.ok) {
    console.error("Erro ao listar atendimentos:", resp.status, await resp.text());
    throw new Error("Erro ao listar atendimentos");
  }

  return resp.json();
}

// POST /pessoas/{pessoa_id}/atendimentos
export async function criarAtendimentoPessoa(pessoaId, dados) {
  const resp = await fetch(`${API_BASE}/pessoas/${pessoaId}/atendimentos`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(dados),
  });

  if (!resp.ok) {
    const erro = await resp.text();
    console.error("Erro ao criar atendimento:", resp.status, erro);
    throw new Error("Erro ao criar atendimento");
  }

  return resp.json();
}