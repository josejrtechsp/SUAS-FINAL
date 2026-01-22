from __future__ import annotations

from datetime import datetime, date
from typing import Optional

from sqlmodel import SQLModel, Field
from sqlalchemy import Column, Text


class RmaEvento(SQLModel, table=True):
    """Evento de coleta do RMA (Registro Mensal de Atendimentos).

    A ideia é coletar durante a operação e exportar por mês com 1 clique.
    """
    __tablename__ = "rma_evento"
    __table_args__ = {"extend_existing": True}

    id: Optional[int] = Field(default=None, primary_key=True)

    municipio_id: int = Field(foreign_key="municipio.id", index=True)

    unidade_id: Optional[int] = Field(default=None, index=True)

    servico: str = Field(index=True, max_length=40)   # ex: PAIF, SCFV, CADUNICO, CASOS, ENCAMINHAMENTO_SUAS, DOCUMENTO, TAREFA
    acao: str = Field(index=True, max_length=60)      # ex: criar, atualizar, concluir, cobrar, retornar

    alvo_tipo: Optional[str] = Field(default=None, index=True, max_length=20)  # pessoa|familia|caso|outro
    alvo_id: Optional[int] = Field(default=None, index=True)

    pessoa_id: Optional[int] = Field(default=None, index=True)   # PessoaSUAS id (se houver)
    familia_id: Optional[int] = Field(default=None, index=True)  # FamiliaSUAS id (se houver)
    caso_id: Optional[int] = Field(default=None, index=True)     # Caso CRAS id (se houver)

    data_evento: date = Field(default_factory=date.today, index=True)

    meta_json: Optional[str] = Field(default=None, sa_column=Column(Text))  # contexto livre (json)

    criado_em: datetime = Field(default_factory=datetime.utcnow, index=True)
    criado_por_usuario_id: Optional[int] = Field(default=None, index=True)
    criado_por_nome: Optional[str] = Field(default=None, max_length=120)
