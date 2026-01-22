from datetime import date
from typing import Optional

from sqlmodel import SQLModel, Field


class PessoaRuaBase(SQLModel):
    nome_social: Optional[str] = None
    nome_civil: Optional[str] = None

    data_nascimento: Optional[date] = None
    cpf: Optional[str] = None

    # ✅ NOVO: NIS (Número de Identificação Social)
    nis: Optional[str] = None

    genero: Optional[str] = None

    # =========================
    # Complementos (B1/B2)
    # =========================
    estado_civil: Optional[str] = None

    apelido: Optional[str] = None
    telefone: Optional[str] = None
    whatsapp: Optional[str] = None

    contato_referencia_nome: Optional[str] = None
    contato_referencia_telefone: Optional[str] = None

    permanencia_rua: Optional[str] = None
    pontos_circulacao: Optional[str] = None
    horario_mais_encontrado: Optional[str] = None
    motivo_rua: Optional[str] = None

    escolaridade: Optional[str] = None
    ocupacao: Optional[str] = None
    interesses_reinsercao: Optional[str] = None

    cadunico_status: Optional[str] = None
    documentos_pendentes: Optional[str] = None
    fonte_renda: Optional[str] = None

    violencia_risco: Optional[str] = None
    ameaca_territorio: Optional[str] = None
    gestante_status: Optional[str] = None
    protecao_imediata: Optional[str] = None

    interesse_acolhimento: Optional[str] = None
    moradia_recente: Optional[str] = None
    tentativas_saida_rua: Optional[str] = None

    # Indicador operacional para dashboard (sem detalhe clínico)
    dependencia_quimica: Optional[str] = None

    municipio_origem_id: Optional[int] = Field(
        default=None,
        foreign_key="municipio.id",
    )

    tempo_rua: Optional[str] = None
    local_referencia: Optional[str] = None
    observacoes_gerais: Optional[str] = None


class PessoaRua(PessoaRuaBase, table=True):
    __tablename__ = "pessoarua"
    id: Optional[int] = Field(default=None, primary_key=True)