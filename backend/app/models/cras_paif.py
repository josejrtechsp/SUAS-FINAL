from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from sqlmodel import SQLModel, Field


class PaifAcompanhamento(SQLModel, table=True):
    """
    PAIF = acompanhamento (o 'caso' do CRAS)
    """
    __tablename__ = "paif_acompanhamento"

    id: Optional[int] = Field(default=None, primary_key=True)

    pessoa_id: int = Field(foreign_key="pessoarua.id", index=True)
    # ✅ Ponte com o universo SUAS (cadastro mestre)
    pessoa_suas_id: Optional[int] = Field(default=None, foreign_key="pessoa_suas.id", index=True)
    municipio_id: Optional[int] = Field(default=None, foreign_key="municipio.id", index=True)

    # ✅ Caso CRAS (linha do metrô) associado ao acompanhamento
    caso_id: Optional[int] = Field(default=None, foreign_key="caso_cras.id", index=True)

    status: str = Field(default="ativo", index=True)          # ativo | encerrado
    prioridade: str = Field(default="media", index=True)      # baixa | media | alta

    aberto_em: datetime = Field(default_factory=datetime.utcnow)
    encerrado_em: Optional[datetime] = None
    motivo_encerramento: Optional[str] = None

    tecnico_responsavel_id: Optional[int] = Field(default=None, foreign_key="usuarios.id")
    tecnico_responsavel_nome: Optional[str] = None

    atualizado_em: datetime = Field(default_factory=datetime.utcnow)


class PaifProtocolo(SQLModel, table=True):
    """
    Etapa atual do PAIF (fluxo por etapas)
    - 1 registro por paif_id
    """
    __tablename__ = "paif_protocolo"

    id: Optional[int] = Field(default=None, primary_key=True)
    paif_id: int = Field(foreign_key="paif_acompanhamento.id", index=True, unique=True)

    etapa_atual: str = Field(default="TRIAGEM", index=True)

    atualizado_em: datetime = Field(default_factory=datetime.utcnow)
    atualizado_por_id: Optional[int] = Field(default=None, foreign_key="usuarios.id")
    atualizado_por_nome: Optional[str] = None


class PaifChecklistItem(SQLModel, table=True):
    __tablename__ = "paif_checklist_item"

    id: Optional[int] = Field(default=None, primary_key=True)
    paif_id: int = Field(foreign_key="paif_acompanhamento.id", index=True)

    etapa: str = Field(index=True)
    chave: str = Field(index=True)
    titulo: str

    concluido: bool = Field(default=False)
    concluido_em: Optional[datetime] = None
    concluido_por_id: Optional[int] = Field(default=None, foreign_key="usuarios.id")
    concluido_por_nome: Optional[str] = None

    obs: Optional[str] = None


class PaifPlanoAcao(SQLModel, table=True):
    __tablename__ = "paif_plano_acao"

    id: Optional[int] = Field(default=None, primary_key=True)
    paif_id: int = Field(foreign_key="paif_acompanhamento.id", index=True)

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
