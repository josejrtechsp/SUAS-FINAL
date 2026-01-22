from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel, Field


# --------------------------------------------------------------------
# Modelo base do caso Pop Rua
# --------------------------------------------------------------------
class CasoPopRuaBase(SQLModel):
    # Pessoa vinculada ao caso
    pessoa_id: int = Field(foreign_key="pessoarua.id")

    # Observações gerais
    observacoes_iniciais: Optional[str] = None
    observacoes_gerais: Optional[str] = None

    # Status geral do caso
    # valores esperados: "em_andamento" | "encerrado"
    status: str = Field(default="em_andamento")

    # Código da etapa atual na linha de metrô
    # (ABORDAGEM, IDENTIFICACAO, DIAGNOSTICO, PIA, EXECUCAO, MONITORAMENTO,
    #  ARTICULACAO_REDE, REVISAO, ENCERRAMENTO)
    etapa_atual: str = Field(default="ABORDAGEM")

    # Controle de atividade
    ativo: bool = Field(default=True)

    # Datas principais
    data_abertura: datetime = Field(default_factory=datetime.utcnow)
    data_ultima_atualizacao: datetime = Field(default_factory=datetime.utcnow)
    data_encerramento: Optional[datetime] = None
    motivo_encerramento: Optional[str] = None

    # ----------------------------------------------------------------
    # Campos para controle de prazo / estagnação da etapa atual
    # ----------------------------------------------------------------

    # Quando essa etapa atual começou de fato
    data_inicio_etapa_atual: datetime = Field(
        default_factory=datetime.utcnow,
        description="Data em que a etapa_atual foi iniciada."
    )

    # Prazo esperado em dias para concluir a etapa_atual
    # (pode ficar None se o município não quiser usar prazos)
    prazo_etapa_dias: Optional[int] = Field(
        default=None,
        description="Prazo esperado, em dias, para conclusão da etapa atual."
    )

    # Marca se o caso está considerado estagnado na etapa_atual
    estagnado: bool = Field(
        default=False,
        description="Indica se o caso está estagnado na etapa atual."
    )

    # Detalhamento do motivo da estagnação
    motivo_estagnacao: Optional[str] = Field(
        default=None,
        description="Motivo descritivo da estagnação na etapa atual."
    )


# --------------------------------------------------------------------
# Tabela principal do caso (inclui campo ID)
# --------------------------------------------------------------------
class CasoPopRua(CasoPopRuaBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)


# --------------------------------------------------------------------
# Modelo para atualização parcial do caso (PATCH)
# --------------------------------------------------------------------
class CasoPopRuaUpdate(SQLModel):
    """Modelo para atualização parcial do caso."""

    etapa_atual: Optional[str] = None
    status: Optional[str] = None
    observacoes_gerais: Optional[str] = None
    ativo: Optional[bool] = None
    motivo_encerramento: Optional[str] = None

    # Campos de prazo / estagnação também podem ser atualizados
    data_inicio_etapa_atual: Optional[datetime] = None
    prazo_etapa_dias: Optional[int] = None
    estagnado: Optional[bool] = None
    motivo_estagnacao: Optional[str] = None


# --------------------------------------------------------------------
# Histórico das etapas do caso
# (cada vez que a etapa muda, você pode registrar uma linha aqui)
# --------------------------------------------------------------------
class CasoPopRuaEtapaHistorico(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    # Ligação com o caso principal
    caso_id: int = Field(foreign_key="casopoprua.id")

    # Código da etapa (ABORDAGEM, IDENTIFICACAO, DIAGNOSTICO, etc.)
    etapa: str = Field(index=True)

    # Status dessa etapa: "em_andamento", "concluida", "estagnada", etc.
    status_etapa: str = Field(default="em_andamento")

    # Datas de início e fim da etapa
    data_inicio: datetime = Field(default_factory=datetime.utcnow)
    data_fim: Optional[datetime] = None

    # Observações específicas dessa etapa
    observacoes: Optional[str] = None

    # Controle de criação do registro
    criado_em: datetime = Field(default_factory=datetime.utcnow)