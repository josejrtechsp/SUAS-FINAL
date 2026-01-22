from typing import Optional

from sqlmodel import SQLModel, Field


class Municipio(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    nome: str
    uf: str
    codigo_ibge: Optional[str] = None
    ativo: bool = True