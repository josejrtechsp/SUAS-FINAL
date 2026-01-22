from typing import Optional
from datetime import datetime, date
from sqlmodel import SQLModel, Field

class CrasTarefa(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    # escopo
    municipio_id: Optional[int] = Field(default=None, index=True)
    unidade_id: Optional[int] = Field(default=None, index=True)

    # atribuição
    responsavel_id: Optional[int] = Field(default=None, index=True)  # usuario id
    responsavel_nome: Optional[str] = Field(default=None)

    # referência (liga tarefa a algo do sistema)
    ref_tipo: str = Field(index=True)  # "caso" | "cadunico" | "scfv" | "programa" | "ficha" | "encaminhamento" | "manual"
    ref_id: Optional[int] = Field(default=None, index=True)

    # conteúdo
    titulo: str
    descricao: Optional[str] = None
    prioridade: str = Field(default="media", index=True)  # baixa|media|alta|critica

    # SLA
    status: str = Field(default="aberta", index=True)  # aberta|em_andamento|concluida|cancelada
    data_vencimento: Optional[date] = Field(default=None, index=True)
    data_conclusao: Optional[date] = Field(default=None, index=True)

    criado_em: datetime = Field(default_factory=datetime.utcnow, index=True)
    atualizado_em: datetime = Field(default_factory=datetime.utcnow, index=True)
