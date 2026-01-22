from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel, Field


class CasoCras(SQLModel, table=True):
    """Caso do CRAS com 'linha do metrô' + validação + estagnação."""

    __tablename__ = "caso_cras"

    id: Optional[int] = Field(default=None, primary_key=True)

    municipio_id: int = Field(foreign_key="municipio.id", index=True)
    unidade_id: int = Field(foreign_key="cras_unidade.id", index=True)

    # familia | individuo
    tipo_caso: str = Field(default="familia", index=True, max_length=20)

    pessoa_id: Optional[int] = Field(default=None, foreign_key="pessoa_suas.id", index=True)
    familia_id: Optional[int] = Field(default=None, foreign_key="familia_suas.id", index=True)

    status: str = Field(default="em_andamento", index=True, max_length=30)
    etapa_atual: str = Field(default="TRIAGEM", index=True, max_length=40)

    prioridade: str = Field(default="media", index=True, max_length=20)

    tecnico_responsavel_id: Optional[int] = Field(default=None, foreign_key="usuarios.id", index=True)

    observacoes_iniciais: Optional[str] = Field(default=None, max_length=2000)
    observacoes_gerais: Optional[str] = Field(default=None, max_length=2000)

    data_abertura: datetime = Field(default_factory=datetime.utcnow, index=True)
    data_encerramento: Optional[datetime] = Field(default=None, index=True)

    # SLA / estagnação
    data_inicio_etapa_atual: datetime = Field(default_factory=datetime.utcnow, index=True)
    prazo_etapa_dias: Optional[int] = Field(default=None)

    estagnado: bool = Field(default=False, index=True)
    motivo_estagnacao: Optional[str] = Field(default=None, max_length=500)

    # Validação de recebimento (etapa seguinte)
    aguardando_validacao: bool = Field(default=False, index=True)
    pendente_validacao_desde: Optional[datetime] = Field(default=None, index=True)

    atualizado_em: datetime = Field(default_factory=datetime.utcnow, index=True)


class CasoCrasHistorico(SQLModel, table=True):
    """Histórico auditável (abertura/avança/valida/estagna/encerra)."""

    __tablename__ = "caso_cras_historico"

    id: Optional[int] = Field(default=None, primary_key=True)

    caso_id: int = Field(foreign_key="caso_cras.id", index=True)

    etapa: str = Field(index=True, max_length=40)
    tipo_acao: str = Field(index=True, max_length=30)  # abertura|avanco|validacao|estagnacao|encerramento

    usuario_id: Optional[int] = Field(default=None, foreign_key="usuarios.id", index=True)
    usuario_nome: Optional[str] = Field(default=None, max_length=120)

    observacoes: Optional[str] = Field(default=None, max_length=2000)
    motivo_estagnacao: Optional[str] = Field(default=None, max_length=500)

    criado_em: datetime = Field(default_factory=datetime.utcnow, index=True)
