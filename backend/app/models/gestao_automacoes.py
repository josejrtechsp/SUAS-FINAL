from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict, Optional

from sqlmodel import Field, SQLModel


class GestaoLoteRegra(SQLModel, table=True):
    """Regra de automação de lote para Gestão (fila).

    Observação importante:
    - O backend NÃO executa isso sozinho em background.
    - Para rodar automático, um cron/job externo chama o endpoint /gestao/automacoes/executar-devidas.
    """

    __tablename__ = "gestao_lote_regra"

    id: Optional[int] = Field(default=None, primary_key=True)

    # Escopo
    municipio_id: Optional[int] = Field(default=None, foreign_key="municipio.id", index=True)

    nome: str = Field(index=True)
    descricao: Optional[str] = None

    # Ação principal
    acao: str = Field(index=True)  # cobrar|relatorio|oficio

    # Filtros (JSON como texto)
    filtros_json: str = Field(default="{}")

    # Agendamento (JSON como texto)
    # Exemplo:
    # {"freq":"daily","time":"08:30","weekdays":[0,1,2,3,4],"tz":"America/Sao_Paulo"}
    schedule_json: str = Field(default="{}")

    ativo: bool = Field(default=True, index=True)

    # Controle
    criado_em: datetime = Field(default_factory=datetime.utcnow, index=True)
    atualizado_em: datetime = Field(default_factory=datetime.utcnow, index=True)

    last_run_at: Optional[datetime] = Field(default=None, index=True)
    last_run_status: Optional[str] = Field(default=None)

    def filtros(self) -> Dict[str, Any]:
        try:
            v = json.loads(self.filtros_json or "{}")
            return v if isinstance(v, dict) else {}
        except Exception:
            return {}

    def schedule(self) -> Dict[str, Any]:
        try:
            v = json.loads(self.schedule_json or "{}")
            return v if isinstance(v, dict) else {}
        except Exception:
            return {}


class GestaoLoteExecucao(SQLModel, table=True):
    """Log/auditoria de execução de uma regra de lote."""

    __tablename__ = "gestao_lote_execucao"

    id: Optional[int] = Field(default=None, primary_key=True)

    regra_id: Optional[int] = Field(default=None, foreign_key="gestao_lote_regra.id", index=True)
    municipio_id: Optional[int] = Field(default=None, foreign_key="municipio.id", index=True)

    acao: str = Field(index=True)

    iniciado_em: datetime = Field(default_factory=datetime.utcnow, index=True)
    finalizado_em: Optional[datetime] = Field(default=None, index=True)

    status: str = Field(default="running", index=True)  # running|ok|partial|error

    total: int = Field(default=0)
    ok: int = Field(default=0)
    falhas: int = Field(default=0)

    # Resumo (JSON como texto)
    resumo_json: str = Field(default="{}")

    criado_por_usuario_id: Optional[int] = Field(default=None, foreign_key="usuarios.id", index=True)

    def resumo(self) -> Dict[str, Any]:
        try:
            v = json.loads(self.resumo_json or "{}")
            return v if isinstance(v, dict) else {}
        except Exception:
            return {}

    def set_resumo(self, data: Dict[str, Any]) -> None:
        try:
            self.resumo_json = json.dumps(data or {}, ensure_ascii=False)
        except Exception:
            self.resumo_json = "{}"
