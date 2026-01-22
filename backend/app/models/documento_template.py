from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class DocumentoTemplate(SQLModel, table=True):
    """Template de documento (texto com placeholders)."""

    __tablename__ = "documento_template"

    id: Optional[int] = Field(default=None, primary_key=True)

    # None = template global (vale para qualquer município)
    municipio_id: Optional[int] = Field(default=None, index=True)

    # Ex.: oficio, memorando, relatorio, declaracao
    tipo: str = Field(index=True)

    titulo: str
    assunto_padrao: Optional[str] = None

    # Texto (Jinja2). Ex: "Prezado(a) {{destinatario_nome}}, ..."
    corpo_template: str

    # Assinatura (Jinja2 opcional). Ex: "{{assinante_nome}}\n{{assinante_cargo}}"
    assinatura_template: Optional[str] = None

    ativo: bool = Field(default=True, index=True)

    criado_em: datetime = Field(default_factory=datetime.utcnow)
    atualizado_em: datetime = Field(default_factory=datetime.utcnow)
