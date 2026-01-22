from typing import Optional
from datetime import date

from sqlmodel import SQLModel, Field


class FamiliaReferenciaBase(SQLModel):
    """
    Dados básicos da família de referência da pessoa em situação de rua.
    Aqui vamos guardar apenas um contato principal / referência.
    """

    nome_referencia: Optional[str] = None        # ex.: mãe, pai, irmã, companheiro
    parentesco: Optional[str] = None             # ex.: mãe, pai, irmã, companheiro
    telefone: Optional[str] = None
    municipio_id: Optional[int] = None           # município onde vive a família de referência
    observacoes: Optional[str] = None            # observações sobre vínculos, contatos, etc.


class FamiliaReferencia(FamiliaReferenciaBase, table=True):
    """
    Tabela de família de referência para cada pessoa em situação de rua.
    Pressupomos 0 ou 1 registro por pessoa.
    """

    __tablename__ = "familias_referencia"

    id: Optional[int] = Field(default=None, primary_key=True)
    pessoa_id: int = Field(index=True)


class BeneficioPessoaBase(SQLModel):
    """
    Dados básicos de um benefício que a pessoa recebe, recebeu ou está pleiteando.
    """

    tipo: str                                     # ex.: "BPC", "Bolsa Família", "Benefício eventual", etc.
    situacao: str = "ativo"                       # ex.: "ativo", "suspenso", "encerrado", "em_analise"
    descricao: Optional[str] = None               # detalhes ou outras info relevantes
    data_inicio: Optional[date] = None
    data_fim: Optional[date] = None
    orgao_gestor: Optional[str] = None            # ex.: INSS, Prefeitura, Estado
    numero_nis: Optional[str] = None              # caso esse benefício esteja ligado ao NIS


class BeneficioPessoa(BeneficioPessoaBase, table=True):
    """
    Tabela de benefícios associados a uma pessoa em situação de rua.
    """

    __tablename__ = "beneficios_pessoa"

    id: Optional[int] = Field(default=None, primary_key=True)
    pessoa_id: int = Field(index=True)