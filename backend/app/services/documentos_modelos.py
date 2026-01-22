from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


def _norm(s: str) -> str:
    return (s or "").strip().lower().replace("-", "_").replace(" ", "_")


@dataclass(frozen=True)
class ModeloDocumento:
    """Modelo de documento (biblioteca) usado para geração guiada."""

    key: str
    tipo: str
    titulo: str
    descricao: str
    assunto_padrao: Optional[str]
    corpo_template: str
    assinatura_template: str
    campos_obrigatorios: List[str]
    campos_opcionais: List[str]
    numero_titulo: Optional[str] = None  # ex: "OFÍCIO"

    def _sugerir_emissor(self) -> Optional[str]:
        s = _norm(f"{self.key} {self.titulo}")
        if "cras" in s:
            return "cras"
        if "creas" in s:
            return "creas"
        if "poprua" in s or "pop_rua" in s:
            return "poprua"
        if "gestao" in s:
            return "gestao"
        return None

    def exemplo_payload(self) -> Dict[str, Any]:
        """Exemplo mínimo para uso via /documentos/gerar.

        Observação: inclui sugestão de `emissor` quando o modelo deixa isso claro
        (ex.: CRAS/CREAS/PopRua).
        """
        campos: Dict[str, Any] = {}
        for k in self.campos_obrigatorios:
            campos[k] = f"<{k}>"

        payload: Dict[str, Any] = {
            "tipo": self.tipo,
            "modelo": self.key,
            "assunto": self.assunto_padrao or "",
            "destinatario_nome": "<Nome do destinatário>",
            "destinatario_cargo": "<Cargo>",
            "destinatario_orgao": "<Órgão/Setor>",
            "campos": campos,
            "salvar": True,
        }

        emissor = self._sugerir_emissor()
        if emissor:
            payload["emissor"] = emissor

        return payload


# ======================================================================
# Biblioteca (global)
# ======================================================================


MODELOS: List[ModeloDocumento] = [
    # ------------------------
    # BASE (padrões simples)
    # ------------------------
    ModeloDocumento(
        key="oficio_padrao",
        tipo="oficio",
        titulo="OFÍCIO",
        descricao="Ofício padrão (texto livre).",
        assunto_padrao=None,
        corpo_template=(
            "{% if destinatario_nome %}"
            "<b>{{destinatario_nome}}</b><br/>"
            "{% if destinatario_cargo %}{{destinatario_cargo}}<br/>{% endif %}"
            "{% if destinatario_orgao %}{{destinatario_orgao}}<br/>{% endif %}"
            "<br/>{% endif %}"
            "Prezado(a) {% if destinatario_nome %}{{destinatario_nome}}{% else %}Senhor(a){% endif %},\n\n"
            "{{texto or 'Descreva aqui o conteúdo do ofício.'}}\n\n"
            "Sem mais para o momento."
        ),
        assinatura_template="{{assinante_nome or 'Nome do(a) assinante'}}\n{{assinante_cargo or 'Cargo do(a) assinante'}}",
        campos_obrigatorios=[],
        campos_opcionais=["texto", "assinante_nome", "assinante_cargo"],
        numero_titulo="OFÍCIO",
    ),
    ModeloDocumento(
        key="memorando_padrao",
        tipo="memorando",
        titulo="MEMORANDO",
        descricao="Memorando padrão (texto livre).",
        assunto_padrao=None,
        corpo_template=(
            "À/ao: {% if destinatario_orgao %}{{destinatario_orgao}}{% else %}Setor/Órgão{% endif %}\n"
            "{% if destinatario_nome %}Responsável: {{destinatario_nome}}\n{% endif %}\n"
            "{% if assunto %}<b>Assunto:</b> {{assunto}}\n\n{% endif %}"
            "{{texto or 'Descreva aqui o conteúdo do memorando.'}}"
        ),
        assinatura_template="{{assinante_nome or 'Nome do(a) assinante'}}\n{{assinante_cargo or 'Cargo do(a) assinante'}}",
        campos_obrigatorios=[],
        campos_opcionais=["texto", "assunto", "assinante_nome", "assinante_cargo"],
        numero_titulo="MEMORANDO",
    ),
    ModeloDocumento(
        key="relatorio_padrao",
        tipo="relatorio",
        titulo="RELATÓRIO",
        descricao="Relatório padrão (seções simples).",
        assunto_padrao=None,
        corpo_template=(
            "<b>1. Contexto</b>\n\n"
            "{{contexto or 'Descreva o contexto.'}}\n\n"
            "<b>2. Descrição</b>\n\n"
            "{{descricao or 'Descreva os fatos/ações.'}}\n\n"
            "<b>3. Encaminhamentos</b>\n\n"
            "{{encaminhamentos or 'Liste encaminhamentos e prazos.'}}"
        ),
        assinatura_template="{{assinante_nome or 'Nome do(a) responsável'}}\n{{assinante_cargo or 'Cargo'}}",
        campos_obrigatorios=[],
        campos_opcionais=["contexto", "descricao", "encaminhamentos", "assinante_nome", "assinante_cargo"],
        numero_titulo="RELATÓRIO",
    ),
    ModeloDocumento(
        key="declaracao_padrao",
        tipo="declaracao",
        titulo="DECLARAÇÃO",
        descricao="Declaração simples (texto guiado).",
        assunto_padrao=None,
        corpo_template=(
            "Declaramos, para os devidos fins, que {{nome_declarado or 'NOME'}}"
            "{% if documento_declarado %} ({{documento_declarado}}){% endif %} "
            "{{texto or 'esteve/foi atendido(a) neste equipamento.'}}\n\n"
            "{{data_extenso}}"
        ),
        assinatura_template="{{assinante_nome or 'Nome do(a) responsável'}}\n{{assinante_cargo or 'Cargo'}}",
        campos_obrigatorios=[],
        campos_opcionais=["nome_declarado", "documento_declarado", "texto", "assinante_nome", "assinante_cargo"],
        numero_titulo="DECLARAÇÃO",
    ),

    # ------------------------
    # OFÍCIOS guiados (SUAS)
    # ------------------------
    ModeloDocumento(
        key="oficio_encaminhamento",
        tipo="oficio",
        titulo="OFÍCIO — Encaminhamento",
        descricao="Encaminhamento para outro equipamento/OSC, com motivo e solicitação guiados.",
        assunto_padrao="Encaminhamento",
        corpo_template=(
            "{% if destinatario_nome %}"
            "<b>{{destinatario_nome}}</b><br/>"
            "{% if destinatario_cargo %}{{destinatario_cargo}}<br/>{% endif %}"
            "{% if destinatario_orgao %}{{destinatario_orgao}}<br/>{% endif %}"
            "<br/>{% endif %}"
            "Prezado(a) {% if destinatario_nome %}{{destinatario_nome}}{% else %}Senhor(a){% endif %},\n\n"
            "Encaminhamos para apreciação e providências: <b>{{referencia}}</b>."
            "{% if protocolo %} (Protocolo: {{protocolo}}){% endif %}\n\n"
            "<b>Motivo/Contexto</b>\n{{motivo}}\n\n"
            "<b>Solicitação</b>\n{{solicitacao}}\n\n"
            "{% if prazo %}<b>Prazo sugerido</b>: {{prazo}}\n\n{% endif %}"
            "{% if contato_retorno %}<b>Contato para devolutiva</b>: {{contato_retorno}}\n\n{% endif %}"
            "Sem mais para o momento."
        ),
        assinatura_template=(
            "{{assinante_nome or 'Nome do(a) assinante'}}\n"
            "{{assinante_cargo or 'Cargo do(a) assinante'}}"
            "{% if assinante_orgao %}\n{{assinante_orgao}}{% endif %}"
        ),
        campos_obrigatorios=["referencia", "motivo", "solicitacao"],
        campos_opcionais=[
            "protocolo",
            "prazo",
            "contato_retorno",
            "assinante_nome",
            "assinante_cargo",
            "assinante_orgao",
        ],
        numero_titulo="OFÍCIO",
    ),
    ModeloDocumento(
        key="oficio_cobranca_devolutiva",
        tipo="oficio",
        titulo="OFÍCIO — Cobrança de devolutiva",
        descricao="Cobrança formal de devolutiva/retorno de encaminhamento (Rede SUAS), com prazo e referência.",
        assunto_padrao="Cobrança de devolutiva",
        corpo_template=(
            "{% if destinatario_nome %}"
            "<b>{{destinatario_nome}}</b><br/>"
            "{% if destinatario_cargo %}{{destinatario_cargo}}<br/>{% endif %}"
            "{% if destinatario_orgao %}{{destinatario_orgao}}<br/>{% endif %}"
            "<br/>{% endif %}"
            "Prezado(a) {% if destinatario_nome %}{{destinatario_nome}}{% else %}Senhor(a){% endif %},\n\n"
            "Em referência a <b>{{referencia}}</b>"
            "{% if numero_referencia %} (Ofício nº {{numero_referencia}}){% endif %}"
            "{% if protocolo %} (Protocolo: {{protocolo}}){% endif %}"
            "{% if data_envio %}, encaminhado em {{data_envio}}{% endif %}, informamos que até o momento não recebemos devolutiva.\n\n"
            "Solicitamos que a devolutiva/retorno seja registrada no sistema no prazo de <b>{{prazo}}</b>.\n\n"
            "Caso não seja possível atender no prazo, solicitamos informar justificativa e previsão de atendimento.\n\n"
            "{% if solicitacao %}<b>Solicitação</b>\n{{solicitacao}}\n\n{% endif %}"
            "{% if contato_retorno %}<b>Contato para retorno</b>: {{contato_retorno}}\n\n{% endif %}"
            "Sem mais para o momento."
        ),
        assinatura_template=(
            "{{assinante_nome or 'Nome do(a) responsável'}}\n"
            "{{assinante_cargo or 'Cargo'}}"
            "{% if assinante_orgao %}\n{{assinante_orgao}}{% endif %}"
        ),
        campos_obrigatorios=["referencia", "prazo"],
        campos_opcionais=[
            "numero_referencia",
            "data_envio",
            "protocolo",
            "solicitacao",
            "contato_retorno",
            "assinante_nome",
            "assinante_cargo",
            "assinante_orgao",
        ],
        numero_titulo="OFÍCIO",
    ),
    ModeloDocumento(
        key="oficio_solicitacao_beneficio_eventual",
        tipo="oficio",
        titulo="OFÍCIO — Solicitação de benefício eventual",
        descricao="Solicitação formal de benefício eventual (ex.: alimentação, passagem, auxílio-natalidade), com justificativa e identificação.",
        assunto_padrao="Solicitação de benefício eventual",
        corpo_template=(
            "{% if destinatario_orgao %}"
            "À/ao <b>{{destinatario_orgao}}</b><br/>"
            "{% if destinatario_nome %}A/C {{destinatario_nome}}<br/>{% endif %}"
            "{% if destinatario_cargo %}{{destinatario_cargo}}<br/>{% endif %}"
            "<br/>{% endif %}"
            "Prezados(as),\n\n"
            "Solicitamos a concessão de <b>benefício eventual</b> para <b>{{nome_beneficiario}}</b>"
            "{% if documento_beneficiario %} ({{documento_beneficiario}}){% endif %}"
            "{% if nis %} — NIS {{nis}}{% endif %}.\n\n"
            "<b>Tipo de benefício</b>: {{tipo_beneficio}}\n"
            "{% if valor_estimado %}<b>Valor/quantidade estimada</b>: {{valor_estimado}}\n{% endif %}"
            "{% if endereco %}<b>Endereço/Referência</b>: {{endereco}}\n{% endif %}"
            "{% if composicao_familiar %}<b>Composição familiar</b>: {{composicao_familiar}}\n{% endif %}"
            "\n<b>Justificativa</b>\n{{justificativa}}\n\n"
            "{% if prazo %}<b>Prazo</b>: {{prazo}}\n\n{% endif %}"
            "{% if contato_retorno %}<b>Contato</b>: {{contato_retorno}}\n\n{% endif %}"
            "Sem mais para o momento."
        ),
        assinatura_template=(
            "{{assinante_nome or 'Responsável técnico'}}\n"
            "{{assinante_cargo or 'Cargo'}}"
            "{% if assinante_orgao %}\n{{assinante_orgao}}{% endif %}"
        ),
        campos_obrigatorios=["nome_beneficiario", "tipo_beneficio", "justificativa"],
        campos_opcionais=[
            "documento_beneficiario",
            "nis",
            "endereco",
            "composicao_familiar",
            "valor_estimado",
            "prazo",
            "contato_retorno",
            "assinante_nome",
            "assinante_cargo",
            "assinante_orgao",
        ],
        numero_titulo="OFÍCIO",
    ),
    ModeloDocumento(
        key="oficio_convocacao",
        tipo="oficio",
        titulo="OFÍCIO — Convocação",
        descricao="Convocação/Notificação para comparecimento em atendimento (orientações e documentos).",
        assunto_padrao="Convocação",
        corpo_template=(
            "<b>{{nome_convocado}}</b>"
            "{% if documento_convocado %} ({{documento_convocado}}){% endif %}\n\n"
            "Fica o(a) Sr(a). convocado(a) a comparecer em <b>{{data_comparecimento}}</b>"
            "{% if horario_comparecimento %} às <b>{{horario_comparecimento}}</b>{% endif %}, "
            "no local <b>{{local_comparecimento}}</b>.\n\n"
            "{% if motivo %}<b>Motivo</b>\n{{motivo}}\n\n{% endif %}"
            "{% if orientacoes %}<b>Orientações</b>\n{{orientacoes}}\n\n{% endif %}"
            "Solicitamos que traga documentos pessoais e comprovantes pertinentes, quando disponíveis."
        ),
        assinatura_template=(
            "{{assinante_nome or 'Responsável'}}\n"
            "{{assinante_cargo or 'Cargo'}}"
        ),
        campos_obrigatorios=["nome_convocado", "data_comparecimento", "local_comparecimento"],
        campos_opcionais=[
            "documento_convocado",
            "horario_comparecimento",
            "motivo",
            "orientacoes",
            "assinante_nome",
            "assinante_cargo",
        ],
        numero_titulo="OFÍCIO",
    ),

    # ------------------------
    # MEMORANDOS guiados
    # ------------------------
    ModeloDocumento(
        key="memorando_interno",
        tipo="memorando",
        titulo="MEMORANDO — Interno",
        descricao="Memorando interno com campos claros (para/assunto/solicitação/prazo).",
        assunto_padrao=None,
        corpo_template=(
            "À/ao: <b>{{para_setor}}</b>\n"
            "{% if para_responsavel %}Responsável: {{para_responsavel}}\n{% endif %}"
            "{% if assunto %}<b>Assunto:</b> {{assunto}}\n{% endif %}\n"
            "<b>Solicitação</b>\n{{solicitacao}}\n\n"
            "{% if prazo %}<b>Prazo sugerido</b>: {{prazo}}\n{% endif %}"
            "{% if observacoes %}\n<b>Observações</b>\n{{observacoes}}{% endif %}"
        ),
        assinatura_template="{{assinante_nome or 'Nome do(a) servidor(a)'}}\n{{assinante_cargo or 'Cargo'}}",
        campos_obrigatorios=["para_setor", "solicitacao"],
        campos_opcionais=["para_responsavel", "assunto", "prazo", "observacoes", "assinante_nome", "assinante_cargo"],
        numero_titulo="MEMORANDO",
    ),

    # ------------------------
    # RELATÓRIOS técnicos guiados
    # ------------------------
    ModeloDocumento(
        key="relatorio_tecnico_cras",
        tipo="relatorio",
        titulo="RELATÓRIO TÉCNICO — CRAS",
        descricao="Relatório técnico CRAS (identificação, demanda, intervenções, avaliação, encaminhamentos).",
        assunto_padrao="Relatório técnico",
        corpo_template=(
            "<b>1. Identificação</b>\n\n{{identificacao}}\n\n"
            "<b>2. Demanda</b>\n\n{{demanda}}\n\n"
            "<b>3. Intervenções/Atendimentos realizados</b>\n\n{{intervencoes}}\n\n"
            "<b>4. Avaliação técnica</b>\n\n{{avaliacao}}\n\n"
            "<b>5. Encaminhamentos e prazos</b>\n\n{{encaminhamentos}}"
        ),
        assinatura_template="{{assinante_nome or 'Responsável técnico'}}\n{{assinante_cargo or 'Cargo'}}",
        campos_obrigatorios=["identificacao", "demanda", "intervencoes", "avaliacao", "encaminhamentos"],
        campos_opcionais=["assinante_nome", "assinante_cargo"],
        numero_titulo="RELATÓRIO",
    ),
    ModeloDocumento(
        key="relatorio_tecnico_creas",
        tipo="relatorio",
        titulo="RELATÓRIO TÉCNICO — CREAS",
        descricao="Relatório técnico CREAS/PAEFI (fatos, risco, medidas, avaliação, encaminhamentos).",
        assunto_padrao="Relatório técnico",
        corpo_template=(
            "<b>1. Identificação</b>\n\n{{identificacao}}\n\n"
            "<b>2. Síntese dos fatos</b>\n\n{{fatos}}\n\n"
            "<b>3. Avaliação de risco</b>\n\n{{risco}}\n\n"
            "<b>4. Medidas/Intervenções realizadas</b>\n\n{{intervencoes}}\n\n"
            "<b>5. Encaminhamentos e recomendações</b>\n\n{{encaminhamentos}}"
        ),
        assinatura_template="{{assinante_nome or 'Responsável técnico'}}\n{{assinante_cargo or 'Cargo'}}",
        campos_obrigatorios=["identificacao", "fatos", "risco", "intervencoes", "encaminhamentos"],
        campos_opcionais=["assinante_nome", "assinante_cargo"],
        numero_titulo="RELATÓRIO",
    ),
    ModeloDocumento(
        key="relatorio_tecnico_poprua",
        tipo="relatorio",
        titulo="RELATÓRIO TÉCNICO — Pop Rua",
        descricao="Relatório técnico Pop Rua (abordagem, histórico, necessidades, encaminhamentos).",
        assunto_padrao="Relatório técnico",
        corpo_template=(
            "<b>1. Identificação</b>\n\n{{identificacao}}\n\n"
            "<b>2. Abordagem/Localização</b>\n\n{{abordagem}}\n\n"
            "<b>3. Síntese do histórico</b>\n\n{{historico}}\n\n"
            "<b>4. Necessidades identificadas</b>\n\n{{necessidades}}\n\n"
            "<b>5. Encaminhamentos</b>\n\n{{encaminhamentos}}"
        ),
        assinatura_template="{{assinante_nome or 'Responsável técnico'}}\n{{assinante_cargo or 'Cargo'}}",
        campos_obrigatorios=["identificacao", "abordagem", "historico", "necessidades", "encaminhamentos"],
        campos_opcionais=["assinante_nome", "assinante_cargo"],
        numero_titulo="RELATÓRIO",
    ),
    ModeloDocumento(
        key="relatorio_visita_domiciliar",
        tipo="relatorio",
        titulo="RELATÓRIO TÉCNICO — Visita domiciliar",
        descricao="Relatório de visita domiciliar (identificação, objetivo, observações, avaliação e encaminhamentos).",
        assunto_padrao="Relatório de visita domiciliar",
        corpo_template=(
            "<b>1. Identificação</b>\n\n{{identificacao}}\n\n"
            "<b>2. Objetivo da visita</b>\n\n{{objetivo}}\n\n"
            "<b>3. Data e local</b>\n\nData: {{data_visita}}\nEndereço/Referência: {{endereco}}\n"
            "{% if presentes %}\nPessoas presentes: {{presentes}}\n{% endif %}\n\n"
            "<b>4. Observações</b>\n\n{{observacoes}}\n\n"
            "<b>5. Avaliação técnica</b>\n\n{{avaliacao}}\n\n"
            "<b>6. Encaminhamentos</b>\n\n{{encaminhamentos}}"
        ),
        assinatura_template="{{assinante_nome or 'Responsável técnico'}}\n{{assinante_cargo or 'Cargo'}}",
        campos_obrigatorios=["identificacao", "objetivo", "data_visita", "endereco", "observacoes", "avaliacao", "encaminhamentos"],
        campos_opcionais=["presentes", "assinante_nome", "assinante_cargo"],
        numero_titulo="RELATÓRIO",
    ),

    # ------------------------
    # DECLARAÇÕES guiadas
    # ------------------------
    ModeloDocumento(
        key="declaracao_comparecimento",
        tipo="declaracao",
        titulo="DECLARAÇÃO — Comparecimento",
        descricao="Declaração de comparecimento (data/horário/identificação).",
        assunto_padrao="Declaração de comparecimento",
        corpo_template=(
            "Declaramos, para os devidos fins, que <b>{{nome_declarado}}</b>"
            "{% if documento_declarado %} ({{documento_declarado}}){% endif %} "
            "compareceu a este equipamento/serviço em <b>{{data_comparecimento}}</b>"
            "{% if horario %}, no período {{horario}}{% endif %}.\n\n"
            "{% if finalidade %}<b>Finalidade</b>: {{finalidade}}\n\n{% endif %}"
            "{{data_extenso}}"
        ),
        assinatura_template="{{assinante_nome or 'Responsável'}}\n{{assinante_cargo or 'Cargo'}}",
        campos_obrigatorios=["nome_declarado", "data_comparecimento"],
        campos_opcionais=["documento_declarado", "horario", "finalidade", "assinante_nome", "assinante_cargo"],
        numero_titulo="DECLARAÇÃO",
    ),
    ModeloDocumento(
        key="declaracao_atendimento",
        tipo="declaracao",
        titulo="DECLARAÇÃO — Atendimento",
        descricao="Declaração de atendimento (data/serviço/profissional opcional).",
        assunto_padrao="Declaração de atendimento",
        corpo_template=(
            "Declaramos, para os devidos fins, que <b>{{nome_declarado}}</b>"
            "{% if documento_declarado %} ({{documento_declarado}}){% endif %} "
            "foi atendido(a) neste equipamento/serviço em <b>{{data_atendimento}}</b>.\n\n"
            "{% if servico %}<b>Serviço</b>: {{servico}}\n{% endif %}"
            "{% if profissional %}<b>Profissional</b>: {{profissional}}\n{% endif %}"
            "{% if observacoes %}\n<b>Observações</b>\n{{observacoes}}\n{% endif %}"
            "\n{{data_extenso}}"
        ),
        assinatura_template="{{assinante_nome or 'Responsável'}}\n{{assinante_cargo or 'Cargo'}}",
        campos_obrigatorios=["nome_declarado", "data_atendimento"],
        campos_opcionais=["documento_declarado", "servico", "profissional", "observacoes", "assinante_nome", "assinante_cargo"],
        numero_titulo="DECLARAÇÃO",
    ),
    ModeloDocumento(
        key="declaracao_vulnerabilidade",
        tipo="declaracao",
        titulo="DECLARAÇÃO — Vulnerabilidade social",
        descricao="Declaração de situação de vulnerabilidade social (para fins administrativos), com fundamento/resumo técnico.",
        assunto_padrao="Declaração de vulnerabilidade social",
        corpo_template=(
            "Declaramos, para os devidos fins, que <b>{{nome_declarado}}</b>"
            "{% if documento_declarado %} ({{documento_declarado}}){% endif %} "
            "encontra-se em acompanhamento/atendimento no âmbito do SUAS e, no momento, "
            "apresenta <b>situação de vulnerabilidade social</b>, conforme síntese técnica a seguir:\n\n"
            "{{fundamento}}\n\n"
            "{% if periodo_acompanhamento %}<b>Período de acompanhamento</b>: {{periodo_acompanhamento}}\n\n{% endif %}"
            "{% if encaminhamentos %}<b>Encaminhamentos</b>\n{{encaminhamentos}}\n\n{% endif %}"
            "{{data_extenso}}"
        ),
        assinatura_template="{{assinante_nome or 'Responsável técnico'}}\n{{assinante_cargo or 'Cargo'}}",
        campos_obrigatorios=["nome_declarado", "fundamento"],
        campos_opcionais=["documento_declarado", "periodo_acompanhamento", "encaminhamentos", "assinante_nome", "assinante_cargo"],
        numero_titulo="DECLARAÇÃO",
    ),
    # ------------------------
    # OFÍCIOS formais (SUAS/Rede) — “carimbo prefeitura”
    # ------------------------
    ModeloDocumento(
        key="oficio_reiteracao_cobranca_devolutiva",
        tipo="oficio",
        titulo="OFÍCIO — Reiteração de cobrança de devolutiva",
        descricao="Reiteração formal de cobrança de devolutiva/retorno (2ª cobrança), com prazo e referência.",
        assunto_padrao="Reiteração de cobrança de devolutiva",
        corpo_template=(
            "{% if destinatario_nome %}"
            "<b>{{destinatario_nome}}</b><br/>"
            "{% if destinatario_cargo %}{{destinatario_cargo}}<br/>{% endif %}"
            "{% if destinatario_orgao %}{{destinatario_orgao}}<br/>{% endif %}"
            "<br/>{% endif %}"
            "Prezado(a) {% if destinatario_nome %}{{destinatario_nome}}{% else %}Senhor(a){% endif %},\n\n"
            "<b>Reiteramos</b> a solicitação de devolutiva referente a <b>{{referencia}}</b>"
            "{% if numero_referencia %} (Ofício nº {{numero_referencia}}){% endif %}"
            "{% if protocolo %} (Protocolo: {{protocolo}}){% endif %}"
            "{% if data_envio %}, encaminhado em {{data_envio}}{% endif %}.\n\n"
            "{% if data_ultima_cobranca %}Ressaltamos que já houve cobrança anterior em {{data_ultima_cobranca}}.\n\n{% endif %}"
            "Solicitamos que a devolutiva seja registrada no sistema no prazo de <b>{{prazo}}</b>.\n\n"
            "Caso não seja possível atender no prazo, solicitamos informar justificativa e nova previsão de atendimento.\n\n"
            "{% if contato_retorno %}<b>Contato para retorno</b>: {{contato_retorno}}\n\n{% endif %}"
            "Sem mais para o momento."
        ),
        assinatura_template=(
            "{{assinante_nome or 'Nome do(a) responsável'}}\n"
            "{{assinante_cargo or 'Cargo'}}"
            "{% if assinante_orgao %}\n{{assinante_orgao}}{% endif %}"
        ),
        campos_obrigatorios=["referencia", "prazo"],
        campos_opcionais=[
            "numero_referencia",
            "data_envio",
            "data_ultima_cobranca",
            "protocolo",
            "contato_retorno",
            "assinante_nome",
            "assinante_cargo",
            "assinante_orgao",
        ],
        numero_titulo="OFÍCIO",
    ),
    ModeloDocumento(
        key="oficio_resposta_devolutiva",
        tipo="oficio",
        titulo="OFÍCIO — Devolutiva/Resposta",
        descricao="Resposta formal (devolutiva) ao encaminhamento/ofício recebido, com situação, providências e encaminhamentos.",
        assunto_padrao="Devolutiva/Resposta",
        corpo_template=(
            "{% if destinatario_nome %}"
            "<b>{{destinatario_nome}}</b><br/>"
            "{% if destinatario_cargo %}{{destinatario_cargo}}<br/>{% endif %}"
            "{% if destinatario_orgao %}{{destinatario_orgao}}<br/>{% endif %}"
            "<br/>{% endif %}"
            "Prezado(a) {% if destinatario_nome %}{{destinatario_nome}}{% else %}Senhor(a){% endif %},\n\n"
            "Em resposta a <b>{{referencia}}</b>"
            "{% if numero_referencia %} (Ofício nº {{numero_referencia}}){% endif %}"
            "{% if protocolo %} (Protocolo: {{protocolo}}){% endif %}, apresentamos a devolutiva a seguir:\n\n"
            "<b>1. Situação</b>\n{{situacao}}\n\n"
            "<b>2. Providências adotadas</b>\n{{providencias}}\n\n"
            "{% if data_atendimento %}<b>3. Data do atendimento</b>: {{data_atendimento}}\n{% endif %}"
            "{% if responsavel_atendimento %}<b>Responsável</b>: {{responsavel_atendimento}}\n{% endif %}"
            "{% if encaminhamentos %}\n<b>4. Encaminhamentos</b>\n{{encaminhamentos}}\n{% endif %}"
            "{% if observacoes %}\n<b>Observações</b>\n{{observacoes}}\n{% endif %}"
            "\nSem mais para o momento."
        ),
        assinatura_template=(
            "{{assinante_nome or 'Nome do(a) responsável'}}\n"
            "{{assinante_cargo or 'Cargo'}}"
            "{% if assinante_orgao %}\n{{assinante_orgao}}{% endif %}"
        ),
        campos_obrigatorios=["referencia", "situacao", "providencias"],
        campos_opcionais=[
            "numero_referencia",
            "protocolo",
            "data_atendimento",
            "responsavel_atendimento",
            "encaminhamentos",
            "observacoes",
            "assinante_nome",
            "assinante_cargo",
            "assinante_orgao",
        ],
        numero_titulo="OFÍCIO",
    ),
    ModeloDocumento(
        key="oficio_comunicado_rede_intersetorial",
        tipo="oficio",
        titulo="OFÍCIO — Comunicado de Rede Intersetorial",
        descricao="Comunicado formal para a Rede Intersetorial (tema, contexto e ações solicitadas).",
        assunto_padrao="Comunicado de Rede Intersetorial",
        corpo_template=(
            "{% if destinatario_orgao %}"
            "À/ao <b>{{destinatario_orgao}}</b><br/>"
            "{% if destinatario_nome %}A/C {{destinatario_nome}}<br/>{% endif %}"
            "{% if destinatario_cargo %}{{destinatario_cargo}}<br/>{% endif %}"
            "<br/>{% endif %}"
            "Prezados(as),\n\n"
            "Comunicamos à Rede Intersetorial o seguinte tema/assunto: <b>{{tema}}</b>.\n\n"
            "<b>Contexto</b>\n{{contexto}}\n\n"
            "<b>Ações solicitadas</b>\n{{acoes_solicitadas}}\n\n"
            "{% if prazo %}<b>Prazo sugerido</b>: {{prazo}}\n\n{% endif %}"
            "{% if contato_retorno %}<b>Contato</b>: {{contato_retorno}}\n\n{% endif %}"
            "Sem mais para o momento."
        ),
        assinatura_template=(
            "{{assinante_nome or 'Nome do(a) responsável'}}\n"
            "{{assinante_cargo or 'Cargo'}}"
            "{% if assinante_orgao %}\n{{assinante_orgao}}{% endif %}"
        ),
        campos_obrigatorios=["tema", "contexto", "acoes_solicitadas"],
        campos_opcionais=[
            "prazo",
            "contato_retorno",
            "assinante_nome",
            "assinante_cargo",
            "assinante_orgao",
        ],
        numero_titulo="OFÍCIO",
    ),
    ModeloDocumento(
        key="oficio_convocacao_ciencia",
        tipo="oficio",
        titulo="OFÍCIO — Convocação (com ciência)",
        descricao="Convocação/Notificação para comparecimento com seção de ciência/recebido (assinatura do(a) convocado(a)).",
        assunto_padrao="Convocação",
        corpo_template=(
            "<b>{{nome_convocado}}</b>"
            "{% if documento_convocado %} ({{documento_convocado}}){% endif %}\n\n"
            "Fica o(a) Sr(a). convocado(a) a comparecer em <b>{{data_comparecimento}}</b>"
            "{% if horario_comparecimento %} às <b>{{horario_comparecimento}}</b>{% endif %}, "
            "no local <b>{{local_comparecimento}}</b>.\n\n"
            "{% if motivo %}<b>Motivo</b>\n{{motivo}}\n\n{% endif %}"
            "{% if orientacoes %}<b>Orientações</b>\n{{orientacoes}}\n\n{% endif %}"
            "Solicitamos que traga documentos pessoais e comprovantes pertinentes, quando disponíveis.\n\n"
            "<b>CIÊNCIA/RECEBIDO</b>\n\n"
            "Declaro ter ciência do conteúdo deste documento.\n\n"
            "Nome: _________________________________\n"
            "Assinatura: ____________________________\n"
            "Data: ____/____/______"
        ),
        assinatura_template=(
            "{{assinante_nome or 'Responsável'}}\n"
            "{{assinante_cargo or 'Cargo'}}"
        ),
        campos_obrigatorios=["nome_convocado", "data_comparecimento", "local_comparecimento"],
        campos_opcionais=[
            "documento_convocado",
            "horario_comparecimento",
            "motivo",
            "orientacoes",
            "assinante_nome",
            "assinante_cargo",
        ],
        numero_titulo="OFÍCIO",
    ),

]


_MAP: Dict[str, ModeloDocumento] = {}
for m in MODELOS:
    _MAP[_norm(m.key)] = m
    _MAP[_norm(m.titulo)] = m


def listar_modelos() -> List[ModeloDocumento]:
    return list(MODELOS)


def get_modelo(chave_ou_titulo: str) -> Optional[ModeloDocumento]:
    return _MAP.get(_norm(chave_ou_titulo or ""))
