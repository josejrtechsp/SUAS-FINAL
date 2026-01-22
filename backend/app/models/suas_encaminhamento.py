from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel, Field
from sqlalchemy import Column, Text


class SuasEncaminhamento(SQLModel, table=True):
    """Encaminhamento interno entre módulos (CRAS/CREAS/POPRUA).

    Status: enviado|recebido|em_atendimento|retorno_enviado|concluido|cancelado
    """

    __tablename__ = "suas_encaminhamento"
    __table_args__ = {"extend_existing": True}

    id: Optional[int] = Field(default=None, primary_key=True)

    municipio_id: int = Field(foreign_key="municipio.id", index=True)

    origem_modulo: str = Field(default="CRAS", index=True, max_length=20)
    destino_modulo: str = Field(default="CREAS", index=True, max_length=20)

    origem_unidade_id: Optional[int] = Field(default=None, index=True)
    destino_unidade_id: Optional[int] = Field(default=None, index=True)

    origem_caso_id: Optional[int] = Field(default=None, index=True)
    origem_caso_label: Optional[str] = Field(default=None, max_length=120)

    destino_caso_id: Optional[int] = Field(default=None, index=True)

    # vínculos SUAS
    pessoa_id: Optional[int] = Field(default=None, foreign_key="pessoa_suas.id", index=True)
    familia_id: Optional[int] = Field(default=None, foreign_key="familia_suas.id", index=True)

    assunto: str = Field(default="Encaminhamento SUAS", max_length=200)
    motivo: str = Field(sa_column=Column(Text, nullable=False))

    prioridade: str = Field(default="media", max_length=20, index=True)  # alta|media|baixa
    prazo_retorno: Optional[str] = Field(default=None, max_length=10, index=True)  # YYYY-MM-DD

    status: str = Field(default="enviado", max_length=40, index=True)
    status_em: datetime = Field(default_factory=datetime.utcnow, index=True)

    retorno_texto: Optional[str] = Field(default=None, sa_column=Column(Text))
    retorno_detalhe: Optional[str] = Field(default=None, sa_column=Column(Text))
    retorno_modelo_json: Optional[str] = Field(default=None, sa_column=Column(Text))
    retorno_em: Optional[datetime] = Field(default=None, index=True)

    cobranca_total: int = Field(default=0, index=True)
    cobranca_ultimo_em: Optional[datetime] = Field(default=None)
    cobranca_ultimo_texto: Optional[str] = Field(default=None, sa_column=Column(Text))

    criado_em: datetime = Field(default_factory=datetime.utcnow, index=True)
    atualizado_em: datetime = Field(default_factory=datetime.utcnow, index=True)

    criado_por_usuario_id: Optional[int] = Field(default=None, index=True)
    criado_por_nome: Optional[str] = Field(default=None, max_length=160)
    atualizado_por_nome: Optional[str] = Field(default=None, max_length=160)


class SuasEncaminhamentoEvento(SQLModel, table=True):
    __tablename__ = "suas_encaminhamento_evento"
    __table_args__ = {"extend_existing": True}

    id: Optional[int] = Field(default=None, primary_key=True)

    encaminhamento_id: int = Field(foreign_key="suas_encaminhamento.id", index=True)

    tipo: str = Field(max_length=40, index=True)
    detalhe: Optional[str] = Field(default=None, sa_column=Column(Text))

    por_usuario_id: Optional[int] = Field(default=None, index=True)
    por_nome: Optional[str] = Field(default=None, max_length=160)

    em: datetime = Field(default_factory=datetime.utcnow, index=True)
