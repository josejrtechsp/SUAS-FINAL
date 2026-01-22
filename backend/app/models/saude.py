# app/models/saude.py
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel, Field
from sqlalchemy import Column, Text


class SaudeClinicoRegistro(SQLModel, table=True):
    """
    MÓDULO CLÍNICO (somente Saúde)
    - guarda JSON livre (conteudo_json) + metadados básicos
    """
    __tablename__ = "saude_clinico_registros"

    id: Optional[int] = Field(default=None, primary_key=True)
    caso_id: int = Field(foreign_key="casopoprua.id", index=True)

    criado_em: datetime = Field(default_factory=datetime.utcnow, index=True)
    criado_por_user_id: Optional[int] = Field(default=None, foreign_key="usuarios.id")
    criado_por_nome: Optional[str] = Field(default=None)

    tipo_registro: str = Field(default="registro", index=True)

    # JSON guardado como texto (SQLite)
    conteudo_json: str = Field(sa_column=Column(Text, nullable=False))


class SaudeIntersetorialRegistro(SQLModel, table=True):
    """
    CAMADA INTERSETORIAL (mínimo necessário)
    - pode ser lida por outros setores (assistência/habitação/justiça)
    - NÃO guarda diagnóstico, CID, HIV/TB etc.
    - guarda apenas logística/funcionalidade/encaminhamentos de saúde
    """
    __tablename__ = "saude_intersetorial_registros"

    id: Optional[int] = Field(default=None, primary_key=True)
    caso_id: int = Field(foreign_key="casopoprua.id", index=True)

    criado_em: datetime = Field(default_factory=datetime.utcnow, index=True)
    atualizado_em: datetime = Field(default_factory=datetime.utcnow, index=True)

    # status operacional do fluxo de saúde (intersetorial)
    status: str = Field(default="aberto", index=True)  # aberto | em_andamento | concluido | cancelado

    # JSON mínimo (sem clínica)
    conteudo_json: str = Field(sa_column=Column(Text, nullable=False))