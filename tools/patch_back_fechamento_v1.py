#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
from datetime import datetime
import re, sys

def tag(): return datetime.now().strftime("%Y%m%d_%H%M%S")
def backup(p: Path, s: str):
    p.with_suffix(p.suffix + f".bak_{tag()}").write_text(s, encoding="utf-8")

def patch_db(db_path: Path) -> bool:
    s0 = db_path.read_text(encoding="utf-8")
    if "app.models.prontuario_pes" in s0:
        return False
    m = re.search(r"modules\s*=\s*\[\s*\n", s0)
    if not m:
        backup(db_path, s0)
        db_path.write_text(s0 + "\n# PATCH_FECHAMENTO_V1\n", encoding="utf-8")
        return True
    ins = m.end()
    s = s0[:ins] + '        "app.models.prontuario_pes",\n' + s0[ins:]
    backup(db_path, s0); db_path.write_text(s, encoding="utf-8")
    return True

def patch_main(main_path: Path) -> bool:
    s0 = main_path.read_text(encoding="utf-8")
    s = s0
    changed = False

    if "cras_pes_router" not in s:
        block = (
            "\ntry:\n"
            "    from app.routers.cras_pes import router as cras_pes_router  # type: ignore\n"
            "except Exception:\n"
            "    cras_pes_router = None\n"
        )
        last = None
        for mm in re.finditer(r"from app\.routers\.[a-zA-Z0-9_]+\s+import\s+router as [a-zA-Z0-9_]+\n", s):
            last = mm
        if last:
            s = s[:last.end()] + block + s[last.end():]
        else:
            s = block + "\n" + s
        changed = True

    if "app.include_router(cras_pes_router)" not in s:
        block2 = "\nif cras_pes_router:\n    app.include_router(cras_pes_router)\n"
        pos = None
        m = re.search(r"\nif cras_prontuario_router:\n\s*app\.include_router\(cras_prontuario_router\)\n", s)
        if m: pos = m.end()
        else:
            m2 = re.search(r"\napp\.include_router\(cras_router\)\n", s)
            pos = m2.end() if m2 else None
        s = s + block2 if pos is None else (s[:pos] + block2 + s[pos:])
        changed = True

    if changed:
        backup(main_path, s0); main_path.write_text(s, encoding="utf-8")
    return changed

def patch_rma(rma_path: Path) -> bool:
    s0 = rma_path.read_text(encoding="utf-8")
    if "# RMA_PRESTACAO_V1" in s0:
        return False
    s = s0

    if "from app.models.rma_meta import RmaMeta" not in s:
        m = re.search(r"from app\.models\.rma_evento import RmaEvento\s*\n", s)
        if m:
            s = s[:m.end()] + "from app.models.rma_meta import RmaMeta\n" + s[m.end():]
        else:
            s = "from app.models.rma_meta import RmaMeta\n" + s

    s += r'''
# RMA_PRESTACAO_V1

@router.get("/prestacao.csv")
def prestacao_csv(
    mes: str = Query(..., description="YYYY-MM"),
    unidade_id: Optional[int] = Query(None),
    municipio_id: Optional[int] = Query(None),
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    yy, mm = _parse_mes(mes)

    mid = municipio_id or getattr(usuario, "municipio_id", None)
    if mid is None and not _is_admin_or_consorcio(usuario):
        raise HTTPException(status_code=400, detail="municipio_id é obrigatório para este usuário.")
    if not _is_admin_or_consorcio(usuario):
        mid = getattr(usuario, "municipio_id", None)

    q = select(RmaEvento).where(RmaEvento.municipio_id == int(mid))
    if unidade_id is not None:
        q = q.where(RmaEvento.unidade_id == int(unidade_id))
    rows = session.exec(q).all()
    rows = [r for r in rows if _in_month(r.data_evento, yy, mm)]

    qm = select(RmaMeta).where(RmaMeta.municipio_id == int(mid), RmaMeta.mes == mes)
    if unidade_id is not None:
        qm = qm.where(RmaMeta.unidade_id == int(unidade_id))
    metas = session.exec(qm).all()
    meta_by_serv = {m.servico: int(m.meta_total or 0) for m in metas}

    real_by_serv = {}
    total_by_day = {}
    for r in rows:
        serv = r.servico
        real_by_serv[serv] = real_by_serv.get(serv, 0) + 1
        d = r.data_evento.isoformat()
        total_by_day[d] = total_by_day.get(d, 0) + 1

    servicos = sorted(set(list(real_by_serv.keys()) + list(meta_by_serv.keys())))

    def gen():
        yield "tipo,mes,unidade_id,servico,meta_total,realizado_total,pct,dia,qtd_dia\n"
        for serv in servicos:
            meta = int(meta_by_serv.get(serv, 0))
            real = int(real_by_serv.get(serv, 0))
            pct = (round((real / meta) * 100) if meta else "")
            yield f"resumo,{mes},{unidade_id or ''},{serv},{meta},{real},{pct},,\n"
        for dia in sorted(total_by_day.keys()):
            yield f"serie,{mes},{unidade_id or ''},TOTAL,,, ,{dia},{total_by_day[dia]}\n"

    filename = f"prestacao_rma_{mes}_municipio_{int(mid)}.csv"
    if unidade_id is not None:
        filename = f"prestacao_rma_{mes}_unidade_{int(unidade_id)}.csv"
    return StreamingResponse(gen(), media_type="text/csv", headers={"Content-Disposition": f'attachment; filename="{filename}"'})
'''
    backup(rma_path, s0); rma_path.write_text(s, encoding="utf-8")
    return True

def main() -> int:
    root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(".").resolve()
    db = root / "backend/app/core/db.py"
    main_py = root / "backend/app/main.py"
    rma = root / "backend/app/routers/cras_rma.py"
    if not db.exists() or not main_py.exists() or not rma.exists():
        print("ERRO: não encontrei db/main/cras_rma")
        return 2
    print("OK:", {"db": patch_db(db), "main": patch_main(main_py), "rma": patch_rma(rma)})
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
