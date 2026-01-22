from typing import Optional, List, Dict, Any
from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.core.db import get_session
from app.core.auth import get_current_user, pode_acesso_global
from app.models.usuario import Usuario
from app.models.cras_tarefas import CrasTarefa

router = APIRouter(prefix="/cras/tarefas", tags=["CRAS · Tarefas"])


def _mun_id(usuario: Usuario) -> Optional[int]:
    mid = getattr(usuario, "municipio_id", None)
    return int(mid) if mid is not None else None


def _check_municipio(usuario: Usuario, municipio_id: Optional[int]) -> int:
    """Retorna o município efetivo permitido para o usuário (ou levanta 403/400)."""
    if pode_acesso_global(usuario):
        if municipio_id is None:
            raise HTTPException(status_code=400, detail="municipio_id é obrigatório para usuário global")
        return int(municipio_id)

    mid = _mun_id(usuario)
    if mid is None:
        raise HTTPException(status_code=403, detail="Usuário sem município")

    if municipio_id is not None and int(municipio_id) != int(mid):
        raise HTTPException(status_code=403, detail="Acesso negado (município)")

    return int(mid)


def _db_error_detail(e: Exception) -> str:
    # Útil para DEV: devolve o tipo e a mensagem do erro.
    msg = str(e)
    if len(msg) > 400:
        msg = msg[:400] + "…"
    return f"{type(e).__name__}: {msg}"


def _coerce_date(v: Any) -> Optional[date]:
    """Aceita date/datetime/str(YYYY-MM-DD) e devolve date ou None.

    Alguns clients (front) mandam datas como string ISO, e SQLite Date exige datetime.date.
    """
    if v is None:
        return None

    # datetime é subclass de date, por isso checamos datetime antes
    if isinstance(v, datetime):
        return v.date()

    if isinstance(v, date):
        return v

    if isinstance(v, str):
        s = v.strip()
        if not s:
            return None
        try:
            # aceita YYYY-MM-DD ou YYYY-MM-DDTHH:MM...
            return date.fromisoformat(s[:10])
        except Exception:
            raise HTTPException(status_code=422, detail=f"Data inválida: {v!r}. Use YYYY-MM-DD")

    # tipo inesperado
    raise HTTPException(status_code=422, detail=f"Data inválida (tipo): {type(v).__name__}")


@router.get("", response_model=List[CrasTarefa])
def listar(
    unidade_id: Optional[int] = None,
    municipio_id: Optional[int] = None,
    status: Optional[str] = None,
    responsavel_id: Optional[int] = None,
    vencidas: Optional[bool] = None,
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    # Segurança municipal
    mid = _check_municipio(usuario, municipio_id)

    q = select(CrasTarefa).where(CrasTarefa.municipio_id == mid)
    if unidade_id is not None:
        q = q.where(CrasTarefa.unidade_id == unidade_id)
    if status:
        q = q.where(CrasTarefa.status == status)
    if responsavel_id is not None:
        q = q.where(CrasTarefa.responsavel_id == responsavel_id)
    if vencidas:
        today = date.today()
        q = (
            q.where(CrasTarefa.status != "concluida")
            .where(CrasTarefa.data_vencimento.is_not(None))
            .where(CrasTarefa.data_vencimento < today)
        )

    q = q.order_by(CrasTarefa.status, CrasTarefa.data_vencimento, CrasTarefa.criado_em.desc())
    return session.exec(q).all()


# ✅ IMPORTANTE: /resumo PRECISA vir antes de /{tarefa_id}
@router.get("/resumo")
def resumo(
    unidade_id: Optional[int] = None,
    municipio_id: Optional[int] = None,
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    today = date.today()

    mid = _check_municipio(usuario, municipio_id)

    q = select(CrasTarefa).where(CrasTarefa.municipio_id == mid)
    if unidade_id is not None:
        q = q.where(CrasTarefa.unidade_id == unidade_id)

    tarefas = session.exec(q).all()

    por: Dict[str, Dict[str, Any]] = {}
    total_abertas = 0
    total_vencidas = 0

    for t in tarefas:
        if t.status != "concluida":
            total_abertas += 1
            if t.data_vencimento and t.data_vencimento < today:
                total_vencidas += 1

        key = str(t.responsavel_id or 0)
        if key not in por:
            por[key] = {
                "responsavel_id": t.responsavel_id,
                "responsavel_nome": t.responsavel_nome or "—",
                "abertas": 0,
                "vencidas": 0,
                "concluidas": 0,
            }

        if t.status == "concluida":
            por[key]["concluidas"] += 1
        else:
            por[key]["abertas"] += 1
            if t.data_vencimento and t.data_vencimento < today:
                por[key]["vencidas"] += 1

    lista = list(por.values())
    lista.sort(key=lambda x: (x["vencidas"], x["abertas"]), reverse=True)

    return {
        "total_abertas": total_abertas,
        "total_vencidas": total_vencidas,
        "por_tecnico": lista,
    }


@router.get("/{tarefa_id}", response_model=CrasTarefa)
def obter(
    tarefa_id: int,
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    t = session.get(CrasTarefa, tarefa_id)
    if not t:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada")

    mid = _check_municipio(usuario, getattr(t, "municipio_id", None))
    if getattr(t, "municipio_id", None) != mid:
        raise HTTPException(status_code=403, detail="Acesso negado (município)")

    return t


@router.post("", response_model=CrasTarefa)
def criar(
    t: CrasTarefa,
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    # Segurança municipal
    mid = _check_municipio(usuario, getattr(t, "municipio_id", None))
    t.municipio_id = mid

    # Normaliza datas (alguns clients mandam string)
    if hasattr(t, "data_vencimento"):
        t.data_vencimento = _coerce_date(getattr(t, "data_vencimento", None))
    if hasattr(t, "data_conclusao"):
        t.data_conclusao = _coerce_date(getattr(t, "data_conclusao", None))

    # defaults defensivos (evita NOT NULL no banco)
    if not getattr(t, "prioridade", None):
        t.prioridade = "media"
    if not getattr(t, "status", None):
        t.status = "aberta"

    t.criado_em = datetime.utcnow()
    t.atualizado_em = datetime.utcnow()

    try:
        session.add(t)
        session.commit()
        session.refresh(t)
        return t
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Falha ao criar tarefa: {_db_error_detail(e)}")


@router.patch("/{tarefa_id}", response_model=CrasTarefa)
def atualizar(
    tarefa_id: int,
    payload: Dict[str, Any],
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    t = session.get(CrasTarefa, tarefa_id)
    if not t:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada")

    _check_municipio(usuario, getattr(t, "municipio_id", None))

    for k, v in payload.items():
        if not hasattr(t, k):
            continue

        if k in ("data_vencimento", "data_conclusao"):
            setattr(t, k, _coerce_date(v))
        else:
            setattr(t, k, v)

    # auto data_conclusao
    if getattr(t, "status", None) == "concluida" and getattr(t, "data_conclusao", None) is None:
        t.data_conclusao = date.today()

    t.atualizado_em = datetime.utcnow()

    try:
        session.add(t)
        session.commit()
        session.refresh(t)
        return t
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Falha ao atualizar tarefa: {_db_error_detail(e)}")


@router.delete("/{tarefa_id}")
def excluir(
    tarefa_id: int,
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    t = session.get(CrasTarefa, tarefa_id)
    if not t:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada")

    _check_municipio(usuario, getattr(t, "municipio_id", None))

    try:
        session.delete(t)
        session.commit()
        return {"ok": True}
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Falha ao excluir tarefa: {_db_error_detail(e)}")
