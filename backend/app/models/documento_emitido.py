from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class DocumentoEmitido(SQLModel, table=True):
    """Registro do documento emitido (PDF gerado + numeração + auditoria)."""

    __tablename__ = "documento_emitido"

    id: Optional[int] = Field(default=None, primary_key=True)

    municipio_id: int = Field(index=True)
    tipo: str = Field(index=True)

    ano: int = Field(index=True)
    numero_seq: int = Field(index=True)
    numero: str = Field(index=True)

    template_id: Optional[int] = Field(default=None, index=True)

    assunto: Optional[str] = None
    destinatario_nome: Optional[str] = None
    destinatario_cargo: Optional[str] = None
    destinatario_orgao: Optional[str] = None

    # Texto final renderizado (opcional)
    corpo_renderizado: Optional[str] = None

    # Caminho do PDF no storage (ex.: storage/documentos/1/2025/oficio/OF-0001-2025.pdf)
    arquivo_path: str

    criado_por_user_id: Optional[int] = Field(default=None, index=True)
    criado_em: datetime = Field(default_factory=datetime.utcnow)
