from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import UniqueConstraint
from sqlmodel import Field, SQLModel


class DocumentoConfig(SQLModel, table=True):
    """Configuração de documentos por município.

    Esta tabela evita hardcode no backend e permite que cada prefeitura defina:
      - numeração padrão (estilo + dígitos)
      - emissor padrão (smas/cras/creas)
      - siglas por emissor (SMAS/CRAS/CREAS) e sigla padrão
      - se a sequência é única (município+tipo+ano) ou separada por emissor

    Obs.: campos JSON são strings (armazenadas como TEXT) para evitar dependências.
    """

    __tablename__ = "documento_config"
    __table_args__ = (UniqueConstraint("municipio_id", name="uq_documento_config_municipio"),)

    id: Optional[int] = Field(default=None, primary_key=True)

    municipio_id: int = Field(index=True)

    # Defaults de numeração
    numero_estilo_default: str = "prefeitura"  # prefeitura|curto|hifen
    digitos_seq_default: int = 3

    # Emissor padrão e como sequenciar
    emissor_padrao: str = "smas"  # smas|cras|creas|poprua|gestao...
    sequenciar_por_emissor: bool = True

    # Siglas
    sigla_padrao: Optional[str] = "SMAS"
    siglas_json: Optional[str] = None  # ex.: {"smas":"SMAS","cras":"CRAS","creas":"CREAS"}

    # Prefixos por tipo (opcional)
    prefixos_json: Optional[str] = None  # ex.: {"oficio":"OF","memorando":"MEM"}

    criado_em: datetime = Field(default_factory=datetime.utcnow)
    atualizado_em: datetime = Field(default_factory=datetime.utcnow)
