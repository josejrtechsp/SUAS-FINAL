#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "== SLA por técnico: aplicando patch (backend + frontend) =="

# -------------------------
# BACKEND: model + router
# -------------------------
mkdir -p backend/app/models backend/app/routers

cat > backend/app/models/cras_tarefas.py <<'PY'
from typing import Optional
from datetime import datetime, date
from sqlmodel import SQLModel, Field

class CrasTarefa(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    # escopo
    municipio_id: Optional[int] = Field(default=None, index=True)
    unidade_id: Optional[int] = Field(default=None, index=True)

    # atribuição
    responsavel_id: Optional[int] = Field(default=None, index=True)  # usuario id
    responsavel_nome: Optional[str] = Field(default=None)

    # referência (liga tarefa a algo do sistema)
    ref_tipo: str = Field(index=True)  # "caso" | "cadunico" | "scfv" | "programa" | "ficha" | "encaminhamento" | "manual"
    ref_id: Optional[int] = Field(default=None, index=True)

    # conteúdo
    titulo: str
    descricao: Optional[str] = None
    prioridade: str = Field(default="media", index=True)  # baixa|media|alta|critica

    # SLA
    status: str = Field(default="aberta", index=True)  # aberta|em_andamento|concluida|cancelada
    data_vencimento: Optional[date] = Field(default=None, index=True)
    data_conclusao: Optional[date] = Field(default=None, index=True)

    criado_em: datetime = Field(default_factory=datetime.utcnow, index=True)
    atualizado_em: datetime = Field(default_factory=datetime.utcnow, index=True)
PY

cat > backend/app/routers/cras_tarefas.py <<'PY'
from typing import Optional, List
from datetime import date, datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select
from ..db import get_session
from ..models.cras_tarefas import CrasTarefa

router = APIRouter(prefix="/cras/tarefas", tags=["CRAS · Tarefas"])

@router.get("", response_model=List[CrasTarefa])
def listar(
    unidade_id: Optional[int] = None,
    municipio_id: Optional[int] = None,
    status: Optional[str] = None,
    responsavel_id: Optional[int] = None,
    vencidas: Optional[bool] = None,
    session: Session = Depends(get_session),
):
    q = select(CrasTarefa)
    if unidade_id is not None:
        q = q.where(CrasTarefa.unidade_id == unidade_id)
    if municipio_id is not None:
        q = q.where(CrasTarefa.municipio_id == municipio_id)
    if status:
        q = q.where(CrasTarefa.status == status)
    if responsavel_id is not None:
        q = q.where(CrasTarefa.responsavel_id == responsavel_id)
    if vencidas:
        today = date.today()
        q = q.where(CrasTarefa.status != "concluida").where(CrasTarefa.data_vencimento.is_not(None)).where(CrasTarefa.data_vencimento < today)
    q = q.order_by(CrasTarefa.status, CrasTarefa.data_vencimento, CrasTarefa.criado_em.desc())
    return session.exec(q).all()

@router.post("", response_model=CrasTarefa)
def criar(t: CrasTarefa, session: Session = Depends(get_session)):
    t.criado_em = datetime.utcnow()
    t.atualizado_em = datetime.utcnow()
    session.add(t)
    session.commit()
    session.refresh(t)
    return t

@router.patch("/{tarefa_id}", response_model=CrasTarefa)
def atualizar(tarefa_id: int, payload: dict, session: Session = Depends(get_session)):
    t = session.get(CrasTarefa, tarefa_id)
    if not t:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada")
    for k, v in payload.items():
        if hasattr(t, k):
            setattr(t, k, v)
    t.atualizado_em = datetime.utcnow()
    session.add(t)
    session.commit()
    session.refresh(t)
    return t

@router.get("/resumo")
def resumo(
    unidade_id: Optional[int] = None,
    municipio_id: Optional[int] = None,
    session: Session = Depends(get_session),
):
    today = date.today()

    q = select(CrasTarefa)
    if unidade_id is not None:
        q = q.where(CrasTarefa.unidade_id == unidade_id)
    if municipio_id is not None:
        q = q.where(CrasTarefa.municipio_id == municipio_id)

    tarefas = session.exec(q).all()

    por = {}
    total_abertas = 0
    total_vencidas = 0

    for t in tarefas:
        if t.status != "concluida":
            total_abertas += 1
            if t.data_vencimento and t.data_vencimento < today:
                total_vencidas += 1

        key = str(t.responsavel_id or 0)
        if key not in por:
            por[key] = {"responsavel_id": t.responsavel_id, "responsavel_nome": t.responsavel_nome or "—", "abertas": 0, "vencidas": 0, "concluidas": 0}
        if t.status == "concluida":
            por[key]["concluidas"] += 1
        else:
            por[key]["abertas"] += 1
            if t.data_vencimento and t.data_vencimento < today:
                por[key]["vencidas"] += 1

    # % simples: dentro do prazo = abertas - vencidas (proxy) + concluidas (sem SLA ainda)
    lista = list(por.values())
    lista.sort(key=lambda x: (x["vencidas"], x["abertas"]), reverse=True)

    return {
        "total_abertas": total_abertas,
        "total_vencidas": total_vencidas,
        "por_tecnico": lista,
    }
PY

# incluir router no main.py se ainda não estiver
python3 - <<'PY'
from pathlib import Path
import re

p = Path("backend/app/main.py")
txt = p.read_text(encoding="utf-8")

if "cras_tarefas" not in txt:
    # adiciona import e include_router no final dos routers
    # tenta inserir próximo de outros include_router do CRAS
    if "include_router" not in txt:
        raise SystemExit("Não encontrei include_router em app/main.py")

    # import
    insert_import = "\nfrom .routers import cras_tarefas\n"
    # coloca após outros imports de routers (heurística: após a última linha 'from .routers import ...')
    m = list(re.finditer(r"^from \.routers import .*$", txt, flags=re.M))
    if m:
        pos = m[-1].end()
        txt = txt[:pos] + insert_import + txt[pos:]
    else:
        # fallback após imports gerais
        pos = txt.find("\n\n")
        txt = txt[:pos] + insert_import + txt[pos:]

    # include_router
    # insere perto dos outros include_router (antes de return/uvicorn)
    txt = re.sub(r"(app\.include_router\([^\)]*\)\s*\n)(?![\s\S]*cras_tarefas)",
                 r"\1app.include_router(cras_tarefas.router)\n",
                 txt, count=1)

    p.write_text(txt, encoding="utf-8")
    print("OK: include_router(cras_tarefas) inserido em app/main.py")
else:
    print("OK: cras_tarefas já estava incluído")
PY

# -------------------------
# FRONTEND: dashboard mostra por técnico
# -------------------------
python3 - <<'PY'
from pathlib import Path
import re

p = Path("frontend/src/TelaCrasInicioDashboard.jsx")
if not p.exists():
    raise SystemExit("Não encontrei frontend/src/TelaCrasInicioDashboard.jsx")

txt = p.read_text(encoding="utf-8")

# injeta chamada do resumo de tarefas no load()
if "tarefasResumo" not in txt:
    txt = txt.replace("const [data, setData] = useState(null);", "const [data, setData] = useState(null);\n  const [tarefasResumo, setTarefasResumo] = useState(null);")

# dentro do load(), após setData(d)
if "setTarefasResumo" not in txt:
    txt = re.sub(
        r"setData\(d\);\s*",
        "setData(d);\n      try {\n        const u = new URL(`${apiBase}/cras/tarefas/resumo`);\n        const r = await apiFetch(u.toString());\n        const j = await r.json();\n        setTarefasResumo(j);\n      } catch {}\n",
        txt,
        count=1
    )

# renderizar tabela
if "Equipe e prazos" not in txt:
    insert_point = "      {/* Ações rápidas */}"
    table = """
      <div className="card" style={{ padding: 12, borderRadius: 16, marginTop: 12 }}>
        <div style={{ display: "flex", justifyContent: "space-between", gap: 10, flexWrap: "wrap", alignItems: "center" }}>
          <div style={{ fontWeight: 950 }}>Equipe e prazos (tarefas/SLA)</div>
          <div className="texto-suave">
            Abertas: <strong>{tarefasResumo?.total_abertas ?? "—"}</strong> · Vencidas: <strong>{tarefasResumo?.total_vencidas ?? "—"}</strong>
          </div>
        </div>

        <div style={{ overflowX: "auto", marginTop: 10 }}>
          <table className="table" style={{ width: "100%" }}>
            <thead>
              <tr>
                <th>Técnico</th>
                <th style={{ textAlign: "right" }}>Abertas</th>
                <th style={{ textAlign: "right" }}>Vencidas</th>
                <th style={{ textAlign: "right" }}>Concluídas</th>
              </tr>
            </thead>
            <tbody>
              {(tarefasResumo?.por_tecnico || []).map((x, idx) => (
                <tr key={idx}>
                  <td><strong>{x.responsavel_nome || "—"}</strong></td>
                  <td style={{ textAlign: "right" }}>{x.abertas}</td>
                  <td style={{ textAlign: "right" }}>{x.vencidas}</td>
                  <td style={{ textAlign: "right" }}>{x.concluidas}</td>
                </tr>
              ))}
              {(!tarefasResumo?.por_tecnico || tarefasResumo.por_tecnico.length === 0) ? (
                <tr><td colSpan={4} className="texto-suave">Sem tarefas cadastradas/atribuídas ainda.</td></tr>
              ) : null}
            </tbody>
          </table>
        </div>

        <div className="texto-suave" style={{ marginTop: 8 }}>
          Dica: tarefas são a base do SLA por servidor. Use para registrar “visita domiciliar”, “contato”, “atualizar CadÚnico”, “cobrar devolutiva”, etc.
        </div>
      </div>

"""
    txt = txt.replace(insert_point, table + "\n" + insert_point)

p.write_text(txt, encoding="utf-8")
print("OK: Dashboard agora mostra resumo de tarefas por técnico.")
PY

echo "== Diagnóstico obrigatório =="
cd frontend
npm install >/dev/null
npm run build
cd ..

python3 - <<'PY'
import compileall
ok = compileall.compile_dir("backend/app", quiet=1)
print("Backend compileall:", "OK" if ok else "FALHOU")
raise SystemExit(0 if ok else 1)
PY

echo "OK: Patch SLA por técnico aplicado."
