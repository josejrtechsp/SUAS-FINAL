from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import UniqueConstraint
from sqlmodel import Field, SQLModel


class MetaKpi(SQLModel, table=True):
    """Metas (KPIs) por município e (opcionalmente) por unidade.

    Exemplo de uso: definir metas mensais/anuais para indicadores do dashboard.
    """

    __tablename__ = "meta_kpi"
    __table_args__ = (
        UniqueConstraint(
            "municipio_id",
            "unidade_tipo",
            "unidade_id",
            "modulo",
            "kpi",
            "periodo",
            name="uq_meta_kpi_chave",
        ),
    )

    id: Optional[int] = Field(default=None, primary_key=True)

    # Escopo
    municipio_id: Optional[int] = Field(default=None, foreign_key="municipio.id", index=True)
    unidade_tipo: Optional[str] = Field(default=None, index=True)
    unidade_id: Optional[int] = Field(default=None, index=True)

    # Identidade
    modulo: str = Field(index=True)  # ex: "gestao", "rede", "cras"
    kpi: str = Field(index=True)     # ex: "pct_devolutiva_no_prazo"
    periodo: str = Field(default="mensal", index=True)  # mensal|trimestral|anual|etc

    # Valor meta (numérico)
    valor_meta: float = Field(default=0.0)

    # Controle
    ativo: bool = Field(default=True, index=True)
    criado_em: datetime = Field(default_factory=datetime.utcnow, index=True)
    atualizado_em: datetime = Field(default_factory=datetime.utcnow, index=True)
