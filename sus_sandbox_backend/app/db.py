from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Any, Dict, Optional

BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "sus_db.json")

DEFAULT_DB: Dict[str, Any] = {
    "meta": {"version": 4, "updated_at": None},
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
    "auditoria": [],
    "counters": {},
}

def _ensure_dirs() -> None:
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(os.path.join(BASE_DIR, "uploads"), exist_ok=True)

def load_db() -> Dict[str, Any]:
    _ensure_dirs()
    if not os.path.exists(DB_PATH):
        save_db(DEFAULT_DB)
        return json.loads(json.dumps(DEFAULT_DB))
    try:
        with open(DB_PATH, "r", encoding="utf-8") as f:
            db = json.load(f)
    except Exception:
        db = json.loads(json.dumps(DEFAULT_DB))
        save_db(db)
    for k, v in DEFAULT_DB.items():
        if k not in db:
            db[k] = json.loads(json.dumps(v))
    if "counters" not in db or not isinstance(db["counters"], dict):
        db["counters"] = {}
    if "meta" not in db or not isinstance(db["meta"], dict):
        db["meta"] = {"version": 4, "updated_at": None}
    return db

def save_db(db: Dict[str, Any]) -> None:
    _ensure_dirs()
    db.setdefault("meta", {})
    db["meta"]["updated_at"] = datetime.utcnow().isoformat() + "Z"
    tmp = DB_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)
    os.replace(tmp, DB_PATH)

def _next_id(db: Dict[str, Any], table: str) -> int:
    counters = db.setdefault("counters", {})
    if table in counters and isinstance(counters[table], int):
        nid = counters[table]
        counters[table] = nid + 1
        return nid
    max_id = 0
    for row in db.get(table, []) or []:
        try:
            max_id = max(max_id, int(row.get("id", 0)))
        except Exception:
            pass
    nid = max_id + 1
    counters[table] = nid + 1
    return nid

def now_iso() -> str:
    return datetime.utcnow().isoformat() + "Z"

def insert(db: Dict[str, Any], table: str, row: Dict[str, Any]) -> Dict[str, Any]:
    row = dict(row)
    row["id"] = _next_id(db, table)
    row.setdefault("criado_em", now_iso())
    row.setdefault("atualizado_em", row["criado_em"])
    db[table].append(row)
    save_db(db)
    return row

def update(db: Dict[str, Any], table: str, row_id: int, patch: Dict[str, Any]) -> Dict[str, Any]:
    rows = db.get(table, []) or []
    for i, r in enumerate(rows):
        if int(r.get("id")) == int(row_id):
            new = dict(r)
            for k, v in (patch or {}).items():
                if v is not None:
                    new[k] = v
            new["atualizado_em"] = now_iso()
            rows[i] = new
            db[table] = rows
            save_db(db)
            return new
    raise KeyError(f"{table} id={row_id} not found")

def delete(db: Dict[str, Any], table: str, row_id: int) -> None:
    rows = db.get(table, []) or []
    new_rows = [r for r in rows if int(r.get("id")) != int(row_id)]
    if len(new_rows) == len(rows):
        raise KeyError(f"{table} id={row_id} not found")
    db[table] = new_rows
    save_db(db)

def get_one(db: Dict[str, Any], table: str, row_id: int) -> Optional[Dict[str, Any]]:
    for r in db.get(table, []) or []:
        try:
            if int(r.get("id")) == int(row_id):
                return r
        except Exception:
            continue
    return None
