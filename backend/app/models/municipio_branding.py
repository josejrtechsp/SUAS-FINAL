from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import UniqueConstraint
from sqlmodel import Field, SQLModel


class MunicipioBranding(SQLModel, table=True):
    """Branding por município (logo, cabeçalho, rodapé e ajustes de layout)."""

    __tablename__ = "municipio_branding"
    __table_args__ = (UniqueConstraint("municipio_id", name="uq_branding_municipio"),)

    id: Optional[int] = Field(default=None, primary_key=True)
    municipio_id: int = Field(index=True)

    # Identidade
    nome_instituicao: Optional[str] = None
    logo_path: Optional[str] = None  # caminho no storage (ex.: storage/branding/municipio_1.png)

    # Cabeçalho / rodapé (texto simples; usar \n para múltiplas linhas)
    header_text: Optional[str] = None
    footer_text: Optional[str] = None

    # Layout (mm)
    margin_top_mm: float = 20.0
    margin_bottom_mm: float = 20.0
    margin_left_mm: float = 20.0
    margin_right_mm: float = 20.0

    # Logo (mm) - altura é opcional; se None, mantém proporção pela largura
    logo_width_mm: float = 28.0
    logo_height_mm: Optional[float] = None

    # Tipografia
    font_name: str = "Helvetica"
    font_size: int = 11

    criado_em: datetime = Field(default_factory=datetime.utcnow)
    atualizado_em: datetime = Field(default_factory=datetime.utcnow)
