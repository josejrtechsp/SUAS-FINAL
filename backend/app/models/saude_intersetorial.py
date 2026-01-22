# app/models/saude_intersetorial.py
from __future__ import annotations

from datetime import datetime
from typing import Optional

import json
from sqlalchemy import Column, Text
from sqlmodel import SQLModel, Field


class SaudeIntersetorialRegistro(SQLModel, table=True):
    """
    MÓDULO SAÚDE (INTERSETORIAL) — mínimo necessário (LGPD)
    - NUNCA guardar diagnóstico, CID, laudos, exames, sorologia, etc.
    - Guardar apenas o que organiza o fluxo: prioridade, serviço, data/hora, status e alertas operacionais.
    - Armazena payload em JSON (texto) para manter flexível sem espalhar colunas.

    Tabela propositalmente com nome ÚNICO para evitar conflito com versões antigas.
    """
    __tablename__ = "saude_intersetorial_logs"

    id: Optional[int] = Field(default=None, primary_key=True)

    caso_id: int = Field(foreign_key="casopoprua.id", index=True)

    # auditoria mínima
    criado_em: datetime = Field(default_factory=datetime.utcnow, index=True)
    criado_por_user_id: Optional[int] = Field(default=None, foreign_key="usuarios.id", index=True)
    criado_por_nome: Optional[str] = Field(default=None)

    # intersetorial (e não clínico!)
    tipo_registro: str = Field(default="intersetorial", index=True)  # intersetorial | status

    # JSON em texto (sqlite-friendly)
    payload_json: str = Field(default="{}", sa_column=Column(Text))

    def payload_dict(self) -> dict:
        try:
            return json.loads(self.payload_json or "{}")
        except Exception:
            return {}