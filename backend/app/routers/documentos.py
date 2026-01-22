from __future__ import annotations

import json
import os
import base64
import html as html_lib
import hashlib
import hmac
from dataclasses import dataclass
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from io import BytesIO
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import FileResponse, StreamingResponse, HTMLResponse
from pydantic import BaseModel, Field as PField
from sqlmodel import Session, select

from app.core.auth import exigir_minimo_perfil, get_current_user, pode_acesso_global
from app.core.db import get_session
from app.models.usuario import Usuario
from app.models.municipio import Municipio
from app.models.municipio_branding import MunicipioBranding
from app.models.documento_template import DocumentoTemplate
from app.models.documento_emitido import DocumentoEmitido
from app.models.documento_config import DocumentoConfig
from app.models.documento_sequencia import DocumentoSequencia
from app.models.cras_encaminhamento import CrasEncaminhamento
# Intermunicipal (opcional): permite usar o mesmo endpoint de cobrança na Gestão
try:
    from app.models.encaminhamentos import EncaminhamentoIntermunicipal  # type: ignore
except Exception:  # pragma: no cover
    EncaminhamentoIntermunicipal = None  # type: ignore

from app.services.documentos_modelos import get_modelo, listar_modelos

# IA (opcional)
try:
    from app.services.ai_service import generate_text  # type: ignore
except Exception:  # pragma: no cover
    generate_text = None  # type: ignore


router = APIRouter(prefix="/documentos", tags=["documentos"])


# =========================================================
# Helpers
# =========================================================

MESES_PT = [
    "janeiro",
    "fevereiro",
    "março",
    "abril",
    "maio",
    "junho",
    "julho",
    "agosto",
    "setembro",
    "outubro",
    "novembro",
    "dezembro",
]


# Assinatura padrão (pode ser sobrescrita em ctx/campos)
DEFAULT_ASSINANTE_CARGO_SMAS = os.getenv("POPRUA_ASSINANTE_CARGO_SMAS") or "Secretário Municipal de Assistência Social"
DEFAULT_ASSINANTE_NOME_SMAS = (os.getenv("POPRUA_ASSINANTE_NOME_SMAS") or "").strip()
DEFAULT_ASSINANTE_ORGAO_SMAS = (os.getenv("POPRUA_ASSINANTE_ORGAO_SMAS") or "").strip()


def _is_blank_or_placeholder(v: Any) -> bool:
    """True quando vazio ou placeholder típico de IA (ex.: <NOME>, <CARGO>)."""
    try:
        s = ("" if v is None else str(v)).strip()
    except Exception:
        return True
    if not s:
        return True
    if s.startswith("<") and s.endswith(">"):
        return True
    low = s.lower()
    if low in {
        "<nome>",
        "<cargo>",
        "nome do(a) assinante",
        "cargo do(a) assinante",
        "nome do(a) responsável",
        "nome do(a) responsavel",
        "cargo",
    }:
        return True
    return False




def _now_utc_naive() -> datetime:
    """Horário local (timezone configurável) como datetime naive.

    Motivo: documentos e numeração devem seguir o horário local da prefeitura (ex.: America/Sao_Paulo).
    Mantemos datetime naive para compatibilidade com o schema existente.
    """
    tz_name = os.getenv("POPRUA_TZ", "America/Sao_Paulo")
    try:
        return datetime.now(ZoneInfo(tz_name)).replace(tzinfo=None)
    except Exception:
        # fallback: horário local do SO
        return datetime.now().replace(tzinfo=None)

def _backend_dir() -> str:
    # routers -> app -> backend
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def _storage_dir() -> str:
    return os.getenv("POPRUA_STORAGE_DIR", os.path.join(_backend_dir(), "storage"))


def _idempotency_dir() -> str:
    return os.path.join(_storage_dir(), "idempotency")


def _idem_path(key: str) -> str:
    h = hashlib.sha256(key.encode("utf-8")).hexdigest()
    return os.path.join(_idempotency_dir(), h[:2], f"{h}.json")


def _idem_load(key: str) -> Optional[Dict[str, Any]]:
    try:
        path = _idem_path(key)
        if not os.path.exists(path):
            return None
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else None
    except Exception:
        return None


def _idem_save(key: str, data: Dict[str, Any]) -> None:
    try:
        path = _idem_path(key)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        payload = dict(data or {})
        payload.setdefault("ts", datetime.now(timezone.utc).isoformat())
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False)
    except Exception:
        # idempotência nunca pode quebrar a geração
        pass


def _to_abspath(path: str) -> str:
    if os.path.isabs(path):
        return path
    return os.path.join(_backend_dir(), path)


def _to_relpath(abs_path: str) -> str:
    try:
        return os.path.relpath(abs_path, _backend_dir())
    except Exception:
        return abs_path



def _verif_secret() -> bytes:
    # IMPORTANTE: em produção, defina POPRUA_DOC_VERIF_SECRET (não mudar depois).
    return (os.getenv("POPRUA_DOC_VERIF_SECRET") or "dev-secret").encode("utf-8")


def _verif_base_url() -> str:
    # Ex.: https://poprua.prefeitura.sp.gov.br (sem barra no final)
    return (os.getenv("POPRUA_DOC_VERIF_BASE_URL") or "").rstrip("/")



def _branding_public_base_url(municipio_id: int) -> str:
    """URL pública oficial configurada por município (branding).

    - Lido de: storage/branding/<municipio_id>/public_base_url.txt
    - Retorna sem barra no final
    - Não depende de restart do servidor (é lido sob demanda)
    """
    try:
        base_dir = _storage_dir()
        abs_path = os.path.join(base_dir, "branding", str(municipio_id), "public_base_url.txt")
        if os.path.exists(abs_path):
            with open(abs_path, "r", encoding="utf-8") as f:
                u = (f.read() or "").strip()
            return u.rstrip("/") if u else ""
    except Exception:
        pass
    return ""


def _calc_verif_code(doc: DocumentoEmitido) -> str:
    """Gera um código curto de verificação (determinístico) sem alterar o schema do banco."""
    if not getattr(doc, "id", None):
        return ""
    msg = f"{doc.id}|{doc.municipio_id}|{doc.tipo}|{doc.ano}|{doc.numero_seq}|{doc.numero}".encode("utf-8")
    digest = hmac.new(_verif_secret(), msg, hashlib.sha256).hexdigest().upper()
    return digest[:12]


def _build_verif_url(doc_id: int, code: str) -> str:
    path = f"/documentos/{doc_id}/verificar?c={code}"
    base = _verif_base_url()
    return f"{base}{path}" if base else path


def _sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _data_extenso(dt: datetime) -> str:
    return f"{dt.day} de {MESES_PT[dt.month - 1]} de {dt.year}"


def _resolver_municipio(usuario: Usuario, municipio_id: Optional[int]) -> int:
    if pode_acesso_global(usuario):
        if municipio_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="municipio_id é obrigatório para este usuário (acesso global).",
            )
        return int(municipio_id)
    mid = getattr(usuario, "municipio_id", None)
    if not mid:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuário sem município associado.",
        )
    return int(mid)


def _prefixo_tipo(tipo: str) -> str:
    t = (tipo or "").strip().lower()
    return {
        "oficio": "OF",
        "memorando": "MEM",
        "relatorio": "REL",
        "declaracao": "DEC",
    }.get(t, (t[:3].upper() if t else "DOC"))


DEFAULT_TITULOS_POR_TIPO = {
    "oficio": "OFÍCIO",
    "memorando": "MEMORANDO",
    "relatorio": "RELATÓRIO",
    "declaracao": "DECLARAÇÃO",
}


def _format_numero(
    *,
    estilo: str,
    tipo: str,
    prefixo: str,
    seq: int,
    ano: int,
    digitos: int = 3,
    sigla: Optional[str] = None,
) -> str:
    """Formata o número (parte numérica exibida no PDF).

    - hifen: OF-0001/2025
    - prefeitura: 001/2025 (título já indica o tipo)
    - curto: OF 001/2025
    """
    est = (estilo or "").strip().lower()
    dig = max(2, min(int(digitos or 3), 6))
    sigla = (sigla or "").strip()

    if est in ("prefeitura", "padrao_prefeitura", "n"):
        n = f"{seq:0{dig}d}/{ano}"
        if sigla:
            n = f"{n} - {sigla}"
        return n

    if est in ("curto", "sigla"):
        n = f"{prefixo} {seq:0{dig}d}/{ano}"
        if sigla:
            n = f"{n} - {sigla}"
        return n

    # default: legado
    n = f"{prefixo}-{seq:04d}/{ano}"
    if sigla:
        n = f"{n} - {sigla}"
    return n


def _filename_safe(prefixo: str, seq: int, ano: int, tipo: str) -> str:
    """Nome de arquivo previsível (evita acentos e símbolos)."""
    p = (prefixo or _prefixo_tipo(tipo)).strip().upper() or "DOC"
    return f"{p}-{seq:04d}-{ano}.pdf"


def _get_branding(session: Session, municipio_id: int) -> MunicipioBranding:
    branding = session.exec(
        select(MunicipioBranding).where(MunicipioBranding.municipio_id == municipio_id)
    ).first()
    if branding:
        return branding
    # fallback: branding "padrão"
    return MunicipioBranding(municipio_id=municipio_id)


def _get_municipio(session: Session, municipio_id: int) -> Optional[Municipio]:
    return session.get(Municipio, municipio_id)


# =========================================================
# Config de documentos (numeração/prefixos/siglas)
# =========================================================


def _get_doc_config(session: Session, municipio_id: int) -> DocumentoConfig:
    """Obtém config de documentos do município (cria defaults se não existir)."""
    cfg = session.exec(
        select(DocumentoConfig).where(DocumentoConfig.municipio_id == municipio_id)
    ).first()
    if cfg:
        return cfg

    now = _now_utc_naive()
    siglas_default = json.dumps({"smas": "SMAS", "cras": "CRAS", "creas": "CREAS"}, ensure_ascii=False)
    prefixos_default = json.dumps({"oficio": "OF", "memorando": "MEM", "relatorio": "REL", "declaracao": "DEC"}, ensure_ascii=False)

    cfg = DocumentoConfig(
        municipio_id=municipio_id,
        numero_estilo_default="prefeitura",
        digitos_seq_default=3,
        emissor_padrao="smas",
        sequenciar_por_emissor=True,
        sigla_padrao="SMAS",
        siglas_json=siglas_default,
        prefixos_json=prefixos_default,
        criado_em=now,
        atualizado_em=now,
    )
    session.add(cfg)
    session.commit()
    session.refresh(cfg)
    return cfg


def _cfg_siglas(cfg: DocumentoConfig) -> Dict[str, str]:
    try:
        d = json.loads(cfg.siglas_json) if cfg.siglas_json else {}
        return {str(k).strip().lower(): str(v).strip() for k, v in d.items() if str(k).strip()}
    except Exception:
        return {}


def _cfg_prefixos(cfg: DocumentoConfig) -> Dict[str, str]:
    try:
        d = json.loads(cfg.prefixos_json) if cfg.prefixos_json else {}
        return {str(k).strip().lower(): str(v).strip().upper() for k, v in d.items() if str(k).strip()}
    except Exception:
        return {}


def _resolve_emissor_key(payload_emissor: Optional[str], cfg: DocumentoConfig) -> str:
    k = (payload_emissor or "").strip().lower()
    if not k:
        k = (getattr(cfg, "emissor_padrao", "") or "").strip().lower() or "smas"
    return k


def _resolve_sigla(cfg: DocumentoConfig, emissor_key: str, payload_sigla: Optional[str]) -> Optional[str]:
    if payload_sigla is not None:
        s = (payload_sigla or "").strip()
        return s or None

    siglas = _cfg_siglas(cfg)
    if emissor_key and emissor_key in siglas:
        return siglas[emissor_key]

    s = (getattr(cfg, "sigla_padrao", None) or "").strip()
    if s:
        return s

    # fallback: se quiser diferenciar séries, usa o próprio emissor como sigla
    if emissor_key:
        return emissor_key.upper()
    return None


def _resolve_prefixo(cfg: DocumentoConfig, tipo: str, payload_prefixo: Optional[str]) -> str:
    if payload_prefixo:
        return payload_prefixo.strip().upper()
    pref = _cfg_prefixos(cfg)
    t = (tipo or "").strip().lower()
    if t and t in pref:
        return pref[t]
    return _prefixo_tipo(tipo)


def _find_template_by_title(
    session: Session, municipio_id: int, tipo: str, titulo: str
) -> Optional[DocumentoTemplate]:
    titulo = (titulo or "").strip()
    if not titulo:
        return None

    # 1) municipal
    tpl = session.exec(
        select(DocumentoTemplate)
        .where(
            (DocumentoTemplate.ativo == True)  # noqa: E712
            & (DocumentoTemplate.tipo == tipo)
            & (DocumentoTemplate.titulo == titulo)
            & (DocumentoTemplate.municipio_id == municipio_id)
        )
        .order_by(DocumentoTemplate.id.desc())
    ).first()
    if tpl:
        return tpl

    # 2) global
    tpl = session.exec(
        select(DocumentoTemplate)
        .where(
            (DocumentoTemplate.ativo == True)  # noqa: E712
            & (DocumentoTemplate.tipo == tipo)
            & (DocumentoTemplate.titulo == titulo)
            & (DocumentoTemplate.municipio_id.is_(None))
        )
        .order_by(DocumentoTemplate.id.desc())
    ).first()
    return tpl


def _pick_template(
    session: Session,
    municipio_id: int,
    template_id: Optional[int],
    tipo: str,
    titulo_preferido: Optional[str] = None,
) -> DocumentoTemplate:
    if template_id:
        tpl = session.get(DocumentoTemplate, template_id)
        if not tpl or not tpl.ativo:
            raise HTTPException(status_code=404, detail="Template não encontrado.")
        # segurança: se template é municipal, precisa bater
        if tpl.municipio_id is not None and tpl.municipio_id != municipio_id:
            raise HTTPException(status_code=403, detail="Template não pertence ao município.")
        return tpl

    # Se informaram título preferido (modelo), tenta por título primeiro
    if titulo_preferido:
        tpl = _find_template_by_title(session, municipio_id, tipo, titulo_preferido)
        if tpl:
            return tpl

    # Se houver mais de um template por tipo, tenta o default "OFÍCIO/MEM/REL/DEC"
    titulo_default = DEFAULT_TITULOS_POR_TIPO.get((tipo or "").strip().lower())
    if titulo_default:
        tpl = _find_template_by_title(session, municipio_id, tipo, titulo_default)
        if tpl:
            return tpl

    # 1) template municipal por tipo (mais recente)
    tpl = session.exec(
        select(DocumentoTemplate)
        .where(
            (DocumentoTemplate.ativo == True)  # noqa: E712
            & (DocumentoTemplate.tipo == tipo)
            & (DocumentoTemplate.municipio_id == municipio_id)
        )
        .order_by(DocumentoTemplate.id.desc())
    ).first()
    if tpl:
        return tpl

    # 2) template global por tipo (mais recente)
    tpl = session.exec(
        select(DocumentoTemplate)
        .where(
            (DocumentoTemplate.ativo == True)  # noqa: E712
            & (DocumentoTemplate.tipo == tipo)
            & (DocumentoTemplate.municipio_id.is_(None))
        )
        .order_by(DocumentoTemplate.id.desc())
    ).first()
    if tpl:
        return tpl

    # 3) fallback: template mínimo
    return DocumentoTemplate(
        municipio_id=None,
        tipo=tipo,
        titulo=f"Documento ({tipo})",
        corpo_template="",
        assinatura_template="",
        ativo=True,
    )


def _render_jinja(texto: str, ctx: Dict[str, Any]) -> str:
    if not texto:
        return ""
    try:
        from jinja2 import Template  # type: ignore
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Dependência ausente: instale 'jinja2' (pip install jinja2).",
        )
    return Template(texto).render(**ctx)


def _build_pdf_bytes(
    branding: MunicipioBranding,
    municipio: Optional[Municipio],
    numero: str,
    titulo: str,
    assunto: str,
    corpo: str,
    assinatura: str,
    emitido_em: datetime,
    verificacao_codigo: Optional[str] = None,
    verificacao_url: Optional[str] = None,
) -> bytes:
    try:
        from reportlab.lib.pagesizes import A4  # type: ignore
        from reportlab.lib.units import mm  # type: ignore
        from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_RIGHT  # type: ignore
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle  # type: ignore
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage  # type: ignore
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Dependência ausente: instale 'reportlab' (pip install reportlab).",
        )

    buf = BytesIO()

    # layout
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=float(branding.margin_left_mm) * mm,
        rightMargin=float(branding.margin_right_mm) * mm,
        topMargin=float(branding.margin_top_mm) * mm,
        bottomMargin=float(branding.margin_bottom_mm) * mm,
        title=titulo,
    )

    styles = getSampleStyleSheet()

    base = ParagraphStyle(
        "base",
        parent=styles["Normal"],
        fontName=getattr(branding, "font_name", "Helvetica") or "Helvetica",
        fontSize=int(getattr(branding, "font_size", 11) or 11),
        leading=int((getattr(branding, "font_size", 11) or 11) * 1.35),
        alignment=TA_JUSTIFY,
    )

    header_style = ParagraphStyle(
        "header",
        parent=base,
        alignment=TA_CENTER,
        fontSize=max(9, base.fontSize - 2),
        leading=max(11, base.leading - 2),
    )

    title_style = ParagraphStyle(
        "title",
        parent=base,
        alignment=TA_CENTER,
        fontSize=14,
        leading=18,
    )

    right_style = ParagraphStyle(
        "right",
        parent=base,
        alignment=TA_RIGHT,
    )

    story: List[Any] = []

    # Logo + cabeçalho
    if branding.logo_path:
        abs_logo = _to_abspath(branding.logo_path)
        if os.path.exists(abs_logo):
            w = float(getattr(branding, "logo_width_mm", 28.0) or 28.0) * mm
            h_cfg = getattr(branding, "logo_height_mm", None)
            if h_cfg:
                h = float(h_cfg) * mm
            else:
                # mantém proporção automaticamente pelo tamanho do arquivo (px)
                h = w
                try:
                    from PIL import Image as PILImage  # type: ignore

                    im = PILImage.open(abs_logo)
                    iw, ih = im.size
                    if iw and ih:
                        h = w * (float(ih) / float(iw))
                except Exception:
                    pass
            story.append(RLImage(abs_logo, width=w, height=h))
            story.append(Spacer(1, 6))

    if branding.header_text:
        for line in (branding.header_text or "").splitlines():
            if line.strip():
                story.append(Paragraph(line.strip(), header_style))
        story.append(Spacer(1, 10))

    # Título
    story.append(Paragraph(f"<b>{titulo}</b>", title_style))
    story.append(Spacer(1, 12))

    # Número + Data
    cidade = ""
    if municipio:
        cidade = f"{municipio.nome}/{municipio.uf}"
    data_ext = _data_extenso(emitido_em)
    if cidade:
        story.append(Paragraph(f"{cidade}, {data_ext}", right_style))
        story.append(Spacer(1, 6))

    story.append(Paragraph(f"<b>Nº:</b> {numero}", base))
    if assunto:
        story.append(Spacer(1, 6))
        story.append(Paragraph(f"<b>Assunto:</b> {assunto}", base))
    story.append(Spacer(1, 12))

    # Corpo (quebras de parágrafo por linha em branco)
    corpo = (corpo or "").strip()
    if corpo:
        partes = [p.strip() for p in corpo.split("\n\n") if p.strip()]
        for p in partes:
            p = p.replace("\n", "<br/>")
            story.append(Paragraph(p, base))
            story.append(Spacer(1, 10))

    # Assinatura
    assinatura = (assinatura or "").strip()
    if assinatura:
        story.append(Spacer(1, 18))
        for line in assinatura.splitlines():
            if line.strip():
                story.append(Paragraph(line.strip(), base))

    # Rodapé (apenas como callback simples)
    footer_lines = [ln.strip() for ln in (branding.footer_text or "").splitlines() if ln.strip()]

    def _on_page(canvas, doc_):
        canvas.saveState()

        # Rodapé textual (centralizado)
        if footer_lines:
            canvas.setFont(base.fontName, 9)
            y = 12 * mm
            for ln in reversed(footer_lines):
                canvas.drawCentredString(A4[0] / 2.0, y, ln)
                y += 10

        # Verificação (QR + código)
        if verificacao_codigo:
            try:
                canvas.setFont(base.fontName, 7)
                left_x = getattr(doc_, "leftMargin", 20 * mm)
                canvas.drawString(left_x, 8 * mm, f"Verificação: {verificacao_codigo}")
                if verificacao_url:
                    canvas.drawString(left_x, 4.5 * mm, verificacao_url)

                if verificacao_url:
                    from reportlab.graphics.barcode.qr import QrCodeWidget  # type: ignore
                    from reportlab.graphics.shapes import Drawing  # type: ignore
                    from reportlab.graphics import renderPDF  # type: ignore

                    size = 18 * mm
                    qr = QrCodeWidget(verificacao_url)
                    bounds = qr.getBounds()
                    w = bounds[2] - bounds[0]
                    h = bounds[3] - bounds[1]
                    if w <= 0 or h <= 0:
                        raise ValueError("QR bounds inválidos")
                    d = Drawing(size, size, transform=[size / w, 0, 0, size / h, 0, 0])
                    d.add(qr)
                    right_margin = getattr(doc_, "rightMargin", 20 * mm)
                    x = A4[0] - right_margin - size
                    y = 4 * mm
                    renderPDF.draw(d, canvas, x, y)
            except Exception:
                # Não falha a geração do PDF por conta do QR
                pass

        canvas.restoreState()

    doc.build(story, onFirstPage=_on_page, onLaterPages=_on_page)
    return buf.getvalue()


# =========================================================
# Schemas
# =========================================================

class TemplateCreate(BaseModel):
    municipio_id: Optional[int] = None
    tipo: str = PField(..., min_length=1)
    titulo: str = PField(..., min_length=1)
    assunto_padrao: Optional[str] = None
    corpo_template: str = PField(..., min_length=0)
    assinatura_template: Optional[str] = None
    ativo: bool = True


class TemplateUpdate(BaseModel):
    tipo: Optional[str] = None
    titulo: Optional[str] = None
    assunto_padrao: Optional[str] = None
    corpo_template: Optional[str] = None
    assinatura_template: Optional[str] = None
    ativo: Optional[bool] = None


class DocumentoGerar(BaseModel):
    municipio_id: Optional[int] = None

    tipo: str = PField(..., min_length=1)
    template_id: Optional[int] = None

    # Biblioteca guiada (opcional): usa um "modelo" conhecido (sem exigir template_id)
    modelo: Optional[str] = None

    assunto: Optional[str] = None

    destinatario_nome: Optional[str] = None
    destinatario_cargo: Optional[str] = None
    destinatario_orgao: Optional[str] = None

    dados: Dict[str, Any] = PField(default_factory=dict)
    # Campos guiados (biblioteca): merge em ctx (mais explícito para usuários)
    campos: Dict[str, Any] = PField(default_factory=dict)

    salvar: bool = True
    prefixo_numero: Optional[str] = None  # override

    # numeração (configurável por município)
    numero_estilo: Optional[str] = None  # hifen|prefeitura|curto
    digitos_seq: Optional[int] = None

    # emissor (para séries distintas por secretaria/setor)
    emissor: Optional[str] = None  # ex.: smas|cras|creas
    sigla_orgao: Optional[str] = None

    # Preview: quando salvar=false, pode retornar PDF direto (download)
    retornar_pdf: bool = False
    arquivo_nome: Optional[str] = None


# =========================================================
# Templates
# =========================================================


@router.get("/modelos", dependencies=[Depends(exigir_minimo_perfil("operador"))])
def listar_modelos_documentos():
    """Biblioteca de modelos prontos (campos guiados)."""
    out = []
    for m in listar_modelos():
        out.append(
            {
                "key": m.key,
                "tipo": m.tipo,
                "titulo": m.titulo,
                "descricao": m.descricao,
                "campos_obrigatorios": m.campos_obrigatorios,
                "campos_opcionais": m.campos_opcionais,
                "exemplo": m.exemplo_payload(),
            }
        )
    return out


class ModelosAplicar(BaseModel):
    municipio_id: Optional[int] = None
    chaves: Optional[List[str]] = None  # se None, aplica tudo
    overwrite: bool = False


@router.post("/modelos/aplicar", dependencies=[Depends(exigir_minimo_perfil("coord_municipal"))])
def aplicar_modelos_no_municipio(
    payload: ModelosAplicar,
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    """Instala a biblioteca como templates do município (para customizar por prefeitura)."""
    mid = _resolver_municipio(usuario, payload.municipio_id)
    wanted = set([(w or "").strip().lower() for w in (payload.chaves or []) if (w or "").strip()])

    insert = update = skip = 0
    now = _now_utc_naive()
    for m in listar_modelos():
        if wanted and (m.key.lower() not in wanted) and (m.titulo.lower() not in wanted):
            continue

        existing = session.exec(
            select(DocumentoTemplate).where(
                (DocumentoTemplate.municipio_id == mid)
                & (DocumentoTemplate.tipo == m.tipo)
                & (DocumentoTemplate.titulo == m.titulo)
            )
        ).first()

        if existing:
            if payload.overwrite:
                existing.assunto_padrao = m.assunto_padrao
                existing.corpo_template = m.corpo_template
                existing.assinatura_template = m.assinatura_template
                existing.ativo = True
                existing.atualizado_em = now
                session.add(existing)
                update += 1
            else:
                skip += 1
            continue

        tpl = DocumentoTemplate(
            municipio_id=mid,
            tipo=m.tipo,
            titulo=m.titulo,
            assunto_padrao=m.assunto_padrao,
            corpo_template=m.corpo_template,
            assinatura_template=m.assinatura_template,
            ativo=True,
            criado_em=now,
            atualizado_em=now,
        )
        session.add(tpl)
        insert += 1

    session.commit()
    return {"municipio_id": mid, "insert": insert, "update": update, "skip": skip}

@router.get("/templates", dependencies=[Depends(exigir_minimo_perfil("operador"))])
def listar_templates(
    municipio_id: Optional[int] = Query(default=None),
    tipo: Optional[str] = Query(default=None),
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    mid = _resolver_municipio(usuario, municipio_id) if (municipio_id is not None or not pode_acesso_global(usuario)) else None

    q = select(DocumentoTemplate).where(DocumentoTemplate.ativo == True)  # noqa: E712
    if tipo:
        q = q.where(DocumentoTemplate.tipo == tipo)
    if mid is not None:
        # municipal: mostra templates globais + do município
        q = q.where((DocumentoTemplate.municipio_id.is_(None)) | (DocumentoTemplate.municipio_id == mid))
    return session.exec(q.order_by(DocumentoTemplate.municipio_id.desc(), DocumentoTemplate.id.desc())).all()


@router.post("/templates", dependencies=[Depends(exigir_minimo_perfil("coord_municipal"))])
def criar_template(
    payload: TemplateCreate,
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    mid = None
    if payload.municipio_id is not None or not pode_acesso_global(usuario):
        mid = _resolver_municipio(usuario, payload.municipio_id)

    tpl = DocumentoTemplate(
        municipio_id=mid,
        tipo=payload.tipo.strip().lower(),
        titulo=payload.titulo.strip(),
        assunto_padrao=payload.assunto_padrao,
        corpo_template=payload.corpo_template or "",
        assinatura_template=payload.assinatura_template,
        ativo=bool(payload.ativo),
        criado_em=_now_utc_naive(),
        atualizado_em=_now_utc_naive(),
    )
    session.add(tpl)
    session.commit()
    session.refresh(tpl)
    return tpl


@router.put("/templates/{template_id}", dependencies=[Depends(exigir_minimo_perfil("coord_municipal"))])
def atualizar_template(
    template_id: int,
    payload: TemplateUpdate,
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    tpl = session.get(DocumentoTemplate, template_id)
    if not tpl:
        raise HTTPException(status_code=404, detail="Template não encontrado.")

    # segurança: template municipal não pode ser editado por outro município
    if tpl.municipio_id is not None:
        mid = _resolver_municipio(usuario, tpl.municipio_id)
        if mid != tpl.municipio_id:
            raise HTTPException(status_code=403, detail="Sem permissão para este município.")

    for field in ("tipo", "titulo", "assunto_padrao", "corpo_template", "assinatura_template", "ativo"):
        v = getattr(payload, field, None)
        if v is None:
            continue
        if field == "tipo" and isinstance(v, str):
            v = v.strip().lower()
        if field == "titulo" and isinstance(v, str):
            v = v.strip()
        setattr(tpl, field, v)

    tpl.atualizado_em = _now_utc_naive()
    session.add(tpl)
    session.commit()
    session.refresh(tpl)
    return tpl


# =========================================================
# Documentos emitidos
# =========================================================

@router.post("/gerar", dependencies=[Depends(exigir_minimo_perfil("operador"))])
def gerar_documento(
    payload: DocumentoGerar,
    request: Request,
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    mid = _resolver_municipio(usuario, payload.municipio_id)
    tipo = payload.tipo.strip().lower()

    modelo = get_modelo(payload.modelo) if payload.modelo else None
    if payload.modelo and not modelo:
        raise HTTPException(status_code=400, detail=f"Modelo não encontrado: {payload.modelo}")
    if modelo and modelo.tipo != tipo:
        raise HTTPException(
            status_code=400,
            detail=f"Tipo '{tipo}' não corresponde ao modelo '{modelo.key}' ({modelo.tipo}).",
        )

    # Se modelo, tenta template municipal/global com mesmo título; se não existir, usa o próprio modelo.
    tpl = None
    if payload.template_id:
        tpl = _pick_template(session, mid, payload.template_id, tipo)
    elif modelo:
        tpl = _find_template_by_title(session, mid, tipo, modelo.titulo)
        if not tpl:
            tpl = DocumentoTemplate(
                municipio_id=None,
                tipo=tipo,
                titulo=modelo.titulo,
                assunto_padrao=modelo.assunto_padrao,
                corpo_template=modelo.corpo_template,
                assinatura_template=modelo.assinatura_template,
                ativo=True,
            )
    else:
        tpl = _pick_template(session, mid, None, tipo)

    branding = _get_branding(session, mid)
    municipio = _get_municipio(session, mid)

    emitido_em = _now_utc_naive()
    ano = emitido_em.year

    # numeração (config + sequência por emissor)
    cfg = _get_doc_config(session, mid)
    emissor_key = _resolve_emissor_key(payload.emissor, cfg)
    series_key = emissor_key if getattr(cfg, "sequenciar_por_emissor", True) else ""

    estilo = (payload.numero_estilo or getattr(cfg, "numero_estilo_default", None) or "prefeitura").strip().lower()
    digitos = int(payload.digitos_seq or getattr(cfg, "digitos_seq_default", None) or 3)

    sigla = _resolve_sigla(cfg, emissor_key, payload.sigla_orgao)
    prefixo = _resolve_prefixo(cfg, tipo, payload.prefixo_numero)

    # base atual (continuidade)
    last_doc = session.exec(
        select(DocumentoEmitido)
        .where(
            (DocumentoEmitido.municipio_id == mid)
            & (DocumentoEmitido.tipo == tipo)
            & (DocumentoEmitido.ano == ano)
        )
        .order_by(DocumentoEmitido.numero_seq.desc())
    ).first()
    base_doc = int(last_doc.numero_seq) if last_doc else 0

    seq_row = session.exec(
        select(DocumentoSequencia).where(
            (DocumentoSequencia.municipio_id == mid)
            & (DocumentoSequencia.tipo == tipo)
            & (DocumentoSequencia.ano == ano)
            & (DocumentoSequencia.emissor_key == series_key)
        )
    ).first()

    emissor_padrao = (getattr(cfg, "emissor_padrao", "smas") or "smas").strip().lower()

    if seq_row:
        next_seq = int(seq_row.seq_atual) + 1
        if payload.salvar:
            seq_row.seq_atual = next_seq
            seq_row.atualizado_em = emitido_em
            session.add(seq_row)
    else:
        # Se for a série padrão do município, mantém continuidade (base_doc).
        # Se for uma série de outro emissor, inicia em 1 (série própria).
        base = base_doc if (not getattr(cfg, "sequenciar_por_emissor", True) or series_key in ("", emissor_padrao)) else 0
        next_seq = base + 1
        if payload.salvar:
            seq_row = DocumentoSequencia(
                municipio_id=mid,
                tipo=tipo,
                ano=ano,
                emissor_key=series_key,
                seq_atual=next_seq,
                atualizado_em=emitido_em,
            )
            session.add(seq_row)

    numero = _format_numero(
        estilo=estilo,
        tipo=tipo,
        prefixo=prefixo,
        seq=next_seq,
        ano=ano,
        digitos=digitos,
        sigla=sigla,
    )
    numero_codigo = f"{prefixo}-{next_seq:04d}/{ano}"
    # contexto comum
    ctx: Dict[str, Any] = dict(payload.dados or {})
    # campos guiados têm prioridade
    if payload.campos:
        ctx.update(payload.campos)
    ctx.update(
        {
            "numero": numero,
            "numero_codigo": numero_codigo,
            "ano": ano,
            "seq": next_seq,
            "emissor": emissor_key,
            "sigla_orgao": sigla or "",
            "data": emitido_em.strftime("%Y-%m-%d"),
            "data_extenso": _data_extenso(emitido_em),
            "municipio_nome": getattr(municipio, "nome", "") if municipio else "",
            "municipio_uf": getattr(municipio, "uf", "") if municipio else "",
            "destinatario_nome": payload.destinatario_nome or "",
            "destinatario_cargo": payload.destinatario_cargo or "",
            "destinatario_orgao": payload.destinatario_orgao or "",
        }
    )

    # assunto também disponível no template
    assunto = payload.assunto or getattr(tpl, "assunto_padrao", None) or (modelo.assunto_padrao if modelo else "") or ""
    ctx["assunto"] = assunto


    # Defaults de assinatura (evita <NOME>/<CARGO> vindos de IA e padroniza o Secretário)
    if _is_blank_or_placeholder(ctx.get("assinante_nome")):
        nome_padrao = ""
        if emissor_key in ("smas", "gestao") and DEFAULT_ASSINANTE_NOME_SMAS:
            nome_padrao = DEFAULT_ASSINANTE_NOME_SMAS
        else:
            nome_padrao = (getattr(usuario, "nome", "") or "").strip()
        if nome_padrao:
            ctx["assinante_nome"] = nome_padrao

    if _is_blank_or_placeholder(ctx.get("assinante_cargo")):
        if emissor_key in ("smas", "gestao"):
            ctx["assinante_cargo"] = DEFAULT_ASSINANTE_CARGO_SMAS

    if _is_blank_or_placeholder(ctx.get("assinante_orgao")):
        if emissor_key in ("smas", "gestao") and DEFAULT_ASSINANTE_ORGAO_SMAS:
            ctx["assinante_orgao"] = DEFAULT_ASSINANTE_ORGAO_SMAS
    # validação de campos obrigatórios do modelo
    if modelo and modelo.campos_obrigatorios:
        faltando = [k for k in modelo.campos_obrigatorios if not (ctx.get(k) or "").__str__().strip()]
        if faltando:
            raise HTTPException(
                status_code=422,
                detail={
                    "erro": "Campos obrigatórios ausentes para o modelo",
                    "modelo": modelo.key,
                    "faltando": faltando,
                },
            )

    corpo = _render_jinja(tpl.corpo_template or "", ctx)
    assinatura = _render_jinja(tpl.assinatura_template or "", ctx)
    titulo_doc = tpl.titulo or f"Documento ({tipo})"

    if payload.salvar:
        base_dir = _storage_dir()
        folder_key = (series_key or "geral") if getattr(cfg, "sequenciar_por_emissor", True) else "geral"
        abs_dir = os.path.join(base_dir, "documentos", str(mid), str(ano), tipo, folder_key)
        os.makedirs(abs_dir, exist_ok=True)
        filename = _filename_safe(prefixo=prefixo, seq=next_seq, ano=ano, tipo=tipo)
        abs_path = os.path.join(abs_dir, filename)
        rel_path = _to_relpath(abs_path)

        # cria o registro antes do PDF (precisa do ID para QR/código de verificação)
        doc = DocumentoEmitido(
            municipio_id=mid,
            tipo=tipo,
            ano=ano,
            numero_seq=next_seq,
            numero=numero,
            template_id=tpl.id if tpl and tpl.id else None,
            assunto=assunto,
            destinatario_nome=payload.destinatario_nome,
            destinatario_cargo=payload.destinatario_cargo,
            destinatario_orgao=payload.destinatario_orgao,
            corpo_renderizado=corpo,
            arquivo_path=rel_path,
            criado_por_user_id=getattr(usuario, "id", None),
            criado_em=emitido_em,
        )
        session.add(doc)
        session.flush()

        codigo = _calc_verif_code(doc)
        path_ver = f"/documentos/{int(doc.id)}/verificar?c={codigo}" if (doc.id and codigo) else ""
        base_ver = _branding_public_base_url(mid) or _verif_base_url() or str(request.base_url).rstrip("/")
        url = f"{base_ver}{path_ver}" if (base_ver and path_ver) else path_ver
        pdf_bytes = _build_pdf_bytes(
            branding=branding,
            municipio=municipio,
            numero=numero,
            titulo=titulo_doc,
            assunto=assunto,
            corpo=corpo,
            assinatura=assinatura,
            emitido_em=emitido_em,
            verificacao_codigo=codigo or None,
            verificacao_url=url or None,
        )

        with open(abs_path, "wb") as f:
            f.write(pdf_bytes)

        session.commit()
        session.refresh(doc)
        return {
            "id": doc.id,
            "numero": doc.numero,
            "tipo": doc.tipo,
            "download": f"/documentos/{doc.id}/download",
            "verificacao": {"codigo": codigo, "url": url, "path": path_ver},
        }

    # sem salvar: gera PDF sem QR/verificação
    pdf_bytes = _build_pdf_bytes(
        branding=branding,
        municipio=municipio,
        numero=numero,
        titulo=titulo_doc,
        assunto=assunto,
        corpo=corpo,
        assinatura=assinatura,
        emitido_em=emitido_em,
        verificacao_codigo=None,
        verificacao_url=None,
    )

# preview (sem salvar)
    if payload.retornar_pdf:
        filename = (payload.arquivo_nome or "").strip() or _filename_safe(
            prefixo=prefixo, seq=next_seq, ano=ano, tipo=tipo
        )
        headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
        return StreamingResponse(BytesIO(pdf_bytes), media_type="application/pdf", headers=headers)

    return {
        "id": None,
        "numero": numero,
        "tipo": tipo,
        "pdf_base64": base64.b64encode(pdf_bytes).decode("ascii"),
    }


@router.get("/{documento_id}", dependencies=[Depends(exigir_minimo_perfil("operador"))])
def get_documento(
    documento_id: int,
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    doc = session.get(DocumentoEmitido, documento_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Documento não encontrado.")

    # segurança municipal
    if not pode_acesso_global(usuario):
        mid = getattr(usuario, "municipio_id", None)
        if mid and doc.municipio_id != int(mid):
            raise HTTPException(status_code=403, detail="Sem permissão para este município.")

    return doc


@router.get("/{documento_id}/download", dependencies=[Depends(exigir_minimo_perfil("operador"))])
def download_documento(
    documento_id: int,
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    doc = session.get(DocumentoEmitido, documento_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Documento não encontrado.")

    if not pode_acesso_global(usuario):
        mid = getattr(usuario, "municipio_id", None)
        if mid and doc.municipio_id != int(mid):
            raise HTTPException(status_code=403, detail="Sem permissão para este município.")

    abs_path = _to_abspath(doc.arquivo_path)
    if not os.path.exists(abs_path):
        raise HTTPException(status_code=404, detail="Arquivo não encontrado no storage.")

    filename = os.path.basename(abs_path)
    return FileResponse(
        abs_path,
        media_type="application/pdf",
        filename=filename,
    )

@router.get("/{documento_id}/verificar")
def verificar_documento(
    documento_id: int,
    request: Request,
    c: str = Query(..., min_length=6, max_length=128),
    format: Optional[str] = Query(
        None,
        description="Formato de retorno: json|html. Se omitido, escolhe HTML quando o navegador pedir (Accept: text/html).",
    ),
    session: Session = Depends(get_session),
):
    """Verificação pública de documento (QR/código).

    - NÃO exige token.
    - Retorna apenas metadados mínimos (não expõe destinatário/corpo).
    - Se o código estiver incorreto, não revela dados do documento.
    - Para QR em celular: retorna HTML automaticamente (Accept: text/html).
    """

    def want_html() -> bool:
        if format:
            f = (format or "").strip().lower()
            if f == "html":
                return True
            if f == "json":
                return False
        accept = (request.headers.get("accept") or "").lower()
        return "text/html" in accept

    def page_html(*, valido: bool, payload: Optional[Dict[str, Any]] = None) -> HTMLResponse:
        ok = bool(valido)
        title = "Verificação de documento"
        badge = "✅ Documento válido" if ok else "❌ Documento inválido"
        subtitle = (
            "Este portal confirma a autenticidade do documento emitido pelo sistema."
            if ok
            else "O código informado não corresponde ao documento."
        )

        # Links úteis
        code = (c or "").strip()
        base = _verif_base_url() or str(request.base_url).rstrip("/")
        ver_path = f"/documentos/{int(documento_id)}/verificar?c={code}"
        ver_json = f"{base}{ver_path}" if base else ver_path
        ver_json = f"{ver_json}&format=json" if "?" in ver_json else f"{ver_json}?format=json"

        download_path = f"/documentos/{int(documento_id)}/download"
        download_url = f"{base}{download_path}" if base else download_path

        # Campos visíveis (sem conteúdo sensível)
        rows = ""
        if payload:
            def _row(k: str, v: Any) -> str:
                return f"<tr><th>{html_lib.escape(str(k))}</th><td>{html_lib.escape(str(v))}</td></tr>"

            rows_list = [
                _row("Número", payload.get("numero")),
                _row("Tipo", payload.get("tipo_label") or payload.get("tipo")),
                _row("Emissor", payload.get("emissor_label") or payload.get("emissor") or "-"),
                _row("Município", payload.get("municipio_label") or payload.get("municipio_id")),
                _row("Ano", payload.get("ano")),
                _row("Emitido em", payload.get("criado_em_fmt") or payload.get("criado_em")),
                _row("Arquivo existe", "Sim" if payload.get("arquivo_existe") else "Não"),
                _row("SHA-256", payload.get("arquivo_sha256") or "-"),
                _row("Tamanho (bytes)", payload.get("tamanho_bytes") or "-"),
            ]
            rows = "\n".join(rows_list)

        html = f"""<!doctype html>
<html lang="pt-br">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width,initial-scale=1"/>
  <title>{title}</title>
  <style>
    body{{margin:0;background:#0b1220;color:#e5e7eb;font-family:system-ui,-apple-system,Segoe UI,Roboto,Arial;}}
    .wrap{{max-width:920px;margin:0 auto;padding:24px;}}
    .card{{background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.12);border-radius:14px;padding:18px;}}
    .badge{{display:inline-block;padding:8px 12px;border-radius:999px;font-weight:800;}}
    .ok{{background:rgba(34,197,94,.18);border:1px solid rgba(34,197,94,.35);}}
    .bad{{background:rgba(239,68,68,.16);border:1px solid rgba(239,68,68,.35);}}
    h1{{margin:10px 0 6px;font-size:20px;}}
    p{{margin:6px 0 0;color:rgba(229,231,235,.8)}}
    table{{width:100%;border-collapse:collapse;margin-top:14px;}}
    th,td{{padding:10px 8px;border-top:1px solid rgba(255,255,255,.10);font-size:14px;text-align:left;vertical-align:top;}}
    th{{width:220px;color:rgba(229,231,235,.85);font-weight:700;}}
    a{{color:#93c5fd;text-decoration:none}}
    a:hover{{text-decoration:underline}}
    .actions{{display:flex;gap:10px;flex-wrap:wrap;margin-top:14px}}
    .btn{{display:inline-block;padding:10px 12px;border-radius:10px;border:1px solid rgba(255,255,255,.15);background:rgba(255,255,255,.06)}}
    .small{{font-size:12px;color:rgba(229,231,235,.7);margin-top:10px;line-height:1.35}}
    code{{background:rgba(255,255,255,.06);padding:2px 6px;border-radius:6px}}
  </style>
</head>
<body>
  <div class="wrap">
    <div class="card">
      <div class="badge {'ok' if ok else 'bad'}">{badge}</div>
      <h1>{title}</h1>
      <p>{subtitle}</p>

      {'<table>'+rows+'</table>' if rows else ''}

      <div class="actions">
        <a class="btn" href="{html_lib.escape(ver_json)}">Ver JSON</a>
        <a class="btn" href="{html_lib.escape(download_url)}">Baixar PDF (requer login)</a>
      </div>

      <div class="small">
        Código consultado: <code>{html_lib.escape(code)}</code><br/>
        Observação: esta página não exibe o conteúdo do documento, apenas metadados mínimos para verificação.
      </div>
    </div>
  </div>
</body>
</html>
"""
        return HTMLResponse(content=html, status_code=200)

    doc = session.get(DocumentoEmitido, documento_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Documento não encontrado.")

    expected = _calc_verif_code(doc)
    provided = (c or "").strip()
    valido = bool(expected) and hmac.compare_digest(expected.lower(), provided.lower())

    if not valido:
        if want_html():
            return page_html(valido=False)
        return {"id": documento_id, "valido": False}

    abs_path = _to_abspath(doc.arquivo_path)
    existe = bool(abs_path) and os.path.exists(abs_path)

    sha256 = None
    tamanho = None
    if existe:
        try:
            tamanho = os.path.getsize(abs_path)
            sha256 = _sha256_file(abs_path)
        except Exception:
            sha256 = None

    emissor = None
    try:
        # storage/documentos/<mid>/<ano>/<tipo>/<emissor>/...
        parts = (doc.arquivo_path or "").split("/")
        if len(parts) >= 6 and parts[0] == "storage" and parts[1] == "documentos":
            emissor = parts[5]  # 0 storage,1 documentos,2 mid,3 ano,4 tipo,5 emissor
    except Exception:
        emissor = None

    mun = _get_municipio(session, int(doc.municipio_id)) if getattr(doc, "municipio_id", None) else None
    municipio_label = f"{mun.nome}/{mun.uf}" if mun else (str(doc.municipio_id) if doc.municipio_id is not None else "-")
    tipo_label = DEFAULT_TITULOS_POR_TIPO.get((doc.tipo or "").strip().lower(), doc.tipo)
    emissor_label = (emissor or "").upper() if emissor else None
    criado_em_fmt = None
    try:
        if isinstance(doc.criado_em, datetime):
            criado_em_fmt = doc.criado_em.strftime("%d/%m/%Y %H:%M:%S")
        else:
            criado_em_fmt = str(doc.criado_em)
    except Exception:
        criado_em_fmt = None

    payload = {
        "id": doc.id,
        "valido": True,
        "tipo": doc.tipo,
        "numero": doc.numero,
        "ano": doc.ano,
        "municipio_id": doc.municipio_id,
        "emissor": emissor,
        "emissor_label": emissor_label,
        "tipo_label": tipo_label,
        "municipio_label": municipio_label,
        "criado_em_fmt": criado_em_fmt,
        "criado_em": doc.criado_em,
        "arquivo_existe": existe,
        "arquivo_sha256": sha256,
        "tamanho_bytes": tamanho,
    }

    if want_html():
        return page_html(valido=True, payload=payload)

    return payload



# ============================================================
# Biblioteca de templates por município (clonar / listar)
# ============================================================

class TemplateClonarPayload(BaseModel):
    municipio_destino_id: Optional[int] = PField(
        default=None,
        description="Município destino. None = clona para global (somente admin).",
    )
    novo_titulo: Optional[str] = PField(default=None, description="Opcional: novo título para o template clonado.")
    overwrite: bool = PField(default=False, description="Se true, atualiza template existente (mesma chave lógica) em vez de criar novo.")
    ativar: bool = PField(default=True, description="Se true, garante ativo=true no destino.")


@router.get("/templates/biblioteca", dependencies=[Depends(exigir_minimo_perfil("operador"))])
def templates_biblioteca(
    municipio_id: Optional[int] = Query(None),
    tipo: Optional[str] = Query(None, description="Filtro opcional por tipo (oficio/memorando/relatorio/declaracao)."),
    ativo: Optional[bool] = Query(None, description="Filtro opcional por ativo."),
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    """Lista templates globais e do município (biblioteca)."""
    mid = _resolver_municipio(usuario, municipio_id)

    q_global = select(DocumentoTemplate).where(DocumentoTemplate.municipio_id == None)  # noqa: E711
    q_muni = select(DocumentoTemplate).where(DocumentoTemplate.municipio_id == mid)

    if tipo:
        t = tipo.strip().lower()
        q_global = q_global.where(DocumentoTemplate.tipo == t)
        q_muni = q_muni.where(DocumentoTemplate.tipo == t)
    if ativo is not None:
        q_global = q_global.where(DocumentoTemplate.ativo == ativo)
        q_muni = q_muni.where(DocumentoTemplate.ativo == ativo)

    global_items = session.exec(q_global.order_by(DocumentoTemplate.tipo, DocumentoTemplate.titulo, DocumentoTemplate.id)).all()
    muni_items = session.exec(q_muni.order_by(DocumentoTemplate.tipo, DocumentoTemplate.titulo, DocumentoTemplate.id)).all()

    return {
        "municipio_id": mid,
        "total_global": len(global_items),
        "total_municipal": len(muni_items),
        "global": global_items,
        "municipal": muni_items,
    }


@router.post("/templates/{template_id}/clonar", dependencies=[Depends(exigir_minimo_perfil("coord_municipal"))])
def clonar_template(
    template_id: int,
    payload: TemplateClonarPayload,
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    """Clona um template (global ou de outro município) para um município destino.

    - Se municipio_destino_id for None: cria/atualiza template GLOBAL (somente admin).
    - Se overwrite=true: faz upsert por (municipio_id, tipo, titulo).
    """
    tpl = session.get(DocumentoTemplate, template_id)
    if not tpl:
        raise HTTPException(status_code=404, detail="Template não encontrado")

    dest_mid = payload.municipio_destino_id
    if dest_mid is not None:
        dest_mid = _resolver_municipio(usuario, dest_mid)
    else:
        # clonar para global: somente admin
        if getattr(usuario, "perfil", "") not in ("admin", "gestor_consorcio"):
            raise HTTPException(status_code=403, detail="Somente admin pode clonar template para global (municipio_id=null).")

    novo_titulo = (payload.novo_titulo or getattr(tpl, "titulo", "")).strip() or getattr(tpl, "titulo", "")
    tipo = (getattr(tpl, "tipo", "") or "").strip().lower()

    # procura existente no destino (upsert)
    existing = None
    if payload.overwrite:
        q = (
            select(DocumentoTemplate)
            .where(DocumentoTemplate.municipio_id == dest_mid)
            .where(DocumentoTemplate.tipo == tipo)
            .where(DocumentoTemplate.titulo == novo_titulo)
        )
        existing = session.exec(q).first()

    if existing:
        existing.assunto_padrao = getattr(tpl, "assunto_padrao", None)
        existing.corpo_template = getattr(tpl, "corpo_template", "")
        existing.assinatura_template = getattr(tpl, "assinatura_template", None)
        if payload.ativar:
            existing.ativo = True
        existing.atualizado_em = _now_utc_naive()
        session.add(existing)
        session.commit()
        session.refresh(existing)
        return {"modo": "update", "template": existing}

    cloned = DocumentoTemplate(
        municipio_id=dest_mid,
        tipo=tipo,
        titulo=novo_titulo,
        assunto_padrao=getattr(tpl, "assunto_padrao", None),
        corpo_template=getattr(tpl, "corpo_template", ""),
        assinatura_template=getattr(tpl, "assinatura_template", None),
        ativo=True if payload.ativar else getattr(tpl, "ativo", True),
        criado_em=_now_utc_naive(),
        atualizado_em=_now_utc_naive(),
    )
    session.add(cloned)
    session.commit()
    session.refresh(cloned)
    return {"modo": "insert", "template": cloned}


# ============================================================
# Integração: gerar cobrança de devolutiva a partir da Rede (encaminhamento CRAS)
# ============================================================

class CobrancaDevolutivaAuto(BaseModel):
    encaminhamento_id: int = PField(..., description="ID do encaminhamento CRAS (cras_encaminhamento.id).")
    municipio_id: Optional[int] = PField(default=None, description="Opcional (admin): força município.")
    emissor: str = PField(default="cras", description="Emissor/serie (cras|smas|creas...).")
    prazo: Optional[str] = PField(default=None, description="Override do prazo (ex.: 48h). Se omitido, usa prazo_devolutiva_dias do encaminhamento.")
    contato_retorno: Optional[str] = PField(default=None, description="Contato para retorno (telefone/e-mail).")
    destinatario_nome: Optional[str] = None
    destinatario_cargo: Optional[str] = None
    destinatario_orgao: Optional[str] = None
    salvar: bool = True
    retornar_pdf: bool = False
    arquivo_nome: Optional[str] = None

    idempotency_key: Optional[str] = PField(default=None, description="Chave de idempotência (evita duplicar numeração em reenvios).")
    forcar_novo: bool = PField(default=False, description="Se true, ignora idempotência e força novo documento (consome numeração).")

    # IA (opcional)
    usar_ia: bool = PField(default=False, description="Se true, usa IA para sugerir o trecho de solicitação/cobrança.")
    ia_instructions: Optional[str] = PField(default=None, description="Instruções para a IA (tom/estilo).")
    ia_model: Optional[str] = PField(default=None, description="Override do modelo (ex.: gpt-5.2).")
    ia_reasoning_effort: Optional[str] = PField(default=None, description="Override do reasoning/effort (ex.: low).")


def _fmt_data_br(dt: Optional[datetime]) -> Optional[str]:
    if not dt:
        return None
    try:
        return dt.strftime("%d/%m/%Y")
    except Exception:
        return None


@router.post("/gerar/cobranca-devolutiva", dependencies=[Depends(exigir_minimo_perfil("operador"))])
def gerar_cobranca_devolutiva(
    payload: CobrancaDevolutivaAuto,
    request: Request,
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    """Gera um OFÍCIO de cobrança automaticamente.

    Compatibilidade:
    - Encaminhamento CRAS: usa o modelo `oficio_cobranca_devolutiva` (biblioteca SUAS).
    - Encaminhamento Intermunicipal (Rede): fallback para `oficio_padrao` (texto guiado),
      permitindo que o botão "Cobrar" da Gestão funcione também para itens intermunicipais.
    """

    # 1) Tenta CRAS (padrão)
    enc = session.get(CrasEncaminhamento, payload.encaminhamento_id)
    enc_inter = None
    kind = "cras"

    # 2) Fallback: Intermunicipal (se existir no projeto)
    if not enc and EncaminhamentoIntermunicipal is not None:
        try:
            enc_inter = session.get(EncaminhamentoIntermunicipal, int(payload.encaminhamento_id))
        except Exception:
            enc_inter = None
        if enc_inter:
            kind = "intermunicipal"

    if not enc and not enc_inter:
        raise HTTPException(status_code=404, detail="Encaminhamento não encontrado")

    # Resolve município (global exige municipio_id)
    if kind == "cras":
        mid = _resolver_municipio(usuario, payload.municipio_id or getattr(enc, "municipio_id", None))
        if getattr(enc, "municipio_id", None) not in (None, mid) and not pode_acesso_global(usuario):
            # segurança extra: operador municipal não pode gerar doc de outro município
            raise HTTPException(status_code=403, detail="Sem permissão para esse município")
    else:
        # Intermunicipal: para usuários municipais, a numeração/branding é do seu próprio município.
        # Para global, continua obrigatório informar municipio_id no payload.
        mid = _resolver_municipio(usuario, payload.municipio_id or getattr(usuario, "municipio_id", None))
        if not pode_acesso_global(usuario):
            u_mid = getattr(usuario, "municipio_id", None)
            try:
                allowed = {
                    int(getattr(enc_inter, "municipio_origem_id", -1) or -1),
                    int(getattr(enc_inter, "municipio_destino_id", -1) or -1),
                }
            except Exception:
                allowed = set()
            if u_mid is None or int(u_mid) not in allowed:
                raise HTTPException(status_code=403, detail="Sem permissão para acessar este encaminhamento")

    # Idempotência (opcional): evita duplicar numeração em retries/cliques repetidos.
    # - Se idempotency_key NÃO for fornecida, usa uma chave automática por dia.
    # - Para forçar novo documento (ex.: segunda cobrança no mesmo dia), use forcar_novo=true.
    idem_key: str | None = None
    if payload.salvar and not getattr(payload, "forcar_novo", False):
        auto_day = _now_utc_naive().date().isoformat()
        base_key = (payload.idempotency_key or f"auto:{mid}:{payload.emissor}:{kind}:{payload.encaminhamento_id}:{auto_day}").strip()
        if base_key:
            idem_key = f"cobranca-devolutiva:{base_key}"
            rec = _idem_load(idem_key)
            if rec and rec.get("doc_id"):
                try:
                    doc_id = int(rec["doc_id"])
                    doc = session.get(DocumentoEmitido, doc_id)
                except Exception:
                    doc = None
                if doc and getattr(doc, "id", None):
                    abs_path = _to_abspath(getattr(doc, "arquivo_path", "") or "")
                    if abs_path and os.path.exists(abs_path):
                        codigo = _calc_verif_code(doc)
                        path_ver = f"/documentos/{int(doc.id)}/verificar?c={codigo}" if codigo else ""
                        base_ver = _branding_public_base_url(getattr(doc, "municipio_id", None) or mid) or _verif_base_url() or str(request.base_url).rstrip("/")
                        url = f"{base_ver}{path_ver}" if (base_ver and path_ver) else path_ver
                        return {
                            "id": doc.id,
                            "numero": doc.numero,
                            "tipo": doc.tipo,
                            "download": f"/documentos/{doc.id}/download",
                            "verificacao": {"codigo": codigo, "url": url, "path": path_ver},
                        }

    # =========================================================
    # Caminho CRAS (mantém comportamento)
    # =========================================================
    if kind == "cras":
        destino_tipo = (getattr(enc, "destino_tipo", "") or "").strip()
        destino_nome = (getattr(enc, "destino_nome", "") or "").strip()

        dest_nome = payload.destinatario_nome or (destino_nome or "Destinatário")
        dest_cargo = payload.destinatario_cargo or "Coordenação"
        dest_orgao = payload.destinatario_orgao or (destino_tipo.upper() if destino_tipo else None)

        prazo_default = f"{getattr(enc, 'prazo_devolutiva_dias', 7)} dias"
        prazo = payload.prazo or prazo_default

        campos: Dict[str, Any] = {
            "referencia": f"Encaminhamento #{payload.encaminhamento_id} — {destino_nome}" if destino_nome else f"Encaminhamento #{payload.encaminhamento_id}",
            "prazo": prazo,
        }

        data_envio = _fmt_data_br(getattr(enc, "enviado_em", None))
        if data_envio:
            campos["data_envio"] = data_envio

        # IA (opcional)
        if getattr(payload, "usar_ia", False) and generate_text is not None:
            try:
                instr = payload.ia_instructions or "Escreva formal, padrão prefeitura, curto e objetivo."
                prompt = (
                    f"Crie um parágrafo (1 a 3 frases) cobrando devolutiva de encaminhamento. "
                    f"Referência: {campos.get('referencia')}. Prazo: {prazo}. "
                    + (f"Encaminhado em {data_envio}. " if data_envio else "")
                    + "Solicite que a devolutiva seja registrada no sistema e, se não for possível cumprir o prazo, pedir justificativa e previsão."
                )
                res = generate_text(
                    input_text=prompt,
                    instructions=instr,
                    model=payload.ia_model,
                    reasoning_effort=payload.ia_reasoning_effort,
                    user_id=getattr(usuario, "id", None),
                    municipio_id=mid,
                )
                if res and getattr(res, "text", None):
                    campos["solicitacao"] = res.text.strip()
            except Exception:
                pass

        if payload.contato_retorno:
            campos["contato_retorno"] = payload.contato_retorno

        doc_payload = DocumentoGerar(
            municipio_id=mid,
            tipo="oficio",
            modelo="oficio_cobranca_devolutiva",
            assunto="Cobrança de devolutiva",
            destinatario_nome=dest_nome,
            destinatario_cargo=dest_cargo,
            destinatario_orgao=dest_orgao,
            campos=campos,
            emissor=payload.emissor,
            salvar=payload.salvar,
            retornar_pdf=payload.retornar_pdf,
            arquivo_nome=payload.arquivo_nome,
        )

        resp = gerar_documento(doc_payload, request=request, session=session, usuario=usuario)
        if isinstance(resp, dict) and resp.get("id") and idem_key:
            _idem_save(idem_key, {"doc_id": resp.get("id")})
        return resp

    # =========================================================
    # Caminho Intermunicipal (fallback seguro)
    # =========================================================

    # Nomes dos municípios (se existir)
    dest_muni_nome = None
    orig_muni_nome = None
    try:
        m_dest = _get_municipio(session, int(getattr(enc_inter, "municipio_destino_id", 0) or 0))
        if m_dest:
            dest_muni_nome = getattr(m_dest, "nome", None)
    except Exception:
        dest_muni_nome = None

    try:
        mo = getattr(enc_inter, "municipio_origem_id", None)
        if mo is not None:
            m_orig = _get_municipio(session, int(mo))
            if m_orig:
                orig_muni_nome = getattr(m_orig, "nome", None)
    except Exception:
        orig_muni_nome = None

    status_atual = (getattr(enc_inter, "status", "") or "solicitado").strip()
    motivo = (getattr(enc_inter, "motivo", "") or "").strip()
    criado_em = getattr(enc_inter, "criado_em", None)
    data_criado = _fmt_data_br(criado_em) if isinstance(criado_em, datetime) else None

    # Próximo passo (linha do metrô simplificada)
    ordem = ["solicitado", "contato", "aceito", "agendado", "passagem", "contrarreferencia", "concluido"]
    prox = None
    try:
        idx = ordem.index(status_atual)
        prox = ordem[idx + 1] if idx < len(ordem) - 1 else None
    except Exception:
        prox = None

    # Texto base do ofício
    texto = (
        f"Solicita-se atualização e registro de providências no Sistema referente ao Encaminhamento Intermunicipal nº {payload.encaminhamento_id}"
        + (f" (origem: {orig_muni_nome})" if orig_muni_nome else "")
        + (f" (destino: {dest_muni_nome})" if dest_muni_nome else "")
        + ". "
        + (f"Status atual: {status_atual}. " if status_atual else "")
        + (f"Motivo: {motivo}. " if motivo else "")
        + (f"Data da solicitação: {data_criado}. " if data_criado else "")
        + (f"Próxima etapa esperada: {prox}. " if prox else "")
        + "Favor registrar retorno no sistema e, se não for possível cumprir o prazo operacional, informar justificativa e previsão."
    )

    # IA (opcional): substitui o texto com um parágrafo melhor
    if getattr(payload, "usar_ia", False) and generate_text is not None:
        try:
            instr = payload.ia_instructions or "Escreva formal, padrão prefeitura, curto e objetivo."
            prompt = (
                f"Crie um parágrafo (1 a 3 frases) cobrando atualização de encaminhamento intermunicipal de assistência social. "
                f"Encaminhamento nº {payload.encaminhamento_id}. "
                + (f"Origem: {orig_muni_nome}. " if orig_muni_nome else "")
                + (f"Destino: {dest_muni_nome}. " if dest_muni_nome else "")
                + (f"Status atual: {status_atual}. " if status_atual else "")
                + (f"Próxima etapa esperada: {prox}. " if prox else "")
                + "Solicite que o retorno seja registrado no sistema e, se houver impossibilidade, peça justificativa e previsão."
            )
            res = generate_text(
                input_text=prompt,
                instructions=instr,
                model=payload.ia_model,
                reasoning_effort=payload.ia_reasoning_effort,
                user_id=getattr(usuario, "id", None),
                municipio_id=mid,
            )
            if res and getattr(res, "text", None):
                texto = res.text.strip()
        except Exception:
            pass

    dest_nome = payload.destinatario_nome or "Secretaria Municipal de Assistência Social"
    dest_cargo = payload.destinatario_cargo or ""
    dest_orgao = payload.destinatario_orgao or (f"Município de {dest_muni_nome}" if dest_muni_nome else None)

    doc_payload = DocumentoGerar(
        municipio_id=mid,
        tipo="oficio",
        modelo="oficio_padrao",
        assunto="Cobrança — Encaminhamento intermunicipal",
        destinatario_nome=dest_nome,
        destinatario_cargo=dest_cargo,
        destinatario_orgao=dest_orgao,
        campos={"texto": texto},
        emissor=payload.emissor,
        salvar=payload.salvar,
        retornar_pdf=payload.retornar_pdf,
        arquivo_nome=payload.arquivo_nome,
    )

    resp = gerar_documento(doc_payload, request=request, session=session, usuario=usuario)
    if isinstance(resp, dict) and resp.get("id") and idem_key:
        _idem_save(idem_key, {"doc_id": resp.get("id")})
    return resp
