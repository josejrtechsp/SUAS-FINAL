from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict, Optional

from sqlmodel import Field, SQLModel


class CrasAutomacaoRegra(SQLModel, table=True):
    """
    Regras de automação do CRAS (ex.: criar tarefas a partir de gatilhos).
    Observação:
      - O backend não roda em background sozinho.
      - Para executar automaticamente, um cron/job externo chama /cras/automacoes/executar-devidas.
    """

    __tablename__ = "cras_automacao_regra"

    id: Optional[int] = Field(default=None, primary_key=True)

    municipio_id: int = Field(index=True, foreign_key="municipio.id")
    unidade_id: Optional[int] = Field(default=None, index=True, foreign_key="cras_unidade.id")

    chave: str = Field(index=True, max_length=80)  # ex.: caso_sem_movimentacao
    titulo: str = Field(max_length=160)
    descricao: Optional[str] = Field(default=None, max_length=1000)

    ativo: bool = Field(default=True, index=True)

    # JSON string com parâmetros da regra
    parametros_json: str = Field(default="{}", max_length=8000)

    # Controle de execução
    frequencia_minutos: int = Field(default=1440, index=True)  # 1440 = 1x/dia
    ultima_execucao_em: Optional[datetime] = Field(default=None, index=True)

    criado_em: datetime = Field(default_factory=datetime.utcnow, index=True)
    atualizado_em: datetime = Field(default_factory=datetime.utcnow, index=True)
    criado_por_usuario_id: Optional[int] = Field(default=None, foreign_key="usuarios.id", index=True)

    def parametros(self) -> Dict[str, Any]:
        try:
            v = json.loads(self.parametros_json or "{}")
            return v if isinstance(v, dict) else {}
        except Exception:
            return {}

    def set_parametros(self, data: Dict[str, Any]) -> None:
        try:
            self.parametros_json = json.dumps(data or {}, ensure_ascii=False)
        except Exception:
            self.parametros_json = "{}"


class CrasAutomacaoExecucao(SQLModel, table=True):
    __tablename__ = "cras_automacao_execucao"

    id: Optional[int] = Field(default=None, primary_key=True)
    regra_id: int = Field(index=True, foreign_key="cras_automacao_regra.id")

    municipio_id: int = Field(index=True)
    unidade_id: Optional[int] = Field(default=None, index=True)

    iniciado_em: datetime = Field(default_factory=datetime.utcnow, index=True)
    finalizado_em: Optional[datetime] = Field(default=None, index=True)

    status: str = Field(default="ok", index=True, max_length=20)  # ok|erro
    resumo_json: str = Field(default="{}", max_length=8000)
    erro: Optional[str] = Field(default=None, max_length=2000)

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
