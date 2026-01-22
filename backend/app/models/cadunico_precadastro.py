from __future__ import annotations

from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field

class CadunicoPreCadastro(SQLModel, table=True):
    __tablename__ = "cadunico_precadastro"

    id: Optional[int] = Field(default=None, primary_key=True)

    municipio_id: int = Field(foreign_key="municipio.id", index=True)
    unidade_id: int = Field(foreign_key="cras_unidade.id", index=True)

    pessoa_id: Optional[int] = Field(default=None, foreign_key="pessoa_suas.id", index=True)
    familia_id: Optional[int] = Field(default=None, foreign_key="familia_suas.id", index=True)
    caso_id: Optional[int] = Field(default=None, foreign_key="caso_cras.id", index=True)

    status: str = Field(default="pendente", index=True, max_length=30)  # pendente|agendado|finalizado|nao_compareceu
    data_agendada: Optional[datetime] = Field(default=None, index=True)

    observacoes: Optional[str] = Field(default=None, max_length=2000)

    criado_em: datetime = Field(default_factory=datetime.utcnow, index=True)
    atualizado_em: datetime = Field(default_factory=datetime.utcnow, index=True)
