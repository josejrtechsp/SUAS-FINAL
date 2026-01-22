from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from sqlmodel import SQLModel, Field


class ScfvTurma(SQLModel, table=True):
    __tablename__ = "scfv_turma"

    id: Optional[int] = Field(default=None, primary_key=True)

    municipio_id: int = Field(foreign_key="municipio.id", index=True)
    unidade_id: int = Field(foreign_key="cras_unidade.id", index=True)

    nome: str = Field(index=True, max_length=200)
    publico: Optional[str] = Field(default=None, index=True, max_length=50)  # crianca|adolescente|adulto|idoso|mulher|pcd|outros
    faixa_etaria: Optional[str] = Field(default=None, index=True, max_length=80)
    dias: Optional[str] = Field(default=None, max_length=120)  # ex: "Seg/Qua" ou "2ª,4ª"
    horario: Optional[str] = Field(default=None, max_length=80)  # ex: "14:00-16:00"
    vagas: Optional[int] = Field(default=None)

    local: Optional[str] = Field(default=None, max_length=200)
    ativo: bool = Field(default=True, index=True)

    criado_em: datetime = Field(default_factory=datetime.utcnow, index=True)
    atualizado_em: datetime = Field(default_factory=datetime.utcnow, index=True)


class ScfvParticipante(SQLModel, table=True):
    __tablename__ = "scfv_participante"

    id: Optional[int] = Field(default=None, primary_key=True)

    turma_id: int = Field(foreign_key="scfv_turma.id", index=True)
    pessoa_id: int = Field(foreign_key="pessoa_suas.id", index=True)

    caso_id: Optional[int] = Field(default=None, foreign_key="caso_cras.id", index=True)

    status: str = Field(default="ativo", index=True, max_length=20)  # ativo|encerrado
    data_inicio: Optional[date] = Field(default=None, index=True)
    data_fim: Optional[date] = Field(default=None, index=True)

    criado_em: datetime = Field(default_factory=datetime.utcnow, index=True)
    atualizado_em: datetime = Field(default_factory=datetime.utcnow, index=True)


class ScfvPresenca(SQLModel, table=True):
    __tablename__ = "scfv_presenca"

    id: Optional[int] = Field(default=None, primary_key=True)

    participante_id: int = Field(foreign_key="scfv_participante.id", index=True)
    data: date = Field(index=True)

    presente_bool: bool = Field(default=True, index=True)
    observacao: Optional[str] = Field(default=None, max_length=500)

    criado_em: datetime = Field(default_factory=datetime.utcnow, index=True)
    atualizado_em: datetime = Field(default_factory=datetime.utcnow, index=True)
