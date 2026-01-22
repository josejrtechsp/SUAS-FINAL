// frontend/src/domain/pessoasStore.js
// Cadastro ÚNICO (Ficha Única) para Pessoa/Família — MVP local (localStorage).
// Objetivo: permitir uma “ficha” reaproveitável entre módulos (CRAS/CREAS/PopRua)
// mesmo antes de integrar com backend.

const KEY_PESSOAS = "suas_pessoas_v1";

function nowIso() {
  return new Date().toISOString();
}

function safeParseArray(raw) {
  try {
    const j = JSON.parse(raw);
    return Array.isArray(j) ? j : [];
  } catch {
    return [];
  }
}

function apenasDigitos(v) {
  return String(v || "").replace(/\D/g, "");
}

function pad11(num) {
  const s = String(num).replace(/\D/g, "");
  return s.padStart(11, "0").slice(0, 11);
}

function demoCpf(id) {
  // NÃO é CPF real — apenas para DEMO.
  const n = (Number(id) * 1234567) % 100000000000;
  return pad11(n);
}

function demoNis(id) {
  const n = (Number(id) * 9876543) % 10000000000;
  return String(n).padStart(11, "0");
}

function demoTelefone(id) {
  const base = 900000000 + ((Number(id) * 379) % 90000000);
  return `+55 (16) 9${String(base).slice(1, 5)}-${String(base).slice(5, 9)}`;
}

function demoEndereco(id) {
  const ruas = ["Rua das Flores", "Av. Central", "Rua do Sol", "Rua da Paz", "Av. Brasil", "Rua XV de Novembro"];
  const bairros = ["Centro", "Vila Nova", "Jardim Europa", "São José", "Santa Clara", "Parque Industrial"];
  const idx = Number(id) % ruas.length;
  return {
    logradouro: ruas[idx],
    numero: String(100 + (Number(id) % 900)),
    bairro: bairros[Number(id) % bairros.length],
    cidade: "Altair",
    uf: "SP",
  };
}

function membrosDemo(nome, id) {
  const isFamilia = /familia|família/i.test(String(nome || ""));
  if (!isFamilia) {
    return [
      {
        nome: String(nome || "Pessoa"),
        parentesco: "Referência",
      },
    ];
  }
  return [
    { nome: "Referência familiar", parentesco: "Referência" },
    { nome: "Cônjuge", parentesco: "Cônjuge" },
    { nome: "Filho(a)", parentesco: "Filho(a)" },
    { nome: `Dependente ${Number(id) % 3 + 1}`, parentesco: "Dependente" },
  ];
}

export function getPessoas() {
  try {
    const raw = localStorage.getItem(KEY_PESSOAS);
    return safeParseArray(raw);
  } catch {
    return [];
  }
}

export function savePessoas(pessoas) {
  try {
    localStorage.setItem(KEY_PESSOAS, JSON.stringify(pessoas || []));
  } catch {}
}

export function nextPessoaId() {
  const arr = getPessoas();
  const max = (arr || []).reduce((m, p) => Math.max(m, Number(p?.id || 0)), 0);
  return max + 1;
}

export function getPessoaById(pessoaId) {
  const id = pessoaId != null ? Number(pessoaId) : null;
  if (!id || Number.isNaN(id)) return null;
  return (getPessoas() || []).find((p) => Number(p?.id) === id) || null;
}

export function upsertPessoa(pessoa) {
  if (!pessoa) return null;
  const id = pessoa?.id != null ? Number(pessoa.id) : null;
  if (!id || Number.isNaN(id)) return null;

  const arr = getPessoas();
  const iso = nowIso();

  const cleaned = {
    id,
    nome: String(pessoa?.nome || "Pessoa").trim(),
    cpf: pessoa?.cpf ? apenasDigitos(pessoa.cpf) : null,
    nis: pessoa?.nis ? apenasDigitos(pessoa.nis) : null,
    telefone: pessoa?.telefone || null,
    data_nascimento: pessoa?.data_nascimento || null,
    endereco: pessoa?.endereco || null,
    membros: Array.isArray(pessoa?.membros) ? pessoa.membros : [],
    observacoes: pessoa?.observacoes || null,
    criado_em: pessoa?.criado_em || iso,
    atualizado_em: iso,
  };

  const exists = arr.findIndex((x) => Number(x?.id) === id);
  const next = [...arr];
  if (exists >= 0) next[exists] = { ...arr[exists], ...cleaned, criado_em: arr[exists]?.criado_em || cleaned.criado_em };
  else next.unshift(cleaned);

  savePessoas(next);
  return cleaned;
}

export function ensurePessoaBasica({ pessoa_id, nome, cpf, nis, telefone } = {}) {
  const id = pessoa_id != null ? Number(pessoa_id) : nextPessoaId();
  const existing = getPessoaById(id);
  if (existing) {
    // Atualiza apenas campos vazios (não sobrescreve o que já foi preenchido)
    return upsertPessoa({
      ...existing,
      nome: existing.nome || nome || existing.nome,
      cpf: existing.cpf || (cpf ? apenasDigitos(cpf) : null),
      nis: existing.nis || (nis ? apenasDigitos(nis) : null),
      telefone: existing.telefone || telefone || null,
      membros: (existing.membros && existing.membros.length) ? existing.membros : membrosDemo(nome, id),
      endereco: existing.endereco || demoEndereco(id),
    });
  }

  return upsertPessoa({
    id,
    nome: String(nome || "Pessoa").trim(),
    cpf: cpf ? apenasDigitos(cpf) : demoCpf(id),
    nis: nis ? apenasDigitos(nis) : demoNis(id),
    telefone: telefone || demoTelefone(id),
    endereco: demoEndereco(id),
    membros: membrosDemo(nome, id),
  });
}

export function clearPessoas() {
  try {
    localStorage.removeItem(KEY_PESSOAS);
  } catch {}
  savePessoas([]);
  return [];
}

/**
 * Seed de pessoas DEMO baseado nos casos do CREAS
 * - 1 caso -> 1 ficha (pessoa_id)
 * - Não altera casos; só garante que existam fichas.
 */
export function seedPessoasDemoFromCreasCases(cases, { overwrite = false } = {}) {
  const list = Array.isArray(cases) ? cases : [];
  const current = overwrite ? [] : getPessoas();
  const map = new Map((current || []).map((p) => [Number(p?.id), p]));

  list.forEach((c) => {
    const pessoaId = c?.pessoa_id != null ? Number(c.pessoa_id) : (c?.id != null ? Number(c.id) : null);
    if (!pessoaId || Number.isNaN(pessoaId)) return;
    if (!map.has(pessoaId)) {
      map.set(
        pessoaId,
        ensurePessoaBasica({ pessoa_id: pessoaId, nome: c?.nome || "Pessoa" })
      );
    } else {
      // garante nome/membros se faltarem
      const p = map.get(pessoaId);
      map.set(
        pessoaId,
        upsertPessoa({
          ...p,
          nome: p?.nome || c?.nome || "Pessoa",
          membros: (p?.membros && p.membros.length) ? p.membros : membrosDemo(c?.nome, pessoaId),
          endereco: p?.endereco || demoEndereco(pessoaId),
        })
      );
    }
  });

  const next = Array.from(map.values()).sort((a, b) => Number(a.id) - Number(b.id));
  savePessoas(next);
  return next;
}
