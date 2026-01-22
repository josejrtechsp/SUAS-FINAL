from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from sqlmodel import SQLModel, Field


class PessoaSUAS(SQLModel, table=True):
    """Cadastro base SUAS (indivíduo)."""

    __tablename__ = "pessoa_suas"

    id: Optional[int] = Field(default=None, primary_key=True)

    municipio_id: Optional[int] = Field(default=None, foreign_key="municipio.id", index=True)

    nome: str = Field(index=True)
    nome_social: Optional[str] = Field(default=None, index=True)

    cpf: Optional[str] = Field(default=None, index=True)
    nis: Optional[str] = Field(default=None, index=True)

    data_nascimento: Optional[date] = None
    sexo: Optional[str] = None

    telefone: Optional[str] = None
    email: Optional[str] = None

    endereco: Optional[str] = None
    bairro: Optional[str] = None
    territorio: Optional[str] = None

    observacoes: Optional[str] = Field(default=None, max_length=1000)

    criado_em: datetime = Field(default_factory=datetime.utcnow, index=True)
    atualizado_em: datetime = Field(default_factory=datetime.utcnow, index=True)
