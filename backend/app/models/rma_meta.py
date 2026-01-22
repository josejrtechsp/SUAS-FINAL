from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel, Field
from sqlalchemy import Column, Text


class RmaMeta(SQLModel, table=True):
    """Metas do RMA por mês/serviço (opcionalmente por unidade)."""
    __tablename__ = "rma_meta"
    __table_args__ = {"extend_existing": True}

    id: Optional[int] = Field(default=None, primary_key=True)

    municipio_id: int = Field(foreign_key="municipio.id", index=True)
    unidade_id: Optional[int] = Field(default=None, index=True)

    mes: str = Field(index=True, max_length=7)  # YYYY-MM
    servico: str = Field(index=True, max_length=40)

    meta_total: int = Field(default=0)
    meta_json: Optional[str] = Field(default=None, sa_column=Column(Text))

    criado_em: datetime = Field(default_factory=datetime.utcnow, index=True)
    atualizado_em: datetime = Field(default_factory=datetime.utcnow, index=True)
    atualizado_por_nome: Optional[str] = Field(default=None, max_length=120)
