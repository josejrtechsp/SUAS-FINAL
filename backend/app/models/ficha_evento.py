from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel, Field


class FichaEvento(SQLModel, table=True):
    __tablename__ = "ficha_evento"

    id: Optional[int] = Field(default=None, primary_key=True)

    municipio_id: int = Field(foreign_key="municipio.id", index=True)

    alvo_tipo: str = Field(index=True, max_length=20)  # pessoa|familia
    alvo_id: int = Field(index=True)

    tipo: str = Field(index=True, max_length=80)       # ex: "abertura_via_relatorio"
    detalhe: Optional[str] = Field(default=None, max_length=2000)

    criado_em: datetime = Field(default_factory=datetime.utcnow, index=True)
    criado_por_usuario_id: Optional[int] = Field(default=None, index=True)
    criado_por_nome: Optional[str] = Field(default=None, max_length=120)
