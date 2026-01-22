const comunicacaoTipo = { whatsapp:"WhatsApp", telefone:"Telefone", presencial:"Presencial", email:"E-mail", outro:"Outro" };
const comunicacaoIcon = { whatsapp:"💬", telefone:"📞", presencial:"🏢", email:"✉️", outro:"📝" };

const atendimentoTipo = {
  triagem:"Triagem", acolhimento:"Acolhimento", visita:"Visita domiciliar",
  acompanhamento:"Acompanhamento", orientacao:"Orientação", outro:"Outro"
};

const atendimentoResultado = {
  realizado:"Realizado", nao_compareceu:"Não compareceu", reagendado:"Reagendado",
  encaminhado:"Encaminhado", em_andamento:"Em andamento", outro:"Outro"
};

export function getComunicacaoTipoLabel(key){ if(!key) return "—"; return comunicacaoTipo[String(key).toLowerCase()] || String(key); }
export function getComunicacaoTipoIcon(key){ if(!key) return "📝"; return comunicacaoIcon[String(key).toLowerCase()] || "📝"; }
export function getAtendimentoTipoLabel(key){ if(!key) return "—"; return atendimentoTipo[String(key).toLowerCase()] || String(key); }
export function getAtendimentoResultadoLabel(key){ if(!key) return "—"; return atendimentoResultado[String(key).toLowerCase()] || String(key); }
