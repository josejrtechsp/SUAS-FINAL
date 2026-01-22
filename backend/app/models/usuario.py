# app/models/usuario.py
from typing import Optional
from sqlmodel import SQLModel, Field


class Usuario(SQLModel, table=True):
    __tablename__ = "usuarios"

    id: Optional[int] = Field(default=None, primary_key=True)
    nome: str
    email: str = Field(index=True)
    perfil: str = Field(default="operador", index=True)

    # ✅ pode ser None para admin/consórcio
    municipio_id: Optional[int] = Field(default=None, index=True)

    senha_hash: str
    ativo: bool = Field(default=True)


class UsuarioRead(SQLModel):
    id: int
    nome: str
    email: str
    perfil: str

    # ✅ ESSA LINHA resolve MUITO 500 de login
    municipio_id: Optional[int] = None

    ativo: bool