from __future__ import annotations

from datetime import date, datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select
from sqlalchemy import func

from app.core.db import get_session
from app.core.auth import get_current_user
from app.models.usuario import Usuario
from app.models.pessoa import PessoaRua
from app.models.municipio import Municipio

try:
    from app.models.caso_pop_rua import CasoPopRua  # type: ignore
except Exception:
    CasoPopRua = None

try:
    from app.models.atendimento import Atendimento  # type: ignore
except Exception:
    Atendimento = None

try:
    from app.models.saude import SaudeIntersetorialRegistro  # type: ignore
except Exception:
    SaudeIntersetorialRegistro = None


router = APIRouter(prefix="/dashboard", tags=["dashboard"])


def _perfil(u: Usuario) -> str:
    return (getattr(u, "perfil", "") or "").strip().lower()


def _is_gestor_ou_admin(u: Usuario) -> bool:
    return _perfil(u) in {"admin", "gestor_consorcio"}


def _user_municipio_id(u: Usuario) -> Optional[int]:
    mid = getattr(u, "municipio_id", None)
    return int(mid) if mid is not None else None


def _faixa_etaria(nasc: Optional[date]) -> str:
    if not nasc:
        return "Não informado"
    try:
        today = date.today()
        age = today.year - nasc.year - ((today.month, today.day) < (nasc.month, nasc.day))
    except Exception:
        return "Não informado"

    if age < 18:
        return "0-17"
    if age < 30:
        return "18-29"
    if age < 45:
        return "30-44"
    if age < 60:
        return "45-59"
    return "60+"


def _norm_sim_nao(v: Optional[str]) -> str:
    if not v:
        return "Não informado"
    s = str(v).strip().lower()
    if s in {"sim", "s", "yes", "y"}:
        return "Sim"
    if s in {"nao", "não", "n", "no"}:
        return "Não"
    return "Não informado"


@router.get("/overview")
def dashboard_overview(
    municipio_id: Optional[int] = Query(default=None, description="Filtro opcional por município (gestor/admin)"),
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    """Retorna métricas agregadas para o dashboard (B2)."""

    perfil = _perfil(usuario)
    user_mid = _user_municipio_id(usuario)

    # Controle de acesso
    if not _is_gestor_ou_admin(usuario):
        # municipal só vê seu município
        municipio_id = user_mid
    else:
        # gestor/admin pode filtrar por município ou ver geral
        if municipio_id is not None:
            # ok
            pass

    # Mapa município id -> nome
    muni_map: Dict[int, str] = {}
    for m in session.exec(select(Municipio)).all():
        try:
            muni_map[int(m.id)] = m.nome or m.nome_municipio  # type: ignore
        except Exception:
            continue

    # Pessoas (base)
    stmt_pessoas = select(PessoaRua)
    if municipio_id is not None:
        # pessoas vinculadas ao município (origem) OU com caso/atendimento no município
        conds = [PessoaRua.municipio_origem_id == int(municipio_id)]
        if CasoPopRua is not None:
            sub = select(CasoPopRua.pessoa_id).where(CasoPopRua.municipio_id == int(municipio_id))
            conds.append(PessoaRua.id.in_(sub))
        if Atendimento is not None:
            suba = select(Atendimento.pessoa_id).where(Atendimento.municipio_id == int(municipio_id))
            conds.append(PessoaRua.id.in_(suba))
        from sqlalchemy import or_ as _or
        stmt_pessoas = stmt_pessoas.where(_or(*conds))

    pessoas = list(session.exec(stmt_pessoas).all())

    # Métricas básicas
    total_pessoas = len(pessoas)

    # Casos
    total_casos = 0
    if CasoPopRua is not None:
        stmt_casos = select(func.count()).select_from(CasoPopRua)
        if municipio_id is not None:
            stmt_casos = stmt_casos.where(CasoPopRua.municipio_id == int(municipio_id))
        total_casos = int(session.exec(stmt_casos).one())

    genero: Dict[str, int] = {}
    faixa: Dict[str, int] = {}
    origem: Dict[int, int] = {}
    depq: Dict[str, int] = {"Sim": 0, "Não": 0, "Não informado": 0}

    for p in pessoas:
        g = (getattr(p, "genero", None) or "Não informado").strip() if isinstance(getattr(p, "genero", None), str) else (getattr(p, "genero", None) or "Não informado")
        g = g if g else "Não informado"
        genero[g] = genero.get(g, 0) + 1

        faixa_key = _faixa_etaria(getattr(p, "data_nascimento", None))
        faixa[faixa_key] = faixa.get(faixa_key, 0) + 1

        mid = getattr(p, "municipio_origem_id", None)
        if mid is not None:
            try:
                origem[int(mid)] = origem.get(int(mid), 0) + 1
            except Exception:
                pass

        dep = _norm_sim_nao(getattr(p, "dependencia_quimica", None))
        depq[dep] = depq.get(dep, 0) + 1

    # Passagens por serviços
    passagens: Dict[str, int] = {"saude": 0, "assistencia_social": 0}

    # Assistência social = pessoas com ao menos 1 atendimento
    if Atendimento is not None:
        stmt = select(func.count(func.distinct(Atendimento.pessoa_id)))
        if municipio_id is not None:
            stmt = stmt.where(Atendimento.municipio_id == int(municipio_id))
        try:
            passagens["assistencia_social"] = int(session.exec(stmt).one())
        except Exception:
            pass

    # Saúde = pessoas com ao menos 1 registro intersetorial em algum caso
    if SaudeIntersetorialRegistro is not None and CasoPopRua is not None:
        stmt = (
            select(func.count(func.distinct(CasoPopRua.pessoa_id)))
            .select_from(SaudeIntersetorialRegistro)
            .join(CasoPopRua, CasoPopRua.id == SaudeIntersetorialRegistro.caso_id)
        )
        if municipio_id is not None:
            stmt = stmt.where(CasoPopRua.municipio_id == int(municipio_id))
        try:
            passagens["saude"] = int(session.exec(stmt).one())
        except Exception:
            pass

    # Ordena cidades (top 10)
    origem_top: List[Dict[str, Any]] = []
    for mid, cnt in sorted(origem.items(), key=lambda x: x[1], reverse=True)[:10]:
        origem_top.append({"municipio_id": mid, "municipio_nome": muni_map.get(mid, f"Município {mid}"), "count": cnt})

    return {
        "perfil": perfil,
        "municipio_filtro_id": municipio_id,
        "total_pessoas": total_pessoas,
        "total_casos": total_casos,
        "genero": genero,
        "faixa_etaria": faixa,
        "origem_cidades": origem_top,
        "dependencia_quimica": depq,
        "passagens": passagens,
    }
