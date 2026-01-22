# app/routers/encaminhamentos.py
from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session, select
from sqlalchemy import or_

from app.core.db import get_session
from app.core.security import decodificar_token
from app.models.usuario import Usuario
from app.models.encaminhamentos import EncaminhamentoIntermunicipal, EncaminhamentoEvento

router = APIRouter(prefix="/encaminhamentos", tags=["encaminhamentos"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# =========================================================
# Auth (Bearer obrigatório)
# =========================================================
def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: Session = Depends(get_session),
) -> Usuario:
    try:
        payload = decodificar_token(token)
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Token inválido.")
    except Exception:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado.")

    usuario = session.get(Usuario, int(user_id))
    if not usuario or not getattr(usuario, "ativo", True):
        raise HTTPException(status_code=401, detail="Usuário inválido/inativo.")
    return usuario


def _is_admin_or_consorcio(usuario: Usuario) -> bool:
    p = (getattr(usuario, "perfil", "") or "").lower()
    return p in ("admin", "gestor_consorcio")


# =========================================================
# Workflow (linha do metrô)
# =========================================================
STATUS_ORDEM = [
    "solicitado",
    "contato",
    "aceito",
    "agendado",
    "passagem",
    "contrarreferencia",
    "concluido",
]

STATUS_VALIDOS = set(STATUS_ORDEM + ["cancelado"])


def _agora() -> datetime:
    return datetime.utcnow()


def _idx_status(s: str) -> int:
    try:
        return STATUS_ORDEM.index(s)
    except ValueError:
        return -1


def _proximo_status_atual(atual: str) -> Optional[str]:
    if atual in ("cancelado", "concluido"):
        return None
    idx = _idx_status(atual)
    if idx < 0:
        # se vier algo estranho, assume que ainda está no início
        return "contato"
    if idx >= len(STATUS_ORDEM) - 1:
        return None
    return STATUS_ORDEM[idx + 1]



# =========================================================
# Export padrão da "Linha do Metrô" (mesmo schema de /casos/{id}/linha-metro)
# =========================================================
METRO_ETAPAS = [
    {"codigo": "SOLICITADO", "nome": "Solicitado", "descricao": "Solicitação registrada (com consentimento)."},
    {"codigo": "CONTATO", "nome": "Contato (origem)", "descricao": "Origem tenta contato e organiza o trânsito."},
    {"codigo": "ACEITO", "nome": "Aceite (destino)", "descricao": "Destino aceita o encaminhamento."},
    {"codigo": "AGENDADO", "nome": "Agendado (destino)", "descricao": "Destino agenda data/forma de atendimento."},
    {"codigo": "PASSAGEM", "nome": "Passagem/Logística (origem)", "descricao": "Origem registra passagem/apoios quando aplicável."},
    {"codigo": "CONTRARREFERENCIA", "nome": "Contrarreferência (destino)", "descricao": "Destino registra devolutiva/contrarreferência."},
    {"codigo": "CONCLUIDO", "nome": "Concluído", "descricao": "Fluxo finalizado."},
]

# código -> status do workflow
_METRO_CODIGO_PARA_STATUS = {
    "SOLICITADO": "solicitado",
    "CONTATO": "contato",
    "ACEITO": "aceito",
    "AGENDADO": "agendado",
    "PASSAGEM": "passagem",
    "CONTRARREFERENCIA": "contrarreferencia",
    "CONCLUIDO": "concluido",
}
_STATUS_PARA_METRO_CODIGO = {v: k for k, v in _METRO_CODIGO_PARA_STATUS.items()}


def _metro_status_etapa(idx: int, idx_atual: int, status_enc: str) -> str:
    # Se já concluiu, tudo fica concluído
    if (status_enc or "").lower() == "concluido":
        return "concluida"
    if idx < idx_atual:
        return "concluida"
    if idx == idx_atual:
        return "em_andamento"
    return "nao_iniciada"


def _montar_linha_metro(enc: EncaminhamentoIntermunicipal, eventos: Optional[List[dict]] = None) -> dict:
    status_raw = (enc.status or "solicitado").strip().lower()
    eventos = eventos or []

    # Se cancelado, tentamos inferir o último passo "real" pelos eventos (para não zerar o metrô)
    status_base = status_raw
    if status_raw == "cancelado":
        for ev in reversed(eventos):
            t = (ev.get("tipo") or "").strip().lower()
            if t in STATUS_ORDEM:
                status_base = t
                break
        # Se não achou, assume início
        if status_base == "cancelado":
            status_base = "solicitado"

    idx_atual = _idx_status(status_base)
    if idx_atual < 0:
        idx_atual = 0

    # Agrupa eventos por tipo (status)
    ev_por_tipo: dict = {}
    for ev in eventos:
        t = (ev.get("tipo") or "").strip().lower()
        ev_por_tipo.setdefault(t, []).append(ev)

    def _mk_registros(tipo_status: str):
        arr = ev_por_tipo.get(tipo_status, []) or []
        # ordena do mais recente para o mais antigo
        arr = sorted(arr, key=lambda x: (x.get("em") or ""), reverse=True)
        registros = []
        for x in arr[:10]:
            registros.append(
                {
                    "id": x.get("id"),
                    "responsavel_usuario_id": None,
                    "responsavel_nome": x.get("por_nome"),
                    "data_hora": x.get("em"),
                    "obs": x.get("detalhe"),
                    "atendimento_id": None,
                    "encaminhamentos": None,
                }
            )
        ultimo = registros[0] if registros else None
        return ultimo, registros

    etapas = []
    for ordem, etapa in enumerate(METRO_ETAPAS, start=1):
        codigo = etapa["codigo"]
        st = _METRO_CODIGO_PARA_STATUS.get(codigo, "solicitado")
        ultimo, regs = _mk_registros(st)
        etapas.append(
            {
                "ordem": ordem,
                "codigo": codigo,
                "nome": etapa["nome"],
                "descricao": etapa["descricao"],
                "status": _metro_status_etapa(ordem - 1, idx_atual, status_base),
                "ultimo_registro": ultimo,
                "registros": regs,
            }
        )

    return {
        "tipo": "encaminhamento_intermunicipal",
        "encaminhamento_id": enc.id,
        "status": status_raw,
        "etapa_atual": _STATUS_PARA_METRO_CODIGO.get(status_base, "SOLICITADO"),
        "etapas": etapas,
        "gerado_em": datetime.utcnow().isoformat(),
        "cancelado": status_raw == "cancelado",
        "concluido": status_raw == "concluido",
    }


def _dono_do_passo(status: str) -> str:
    """
    Quem registra cada passo (mais correto):
      - ORIGEM: contato, passagem, concluido
      - DESTINO: aceito, agendado, contrarreferencia
      - solicitado é gerado na criação (origem), mas não é “clicável”
      - cancelado: origem ou destino
    """
    mapa = {
        "solicitado": "ORIGEM",
        "contato": "ORIGEM",
        "aceito": "DESTINO",
        "agendado": "DESTINO",
        "passagem": "ORIGEM",
        "contrarreferencia": "DESTINO",
        "concluido": "ORIGEM",
        "cancelado": "AMBOS",
    }
    return mapa.get(status, "AMBOS")


def _papel_usuario_no_enc(usuario: Usuario, enc: EncaminhamentoIntermunicipal) -> str:
    """
    Retorna ORIGEM / DESTINO / NONE para usuário municipal.
    Admin/consórcio não precisa disso (pode tudo).
    """
    muni_user = getattr(usuario, "municipio_id", None)
    if not muni_user:
        return "NONE"

    if enc.municipio_origem_id is not None and int(enc.municipio_origem_id) == int(muni_user):
        return "ORIGEM"
    if enc.municipio_destino_id is not None and int(enc.municipio_destino_id) == int(muni_user):
        return "DESTINO"
    return "NONE"


def _verifica_acesso_ver(usuario: Usuario, enc: EncaminhamentoIntermunicipal) -> None:
    """
    Admin/consórcio: vê tudo.
    Municipal: vê se for ORIGEM OU DESTINO.
    """
    if _is_admin_or_consorcio(usuario):
        return

    papel = _papel_usuario_no_enc(usuario, enc)
    if papel == "NONE":
        raise HTTPException(status_code=403, detail="Sem permissão para acessar este encaminhamento.")


def _verifica_pode_registrar_etapa(usuario: Usuario, enc: EncaminhamentoIntermunicipal, novo_status: str) -> None:
    """
    Regras fortes no backend:
      1) status deve ser válido
      2) só pode avançar para o PRÓXIMO passo (linha do metrô)
      3) ORIGEM/DESTINO só registram os passos deles
      4) passagem NÃO pode via /status -> tem que usar /passagem
      5) cancelado pode antes de finalizar
    """
    if novo_status not in STATUS_VALIDOS:
        raise HTTPException(status_code=400, detail=f"Status inválido: {novo_status}")

    atual = enc.status or "solicitado"

    # travas de finalização
    if atual == "concluido":
        raise HTTPException(status_code=400, detail="Encaminhamento já está concluído.")
    if atual == "cancelado":
        raise HTTPException(status_code=400, detail="Encaminhamento já está cancelado.")

    # passagem: força endpoint próprio
    if novo_status == "passagem":
        raise HTTPException(status_code=400, detail="Use o endpoint /passagem para registrar passagem.")

    # cancelado pode em qualquer ponto antes de finalizar
    if novo_status == "cancelado":
        return

    # só pode registrar o PRÓXIMO passo
    prox = _proximo_status_atual(atual)
    if prox is None:
        raise HTTPException(status_code=400, detail="Não há próximo passo (fluxo finalizado).")
    if novo_status != prox:
        raise HTTPException(
            status_code=400,
            detail=f"Etapa fora de ordem. Status atual: {atual}. Próximo passo permitido: {prox}.",
        )

    # regra ORIGEM/DESTINO (admin/consórcio pode tudo)
    if _is_admin_or_consorcio(usuario):
        return

    dono = _dono_do_passo(novo_status)
    papel = _papel_usuario_no_enc(usuario, enc)

    if dono == "ORIGEM" and papel != "ORIGEM":
        raise HTTPException(status_code=403, detail="Somente o município de ORIGEM pode registrar esta etapa.")
    if dono == "DESTINO" and papel != "DESTINO":
        raise HTTPException(status_code=403, detail="Somente o município de DESTINO pode registrar esta etapa.")
    if papel == "NONE":
        raise HTTPException(status_code=403, detail="Sem permissão para registrar etapas neste encaminhamento.")


# =========================================================
# Helpers de retorno
# =========================================================
def _eventos_do_enc(session: Session, enc_id: int) -> List[dict]:
    stmt = (
        select(EncaminhamentoEvento)
        .where(EncaminhamentoEvento.encaminhamento_id == enc_id)
        .order_by(EncaminhamentoEvento.em.desc())
    )
    eventos = session.exec(stmt).all()
    return [
        {
            "id": ev.id,
            "tipo": ev.tipo,
            "detalhe": ev.detalhe,
            "por_nome": ev.por_nome,
            "em": ev.em.isoformat() if ev.em else None,
        }
        for ev in eventos
    ]


def _to_dict(enc: EncaminhamentoIntermunicipal, eventos: Optional[List[dict]] = None) -> dict:
    return {
        "id": enc.id,
        "pessoa_id": enc.pessoa_id,
        "caso_id": enc.caso_id,
        "municipio_origem_id": enc.municipio_origem_id,
        "municipio_destino_id": enc.municipio_destino_id,
        "motivo": enc.motivo,
        "observacoes": enc.observacoes,
        "consentimento_registrado": enc.consentimento_registrado,
        "status": enc.status,
        "contato_em": enc.contato_em.isoformat() if enc.contato_em else None,
        "aceite_em": enc.aceite_em.isoformat() if enc.aceite_em else None,
        "agendado_em": enc.agendado_em.isoformat() if enc.agendado_em else None,
        "passagem_em": enc.passagem_em.isoformat() if enc.passagem_em else None,
        "contrarreferencia_em": enc.contrarreferencia_em.isoformat() if enc.contrarreferencia_em else None,
        "concluido_em": enc.concluido_em.isoformat() if enc.concluido_em else None,
        "cancelado_em": enc.cancelado_em.isoformat() if enc.cancelado_em else None,
        "passagem_numero": enc.passagem_numero,
        "passagem_empresa": enc.passagem_empresa,
        "passagem_data_viagem": enc.passagem_data_viagem.isoformat() if enc.passagem_data_viagem else None,
        "kit_lanche": enc.kit_lanche,
        "kit_higiene": enc.kit_higiene,
        "kit_mapa_info": enc.kit_mapa_info,
        "justificativa_passagem": enc.justificativa_passagem,
        "autorizado_por_nome": enc.autorizado_por_nome,
        "criado_em": enc.criado_em.isoformat() if enc.criado_em else None,
        "atualizado_em": enc.atualizado_em.isoformat() if enc.atualizado_em else None,
        "eventos": eventos or [],
    }


def _add_evento(session: Session, enc_id: int, tipo: str, detalhe: Optional[str], por_nome: Optional[str]) -> None:
    ev = EncaminhamentoEvento(
        encaminhamento_id=enc_id,
        tipo=tipo,
        detalhe=detalhe,
        por_nome=por_nome,
        em=_agora(),
    )
    session.add(ev)


# =========================================================
# Endpoints
# =========================================================
@router.get("/")
def listar(
    status_filtro: Optional[str] = None,
    caso_id: Optional[int] = None,
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    stmt = select(EncaminhamentoIntermunicipal).order_by(EncaminhamentoIntermunicipal.id.desc())

    if status_filtro:
        stmt = stmt.where(EncaminhamentoIntermunicipal.status == status_filtro)

    if caso_id is not None:
        stmt = stmt.where(EncaminhamentoIntermunicipal.caso_id == int(caso_id))

    # Municipal: origem OU destino
    if not _is_admin_or_consorcio(usuario):
        muni_user = getattr(usuario, "municipio_id", None)
        if not muni_user:
            raise HTTPException(status_code=403, detail="Usuário sem município vinculado.")

        stmt = stmt.where(
            or_(
                EncaminhamentoIntermunicipal.municipio_origem_id == int(muni_user),
                EncaminhamentoIntermunicipal.municipio_destino_id == int(muni_user),
            )
        )

    itens = session.exec(stmt).all()
    out = []
    for x in itens:
        d = _to_dict(x, eventos=[])
        d["linha_metro"] = _montar_linha_metro(x, eventos=[])
        out.append(d)
    return out


@router.get("/{enc_id}")
def obter(
    enc_id: int,
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    enc = session.get(EncaminhamentoIntermunicipal, enc_id)
    if not enc:
        raise HTTPException(status_code=404, detail="Encaminhamento não encontrado.")

    _verifica_acesso_ver(usuario, enc)
    eventos = _eventos_do_enc(session, enc.id)
    out = _to_dict(enc, eventos=eventos)
    out["linha_metro"] = _montar_linha_metro(enc, eventos=eventos)
    return out




@router.get("/{enc_id}/linha-metro")
def linha_metro_intermunicipal(
    enc_id: int,
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    """Retorna a Linha do Metrô do encaminhamento intermunicipal no padrão do sistema."""
    enc = session.get(EncaminhamentoIntermunicipal, enc_id)
    if not enc:
        raise HTTPException(status_code=404, detail="Encaminhamento não encontrado.")

    _verifica_acesso_ver(usuario, enc)

    eventos = _eventos_do_enc(session, enc.id)
    return _montar_linha_metro(enc, eventos=eventos)

@router.post("/", status_code=201)
def criar(
    payload: dict,
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    pessoa_id = payload.get("pessoa_id")
    destino_id = payload.get("municipio_destino_id")
    caso_id = payload.get("caso_id")
    motivo = (payload.get("motivo") or "").strip()
    observacoes = (payload.get("observacoes") or "").strip() or None
    consent = bool(payload.get("consentimento_registrado"))

    if not pessoa_id:
        raise HTTPException(status_code=400, detail="pessoa_id é obrigatório.")
    if not destino_id:
        raise HTTPException(status_code=400, detail="municipio_destino_id é obrigatório.")
    if not motivo:
        raise HTTPException(status_code=400, detail="motivo é obrigatório.")
    if consent is not True:
        raise HTTPException(status_code=400, detail="consentimento_registrado deve ser TRUE.")

    # ORIGEM: para perfis municipais, sempre é o município do usuário
    origem_id = payload.get("municipio_origem_id")
    if not _is_admin_or_consorcio(usuario):
        origem_id = getattr(usuario, "municipio_id", None)
        if not origem_id:
            raise HTTPException(status_code=403, detail="Usuário sem município vinculado.")

    now = _agora()
    enc = EncaminhamentoIntermunicipal(
        pessoa_id=int(pessoa_id),
        caso_id=int(caso_id) if caso_id else None,
        municipio_origem_id=int(origem_id) if origem_id is not None else None,
        municipio_destino_id=int(destino_id),
        motivo=motivo,
        observacoes=observacoes,
        consentimento_registrado=True,
        status="solicitado",
        criado_em=now,
        atualizado_em=now,
    )

    session.add(enc)
    session.commit()
    session.refresh(enc)

    _add_evento(
        session=session,
        enc_id=enc.id,
        tipo="solicitado",
        detalhe="Solicitação registrada (com consentimento).",
        por_nome=getattr(usuario, "nome", None),
    )
    session.commit()
    session.refresh(enc)

    eventos = _eventos_do_enc(session, enc.id)
    out = _to_dict(enc, eventos=eventos)
    out["linha_metro"] = _montar_linha_metro(enc, eventos=eventos)
    return out


@router.post("/{enc_id}/status")
def atualizar_status(
    enc_id: int,
    payload: dict,
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    enc = session.get(EncaminhamentoIntermunicipal, enc_id)
    if not enc:
        raise HTTPException(status_code=404, detail="Encaminhamento não encontrado.")

    _verifica_acesso_ver(usuario, enc)

    novo_status = (payload.get("status") or "").strip()
    detalhe = (payload.get("detalhe") or "").strip() or None

    if not novo_status:
        raise HTTPException(status_code=400, detail="status é obrigatório.")

    _verifica_pode_registrar_etapa(usuario, enc, novo_status)

    now = _agora()
    enc.status = novo_status
    enc.atualizado_em = now

    # timestamps por marco
    if novo_status == "contato":
        enc.contato_em = enc.contato_em or now
    elif novo_status == "aceito":
        enc.aceite_em = enc.aceite_em or now
    elif novo_status == "agendado":
        enc.agendado_em = enc.agendado_em or now
    elif novo_status == "contrarreferencia":
        enc.contrarreferencia_em = enc.contrarreferencia_em or now
    elif novo_status == "concluido":
        enc.concluido_em = enc.concluido_em or now
    elif novo_status == "cancelado":
        enc.cancelado_em = enc.cancelado_em or now

    session.add(enc)
    session.commit()
    session.refresh(enc)

    _add_evento(
        session=session,
        enc_id=enc.id,
        tipo=novo_status,
        detalhe=detalhe,
        por_nome=getattr(usuario, "nome", None),
    )
    session.commit()
    session.refresh(enc)

    eventos = _eventos_do_enc(session, enc.id)
    out = _to_dict(enc, eventos=eventos)
    out["linha_metro"] = _montar_linha_metro(enc, eventos=eventos)
    return out


@router.post("/{enc_id}/passagem")
def registrar_passagem(
    enc_id: int,
    payload: dict,
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    enc = session.get(EncaminhamentoIntermunicipal, enc_id)
    if not enc:
        raise HTTPException(status_code=404, detail="Encaminhamento não encontrado.")

    _verifica_acesso_ver(usuario, enc)

    # regra: só ORIGEM registra passagem (admin pode)
    if not _is_admin_or_consorcio(usuario):
        papel = _papel_usuario_no_enc(usuario, enc)
        if papel != "ORIGEM":
            raise HTTPException(status_code=403, detail="Somente a ORIGEM pode registrar passagem.")

    # regra: passagem só depois de ACEITE ou AGENDADO
    if enc.status not in ("agendado", "aceito", "passagem"):
        raise HTTPException(status_code=400, detail="Passagem só pode ser registrada após ACEITE/AGENDAMENTO.")

    # Campos
    enc.passagem_numero = payload.get("passagem_numero") or enc.passagem_numero
    enc.passagem_empresa = payload.get("passagem_empresa") or enc.passagem_empresa

    data_viagem = payload.get("passagem_data_viagem")
    if data_viagem:
        try:
            enc.passagem_data_viagem = datetime.fromisoformat(data_viagem.replace("Z", "+00:00")).replace(tzinfo=None)
        except Exception:
            raise HTTPException(status_code=400, detail="passagem_data_viagem inválida (use ISO).")

    enc.kit_lanche = bool(payload.get("kit_lanche", enc.kit_lanche))
    enc.kit_higiene = bool(payload.get("kit_higiene", enc.kit_higiene))
    enc.kit_mapa_info = bool(payload.get("kit_mapa_info", enc.kit_mapa_info))

    enc.justificativa_passagem = payload.get("justificativa_passagem") or enc.justificativa_passagem
    enc.autorizado_por_nome = getattr(usuario, "nome", None)

    # marca status PASSAGEM (e mantém ordem do fluxo)
    now = _agora()
    enc.status = "passagem"
    enc.passagem_em = enc.passagem_em or now
    enc.atualizado_em = now

    session.add(enc)
    session.commit()
    session.refresh(enc)

    _add_evento(
        session=session,
        enc_id=enc.id,
        tipo="passagem",
        detalhe="Passagem/benefício eventual registrado.",
        por_nome=getattr(usuario, "nome", None),
    )
    session.commit()
    session.refresh(enc)

    eventos = _eventos_do_enc(session, enc.id)
    out = _to_dict(enc, eventos=eventos)
    out["linha_metro"] = _montar_linha_metro(enc, eventos=eventos)
    return out