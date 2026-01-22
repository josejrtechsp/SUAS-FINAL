// frontend/src/domain/acl.js
// ACL simples (MVP local) para padronizar perfis e permissões.
// Objetivo: deixar o sistema autoexplicativo e consistente entre módulos.

function norm(s) {
  return String(s || "").trim().toLowerCase();
}

export function getPerfil(usuario) {
  return norm(usuario?.perfil || usuario?.role || "");
}

export function isGestor(usuario) {
  const p = getPerfil(usuario);
  return ["coord_municipal", "gestor", "coordenador", "coord", "admin", "gestor_consorcio"].includes(p);
}

export function isTecnico(usuario) {
  const p = getPerfil(usuario);
  // no seu sistema, "operador" = técnico na ponta.
  return ["operador", "tecnico", "técnico", "referencia", "referência", "tecnico_referencia", "técnico_referencia"].includes(p);
}

export function isRecepcao(usuario) {
  const p = getPerfil(usuario);
  return ["recepcao", "recepção", "atendente", "administrativo", "secretaria"].includes(p);
}

export function isLeitura(usuario) {
  const p = getPerfil(usuario);
  return ["leitura", "controle", "auditoria", "viewer", "observador"].includes(p);
}

export function canAprovarEncerramento(usuario) {
  return isGestor(usuario);
}

export function canSolicitarEncerramento(usuario) {
  return isTecnico(usuario);
}

export function canEditarFichaCompleta(usuario) {
  return isGestor(usuario) || isTecnico(usuario);
}

export function canEditarFichaContato(usuario) {
  return canEditarFichaCompleta(usuario) || isRecepcao(usuario);
}

// Escopo de casos para o técnico: "meus + sem responsável".
export function scopeCases(allCases, usuario) {
  const uid = usuario?.id != null ? Number(usuario.id) : null;
  const tecnico = isTecnico(usuario);
  if (!tecnico || !uid || Number.isNaN(uid)) return allCases || [];

  return (allCases || []).filter((c) => {
    const rid = c?.responsavel_id != null ? Number(c.responsavel_id) : null;
    return !rid || rid === uid;
  });
}

// Acesso às abas principais do CREAS (mantém a estrutura imutável; bloqueia por permissão).
export function canAccessCreasTab(tabKey, usuario) {
  const k = norm(tabKey);

  if (isGestor(usuario)) return true;
  if (isTecnico(usuario)) {
    return ["painel", "novo", "casos", "pendencias", "agenda", "rede", "documentos", "relatorios"].includes(k);
  }
  if (isRecepcao(usuario)) {
    return ["novo", "agenda", "casos"].includes(k);
  }
  if (isLeitura(usuario)) {
    return ["painel", "relatorios"].includes(k);
  }

  return true; // fallback (não trava)
}
