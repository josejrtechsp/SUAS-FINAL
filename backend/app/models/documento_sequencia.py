from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import UniqueConstraint
from sqlmodel import Field, SQLModel


class DocumentoSequencia(SQLModel, table=True):
    """Sequência de numeração por município/tipo/ano e (opcionalmente) emissor.

    Benefícios:
      - reseta automaticamente por ano (chave inclui ano)
      - permite série por secretaria (emissor_key) quando configurado
      - evita depender de scan em documento_emitido para descobrir o próximo número

    emissor_key:
      - "smas", "cras", "creas"...
      - "" (vazio) representa série única do município.
    """

    __tablename__ = "documento_sequencia"
    __table_args__ = (
        UniqueConstraint(
            "municipio_id",
            "tipo",
            "ano",
            "emissor_key",
            name="uq_documento_sequencia",
        ),
    )

    id: Optional[int] = Field(default=None, primary_key=True)

    municipio_id: int = Field(index=True)
    tipo: str = Field(index=True)
    ano: int = Field(index=True)

    emissor_key: str = Field(default="", index=True, max_length=40)

    seq_atual: int = 0

    atualizado_em: datetime = Field(default_factory=datetime.utcnow)
