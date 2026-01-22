from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import UniqueConstraint
from sqlmodel import Field, SQLModel


class SlaRegra(SQLModel, table=True):
    """Regra de SLA por município e (opcionalmente) por unidade.

    Chave lógica (única):
      municipio_id, unidade_tipo, unidade_id, modulo, etapa
    """

    __tablename__ = "sla_regra"
    __table_args__ = (
        UniqueConstraint(
            "municipio_id",
            "unidade_tipo",
            "unidade_id",
            "modulo",
            "etapa",
            name="uq_sla_regra_chave",
        ),
    )

    id: Optional[int] = Field(default=None, primary_key=True)

    # Escopo
    municipio_id: Optional[int] = Field(default=None, foreign_key="municipio.id", index=True)
    unidade_tipo: Optional[str] = Field(default=None, index=True)  # ex: "cras", "creas", "osc"
    unidade_id: Optional[int] = Field(default=None, index=True)    # ex: id do CRAS/CREAS/OSC

    # Identidade do SLA
    modulo: str = Field(index=True)  # ex: "cras_encaminhamento", "rede_intermunicipal"
    etapa: str = Field(index=True)   # status/etapa: "enviado", "solicitado", etc.

    # Valor
    sla_dias: int = Field(default=7)

    # Controle
    ativo: bool = Field(default=True, index=True)
    criado_em: datetime = Field(default_factory=datetime.utcnow, index=True)
    atualizado_em: datetime = Field(default_factory=datetime.utcnow, index=True)
