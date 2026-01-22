from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel, Field


class PessoaIdentidadeLink(SQLModel, table=True):
    """Liga o universo PopRua (pessoarua) ao universo SUAS (pessoa_suas).

    Objetivo:
    - permitir que PAIF/Triagem/Encaminhamentos (PopRua) apareçam na Ficha 360 (SUAS)
    - evitar duplicidade (um vínculo por pessoarua)
    """

    __tablename__ = "pessoa_identidade_link"

    id: Optional[int] = Field(default=None, primary_key=True)

    pessoarua_id: int = Field(foreign_key="pessoarua.id", index=True, unique=True)
    pessoa_suas_id: int = Field(foreign_key="pessoa_suas.id", index=True)

    criado_em: datetime = Field(default_factory=datetime.utcnow, index=True)
