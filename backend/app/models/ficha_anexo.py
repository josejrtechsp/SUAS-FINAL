from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel, Field


class FichaAnexo(SQLModel, table=True):
    __tablename__ = "ficha_anexo"

    id: Optional[int] = Field(default=None, primary_key=True)

    municipio_id: int = Field(foreign_key="municipio.id", index=True)

    alvo_tipo: str = Field(index=True, max_length=20)  # pessoa|familia
    alvo_id: int = Field(index=True)

    titulo: str = Field(max_length=200)
    url: str = Field(max_length=2000)
    tipo: Optional[str] = Field(default=None, max_length=50)  # opcional: "RG", "CPF", "Comprovante", etc.

    criado_em: datetime = Field(default_factory=datetime.utcnow, index=True)
    criado_por_usuario_id: Optional[int] = Field(default=None, index=True)
    criado_por_nome: Optional[str] = Field(default=None, max_length=120)
