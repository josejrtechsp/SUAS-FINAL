from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel, Field


class AtendimentoBase(SQLModel):
    municipio_id: Optional[int] = Field(
        default=None, foreign_key="municipio.id"
    )
    tipo_atendimento: str
    equipamento: str
    resultado: str
    descricao: Optional[str] = None


class Atendimento(AtendimentoBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    pessoa_id: int = Field(foreign_key="pessoarua.id")
    data_atendimento: datetime = Field(default_factory=datetime.utcnow)