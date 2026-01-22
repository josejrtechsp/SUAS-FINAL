from __future__ import annotations

from datetime import datetime, date
from typing import Optional

from sqlmodel import SQLModel, Field
from sqlalchemy import Column, Text


class ProntuarioPES(SQLModel, table=True):
    """Prontuário Eletrônico Simplificado (PES) - campos estruturados."""
    __tablename__ = "prontuario_pes"
    __table_args__ = {"extend_existing": True}

    id: Optional[int] = Field(default=None, primary_key=True)

    municipio_id: int = Field(foreign_key="municipio.id", index=True)
    unidade_id: Optional[int] = Field(default=None, index=True)

    pessoa_id: Optional[int] = Field(default=None, foreign_key="pessoa_suas.id", index=True)
    familia_id: Optional[int] = Field(default=None, foreign_key="familia_suas.id", index=True)
    caso_id: Optional[int] = Field(default=None, index=True)

    forma_acesso: Optional[str] = Field(default=None, max_length=40, index=True)
    primeiro_atendimento_em: Optional[date] = Field(default=None, index=True)

    inserido_paif_em: Optional[date] = Field(default=None, index=True)
    desligado_paif_em: Optional[date] = Field(default=None, index=True)

    observacoes_json: Optional[str] = Field(default=None, sa_column=Column(Text))

    criado_em: datetime = Field(default_factory=datetime.utcnow, index=True)
    atualizado_em: datetime = Field(default_factory=datetime.utcnow, index=True)
    atualizado_por_nome: Optional[str] = Field(default=None, max_length=120)
