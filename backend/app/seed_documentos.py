from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone

from sqlmodel import Session, select

from app.core.db import engine, init_db
from app.models.documento_template import DocumentoTemplate
from app.models.documento_config import DocumentoConfig
from app.models.municipio_branding import MunicipioBranding
from app.models.municipio import Municipio
from app.services.documentos_modelos import listar_modelos


# Biblioteca completa é definida em app.services.documentos_modelos



def _now_utc_naive() -> datetime:
    """UTC como datetime naive (compatível com schema existente)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def upsert_template(
    session: Session,
    municipio_id,
    tipo,
    titulo,
    assunto_padrao,
    corpo_template,
    assinatura_template,
    overwrite=False,
):
    q = select(DocumentoTemplate).where(
        (DocumentoTemplate.municipio_id == municipio_id)
        & (DocumentoTemplate.tipo == tipo)
        & (DocumentoTemplate.titulo == titulo)
    )
    existing = session.exec(q).first()
    now = _now_utc_naive()

    if existing:
        if overwrite:
            existing.assunto_padrao = assunto_padrao
            existing.corpo_template = corpo_template
            existing.assinatura_template = assinatura_template
            existing.ativo = True
            existing.atualizado_em = now
            session.add(existing)
            return "update"
        return "skip"

    tpl = DocumentoTemplate(
        municipio_id=municipio_id,
        tipo=tipo,
        titulo=titulo,
        assunto_padrao=assunto_padrao,
        corpo_template=corpo_template,
        assinatura_template=assinatura_template,
        ativo=True,
        criado_em=now,
        atualizado_em=now,
    )
    session.add(tpl)
    return "insert"


def main():
    parser = argparse.ArgumentParser(
        description="Seed de templates de documentos (globais) e branding municipal opcional."
    )
    parser.add_argument(
        "--municipio-id",
        type=int,
        default=None,
        help="Se informado, cria também branding para este município.",
    )
    parser.add_argument(
        "--overwrite", action="store_true", help="Sobrescreve templates existentes."
    )
    args = parser.parse_args()

    init_db()

    insert = update = skip = 0

    with Session(engine) as session:
        # Templates globais (biblioteca completa)
        for m in listar_modelos():
            r = upsert_template(
                session,
                municipio_id=None,
                tipo=m.tipo,
                titulo=m.titulo,
                assunto_padrao=m.assunto_padrao,
                corpo_template=m.corpo_template,
                assinatura_template=m.assinatura_template,
                overwrite=args.overwrite,
            )
            if r == "insert":
                insert += 1
            elif r == "update":
                update += 1
            else:
                skip += 1

        # Branding municipal opcional
        if args.municipio_id:
            mid = int(args.municipio_id)
            mun = session.get(Municipio, mid)
            now = _now_utc_naive()
            # Branding
            branding = session.exec(
                select(MunicipioBranding).where(MunicipioBranding.municipio_id == mid)
            ).first()
            if not branding:
                nome = mun.nome if mun else None
                nome_inst = f"Prefeitura Municipal de {nome}" if nome else None
                header = None
                if mun:
                    header = f"{nome_inst or mun.nome}/{mun.uf}\nSecretaria Municipal"
                branding = MunicipioBranding(
                    municipio_id=mid,
                    nome_instituicao=nome_inst,
                    header_text=header,
                    footer_text="Documento gerado pelo Sistema Pop Rua",
                    criado_em=now,
                    atualizado_em=now,
                )
                session.add(branding)
        
            # DocumentoConfig (defaults de numeração/siglas)
            cfg = session.exec(
                select(DocumentoConfig).where(DocumentoConfig.municipio_id == mid)
            ).first()
            if not cfg:
                siglas_default = {"smas": "SMAS", "cras": "CRAS", "creas": "CREAS"}
                prefixos_default = {"oficio": "OF", "memorando": "MEM", "relatorio": "REL", "declaracao": "DEC"}
                cfg = DocumentoConfig(
                    municipio_id=mid,
                    numero_estilo_default="prefeitura",
                    digitos_seq_default=3,
                    emissor_padrao="smas",
                    sequenciar_por_emissor=True,
                    sigla_padrao="SMAS",
                    siglas_json=json.dumps(siglas_default, ensure_ascii=False),
                    prefixos_json=json.dumps(prefixos_default, ensure_ascii=False),
                    criado_em=now,
                    atualizado_em=now,
                )
                session.add(cfg)
        session.commit()

    print("Seed documentos: ok")
    print(f"Resumo: insert={insert} update={update} skip={skip}")


if __name__ == "__main__":
    main()
