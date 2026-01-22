from __future__ import annotations
from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field

class CrasTriagem(SQLModel, table=True):
    __tablename__ = "cras_triagem"

    id: Optional[int] = Field(default=None, primary_key=True)

    municipio_id: int = Field(foreign_key="municipio.id", index=True)
    unidade_id: int = Field(foreign_key="cras_unidade.id", index=True)

    pessoa_id: Optional[int] = Field(default=None, foreign_key="pessoarua.id", index=True)
    # ✅ Ponte com o universo SUAS (cadastro mestre)
    pessoa_suas_id: Optional[int] = Field(default=None, foreign_key="pessoa_suas.id", index=True)

    tecnico_id: Optional[int] = Field(default=None, foreign_key="usuarios.id", index=True)
    tecnico_nome: Optional[str] = None

    data_hora: datetime = Field(default_factory=datetime.utcnow, index=True)

    canal: str = Field(default="espontanea", index=True)       # espontanea|agendada|telefone
    demanda_principal: str
    prioridade: str = Field(default="media", index=True)       # baixa|media|alta

    desfecho: str = Field(default="em_atendimento", index=True)  # orientado|agendado|encaminhado|abrir_paif|em_atendimento
    observacao_operacional: Optional[str] = None

    status: str = Field(default="aberta", index=True)          # aberta|encerrada|convertida
    paif_id: Optional[int] = Field(default=None, foreign_key="paif_acompanhamento.id", index=True)

    # ✅ Caso CRAS (linha do metrô) aberto a partir da triagem
    caso_id: Optional[int] = Field(default=None, foreign_key="caso_cras.id", index=True)
