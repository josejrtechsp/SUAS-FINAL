from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel, Field


class CasoEtapaRegistro(SQLModel, table=True):
    """Registro auditável de avanço/execução em uma etapa da linha do metrô.

    Importante:
      - NÃO altera automaticamente `caso.etapa_atual` (decisão do usuário = plano A).
      - Serve para dar materialidade ao visual (responsável, data/hora, evidências).
    """

    __tablename__ = "caso_etapa_registros"
    __table_args__ = {"extend_existing": True}

    id: Optional[int] = Field(default=None, primary_key=True)

    caso_id: int = Field(index=True, foreign_key="casopoprua.id")
    etapa: str = Field(index=True, max_length=60)

    responsavel_usuario_id: int = Field(index=True, foreign_key="usuarios.id")
    data_hora: datetime = Field(default_factory=datetime.utcnow, index=True)

    atendimento_id: Optional[int] = Field(default=None, index=True)
    obs: Optional[str] = Field(default=None, max_length=600)

    criado_em: datetime = Field(default_factory=datetime.utcnow, index=True)


class CasoEtapaRegistroVinculo(SQLModel, table=True):
    """Vínculos de evidência para um registro de etapa.

    Por enquanto usamos `tipo` + `ref_id` para permitir múltiplos tipos.
    Para o MVP (B1.5) usamos:
      - tipo = 'encaminhamento_intermunicipal'
      - ref_id = EncaminhamentoIntermunicipal.id
    """

    __tablename__ = "caso_etapa_registro_vinculos"
    __table_args__ = {"extend_existing": True}

    id: Optional[int] = Field(default=None, primary_key=True)
    registro_id: int = Field(index=True, foreign_key="caso_etapa_registros.id")

    tipo: str = Field(index=True, max_length=60)
    ref_id: int = Field(index=True)

    criado_em: datetime = Field(default_factory=datetime.utcnow, index=True)
