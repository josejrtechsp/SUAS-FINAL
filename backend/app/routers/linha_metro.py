# app/routers/linha_metro.py
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.core.db import get_session
from app.core.auth import get_current_user, pode_acesso_global, nivel_perfil
from app.core.poprua_fluxo import (
    METRO_ETAPAS as ETAPAS,
    METRO_INDEX as ETAPA_INDEX,
    etapa_metro,
    etapa_valida_metro,
    metro_to_caso,
    deve_promover_caso_para_metro,
)
from app.models.usuario import Usuario
from app.models.caso_pop_rua import CasoPopRua, CasoPopRuaEtapaHistorico
from app.models.linha_metro_registro import CasoEtapaRegistro, CasoEtapaRegistroVinculo
from app.models.encaminhamentos import EncaminhamentoIntermunicipal


router = APIRouter(prefix="/casos", tags=["linha_metro"])
 

# =========================================================
# RBAC (hierarquia)
# =========================================================
NIVEL_VER = max(nivel_perfil("recepcao"), nivel_perfil("leitura"), 1)
NIVEL_OPERAR = max(nivel_perfil("tecnico"), nivel_perfil("operador"), 10)


def _exigir_nivel(usuario: Usuario, minimo: int, *, acao: str) -> None:
    if int(nivel_perfil(getattr(usuario, "perfil", None))) < int(minimo):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Acesso negado: perfil sem permissão para {acao}.",
        )


def _status_etapa(idx: int, idx_atual: int, caso_status: str) -> str:
    # Se caso está encerrado, tudo fica concluído
    if (caso_status or "").lower() == "encerrado":
        return "concluida"

    if idx < idx_atual:
        return "concluida"
    if idx == idx_atual:
        return "em_andamento"
    return "nao_iniciada"


@router.get("/linha-metro/etapas")
def listar_etapas(
    usuario: Usuario = Depends(get_current_user),
):
    # endpoint auxiliar (o front pode usar para renderizar a estrutura fixa)
    out = []
    for i, e in enumerate(ETAPAS, start=1):
        out.append(
            {
                "ordem": i,
                "codigo": e["codigo"],
                "nome": e["nome"],
                "descricao": e["descricao"],
            }
        )
    return {"etapas": out}


@router.get("/{caso_id}/linha-metro")
def linha_metro_do_caso(
    caso_id: int,
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    _exigir_nivel(usuario, NIVEL_VER, acao="visualizar linha do metrô")

    caso = session.get(CasoPopRua, caso_id)
    if not caso:
        raise HTTPException(status_code=404, detail="Caso não encontrado.")

    # Regra de acesso por município:
    # - global (gestor_consorcio/admin): vê tudo
    # - demais: só vê casos do seu município
    if not pode_acesso_global(usuario):
        muni_user = getattr(usuario, "municipio_id", None)
        if muni_user is None:
            raise HTTPException(status_code=403, detail="Usuário sem município vinculado.")
        caso_muni = getattr(caso, "municipio_id", None)
        if caso_muni is not None and int(caso_muni) != int(muni_user):
            raise HTTPException(status_code=403, detail="Sem permissão para acessar este caso.")

    etapa_atual_raw = (getattr(caso, "etapa_atual", None) or "ABORDAGEM")
    etapa_atual = etapa_metro(etapa_atual_raw)
    idx_atual = int(ETAPA_INDEX.get(etapa_atual, 0))

    # ---------------------------------------------
    # Registros auditáveis (B1.5)
    # ---------------------------------------------
    stmt_reg = (
        select(CasoEtapaRegistro)
        .where(CasoEtapaRegistro.caso_id == caso_id)
        .order_by(CasoEtapaRegistro.data_hora.desc())
    )
    registros = list(session.exec(stmt_reg).all())

    # Mapa de usuários (id -> nome)
    user_ids = {r.responsavel_usuario_id for r in registros}
    user_map = {}
    if user_ids:
        for uid in user_ids:
            u = session.get(Usuario, int(uid))
            if u:
                user_map[int(uid)] = getattr(u, "nome", None) or getattr(u, "email", None) or f"Usuário {uid}"

    # Vínculos por registro
    vinc_map = {}
    if registros:
        reg_ids = [r.id for r in registros if r.id]
        if reg_ids:
            stmt_v = select(CasoEtapaRegistroVinculo).where(CasoEtapaRegistroVinculo.registro_id.in_(reg_ids))
            vincs = list(session.exec(stmt_v).all())
            for v in vincs:
                vinc_map.setdefault(int(v.registro_id), []).append(v)

    # Carrega encaminhamentos intermunicipais vinculados
    enc_ids = set()
    for vs in vinc_map.values():
        for v in vs:
            if v.tipo == "encaminhamento_intermunicipal":
                enc_ids.add(int(v.ref_id))
    enc_map = {}
    if enc_ids:
        stmt_enc = select(EncaminhamentoIntermunicipal).where(EncaminhamentoIntermunicipal.id.in_(list(enc_ids)))
        for e in session.exec(stmt_enc).all():
            enc_map[int(e.id)] = e

    # organiza por etapa
    reg_por_etapa = {}
    for r in registros:
        reg_por_etapa.setdefault(r.etapa, []).append(r)

    def _enc_resumo(reg_id: int):
        out = []
        for v in vinc_map.get(reg_id, []):
            if v.tipo != "encaminhamento_intermunicipal":
                continue
            e = enc_map.get(int(v.ref_id))
            if not e:
                out.append({"id": int(v.ref_id), "tipo": v.tipo})
                continue
            out.append(
                {
                    "id": e.id,
                    "tipo": "encaminhamento_intermunicipal",
                    "status": e.status,
                    "municipio_origem_id": e.municipio_origem_id,
                    "municipio_destino_id": e.municipio_destino_id,
                    "motivo": e.motivo,
                }
            )
        return out

    etapas = []
    for i, e in enumerate(ETAPAS, start=1):
        codigo = e["codigo"]
        regs_et = reg_por_etapa.get(codigo, [])
        ultimo = regs_et[0] if regs_et else None
        ultimo_dict = None
        if ultimo:
            ultimo_dict = {
                "id": ultimo.id,
                "responsavel_usuario_id": ultimo.responsavel_usuario_id,
                "responsavel_nome": user_map.get(int(ultimo.responsavel_usuario_id)),
                "data_hora": ultimo.data_hora.isoformat() if ultimo.data_hora else None,
                "obs": ultimo.obs,
                "atendimento_id": ultimo.atendimento_id,
                "encaminhamentos": _enc_resumo(int(ultimo.id)),
            }

        registros_dict = []
        for r in regs_et[:10]:
            registros_dict.append(
                {
                    "id": r.id,
                    "responsavel_usuario_id": r.responsavel_usuario_id,
                    "responsavel_nome": user_map.get(int(r.responsavel_usuario_id)),
                    "data_hora": r.data_hora.isoformat() if r.data_hora else None,
                    "obs": r.obs,
                    "atendimento_id": r.atendimento_id,
                    "encaminhamentos": _enc_resumo(int(r.id)) if r.id else [],
                }
            )

        etapas.append(
            {
                "ordem": i,
                "codigo": codigo,
                "nome": e["nome"],
                "descricao": e["descricao"],
                "status": _status_etapa(i - 1, idx_atual, getattr(caso, "status", "") or ""),
                "ultimo_registro": ultimo_dict,
                "registros": registros_dict,
            }
        )

    return {
        "caso_id": caso_id,
        "etapa_atual": etapa_atual,
        "status_caso": getattr(caso, "status", None),
        "data_inicio_etapa_atual": (
            getattr(caso, "data_inicio_etapa_atual", None).isoformat()
            if getattr(caso, "data_inicio_etapa_atual", None)
            else None
        ),
        "etapas": etapas,
        "gerado_em": datetime.utcnow().isoformat(),
    }


@router.post("/{caso_id}/linha-metro/registrar", status_code=201)
def registrar_etapa(
    caso_id: int,
    payload: dict,
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    _exigir_nivel(usuario, NIVEL_OPERAR, acao="registrar etapa no metrô")

    caso = session.get(CasoPopRua, caso_id)
    if not caso:
        raise HTTPException(status_code=404, detail="Caso não encontrado.")

    # regra de acesso (mesma do GET)
    if not pode_acesso_global(usuario):
        muni_user = getattr(usuario, "municipio_id", None)
        if muni_user is None:
            raise HTTPException(status_code=403, detail="Usuário sem município vinculado.")
        caso_muni = getattr(caso, "municipio_id", None)
        if caso_muni is not None and int(caso_muni) != int(muni_user):
            raise HTTPException(status_code=403, detail="Sem permissão para acessar este caso.")

    etapa = (payload.get("etapa") or "").strip().upper()
    if not etapa:
        raise HTTPException(status_code=400, detail="Campo 'etapa' é obrigatório.")
    if not etapa_valida_metro(etapa):
        raise HTTPException(status_code=400, detail=f"Etapa inválida: {etapa}")

    obs = (payload.get("obs") or "").strip() or None
    if obs and len(obs) > 600:
        obs = obs[:600]

    atendimento_id = payload.get("atendimento_id")
    try:
        atendimento_id = int(atendimento_id) if atendimento_id not in (None, "") else None
    except Exception:
        atendimento_id = None

    enc_ids = payload.get("encaminhamentos_ids") or []
    if not isinstance(enc_ids, list):
        enc_ids = []
    enc_ids = [int(x) for x in enc_ids if str(x).isdigit()]

    reg = CasoEtapaRegistro(
        caso_id=caso_id,
        etapa=etapa,
        responsavel_usuario_id=int(usuario.id),
        data_hora=datetime.utcnow(),
        atendimento_id=atendimento_id,
        obs=obs,
    )

    session.add(reg)
    session.commit()

    # -------------------------------------------------
    # Sincronização opcional (fecha lacuna de fluxo)
    # - registra no metrô e, se fizer sentido, promove `caso.etapa_atual`
    #   para manter o caso alinhado com o que está sendo executado.
    # -------------------------------------------------
    try:
        if (getattr(caso, "status", "") or "").lower() != "encerrado":
            if deve_promover_caso_para_metro(getattr(caso, "etapa_atual", None), etapa):
                now = datetime.utcnow()
                novo_etapa_caso = metro_to_caso(etapa)
                antigo = getattr(caso, "etapa_atual", None)

                caso.etapa_atual = novo_etapa_caso
                caso.data_ultima_atualizacao = now
                caso.data_inicio_etapa_atual = now

                if etapa == "ENCERRAMENTO":
                    caso.status = "encerrado"
                    caso.data_encerramento = now

                session.add(caso)

                # histórico mínimo (auditável)
                hist = CasoPopRuaEtapaHistorico(
                    caso_id=int(caso.id),
                    etapa=str(novo_etapa_caso),
                    data_acao=now,
                    usuario_responsavel=getattr(usuario, "nome", None) or "Usuário",
                    observacoes=(obs or f"Registro no metrô: {etapa}")[:600] if (obs or etapa) else None,
                    tipo_acao="linha_metro_registro",
                    motivo_estagnacao=getattr(caso, "motivo_estagnacao", None),
                )
                session.add(hist)
                session.commit()
                session.refresh(caso)
    except Exception:
        # nunca quebra a experiência do usuário por causa da sync
        pass
    session.refresh(reg)

    # vínculos
    for enc_id in enc_ids:
        v = CasoEtapaRegistroVinculo(
            registro_id=int(reg.id),
            tipo="encaminhamento_intermunicipal",
            ref_id=int(enc_id),
        )
        session.add(v)
    session.commit()

    return {
        "id": reg.id,
        "caso_id": reg.caso_id,
        "etapa": reg.etapa,
        "etapa_caso": getattr(caso, "etapa_atual", None),
        "responsavel_usuario_id": reg.responsavel_usuario_id,
        "data_hora": reg.data_hora.isoformat() if reg.data_hora else None,
        "obs": reg.obs,
        "atendimento_id": reg.atendimento_id,
        "encaminhamentos_ids": enc_ids,
    }