#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
from datetime import datetime
import re
import sys

def tag(): return datetime.now().strftime("%Y%m%d_%H%M%S")
def backup(p: Path, s: str):
    p.with_suffix(p.suffix + f".bak_{tag()}").write_text(s, encoding="utf-8")

def patch_db(db_path: Path) -> bool:
    s0 = db_path.read_text(encoding="utf-8")
    if "app.models.rma_meta" in s0:
        return False
    m = re.search(r"modules\s*=\s*\[\s*\n", s0)
    if not m:
        backup(db_path, s0)
        db_path.write_text(s0 + "\n# PATCH_BACK_RMA_METAS_V1\n", encoding="utf-8")
        return True
    ins = m.end()
    s = s0[:ins] + '        "app.models.rma_meta",\n' + s0[ins:]
    backup(db_path, s0)
    db_path.write_text(s, encoding="utf-8")
    return True

def patch_cras_rma(rma_path: Path) -> bool:
    s0 = rma_path.read_text(encoding="utf-8")
    if "# RMA_METAS_V1" in s0:
        return False
    s = s0

    if "from app.models.rma_meta import RmaMeta" not in s:
        m = re.search(r"from app\.models\.rma_evento import RmaEvento\s*\n", s)
        if m:
            s = s[:m.end()] + "from app.models.rma_meta import RmaMeta\n" + s[m.end():]
        else:
            s = "from app.models.rma_meta import RmaMeta\n" + s

    s += r'''
# RMA_METAS_V1

@router.get("/metas")
def listar_metas(
    mes: str = Query(..., description="YYYY-MM"),
    unidade_id: Optional[int] = Query(None),
    servico: Optional[str] = Query(None),
    municipio_id: Optional[int] = Query(None),
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    _parse_mes(mes)
    mid = municipio_id or getattr(usuario, "municipio_id", None)
    if mid is None and not _is_admin_or_consorcio(usuario):
        raise HTTPException(status_code=400, detail="municipio_id é obrigatório para este usuário.")
    if not _is_admin_or_consorcio(usuario):
        mid = getattr(usuario, "municipio_id", None)

    q = select(RmaMeta).where(RmaMeta.municipio_id == int(mid), RmaMeta.mes == mes)
    if unidade_id is not None:
        q = q.where(RmaMeta.unidade_id == int(unidade_id))
    if servico:
        q = q.where(RmaMeta.servico == str(servico).strip().upper())

    rows = session.exec(q).all()
    return [{
        "id": r.id,
        "mes": r.mes,
        "servico": r.servico,
        "unidade_id": r.unidade_id,
        "meta_total": r.meta_total,
        "meta_json": r.meta_json,
        "atualizado_em": r.atualizado_em.isoformat() if r.atualizado_em else None,
        "atualizado_por_nome": r.atualizado_por_nome,
    } for r in rows]


@router.post("/metas")
def upsert_meta(
    payload: Dict[str, Any],
    municipio_id: Optional[int] = Query(None),
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    mes = str(payload.get("mes") or "").strip()
    if not mes or len(mes) != 7:
        raise HTTPException(status_code=400, detail="mes é obrigatório (YYYY-MM)")
    _parse_mes(mes)

    servico = str(payload.get("servico") or "").strip().upper()
    if not servico:
        raise HTTPException(status_code=400, detail="servico é obrigatório")

    unidade_id = payload.get("unidade_id")
    try:
        unidade_id = int(unidade_id) if unidade_id is not None and str(unidade_id).strip() != "" else None
    except Exception:
        unidade_id = None

    meta_total = payload.get("meta_total")
    try:
        meta_total = int(meta_total) if meta_total is not None else 0
    except Exception:
        meta_total = 0

    meta_json = payload.get("meta_json")
    if meta_json is not None and not isinstance(meta_json, str):
        try:
            import json as _json
            meta_json = _json.dumps(meta_json, ensure_ascii=False)
        except Exception:
            meta_json = str(meta_json)

    mid = municipio_id or getattr(usuario, "municipio_id", None)
    if mid is None and not _is_admin_or_consorcio(usuario):
        raise HTTPException(status_code=400, detail="municipio_id é obrigatório para este usuário.")
    if not _is_admin_or_consorcio(usuario):
        mid = getattr(usuario, "municipio_id", None)

    q = select(RmaMeta).where(RmaMeta.municipio_id == int(mid), RmaMeta.mes == mes, RmaMeta.servico == servico)
    if unidade_id is None:
        q = q.where(RmaMeta.unidade_id == None)  # noqa
    else:
        q = q.where(RmaMeta.unidade_id == unidade_id)

    existing = session.exec(q).first()
    now = _agora()

    if existing:
        existing.meta_total = meta_total
        existing.meta_json = meta_json
        existing.atualizado_em = now
        existing.atualizado_por_nome = usuario.nome
        session.add(existing)
        session.commit()
        session.refresh(existing)
        return {"ok": True, "id": existing.id, "updated": True}

    rec = RmaMeta(
        municipio_id=int(mid) if mid is not None else 1,
        unidade_id=unidade_id,
        mes=mes,
        servico=servico[:40],
        meta_total=meta_total,
        meta_json=meta_json,
        criado_em=now,
        atualizado_em=now,
        atualizado_por_nome=usuario.nome,
    )
    session.add(rec)
    session.commit()
    session.refresh(rec)
    return {"ok": True, "id": rec.id, "updated": False}
'''
    backup(rma_path, s0)
    rma_path.write_text(s, encoding="utf-8")
    return True

def main() -> int:
    root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(".").resolve()
    db = root / "backend/app/core/db.py"
    rma = root / "backend/app/routers/cras_rma.py"
    if not db.exists() or not rma.exists():
        print("ERRO: não encontrei db.py ou cras_rma.py")
        return 2
    print("OK:", {"db": patch_db(db), "cras_rma": patch_cras_rma(rma)})
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
