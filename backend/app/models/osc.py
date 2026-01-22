from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class Osc(SQLModel, table=True):
    """Organização da Sociedade Civil (Terceiro Setor)."""

    __tablename__ = "osc"

    id: Optional[int] = Field(default=None, primary_key=True)

    # Escopo
    municipio_id: int = Field(foreign_key="municipio.id", index=True)

    # Identificação
    nome: str
    cnpj: Optional[str] = Field(default=None, index=True)
    tipo: Optional[str] = Field(default=None)  # ex: "associacao", "fundacao", "ong"

    # Atuação / contato
    areas_atuacao: Optional[str] = None  # texto livre (assistencia, crianca, idoso, etc.)
    contato_nome: Optional[str] = None
    contato_email: Optional[str] = None
    contato_telefone: Optional[str] = None
    endereco: Optional[str] = None

    ativo: bool = Field(default=True, index=True)
    criado_em: datetime = Field(default_factory=datetime.utcnow, index=True)


class OscParceria(SQLModel, table=True):
    """Parceria/Instrumento (Lei 13.019/2014) - MVP."""

    __tablename__ = "osc_parceria"

    id: Optional[int] = Field(default=None, primary_key=True)

    municipio_id: int = Field(foreign_key="municipio.id", index=True)
    osc_id: int = Field(foreign_key="osc.id", index=True)

    instrumento: str = Field(default="termo_fomento", index=True)
    numero: Optional[str] = Field(default=None, index=True)
    objeto: str

    valor_total: Optional[float] = None
    data_inicio: Optional[date] = Field(default=None, index=True)
    data_fim: Optional[date] = Field(default=None, index=True)

    status: str = Field(default="ativa", index=True)  # ativa|encerrada|suspensa

    gestor_responsavel_id: Optional[int] = Field(default=None, index=True)
    gestor_responsavel_nome: Optional[str] = None

    criado_em: datetime = Field(default_factory=datetime.utcnow, index=True)
    atualizado_em: datetime = Field(default_factory=datetime.utcnow, index=True)


class OscPrestacaoContas(SQLModel, table=True):
    """Prestação de contas - MVP.

    Usada para alimentar a fila do secretário (Gestão): pendências e prazos críticos.
    """

    __tablename__ = "osc_prestacao_contas"

    id: Optional[int] = Field(default=None, primary_key=True)

    municipio_id: int = Field(foreign_key="municipio.id", index=True)
    parceria_id: int = Field(foreign_key="osc_parceria.id", index=True)

    competencia: Optional[str] = Field(default=None, index=True)  # ex: "2025-12"
    prazo_entrega: Optional[date] = Field(default=None, index=True)

    status: str = Field(default="pendente", index=True)  # pendente|entregue|aprovado|reprovado
    entregue_em: Optional[date] = Field(default=None, index=True)

    responsavel_id: Optional[int] = Field(default=None, index=True)
    responsavel_nome: Optional[str] = None

    observacao: Optional[str] = None

    criado_em: datetime = Field(default_factory=datetime.utcnow, index=True)
    atualizado_em: datetime = Field(default_factory=datetime.utcnow, index=True)


# ==========================================================
# Terceiro Setor (MVP) — complementos
# - Mantém osc/osc_parceria/osc_prestacao_contas
# - Adiciona dirigentes, documentos, plano, metas, precificação e desembolso
# ==========================================================


class OscDirigente(SQLModel, table=True):
    """Dirigentes da OSC (mandato)."""

    __tablename__ = "osc_dirigente"

    id: Optional[int] = Field(default=None, primary_key=True)
    municipio_id: int = Field(foreign_key="municipio.id", index=True)
    osc_id: int = Field(foreign_key="osc.id", index=True)

    nome: str
    cpf: Optional[str] = Field(default=None, index=True)
    cargo: Optional[str] = Field(default=None)

    inicio_mandato: Optional[date] = Field(default=None, index=True)
    fim_mandato: Optional[date] = Field(default=None, index=True)

    criado_em: datetime = Field(default_factory=datetime.utcnow, index=True)


class OscDocumento(SQLModel, table=True):
    """Documentos/Certidões da OSC (com validade)."""

    __tablename__ = "osc_documento"

    id: Optional[int] = Field(default=None, primary_key=True)
    municipio_id: int = Field(foreign_key="municipio.id", index=True)
    osc_id: int = Field(foreign_key="osc.id", index=True)

    tipo: str = Field(index=True)  # estatuto|ata|certidao_fgts|etc
    titulo: Optional[str] = None
    url: str  # /uploads/... ou link externo
    validade: Optional[date] = Field(default=None, index=True)

    criado_em: datetime = Field(default_factory=datetime.utcnow, index=True)
    atualizado_em: datetime = Field(default_factory=datetime.utcnow, index=True)


class OscPlanoTrabalho(SQLModel, table=True):
    """Plano de trabalho (Lei 13.019) — 1 por parceria."""

    __tablename__ = "osc_plano_trabalho"

    id: Optional[int] = Field(default=None, primary_key=True)
    municipio_id: int = Field(foreign_key="municipio.id", index=True)
    parceria_id: int = Field(foreign_key="osc_parceria.id", index=True)

    diagnostico: Optional[str] = None
    descricao_objeto: Optional[str] = None
    publico_alvo: Optional[str] = None
    metodologia: Optional[str] = None

    criado_em: datetime = Field(default_factory=datetime.utcnow, index=True)
    atualizado_em: datetime = Field(default_factory=datetime.utcnow, index=True)


class OscMeta(SQLModel, table=True):
    """Metas e indicadores."""

    __tablename__ = "osc_meta"

    id: Optional[int] = Field(default=None, primary_key=True)
    municipio_id: int = Field(foreign_key="municipio.id", index=True)
    parceria_id: int = Field(foreign_key="osc_parceria.id", index=True)

    codigo: Optional[str] = Field(default=None, index=True)
    titulo: str

    unidade_medida: Optional[str] = None
    quantidade_alvo: Optional[float] = None

    indicador: Optional[str] = None
    linha_base: Optional[str] = None
    criterio_aceite: Optional[str] = None
    meios_verificacao: Optional[str] = None

    prazo: Optional[date] = Field(default=None, index=True)
    marcos: Optional[str] = None  # texto livre/JSON

    criado_em: datetime = Field(default_factory=datetime.utcnow, index=True)
    atualizado_em: datetime = Field(default_factory=datetime.utcnow, index=True)


class OscMetaPrecificacao(SQLModel, table=True):
    """Precificação por meta (custo unitário)."""

    __tablename__ = "osc_meta_precificacao"

    id: Optional[int] = Field(default=None, primary_key=True)
    municipio_id: int = Field(foreign_key="municipio.id", index=True)
    meta_id: int = Field(foreign_key="osc_meta.id", index=True)

    quantidade: Optional[float] = None
    custo_unitario: Optional[float] = None
    custo_total: Optional[float] = None

    memoria_calculo: Optional[str] = None

    criado_em: datetime = Field(default_factory=datetime.utcnow, index=True)
    atualizado_em: datetime = Field(default_factory=datetime.utcnow, index=True)


class OscDesembolsoParcela(SQLModel, table=True):
    """Cronograma de desembolso."""

    __tablename__ = "osc_desembolso_parcela"

    id: Optional[int] = Field(default=None, primary_key=True)
    municipio_id: int = Field(foreign_key="municipio.id", index=True)
    parceria_id: int = Field(foreign_key="osc_parceria.id", index=True)

    numero: int = Field(index=True)
    valor: float
    data_prevista: Optional[date] = Field(default=None, index=True)
    condicao: Optional[str] = None

    criado_em: datetime = Field(default_factory=datetime.utcnow, index=True)
    atualizado_em: datetime = Field(default_factory=datetime.utcnow, index=True)
