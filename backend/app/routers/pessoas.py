from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import Session, select
from sqlalchemy import or_

from app.core.db import get_session
from app.core.auth import get_current_user
from app.models.usuario import Usuario
from app.models.municipio import Municipio
from app.models.pessoa import PessoaRua, PessoaRuaBase

try:
    from app.models.caso_pop_rua import CasoPopRua  # type: ignore
except Exception:
    CasoPopRua = None

try:
    from app.models.atendimento import Atendimento  # type: ignore
except Exception:
    Atendimento = None

router = APIRouter(prefix="/pessoas", tags=["pessoas"])

# -------------------------------------------------------------------
# CANAL DE COMUNICAÇÃO (em memória)
# -------------------------------------------------------------------
COMUNICACOES_MEMORIA: List[dict] = []
COMUNICACAO_NEXT_ID: int = 1

REDACTION_TEXT = "🔒 Restrito (LGPD)"


# =========================================================
# Helpers gerais
# =========================================================
def _dump(obj) -> dict:
    """Compatível com pydantic v1/v2 + SQLModel."""
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    if hasattr(obj, "dict"):
        return obj.dict()
    return dict(obj)


def _perfil(usuario: Usuario) -> str:
    return (getattr(usuario, "perfil", "") or "").strip().lower()


def _is_admin(usuario: Usuario) -> bool:
    return _perfil(usuario) == "admin"


def _is_gestor_ou_admin(usuario: Usuario) -> bool:
    return _perfil(usuario) in {"gestor_consorcio", "admin"}


def _is_municipal(usuario: Usuario) -> bool:
    return _perfil(usuario) in {"operador", "coord_municipal"}


def _user_municipio_id(usuario: Usuario) -> int:
    mun = getattr(usuario, "municipio_id", None)
    if mun is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuário sem município associado. Acesso negado.",
        )
    return int(mun)


def _normalizar_numero(s: Optional[str]) -> Optional[str]:
    if not s:
        return None
    digits = "".join(ch for ch in str(s) if ch.isdigit())
    return digits or None


def _validar_municipio(session: Session, municipio_id: Optional[int]) -> None:
    if municipio_id is None:
        return
    m = session.get(Municipio, int(municipio_id))
    if not m:
        raise HTTPException(status_code=400, detail="Município de origem não encontrado.")


def _redigir_pessoa(p: PessoaRua, usuario: Usuario) -> PessoaRua:
    """
    LGPD:
    - Admin vê tudo
    - Outros: redige campos sensíveis (identificadores e textos livres)
    """
    if _is_admin(usuario):
        return p

    # Mantém dados operacionais e complementos (para trabalho da rede)
    # e redige apenas identificadores sensíveis.
    return PessoaRua(
        id=p.id,
        nome_social=getattr(p, "nome_social", None),
        nome_civil=REDACTION_TEXT,
        data_nascimento=None,
        cpf=None,
        nis=None,
        genero=getattr(p, "genero", None),
        estado_civil=getattr(p, "estado_civil", None),
        apelido=getattr(p, "apelido", None),
        telefone=getattr(p, "telefone", None),
        whatsapp=getattr(p, "whatsapp", None),
        contato_referencia_nome=getattr(p, "contato_referencia_nome", None),
        contato_referencia_telefone=getattr(p, "contato_referencia_telefone", None),
        permanencia_rua=getattr(p, "permanencia_rua", None),
        pontos_circulacao=getattr(p, "pontos_circulacao", None),
        horario_mais_encontrado=getattr(p, "horario_mais_encontrado", None),
        motivo_rua=getattr(p, "motivo_rua", None),
        escolaridade=getattr(p, "escolaridade", None),
        ocupacao=getattr(p, "ocupacao", None),
        interesses_reinsercao=getattr(p, "interesses_reinsercao", None),
        cadunico_status=getattr(p, "cadunico_status", None),
        documentos_pendentes=getattr(p, "documentos_pendentes", None),
        fonte_renda=getattr(p, "fonte_renda", None),
        violencia_risco=getattr(p, "violencia_risco", None),
        ameaca_territorio=getattr(p, "ameaca_territorio", None),
        gestante_status=getattr(p, "gestante_status", None),
        protecao_imediata=getattr(p, "protecao_imediata", None),
        interesse_acolhimento=getattr(p, "interesse_acolhimento", None),
        moradia_recente=getattr(p, "moradia_recente", None),
        tentativas_saida_rua=getattr(p, "tentativas_saida_rua", None),
        dependencia_quimica=getattr(p, "dependencia_quimica", None),
        municipio_origem_id=getattr(p, "municipio_origem_id", None),
        tempo_rua=getattr(p, "tempo_rua", None),
        local_referencia=getattr(p, "local_referencia", None),
        # observações redigidas (texto livre)
        observacoes_gerais=REDACTION_TEXT if getattr(p, "observacoes_gerais", None) else None,
    )


def _stmt_pessoas_visiveis_para_usuario(session: Session, usuario: Usuario):
    """
    Regra de município:
    - gestor/admin: vê tudo
    - operador/coord: vê pessoas associadas ao município do usuário

    Associação tentada:
    1) municipio_origem_id == município do usuário
    2) OU pessoa aparece em CasoPopRua.municipio_id == município do usuário
    3) OU pessoa aparece em Atendimento.municipio_id == município do usuário
    """
    stmt = select(PessoaRua).order_by(PessoaRua.id)

    if _is_gestor_ou_admin(usuario):
        return stmt

    user_mun = _user_municipio_id(usuario)
    condicoes = [PessoaRua.municipio_origem_id == user_mun]

    if CasoPopRua is not None and hasattr(CasoPopRua, "municipio_id"):
        sub_casos = select(CasoPopRua.pessoa_id).where(CasoPopRua.municipio_id == user_mun)
        condicoes.append(PessoaRua.id.in_(sub_casos))

    if Atendimento is not None and hasattr(Atendimento, "municipio_id"):
        sub_at = select(Atendimento.pessoa_id).where(Atendimento.municipio_id == user_mun)
        condicoes.append(PessoaRua.id.in_(sub_at))

    return stmt.where(or_(*condicoes))


def _usuario_pode_acessar_pessoa(session: Session, usuario: Usuario, pessoa_id: int) -> bool:
    if _is_gestor_ou_admin(usuario):
        return True
    stmt = _stmt_pessoas_visiveis_para_usuario(session, usuario).where(PessoaRua.id == pessoa_id)
    return session.exec(stmt).first() is not None


# =========================================================
# PESSOAS (LGPD + município)
# =========================================================
@router.post("/", response_model=PessoaRua)
def criar_pessoa(
    dados: PessoaRuaBase,
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    payload = _dump(dados)

    # municipal: força municipio_origem_id do usuário
    if _is_municipal(usuario):
        user_mun = _user_municipio_id(usuario)
        if payload.get("municipio_origem_id") is not None and int(payload["municipio_origem_id"]) != int(user_mun):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Acesso negado: não é permitido cadastrar pessoa para outro município.",
            )
        payload["municipio_origem_id"] = user_mun

    # normaliza cpf/nis (só dígitos)
    payload["cpf"] = _normalizar_numero(payload.get("cpf"))
    payload["nis"] = _normalizar_numero(payload.get("nis"))

    _validar_municipio(session, payload.get("municipio_origem_id"))

    pessoa = PessoaRua(**payload)
    session.add(pessoa)
    session.commit()
    session.refresh(pessoa)

    return pessoa if _is_admin(usuario) else _redigir_pessoa(pessoa, usuario)


@router.get("/", response_model=List[PessoaRua])
def listar_pessoas(
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    stmt = _stmt_pessoas_visiveis_para_usuario(session, usuario)
    pessoas = list(session.exec(stmt).all())
    return pessoas if _is_admin(usuario) else [_redigir_pessoa(p, usuario) for p in pessoas]


@router.get("/{pessoa_id}", response_model=PessoaRua)
def obter_pessoa(
    pessoa_id: int,
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    pessoa = session.get(PessoaRua, pessoa_id)
    if not pessoa:
        raise HTTPException(status_code=404, detail="Pessoa não encontrada.")

    if not _usuario_pode_acessar_pessoa(session, usuario, pessoa_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado: pessoa fora do seu município.",
        )

    return pessoa if _is_admin(usuario) else _redigir_pessoa(pessoa, usuario)


# =========================================================
# ✅ PATCH: EDIÇÃO MÍNIMA E SEGURA (FICHA DA PESSOA)
# =========================================================
@router.patch("/{pessoa_id}", response_model=PessoaRua)
def atualizar_pessoa_minimo_seguro(
    pessoa_id: int,
    payload: dict,
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    """
    PATCH mínimo e seguro (para a Ficha da Pessoa):
    - municipal só pode editar campos “operacionais”
    - admin/gestor consórcio podem editar também identificadores (cpf/nis/nome_civil/data_nascimento) e municipio_origem_id
    """
    pessoa = session.get(PessoaRua, pessoa_id)
    if not pessoa:
        raise HTTPException(status_code=404, detail="Pessoa não encontrada.")

    if not _usuario_pode_acessar_pessoa(session, usuario, pessoa_id):
        raise HTTPException(status_code=403, detail="Acesso negado: pessoa fora do seu município.")

    # Campos permitidos
    campos_operacionais = {
        "nome_social",
        "genero",
        "estado_civil",
        "tempo_rua",
        "local_referencia",
        "observacoes_gerais",

        # complementos
        "apelido",
        "telefone",
        "whatsapp",
        "contato_referencia_nome",
        "contato_referencia_telefone",
        "permanencia_rua",
        "pontos_circulacao",
        "horario_mais_encontrado",
        "motivo_rua",
        "escolaridade",
        "ocupacao",
        "interesses_reinsercao",
        "cadunico_status",
        "documentos_pendentes",
        "fonte_renda",
        "violencia_risco",
        "ameaca_territorio",
        "gestante_status",
        "protecao_imediata",
        "interesse_acolhimento",
        "moradia_recente",
        "tentativas_saida_rua",
        "dependencia_quimica",
    }

    campos_admin = campos_operacionais | {
        "nome_civil",
        "data_nascimento",
        "cpf",
        "nis",
        "municipio_origem_id",
    }

    permitidos = campos_admin if _is_gestor_ou_admin(usuario) else campos_operacionais

    # municipal não pode alterar município de origem
    if _is_municipal(usuario) and "municipio_origem_id" in (payload or {}):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado: não é permitido alterar município de origem.",
        )

    mudou = False
    for k, v in (payload or {}).items():
        if k not in permitidos:
            continue

        if k in {"cpf", "nis"}:
            v = _normalizar_numero(v)

        if k == "municipio_origem_id" and v is not None:
            _validar_municipio(session, int(v))

        if hasattr(pessoa, k):
            setattr(pessoa, k, v)
            mudou = True

    if not mudou:
        return pessoa if _is_admin(usuario) else _redigir_pessoa(pessoa, usuario)

    session.add(pessoa)
    session.commit()
    session.refresh(pessoa)

    return pessoa if _is_admin(usuario) else _redigir_pessoa(pessoa, usuario)


# =========================================================
# BUSCA SERVER-SIDE
# =========================================================
@router.get("/busca", response_model=List[PessoaRua])
def buscar_pessoas(
    tipo: str = Query("nome", description="nome|cpf|nis"),
    q: str = Query(..., min_length=1, description="Texto de busca"),
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    """
    Busca server-side:
    - tipo=nome: procura em nome_social e nome_civil (LIKE)
    - tipo=cpf: procura por cpf (só dígitos)
    - tipo=nis: procura por nis (só dígitos)

    Aplica filtro de município conforme perfil.
    Retorna redigido para não-admin.
    """
    tipo = (tipo or "").strip().lower()
    q = (q or "").strip()

    if tipo not in {"nome", "cpf", "nis"}:
        raise HTTPException(status_code=400, detail="tipo inválido. Use nome|cpf|nis")

    base_stmt = _stmt_pessoas_visiveis_para_usuario(session, usuario)

    if tipo == "nome":
        term = f"%{q}%"
        stmt = base_stmt.where(
            or_(
                PessoaRua.nome_social.ilike(term),
                PessoaRua.nome_civil.ilike(term),
            )
        )
    elif tipo == "cpf":
        digits = _normalizar_numero(q)
        if not digits:
            raise HTTPException(status_code=400, detail="CPF inválido.")
        stmt = base_stmt.where(PessoaRua.cpf == digits)
    else:  # nis
        digits = _normalizar_numero(q)
        if not digits:
            raise HTTPException(status_code=400, detail="NIS inválido.")
        stmt = base_stmt.where(PessoaRua.nis == digits)

    pessoas = list(session.exec(stmt).all())
    return pessoas if _is_admin(usuario) else [_redigir_pessoa(p, usuario) for p in pessoas]


# =========================================================
# CANAL DE COMUNICAÇÃO – protegido
# =========================================================
@router.get("/{pessoa_id}/comunicacoes")
async def listar_comunicacoes_pessoa(
    pessoa_id: int,
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    pessoa = session.get(PessoaRua, pessoa_id)
    if not pessoa:
        raise HTTPException(status_code=404, detail="Pessoa não encontrada.")

    if not _usuario_pode_acessar_pessoa(session, usuario, pessoa_id):
        raise HTTPException(status_code=403, detail="Acesso negado: pessoa fora do seu município.")

    perfil = _perfil(usuario)
    msgs = [c for c in COMUNICACOES_MEMORIA if c.get("pessoa_id") == pessoa_id]

    if perfil == "operador":
        user_mun = _user_municipio_id(usuario)
        msgs = [m for m in msgs if int(m.get("municipio_id") or 0) == int(user_mun)]

    return msgs


@router.post("/{pessoa_id}/comunicacoes")
async def criar_comunicacao_pessoa(
    pessoa_id: int,
    payload: dict,
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    global COMUNICACAO_NEXT_ID

    pessoa = session.get(PessoaRua, pessoa_id)
    if not pessoa:
        raise HTTPException(status_code=404, detail="Pessoa não encontrada.")

    if not _usuario_pode_acessar_pessoa(session, usuario, pessoa_id):
        raise HTTPException(status_code=403, detail="Acesso negado: pessoa fora do seu município.")

    agora = datetime.utcnow().isoformat()

    municipio_id = payload.get("municipio_id")
    municipio_nome = payload.get("municipio_nome")

    if _is_municipal(usuario):
        municipio_id = _user_municipio_id(usuario)
        m = session.get(Municipio, int(municipio_id))
        municipio_nome = m.nome if m else (municipio_nome or f"Município {municipio_id}")

    autor_nome = getattr(usuario, "nome", None) or payload.get("autor_nome") or "Usuário Pop Rua"

    nova = {
        "id": COMUNICACAO_NEXT_ID,
        "pessoa_id": pessoa_id,
        "caso_id": payload.get("caso_id"),
        "municipio_id": municipio_id,
        "municipio_nome": municipio_nome,
        "autor_nome": autor_nome,
        "tipo": payload.get("tipo", "registro"),
        "texto": payload.get("texto", ""),
        "criado_em": agora,
    }

    COMUNICACAO_NEXT_ID += 1
    COMUNICACOES_MEMORIA.append(nova)
    return nova


@router.get("/comunicacoes-resumo-municipio")
async def resumo_comunicacoes_por_municipio(
    usuario: Usuario = Depends(get_current_user),
):
    if not _is_gestor_ou_admin(usuario):
        raise HTTPException(
            status_code=403,
            detail="Apenas gestor do consórcio e admin podem ver o resumo regional.",
        )

    resumo = {}
    for c in COMUNICACOES_MEMORIA:
        municipio_id = c.get("municipio_id")
        if municipio_id is None:
            continue

        municipio_nome = c.get("municipio_nome") or f"Município {municipio_id}"

        if municipio_id not in resumo:
            resumo[municipio_id] = {
                "municipio_id": municipio_id,
                "municipio_nome": municipio_nome,
                "total_mensagens": 0,
                "total_alertas": 0,
            }

        resumo[municipio_id]["total_mensagens"] += 1
        if c.get("tipo") == "alerta":
            resumo[municipio_id]["total_alertas"] += 1

    return list(resumo.values())