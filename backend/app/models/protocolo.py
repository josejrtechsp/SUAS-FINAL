from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from sqlmodel import SQLModel, Field


# =========================================================
# Protocolo do Caso (B1)
# =========================================================


class CasoProtocolo(SQLModel, table=True):
    """Estado do protocolo do caso.

    - 1 registro por caso
    - Mantém a etapa atual (B1) e metadados de atualização
    """

    __tablename__ = "caso_protocolo"

    id: Optional[int] = Field(default=None, primary_key=True)
    caso_id: int = Field(foreign_key="casopoprua.id", index=True, unique=True)

    # Etapas B1: ACOLHIDA, DIAGNOSTICO, PIA, EXECUCAO, MONITORAMENTO, ENCERRAMENTO
    etapa_atual: str = Field(default="ACOLHIDA", index=True)

    atualizado_em: datetime = Field(default_factory=datetime.utcnow)
    atualizado_por_id: Optional[int] = Field(default=None, foreign_key="usuarios.id")
    atualizado_por_nome: Optional[str] = None


class CasoChecklistItem(SQLModel, table=True):
    """Item de checklist do protocolo.

    - Um item é identificado por (caso_id + chave)
    """

    __tablename__ = "caso_checklist_item"

    id: Optional[int] = Field(default=None, primary_key=True)
    caso_id: int = Field(foreign_key="casopoprua.id", index=True)

    etapa: str = Field(index=True)
    chave: str = Field(index=True)
    titulo: str

    concluido: bool = Field(default=False)
    concluido_em: Optional[datetime] = None
    concluido_por_id: Optional[int] = Field(default=None, foreign_key="usuarios.id")
    concluido_por_nome: Optional[str] = None
    obs: Optional[str] = None


class CasoPlanoAcao(SQLModel, table=True):
    """Plano de ações (PIA operacional) do caso."""

    __tablename__ = "caso_plano_acao"

    id: Optional[int] = Field(default=None, primary_key=True)
    caso_id: int = Field(foreign_key="casopoprua.id", index=True)

    objetivo: str
    acao: str
    responsavel: str

    prazo: Optional[date] = None
    status: str = Field(default="pendente", index=True)  # pendente|em_andamento|concluido|cancelado
    obs: Optional[str] = None

    criado_em: datetime = Field(default_factory=datetime.utcnow)
    criado_por_id: Optional[int] = Field(default=None, foreign_key="usuarios.id")
    criado_por_nome: Optional[str] = None

    atualizado_em: datetime = Field(default_factory=datetime.utcnow)
    atualizado_por_id: Optional[int] = Field(default=None, foreign_key="usuarios.id")
    atualizado_por_nome: Optional[str] = None
