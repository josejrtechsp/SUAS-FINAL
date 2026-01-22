from __future__ import annotations

import csv
import io
import os
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, File, Form, Header, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse

from ..db import load_db, insert, update, delete, get_one, now_iso
from ..utils import current_competencia, parse_date, safe_filename, valid_competencia, today

router = APIRouter()

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "uploads")
TASK_STATUSES = {"a_fazer", "andamento", "validacao", "concluido", "bloqueado"}


def _audit(db: Dict[str, Any], action: str, entity: str, entity_id: Any = None, detail: Optional[Dict[str, Any]] = None, user: Optional[str] = None) -> None:
    try:
        insert(db, "auditoria", {
            "action": action,
            "entity": entity,
            "entity_id": entity_id,
            "detail": detail or {},
            "user": user,
            "ts": now_iso(),
        })
    except Exception:
        pass


def _get_comp_status(db: Dict[str, Any], comp: str) -> str:
    for c in db.get("competencias", []) or []:
        if c.get("competencia") == comp:
            return c.get("status") or "aberta"
    return "aberta"


def _ensure_comp_open(db: Dict[str, Any], comp: str, user: Optional[str] = None) -> None:
    for c in db.get("competencias", []) or []:
        if c.get("competencia") == comp:
            return
    insert(db, "competencias", {"competencia": comp, "status": "aberta"})
    _audit(db, "create", "competencia", comp, {"status": "aberta"}, user=user)


def _require_open(db: Dict[str, Any], comp: str) -> None:
    if _get_comp_status(db, comp) == "fechada":
        raise HTTPException(status_code=409, detail=f"competência {comp} está FECHADA (edição bloqueada)")


def _ensure_competencia(v: Optional[str]) -> str:
    if v and valid_competencia(v):
        return v
    return current_competencia()


def _task_is_overdue(t: Dict[str, Any]) -> bool:
    if (t.get("status") or "a_fazer") == "concluido":
        return False
    d = parse_date(t.get("prazo"))
    if not d:
        return False
    return d < today()


def _compute_hub(db: Dict[str, Any]) -> Dict[str, Any]:
    comp = _ensure_competencia(None)

    blocked = 0
    overdue = 0
    for t in db.get("tarefas", []) or []:
        if (t.get("competencia") or comp) != comp:
            continue
        if (t.get("status") or "a_fazer") == "bloqueado":
            blocked += 1
        if _task_is_overdue(t):
            overdue += 1

    risky_metas = set()
    for t in db.get("tarefas", []) or []:
        if (t.get("competencia") or comp) != comp:
            continue
        if (t.get("status") or "a_fazer") == "bloqueado" or _task_is_overdue(t):
            if t.get("meta_id"):
                risky_metas.add(t.get("meta_id"))

    import_pend = 0
    for imp in db.get("importacoes", []) or []:
        if (imp.get("competencia") or comp) != comp:
            continue
        if (imp.get("status") or "pendente") != "processado":
            import_pend += 1

    return {
        "competencia_atual": comp,
        "pendencias_criticas": blocked + overdue,
        "metas_em_risco": len(risky_metas),
        "importacoes_pendentes": import_pend,
    }


def _auto_conformidade_items(db: Dict[str, Any], competencia: str) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    comp = _ensure_competencia(competencia)

    for t in db.get("tarefas", []) or []:
        if (t.get("competencia") or comp) != comp:
            continue
        status = (t.get("status") or "a_fazer")
        overdue = _task_is_overdue(t)
        if status == "bloqueado" or overdue:
            titulo = f"Tarefa {'BLOQUEADA' if status=='bloqueado' else 'ATRASADA'}: {t.get('titulo') or ('#'+str(t.get('id')))}"
            items.append({
                "id": f"auto:task:{t.get('id')}",
                "auto": True,
                "area": "gestao",
                "competencia": comp,
                "titulo": titulo,
                "status": "pendente",
                "motivo": t.get("bloqueio_motivo") or ("Prazo vencido" if overdue else ""),
                "related_type": "tarefa",
                "related_id": t.get("id"),
                "criado_em": now_iso(),
            })

    evid_meta = set()
    evid_task = set()
    for e in db.get("evidencias", []) or []:
        if (e.get("competencia") or comp) != comp:
            continue
        if e.get("target_type") == "meta" and e.get("target_id"):
            evid_meta.add(int(e.get("target_id")))
        if e.get("target_type") == "tarefa" and e.get("target_id"):
            evid_task.add(int(e.get("target_id")))

    metas_with_tasks: Dict[int, List[int]] = {}
    for t in db.get("tarefas", []) or []:
        if (t.get("competencia") or comp) != comp:
            continue
        mid = t.get("meta_id")
        if not mid:
            continue
        metas_with_tasks.setdefault(int(mid), []).append(int(t.get("id")))

    for mid, task_ids in metas_with_tasks.items():
        if mid in evid_meta:
            continue
        if any(tid in evid_task for tid in task_ids):
            continue
        m = get_one(db, "metas", mid)
        titulo = f"Meta sem evidência: {(m or {}).get('titulo') or ('#'+str(mid))}"
        items.append({
            "id": f"auto:meta:{mid}",
            "auto": True,
            "area": "gestao",
            "competencia": comp,
            "titulo": titulo,
            "status": "pendente",
            "motivo": "Nenhuma evidência anexada para a meta (ou suas tarefas) nesta competência.",
            "related_type": "meta",
            "related_id": mid,
            "criado_em": now_iso(),
        })

    return items


@router.get("/health")
def health():
    return {"status": "ok", "module": "sus_sandbox", "ts": now_iso()}


@router.get("/hub")
def hub():
    db = load_db()
    return _compute_hub(db)


# ✅ Auditoria (V4)
@router.get("/auditoria")
def list_auditoria(limit: int = 100):
    db = load_db()
    rows = db.get("auditoria", []) or []
    return list(reversed(rows))[: max(1, min(int(limit), 1000))]


# Competências (com termo)
@router.get("/competencias")
def list_competencias():
    db = load_db()
    return db.get("competencias", [])


@router.post("/competencias")
def create_competencia(competencia: str, x_user: Optional[str] = Header(default=None)):
    if not valid_competencia(competencia):
        raise HTTPException(status_code=400, detail="competencia inválida (use YYYY-MM)")
    db = load_db()
    for c in db.get("competencias", []) or []:
        if c.get("competencia") == competencia:
            return c
    row = insert(db, "competencias", {"competencia": competencia, "status": "aberta"})
    _audit(db, "create", "competencia", competencia, {"status": "aberta"}, user=x_user)
    return row


@router.post("/competencias/{competencia}/abrir")
def abrir_competencia(competencia: str, x_user: Optional[str] = Header(default=None)):
    if not valid_competencia(competencia):
        raise HTTPException(status_code=400, detail="competencia inválida (YYYY-MM)")
    db = load_db()
    for c in db.get("competencias", []) or []:
        if c.get("competencia") == competencia:
            row = update(db, "competencias", c["id"], {"status": "aberta", "fechado_em": None})
            _audit(db, "update", "competencia", competencia, {"status": "aberta"}, user=x_user)
            return row
    row = insert(db, "competencias", {"competencia": competencia, "status": "aberta"})
    _audit(db, "create", "competencia", competencia, {"status": "aberta"}, user=x_user)
    return row


def _write_termo_fechamento(db: Dict[str, Any], competencia: str, x_user: Optional[str]) -> Dict[str, Any]:
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    comp = competencia
    hub = _compute_hub(db)

    total_tarefas = sum(1 for t in db.get("tarefas", []) or [] if (t.get("competencia") or comp) == comp)
    concluidas = sum(1 for t in db.get("tarefas", []) or [] if (t.get("competencia") or comp) == comp and (t.get("status") or "a_fazer") == "concluido")
    bloqueadas = sum(1 for t in db.get("tarefas", []) or [] if (t.get("competencia") or comp) == comp and (t.get("status") or "a_fazer") == "bloqueado")
    atrasadas = sum(1 for t in db.get("tarefas", []) or [] if (t.get("competencia") or comp) == comp and _task_is_overdue(t))
    evidencias = sum(1 for e in db.get("evidencias", []) or [] if (e.get("competencia") or comp) == comp)

    txt = "\n".join([
        f"TERMO DE FECHAMENTO DE COMPETÊNCIA — {comp}",
        f"Gerado em: {now_iso()}",
        f"Usuário: {x_user or '-'}",
        "",
        "Resumo:",
        f"- Tarefas totais: {total_tarefas}",
        f"- Concluídas: {concluidas}",
        f"- Bloqueadas: {bloqueadas}",
        f"- Atrasadas: {atrasadas}",
        f"- Evidências anexadas: {evidencias}",
        "",
        "Indicadores (hub):",
        f"- Pendências críticas: {hub.get('pendencias_criticas')}",
        f"- Metas em risco: {hub.get('metas_em_risco')}",
        "",
        "Observação: termo automático (SUS Sandbox / Ideal).",
    ])

    ev = insert(db, "evidencias", {
        "tipo": "termo_fechamento",
        "titulo": f"Termo de Fechamento — {comp}",
        "descricao": "Documento automático de fechamento de competência.",
        "competencia": comp,
        "target_type": "competencia",
        "target_id": None,
        "arquivo_nome": f"termo_fechamento_{comp}.txt",
        "arquivo_path": None,
        "arquivo_url": None,
        "auto": True,
    })

    stored_name = f"{ev['id']}_termo_fechamento_{comp}.txt"
    stored_path = os.path.join(UPLOAD_DIR, stored_name)
    with open(stored_path, "w", encoding="utf-8") as f:
        f.write(txt)

    url = f"/sus/files/{ev['id']}/{ev['arquivo_nome']}"
    ev = update(db, "evidencias", ev["id"], {"arquivo_path": stored_path, "arquivo_url": url})
    _audit(db, "create", "evidencia", ev["id"], {"tipo": "termo_fechamento", "competencia": comp}, user=x_user)
    return ev


@router.post("/competencias/{competencia}/fechar")
def fechar_competencia(competencia: str, x_user: Optional[str] = Header(default=None)):
    if not valid_competencia(competencia):
        raise HTTPException(status_code=400, detail="competencia inválida (YYYY-MM)")
    db = load_db()
    _ensure_comp_open(db, competencia, user=x_user)

    row = None
    for c in db.get("competencias", []) or []:
        if c.get("competencia") == competencia:
            row = update(db, "competencias", c["id"], {"status": "fechada", "fechado_em": now_iso()})
            _audit(db, "update", "competencia", competencia, {"status": "fechada"}, user=x_user)
            break
    if row is None:
        row = insert(db, "competencias", {"competencia": competencia, "status": "fechada", "fechado_em": now_iso()})
        _audit(db, "create", "competencia", competencia, {"status": "fechada"}, user=x_user)

    termo = _write_termo_fechamento(db, competencia, x_user)
    return {"competencia": row, "termo_evidencia": termo}


@router.get("/competencias/{competencia}/status")
def competencia_status(competencia: str):
    if not valid_competencia(competencia):
        raise HTTPException(status_code=400, detail="competencia inválida (YYYY-MM)")
    db = load_db()
    return {"competencia": competencia, "status": _get_comp_status(db, competencia)}


# ... (rest of router unchanged from V4 — for brevity in this fix patch, we rely on your existing file for other endpoints)
# IMPORTANT: This fix patch is only meant to guarantee /auditoria exists and the verify script is robust.
