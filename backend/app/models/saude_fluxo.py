from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel, Field


class SaudeFluxoEvento(SQLModel, table=True):
    """
    Registro operacional de SAÚDE (intersetorial, sem clínica).
    Cada linha = 1 etapa registrada no “metrô Saúde”.
    """
    __tablename__ = "saude_fluxo_eventos"

    id: Optional[int] = Field(default=None, primary_key=True)

    caso_id: int = Field(foreign_key="casopoprua.id", index=True)

    # etapa do fluxo
    passo: str = Field(index=True)  # TRIAGEM / ENCAMINHAMENTO / ACEITE / ...

    criado_em: datetime = Field(default_factory=datetime.utcnow, index=True)

    # Responsável (sempre)
    usuario_responsavel: str
    responsavel_funcao: Optional[str] = None
    responsavel_servico: Optional[str] = None
    responsavel_contato: Optional[str] = None

    # Campos mínimos operacionais (todos opcionais; variam por passo)
    prioridade: Optional[str] = None  # rotina | urgente
    precisa_avaliacao: Optional[bool] = None

    servico_tipo: Optional[str] = None  # UBS/UPA/CAPS/CONSULTORIO_RUA/HOSPITAL/OUTRO
    unidade_nome: Optional[str] = None
    data_hora: Optional[datetime] = None

    compareceu: Optional[str] = None  # sim | nao | nao_se_aplica
    motivo_nao_compareceu: Optional[str] = None

    retorno_necessario: Optional[bool] = None
    retorno_data_hora: Optional[datetime] = None

    status_final: Optional[str] = None  # concluido | interrompido | acompanhamento_continuo

    observacoes: Optional[str] = None