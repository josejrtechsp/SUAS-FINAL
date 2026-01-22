from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from sqlmodel import SQLModel, Field


class CrasPiaPlano(SQLModel, table=True):
    __tablename__ = "cras_pia_plano"

    id: Optional[int] = Field(default=None, primary_key=True)

    municipio_id: int = Field(foreign_key="municipio.id", index=True)
    unidade_id: int = Field(foreign_key="cras_unidade.id", index=True)
    caso_id: int = Field(foreign_key="caso_cras.id", index=True)

    resumo_diagnostico: Optional[str] = Field(default=None, max_length=4000)
    objetivos: Optional[str] = Field(default=None, max_length=4000)

    status: str = Field(default="ativo", index=True, max_length=20)  # ativo|finalizado
    data_inicio: Optional[date] = Field(default=None, index=True)
    data_revisao: Optional[date] = Field(default=None, index=True)

    criado_em: datetime = Field(default_factory=datetime.utcnow, index=True)
    atualizado_em: datetime = Field(default_factory=datetime.utcnow, index=True)


class CrasPiaAcao(SQLModel, table=True):
    __tablename__ = "cras_pia_acao"

    id: Optional[int] = Field(default=None, primary_key=True)

    plano_id: int = Field(foreign_key="cras_pia_plano.id", index=True)

    descricao: str = Field(max_length=2000)
    responsavel_usuario_id: Optional[int] = Field(default=None, foreign_key="usuarios.id", index=True)

    prazo: Optional[date] = Field(default=None, index=True)
    status: str = Field(default="pendente", index=True, max_length=20)  # pendente|em_andamento|concluida|cancelada

    evidencias_texto: Optional[str] = Field(default=None, max_length=4000)

    criado_em: datetime = Field(default_factory=datetime.utcnow, index=True)
    atualizado_em: datetime = Field(default_factory=datetime.utcnow, index=True)
