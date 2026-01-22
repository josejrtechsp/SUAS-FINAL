from typing import Optional
from datetime import datetime

from sqlmodel import SQLModel, Field


class AcolhimentoBase(SQLModel):
  """
  Dados básicos de um registro de acolhimento da pessoa em situação de rua.
  """

  caso_id: Optional[int] = None  # pode vincular ao caso Pop Rua (opcional)

  municipio_id: Optional[int] = None  # município onde está o serviço de acolhimento
  unidade_nome: Optional[str] = None  # nome do serviço (Casa de Passagem X, Abrigo Y, etc.)

  # tipo de serviço de acolhimento (segundo Tipificação):
  # ex.: "acolhimento_institucional", "casa_passagem", "republica"
  tipo_servico: Optional[str] = None

  # tipo de vaga: "pernoite", "24h", "emergencia", etc.
  tipo_vaga: Optional[str] = None

  # datas de entrada/saída no acolhimento
  data_entrada: Optional[datetime] = Field(
      default_factory=datetime.utcnow
  )
  data_saida: Optional[datetime] = None

  # motivo de saída: alta planejada, desistência, descumprimento de regras, transferência, óbito...
  motivo_saida: Optional[str] = None

  # destino após a saída: retorno à família, outro serviço, rua, moradia, etc.
  destino_pos_saida: Optional[str] = None

  observacoes: Optional[str] = None


class Acolhimento(AcolhimentoBase, table=True):
  """
  Modelo de tabela de acolhimento.

  Cada registro representa uma entrada em algum serviço de acolhimento para
  uma pessoa em situação de rua.
  """

  __tablename__ = "acolhimentos"

  id: Optional[int] = Field(default=None, primary_key=True)

  # pessoa em situação de rua referenciada
  pessoa_id: int = Field(index=True)