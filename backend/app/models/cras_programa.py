from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from sqlmodel import SQLModel, Field


class CrasPrograma(SQLModel, table=True):
    """Programas e projetos do CRAS."""

    __tablename__ = "cras_programa"

    id: Optional[int] = Field(default=None, primary_key=True)

    municipio_id: int = Field(foreign_key="municipio.id", index=True)
    unidade_id: Optional[int] = Field(default=None, foreign_key="cras_unidade.id", index=True)

    nome: str = Field(index=True)
    publico_alvo: Optional[str] = Field(default=None, index=True)  # crianca|adolescente|adulto|idoso|mulher|...
    descricao: Optional[str] = Field(default=None, max_length=2000)

    capacidade_max: Optional[int] = None

    responsavel_usuario_id: Optional[int] = Field(default=None, foreign_key="usuarios.id", index=True)

    data_inicio: Optional[date] = None
    data_fim: Optional[date] = None

    status: str = Field(default="em_andamento", index=True, max_length=30)

    criado_em: datetime = Field(default_factory=datetime.utcnow, index=True)
    atualizado_em: datetime = Field(default_factory=datetime.utcnow, index=True)


class CrasProgramaParticipante(SQLModel, table=True):
    """Participação de pessoas em um programa/projeto."""

    __tablename__ = "cras_programa_participante"

    id: Optional[int] = Field(default=None, primary_key=True)

    programa_id: int = Field(foreign_key="cras_programa.id", index=True)
    pessoa_id: int = Field(foreign_key="pessoa_suas.id", index=True)

    caso_id: Optional[int] = Field(default=None, foreign_key="caso_cras.id", index=True)

    status: str = Field(default="ativo", index=True, max_length=30)
    data_inicio: Optional[date] = None
    data_fim: Optional[date] = None

    criado_em: datetime = Field(default_factory=datetime.utcnow, index=True)
