# backend/app/schemas/encaminhamentos.py

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

# Compatível com Pydantic v1 e v2
try:
    from pydantic import ConfigDict  # pydantic v2

    class ORMBase(BaseModel):
        model_config = ConfigDict(from_attributes=True)
except Exception:  # pydantic v1
    class ORMBase(BaseModel):
        class Config:
            orm_mode = True


class EncaminhamentoEventoOut(ORMBase):
    id: int
    tipo: str
    detalhe: Optional[str] = None
    por_nome: Optional[str] = None
    em: datetime


class EncaminhamentoOut(ORMBase):
    id: int

    pessoa_id: int
    caso_id: Optional[int] = None

    municipio_origem_id: Optional[int] = None
    municipio_destino_id: int

    motivo: str
    observacoes: Optional[str] = None

    consentimento_registrado: bool
    status: str

    contato_em: Optional[datetime] = None
    aceite_em: Optional[datetime] = None
    agendado_em: Optional[datetime] = None
    passagem_em: Optional[datetime] = None
    contrarreferencia_em: Optional[datetime] = None
    concluido_em: Optional[datetime] = None
    cancelado_em: Optional[datetime] = None

    passagem_numero: Optional[str] = None
    passagem_empresa: Optional[str] = None
    passagem_data_viagem: Optional[datetime] = None

    kit_lanche: bool
    kit_higiene: bool
    kit_mapa_info: bool

    justificativa_passagem: Optional[str] = None
    autorizado_por_nome: Optional[str] = None

    criado_em: datetime
    atualizado_em: datetime

    eventos: List[EncaminhamentoEventoOut] = []


class EncaminhamentoCreateIn(BaseModel):
    pessoa_id: int
    caso_id: Optional[int] = None

    municipio_origem_id: Optional[int] = None
    municipio_destino_id: int

    motivo: str = Field(min_length=3)
    observacoes: Optional[str] = None

    # Regra BR-001: obrigatório registrar consentimento/solicitação do usuário
    consentimento_registrado: bool = True


class EncaminhamentoEventoCreateIn(BaseModel):
    # solicitado/contato/aceito/agendado/passagem/contrarreferencia/concluido/cancelado
    tipo: str = Field(min_length=3)
    detalhe: Optional[str] = None

    # campos opcionais de passagem (usados quando tipo="passagem")
    passagem_numero: Optional[str] = None
    passagem_empresa: Optional[str] = None
    passagem_data_viagem: Optional[datetime] = None

    kit_lanche: Optional[bool] = None
    kit_higiene: Optional[bool] = None
    kit_mapa_info: Optional[bool] = None

    justificativa_passagem: Optional[str] = None