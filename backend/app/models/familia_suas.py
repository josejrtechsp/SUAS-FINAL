from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel, Field


class FamiliaSUAS(SQLModel, table=True):
    """Cadastro de família (SUAS)."""

    __tablename__ = "familia_suas"

    id: Optional[int] = Field(default=None, primary_key=True)

    municipio_id: Optional[int] = Field(default=None, foreign_key="municipio.id", index=True)

    nis_familia: Optional[str] = Field(default=None, index=True)

    endereco: Optional[str] = None
    bairro: Optional[str] = Field(default=None, index=True)
    territorio: Optional[str] = Field(default=None, index=True)

    referencia_pessoa_id: Optional[int] = Field(default=None, foreign_key="pessoa_suas.id", index=True)

    observacoes: Optional[str] = Field(default=None, max_length=1000)

    criado_em: datetime = Field(default_factory=datetime.utcnow, index=True)
    atualizado_em: datetime = Field(default_factory=datetime.utcnow, index=True)


class FamiliaMembro(SQLModel, table=True):
    """Vínculo pessoa ⇄ família."""

    __tablename__ = "familia_membro"

    id: Optional[int] = Field(default=None, primary_key=True)

    familia_id: int = Field(foreign_key="familia_suas.id", index=True)
    pessoa_id: int = Field(foreign_key="pessoa_suas.id", index=True)

    parentesco: Optional[str] = Field(default=None, index=True)
    responsavel_bool: bool = Field(default=False, index=True)

    criado_em: datetime = Field(default_factory=datetime.utcnow, index=True)
