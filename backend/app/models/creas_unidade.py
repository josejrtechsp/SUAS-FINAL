from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel, Field


class CreasUnidade(SQLModel, table=True):
    """Unidade CREAS (equipamento especializado)."""

    __tablename__ = "creas_unidade"

    id: Optional[int] = Field(default=None, primary_key=True)
    municipio_id: int = Field(foreign_key="municipio.id", index=True)

    nome: str
    ativo: bool = Field(default=True, index=True)

    criado_em: datetime = Field(default_factory=datetime.utcnow)
