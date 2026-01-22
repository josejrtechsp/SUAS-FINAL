# app/models/encaminhamentos.py
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel, Field
from sqlalchemy import Column, Text


class EncaminhamentoIntermunicipal(SQLModel, table=True):
    __tablename__ = "encaminhamentos_intermunicipais"
    __table_args__ = {"extend_existing": True}

    id: Optional[int] = Field(default=None, primary_key=True, index=True)

    # vínculos (sem FK por enquanto para não travar seu create_all)
    pessoa_id: int = Field(index=True)
    caso_id: Optional[int] = Field(default=None, index=True)

    municipio_origem_id: Optional[int] = Field(default=None, index=True)
    municipio_destino_id: int = Field(index=True)

    # conteúdo
    motivo: str = Field(sa_column=Column(Text, nullable=False))
    observacoes: Optional[str] = Field(default=None, sa_column=Column(Text))

    consentimento_registrado: bool = Field(default=False, index=True)

    # workflow
    status: str = Field(default="solicitado", max_length=40, index=True)

    # marcos
    contato_em: Optional[datetime] = Field(default=None)
    aceite_em: Optional[datetime] = Field(default=None)
    agendado_em: Optional[datetime] = Field(default=None)
    passagem_em: Optional[datetime] = Field(default=None)
    contrarreferencia_em: Optional[datetime] = Field(default=None)
    concluido_em: Optional[datetime] = Field(default=None)
    cancelado_em: Optional[datetime] = Field(default=None)

    # passagem (benefício eventual)
    passagem_numero: Optional[str] = Field(default=None, max_length=80)
    passagem_empresa: Optional[str] = Field(default=None, max_length=120)
    passagem_data_viagem: Optional[datetime] = Field(default=None)

    kit_lanche: bool = Field(default=False)
    kit_higiene: bool = Field(default=False)
    kit_mapa_info: bool = Field(default=False)

    justificativa_passagem: Optional[str] = Field(default=None, sa_column=Column(Text))
    autorizado_por_nome: Optional[str] = Field(default=None, max_length=160)

    # auditoria mínima
    criado_em: datetime = Field(default_factory=datetime.utcnow)
    atualizado_em: datetime = Field(default_factory=datetime.utcnow)


class EncaminhamentoEvento(SQLModel, table=True):
    __tablename__ = "encaminhamentos_eventos"
    __table_args__ = {"extend_existing": True}

    id: Optional[int] = Field(default=None, primary_key=True, index=True)

    encaminhamento_id: int = Field(index=True)

    tipo: str = Field(max_length=40, index=True)  # solicitado/contato/aceito/...
    detalhe: Optional[str] = Field(default=None, sa_column=Column(Text))

    por_nome: Optional[str] = Field(default=None, max_length=160)
    em: datetime = Field(default_factory=datetime.utcnow, index=True)

class IntermunicipalInbox(SQLModel, table=True):
    """Estado de caixa de entrada por município para encaminhamentos intermunicipais.

    1 linha por (encaminhamento_id, municipio_id).
    - unread=True indica que há novidade para o município.
    - ultimo_evento_em serve para ordenar a inbox e calcular alertas de SLA.
    """

    __tablename__ = "intermunicipal_inbox"
    __table_args__ = {"extend_existing": True}

    id: Optional[int] = Field(default=None, primary_key=True, index=True)

    encaminhamento_id: int = Field(index=True)
    municipio_id: int = Field(index=True)  # município destinatário desta 'inbox'

    # estado do fluxo no momento do último evento
    ultimo_status: Optional[str] = Field(default=None, max_length=40, index=True)
    proximo_status: Optional[str] = Field(default=None, max_length=40)
    pendente_de: Optional[str] = Field(default=None, max_length=16)  # ORIGEM/DESTINO/AMBOS

    # leitura
    unread: bool = Field(default=True, index=True)
    lido_em: Optional[datetime] = Field(default=None)
    lido_por_id: Optional[int] = Field(default=None, index=True)
    lido_por_nome: Optional[str] = Field(default=None, max_length=160)

    # ordenação/auditoria
    ultimo_evento_em: datetime = Field(default_factory=datetime.utcnow, index=True)
    criado_em: datetime = Field(default_factory=datetime.utcnow, index=True)
    atualizado_em: datetime = Field(default_factory=datetime.utcnow, index=True)

class IntermunicipalCasoVinculo(SQLModel, table=True):
    """Vínculo entre encaminhamento intermunicipal e caso criado/assumido no município.

    - Permite que o DESTINO assuma o atendimento criando um CasoPopRua local.
    - Mantém o encaminhamento como trilha auditável (origem↔destino).

    1 linha por (encaminhamento_id, municipio_id).
    """

    __tablename__ = "intermunicipal_caso_vinculos"
    __table_args__ = {"extend_existing": True}

    id: Optional[int] = Field(default=None, primary_key=True, index=True)

    encaminhamento_id: int = Field(index=True)
    municipio_id: int = Field(index=True)
    caso_id: int = Field(index=True)

    criado_em: datetime = Field(default_factory=datetime.utcnow, index=True)
    criado_por_id: Optional[int] = Field(default=None, index=True)
    criado_por_nome: Optional[str] = Field(default=None, max_length=160)

    atualizado_em: datetime = Field(default_factory=datetime.utcnow, index=True)

class IntermunicipalAnexo(SQLModel, table=True):
    """Anexos/evidências do encaminhamento intermunicipal (uploads).

    Armazenamento MVP em disco (UPLOAD_ROOT), com URL /uploads/...
    """

    __tablename__ = "intermunicipal_anexos"
    __table_args__ = {"extend_existing": True}

    id: Optional[int] = Field(default=None, primary_key=True, index=True)

    encaminhamento_id: int = Field(index=True)
    municipio_id: int = Field(index=True)

    titulo: str = Field(max_length=200)
    tipo: Optional[str] = Field(default=None, max_length=80)

    arquivo_nome: Optional[str] = Field(default=None, max_length=260)
    content_type: Optional[str] = Field(default=None, max_length=120)
    tamanho_bytes: Optional[int] = Field(default=None)

    # URL pública (servida por /uploads)
    url: str = Field(sa_column=Column(Text, nullable=False))

    criado_em: datetime = Field(default_factory=datetime.utcnow, index=True)
    criado_por_id: Optional[int] = Field(default=None, index=True)
    criado_por_nome: Optional[str] = Field(default=None, max_length=160)


class IntermunicipalContrarreferencia(SQLModel, table=True):
    """Contrarreferência estruturada registrada pelo município DESTINO."""

    __tablename__ = "intermunicipal_contrarreferencias"
    __table_args__ = {"extend_existing": True}

    id: Optional[int] = Field(default=None, primary_key=True, index=True)

    encaminhamento_id: int = Field(index=True)
    municipio_id: int = Field(index=True)  # município DESTINO que registrou

    resumo: Optional[str] = Field(default=None, sa_column=Column(Text))
    atendimento_realizado: Optional[str] = Field(default=None, sa_column=Column(Text))
    situacao_atual: Optional[str] = Field(default=None, sa_column=Column(Text))
    encaminhamentos_realizados: Optional[str] = Field(default=None, sa_column=Column(Text))
    recomendacoes: Optional[str] = Field(default=None, sa_column=Column(Text))

    # lista de IDs de anexos (json em texto)
    anexo_ids_json: Optional[str] = Field(default=None, sa_column=Column(Text))

    documento_emitido_id: Optional[int] = Field(default=None, index=True)

    criado_em: datetime = Field(default_factory=datetime.utcnow, index=True)
    criado_por_id: Optional[int] = Field(default=None, index=True)
    criado_por_nome: Optional[str] = Field(default=None, max_length=160)

    atualizado_em: datetime = Field(default_factory=datetime.utcnow, index=True)


class IntermunicipalRecebimento(SQLModel, table=True):
    """Confirmação de recebimento da contrarreferência pelo município de ORIGEM.

    1 linha por (encaminhamento_id, municipio_id=ORIGEM).
    Criado como tabela separada para evitar migração/ALTER TABLE em bases já existentes.
    """

    __tablename__ = "intermunicipal_recebimentos"
    __table_args__ = {"extend_existing": True}

    id: Optional[int] = Field(default=None, primary_key=True, index=True)

    encaminhamento_id: int = Field(index=True)
    municipio_id: int = Field(index=True)  # município de ORIGEM

    contrarreferencia_id: Optional[int] = Field(default=None, index=True)

    observacoes: Optional[str] = Field(default=None, sa_column=Column(Text))

    documento_emitido_id: Optional[int] = Field(default=None, index=True)

    recebido_em: datetime = Field(default_factory=datetime.utcnow, index=True)
    recebido_por_id: Optional[int] = Field(default=None, index=True)
    recebido_por_nome: Optional[str] = Field(default=None, max_length=160)
