from __future__ import annotations
from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field
from sqlalchemy import Column, Text

class CrasEncaminhamento(SQLModel, table=True):
    __tablename__ = "cras_encaminhamento"

    id: Optional[int] = Field(default=None, primary_key=True)

    municipio_id: int = Field(foreign_key="municipio.id", index=True)
    unidade_id: int = Field(foreign_key="cras_unidade.id", index=True)

    pessoa_id: Optional[int] = Field(default=None, foreign_key="pessoarua.id", index=True)
    # ✅ Ponte para cadastro mestre SUAS
    pessoa_suas_id: Optional[int] = Field(default=None, foreign_key="pessoa_suas.id", index=True)
    paif_id: Optional[int] = Field(default=None, foreign_key="paif_acompanhamento.id", index=True)

    destino_tipo: str = Field(index=True)   # saude|educacao|habitacao|trabalho|creas|osc|outro
    destino_nome: str

    motivo: str = Field(sa_column=Column(Text, nullable=False))
    observacao_operacional: Optional[str] = Field(default=None, sa_column=Column(Text))

    status: str = Field(default="enviado", index=True)  # enviado|recebido|agendado|atendido|devolutiva|concluido|cancelado

    enviado_em: datetime = Field(default_factory=datetime.utcnow, index=True)
    recebido_em: Optional[datetime] = None
    agendado_em: Optional[datetime] = None
    atendido_em: Optional[datetime] = None
    devolutiva_em: Optional[datetime] = None
    concluido_em: Optional[datetime] = None
    cancelado_em: Optional[datetime] = None

    prazo_devolutiva_dias: int = Field(default=7, index=True)

    criado_por_nome: Optional[str] = None
    atualizado_por_nome: Optional[str] = None

    criado_em: datetime = Field(default_factory=datetime.utcnow)
    atualizado_em: datetime = Field(default_factory=datetime.utcnow)

class CrasEncaminhamentoEvento(SQLModel, table=True):
    __tablename__ = "cras_encaminhamento_evento"

    id: Optional[int] = Field(default=None, primary_key=True)
    encaminhamento_id: int = Field(foreign_key="cras_encaminhamento.id", index=True)

    tipo: str = Field(index=True)           # enviado|recebido|agendado|atendido|devolutiva|concluido|cancelado
    detalhe: Optional[str] = Field(default=None, sa_column=Column(Text))

    por_nome: Optional[str] = None
    em: datetime = Field(default_factory=datetime.utcnow, index=True)
