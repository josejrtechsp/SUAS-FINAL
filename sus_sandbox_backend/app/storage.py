import json
import os
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Tuple

_LOCK = threading.Lock()

def _now_iso() -> str:
    return datetime.utcnow().isoformat(timespec="seconds") + "Z"

def _default_db() -> Dict[str, Any]:
    return {
        "seq": {
            "programa": 0,
            "acao": 0,
            "meta": 0,
            "indicador": 0,
            "tarefa": 0,
            "evidencia": 0,
            "conformidade_item": 0,
            "importacao": 0,
            "relatorio": 0,
        },
        "programas": [],
        "acoes": [],
        "metas": [],
        "indicadores": [],
        "tarefas": [],
        "evidencias": [],
        "competencias": [],
        "conformidade_itens": [],
        "importacoes": [],
        "relatorios": [],
        "meta": {
            "created_at": _now_iso(),
            "updated_at": _now_iso(),
            "version": 1
        }
    }

def ensure_db(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if not db_path.exists():
        tmp = db_path.with_suffix(".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(_default_db(), f, ensure_ascii=False, indent=2)
        os.replace(tmp, db_path)

def load_db(db_path: Path) -> Dict[str, Any]:
    ensure_db(db_path)
    with _LOCK:
        with open(db_path, "r", encoding="utf-8") as f:
            return json.load(f)

def save_db(db_path: Path, db: Dict[str, Any]) -> None:
    ensure_db(db_path)
    db["meta"]["updated_at"] = _now_iso()
    tmp = db_path.with_suffix(".tmp")
    with _LOCK:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(db, f, ensure_ascii=False, indent=2)
        os.replace(tmp, db_path)

def next_id(db: Dict[str, Any], key: str) -> int:
    db["seq"][key] = int(db["seq"].get(key, 0)) + 1
    return db["seq"][key]

def upsert_competencia(db: Dict[str, Any], competencia: str, status: str = "aberta") -> Dict[str, Any]:
    for c in db["competencias"]:
        if c["competencia"] == competencia:
            c["status"] = status
            return c
    item = {"competencia": competencia, "status": status, "criado_em": _now_iso(), "fechado_em": None}
    db["competencias"].append(item)
    return item

DEFAULT_CHECKLIST = {
    "aps": [
        "Responsável definido",
        "Pendências registradas com motivo",
        "Evidências/protocolos anexados",
    ],
    "vig": [
        "Pendências de vigilância registradas",
        "Comprovantes anexados",
    ],
    "farm": [
        "Pendências registradas",
        "Comprovantes anexados",
    ],
    "gest": [
        "Relatórios gerados",
        "Ata/registro de controle social anexado (quando aplicável)",
    ],
}

def ensure_checklist(db: Dict[str, Any], competencia: str) -> None:
    # cria itens padrão se não existir nenhum para a competência
    if any(x.get("competencia") == competencia for x in db["conformidade_itens"]):
        return
    for area, titles in DEFAULT_CHECKLIST.items():
        for t in titles:
            cid = next_id(db, "conformidade_item")
            db["conformidade_itens"].append({
                "id": cid,
                "competencia": competencia,
                "area": area,
                "titulo": t,
                "status": "pendente",
                "responsavel": "",
                "comentario": "",
                "evidencia_ids": [],
                "criado_em": _now_iso(),
                "atualizado_em": _now_iso(),
            })
