from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel, Field


class CasoPopRuaBase(SQLModel):
    # FK corretas (tabelas do seu projeto)
    pessoa_id: int = Field(foreign_key="pessoarua.id")
    municipio_id: int = Field(foreign_key="municipio.id")

    # Textos (LGPD: router pode mascarar)
    observacoes_iniciais: Optional[str] = None
    observacoes_gerais: Optional[str] = None

    # Status geral do caso
    status: str = Field(default="em_andamento")  # em_andamento | encerrado
    etapa_atual: str = Field(default="ABORDAGEM")
    ativo: bool = Field(default=True)

    # Datas principais
    data_abertura: datetime = Field(default_factory=datetime.utcnow)
    data_ultima_atualizacao: datetime = Field(default_factory=datetime.utcnow)
    data_encerramento: Optional[datetime] = None
    motivo_encerramento: Optional[str] = None

    # ✅ ESSA É A COLUNA QUE ESTAVA ESTOURANDO NOT NULL NO SQLITE
    # (garante que SEMPRE será preenchida na criação do caso)
    data_inicio_etapa_atual: datetime = Field(default_factory=datetime.utcnow)

    # Campos que já existem na sua tabela (compat)
    prazo_etapa_dias: Optional[int] = None
    estagnado: bool = Field(default=False)
    motivo_estagnacao: Optional[str] = None

    # Compat com coluna de migração que você aplicou
    data_prevista_proxima_acao: Optional[datetime] = None
    data_ultima_acao: Optional[datetime] = None

    flag_estagnado: bool = Field(default=False)
    dias_estagnado: int = Field(default=0)
    tipo_estagnacao: Optional[str] = None


class CasoPopRua(CasoPopRuaBase, table=True):
    __tablename__ = "casopoprua"
    id: Optional[int] = Field(default=None, primary_key=True)


class CasoPopRuaUpdate(SQLModel):
    observacoes_iniciais: Optional[str] = None
    observacoes_gerais: Optional[str] = None
    status: Optional[str] = None
    etapa_atual: Optional[str] = None
    ativo: Optional[bool] = None

    data_encerramento: Optional[datetime] = None
    motivo_encerramento: Optional[str] = None

    data_inicio_etapa_atual: Optional[datetime] = None
    prazo_etapa_dias: Optional[int] = None
    estagnado: Optional[bool] = None
    motivo_estagnacao: Optional[str] = None

    data_prevista_proxima_acao: Optional[datetime] = None
    data_ultima_acao: Optional[datetime] = None
    flag_estagnado: Optional[bool] = None
    dias_estagnado: Optional[int] = None
    tipo_estagnacao: Optional[str] = None


class CasoPopRuaEtapaHistorico(SQLModel, table=True):
    __tablename__ = "casopopruaetapahistorico"

    id: Optional[int] = Field(default=None, primary_key=True)

    caso_id: int = Field(foreign_key="casopoprua.id")
    etapa: str
    data_acao: datetime = Field(default_factory=datetime.utcnow)

    # ✅ Responsável (o que você pediu)
    usuario_responsavel: str  # nome do responsável
    responsavel_funcao: Optional[str] = None
    responsavel_servico: Optional[str] = None
    responsavel_contato: Optional[str] = None

    observacoes: Optional[str] = None

    tipo_acao: str = Field(default="avanco_etapa")
    motivo_estagnacao: Optional[str] = None
