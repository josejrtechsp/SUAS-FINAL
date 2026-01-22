from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from sqlmodel import Session, select

from app.core.db import engine, init_db
from app.models.meta_kpi import MetaKpi
from app.models.sla_regra import SlaRegra


# ============================================================
# Seed de padrões (SLA + Metas)
# ============================================================
#
# Objetivo: dar um start rápido para prefeituras pequenas/médias e consórcios,
# sem exigir que o usuário configure dezenas de regras na mão.
#
# - Idempotente: roda mais de uma vez sem duplicar.
# - Seguro: por padrão NÃO sobrescreve regras já existentes (use --overwrite).
#
# Como rodar (no macOS):
#   cd ~/POPNEWS1/backend
#   source .venv/bin/activate
#   python -m app.seed_config_sla --perfil media --municipio-id 1
#
# Observação importante:
# - SLA de CRAS encaminhamento é por município (municipio_id do registro).
# - SLA de Rede Intermunicipal no cálculo atual usa, por padrão, municipio_destino_id
#   (o município que precisa responder). Por isso o seed usa GLOBAL (municipio_id=None)
#   para intermunicipal, com possibilidade de virar municipal via --inter-scope.
#


@dataclass(frozen=True)
class SlaPadrao:
    modulo: str
    etapa: str
    sla_dias: int
    unidade_tipo: Optional[str] = None
    unidade_id: Optional[int] = None


@dataclass(frozen=True)
class MetaPadrao:
    modulo: str
    kpi: str
    periodo: str
    valor_meta: float


def _norm(v: Optional[str]) -> Optional[str]:
    if v is None:
        return None
    s = str(v).strip().lower()
    return s or None


def _resolve_perfil(raw: str) -> str:
    p = (_norm(raw) or "media")
    if p in ("pequena", "prefeitura_pequena", "prefeitura-pequena", "small"):
        return "prefeitura_pequena"
    if p in ("media", "média", "prefeitura_media", "prefeitura-média", "prefeitura-media", "medium"):
        return "prefeitura_media"
    if p in ("consorcio", "consórcio", "regional", "consortium"):
        return "consorcio"
    raise ValueError(f"Perfil inválido: {raw!r}. Use pequena|media|consorcio.")


# -------------------------
# SLAs recomendados
# -------------------------
#
# OBS: valores <=7 para CRAS porque _cras_enc_sla_dias limita pelo prazo_devolutiva_dias
# (que em muitos municípios começa em 7).
#
SLA_PADROES: Dict[str, List[SlaPadrao]] = {
    # Baseline conservador (bem próximo do default hardcoded do sistema)
    "prefeitura_pequena": [
        # CRAS encaminhamento (vale para todas as unidades CRAS do município)
        SlaPadrao("cras_encaminhamento", "enviado", 2, unidade_tipo="cras"),
        SlaPadrao("cras_encaminhamento", "recebido", 5, unidade_tipo="cras"),
        SlaPadrao("cras_encaminhamento", "agendado", 7, unidade_tipo="cras"),
        SlaPadrao("cras_encaminhamento", "atendido", 2, unidade_tipo="cras"),
        SlaPadrao("cras_encaminhamento", "devolutiva", 2, unidade_tipo="cras"),
        # Rede intermunicipal (por padrão GLOBAL)
        SlaPadrao("rede_intermunicipal", "solicitado", 2),
        SlaPadrao("rede_intermunicipal", "contato", 2),
        SlaPadrao("rede_intermunicipal", "aceito", 7),
        SlaPadrao("rede_intermunicipal", "agendado", 7),
        SlaPadrao("rede_intermunicipal", "passagem", 3),
        SlaPadrao("rede_intermunicipal", "contrarreferencia", 3),
    ],
    # Mais responsivo (bom para prefeitura média)
    "prefeitura_media": [
        SlaPadrao("cras_encaminhamento", "enviado", 1, unidade_tipo="cras"),
        SlaPadrao("cras_encaminhamento", "recebido", 3, unidade_tipo="cras"),
        SlaPadrao("cras_encaminhamento", "agendado", 5, unidade_tipo="cras"),
        SlaPadrao("cras_encaminhamento", "atendido", 2, unidade_tipo="cras"),
        SlaPadrao("cras_encaminhamento", "devolutiva", 2, unidade_tipo="cras"),
        SlaPadrao("rede_intermunicipal", "solicitado", 1),
        SlaPadrao("rede_intermunicipal", "contato", 1),
        SlaPadrao("rede_intermunicipal", "aceito", 5),
        SlaPadrao("rede_intermunicipal", "agendado", 7),
        SlaPadrao("rede_intermunicipal", "passagem", 3),
        SlaPadrao("rede_intermunicipal", "contrarreferencia", 2),
    ],
    # Mais exigente (bom para consórcio/central de monitoramento)
    "consorcio": [
        SlaPadrao("cras_encaminhamento", "enviado", 1, unidade_tipo="cras"),
        SlaPadrao("cras_encaminhamento", "recebido", 2, unidade_tipo="cras"),
        SlaPadrao("cras_encaminhamento", "agendado", 4, unidade_tipo="cras"),
        SlaPadrao("cras_encaminhamento", "atendido", 2, unidade_tipo="cras"),
        SlaPadrao("cras_encaminhamento", "devolutiva", 1, unidade_tipo="cras"),
        SlaPadrao("rede_intermunicipal", "solicitado", 1),
        SlaPadrao("rede_intermunicipal", "contato", 1),
        SlaPadrao("rede_intermunicipal", "aceito", 3),
        SlaPadrao("rede_intermunicipal", "agendado", 5),
        SlaPadrao("rede_intermunicipal", "passagem", 2),
        SlaPadrao("rede_intermunicipal", "contrarreferencia", 2),
    ],
}


# -------------------------
# Metas (opcionais) – ainda não consumidas pelo front,
# mas já ficam registradas para a futura tela de Gestão/Config.
# -------------------------
META_PADROES: Dict[str, List[MetaPadrao]] = {
    "prefeitura_pequena": [
        MetaPadrao("rede", "pct_devolutiva_no_prazo", "mensal", 0.70),
        MetaPadrao("rede", "pct_inter_contato_no_prazo", "mensal", 0.70),
        MetaPadrao("rede", "pct_inter_contrarref_no_prazo", "mensal", 0.60),
    ],
    "prefeitura_media": [
        MetaPadrao("rede", "pct_devolutiva_no_prazo", "mensal", 0.80),
        MetaPadrao("rede", "pct_inter_contato_no_prazo", "mensal", 0.80),
        MetaPadrao("rede", "pct_inter_contrarref_no_prazo", "mensal", 0.70),
    ],
    "consorcio": [
        MetaPadrao("rede", "pct_devolutiva_no_prazo", "mensal", 0.90),
        MetaPadrao("rede", "pct_inter_contato_no_prazo", "mensal", 0.90),
        MetaPadrao("rede", "pct_inter_contrarref_no_prazo", "mensal", 0.80),
    ],
}


def _upsert_sla(
    session: Session,
    municipio_id: Optional[int],
    unidade_tipo: Optional[str],
    unidade_id: Optional[int],
    modulo: str,
    etapa: str,
    sla_dias: int,
    *,
    overwrite: bool,
) -> Tuple[str, SlaRegra]:
    mid = int(municipio_id) if municipio_id is not None else None
    ut = _norm(unidade_tipo)
    uid = int(unidade_id) if unidade_id is not None else None
    mod = _norm(modulo) or ""
    st = _norm(etapa) or ""

    stmt = select(SlaRegra).where(
        SlaRegra.municipio_id == mid,
        SlaRegra.unidade_tipo == ut,
        SlaRegra.unidade_id == uid,
        SlaRegra.modulo == mod,
        SlaRegra.etapa == st,
    )
    row = session.exec(stmt).first()
    now = datetime.utcnow()

    if row:
        if overwrite:
            row.sla_dias = int(sla_dias)
            row.ativo = True
            row.atualizado_em = now
            session.add(row)
            return ("update", row)
        return ("skip", row)

    row = SlaRegra(
        municipio_id=mid,
        unidade_tipo=ut,
        unidade_id=uid,
        modulo=mod,
        etapa=st,
        sla_dias=int(sla_dias),
        ativo=True,
        criado_em=now,
        atualizado_em=now,
    )
    session.add(row)
    return ("insert", row)


def _upsert_meta(
    session: Session,
    municipio_id: Optional[int],
    unidade_tipo: Optional[str],
    unidade_id: Optional[int],
    modulo: str,
    kpi: str,
    periodo: str,
    valor_meta: float,
    *,
    overwrite: bool,
) -> Tuple[str, MetaKpi]:
    mid = int(municipio_id) if municipio_id is not None else None
    ut = _norm(unidade_tipo)
    uid = int(unidade_id) if unidade_id is not None else None
    mod = _norm(modulo) or ""
    k = _norm(kpi) or ""
    per = _norm(periodo) or "mensal"

    stmt = select(MetaKpi).where(
        MetaKpi.municipio_id == mid,
        MetaKpi.unidade_tipo == ut,
        MetaKpi.unidade_id == uid,
        MetaKpi.modulo == mod,
        MetaKpi.kpi == k,
        MetaKpi.periodo == per,
    )
    row = session.exec(stmt).first()
    now = datetime.utcnow()

    if row:
        if overwrite:
            row.valor_meta = float(valor_meta)
            row.ativo = True
            row.atualizado_em = now
            session.add(row)
            return ("update", row)
        return ("skip", row)

    row = MetaKpi(
        municipio_id=mid,
        unidade_tipo=ut,
        unidade_id=uid,
        modulo=mod,
        kpi=k,
        periodo=per,
        valor_meta=float(valor_meta),
        ativo=True,
        criado_em=now,
        atualizado_em=now,
    )
    session.add(row)
    return ("insert", row)


def aplicar_padroes(
    *,
    perfil: str,
    municipio_id: Optional[int],
    cras_scope: str,
    inter_scope: str,
    overwrite: bool,
    incluir_metas: bool,
    dry_run: bool,
) -> None:
    perfil_key = _resolve_perfil(perfil)

    cras_scope_n = _norm(cras_scope) or "municipal"
    inter_scope_n = _norm(inter_scope) or "global"

    if cras_scope_n not in ("municipal", "global"):
        raise ValueError("cras_scope deve ser municipal|global")
    if inter_scope_n not in ("municipal", "global"):
        raise ValueError("inter_scope deve ser municipal|global")

    if cras_scope_n == "municipal" and municipio_id is None:
        raise ValueError("cras_scope=municipal exige --municipio-id.")
    if inter_scope_n == "municipal" and municipio_id is None:
        raise ValueError("inter_scope=municipal exige --municipio-id.")

    cras_mid = None if cras_scope_n == "global" else int(municipio_id)  # type: ignore[arg-type]
    inter_mid = None if inter_scope_n == "global" else int(municipio_id)  # type: ignore[arg-type]

    print(
        f"Aplicando padrões: perfil={perfil_key} cras_scope={cras_scope_n} inter_scope={inter_scope_n} "
        f"municipio_id={municipio_id} overwrite={overwrite} dry_run={dry_run}"
    )

    init_db()

    counts = {"insert": 0, "update": 0, "skip": 0}

    with Session(engine) as session:
        # SLA
        for r in SLA_PADROES.get(perfil_key, []):
            is_inter = (_norm(r.modulo) == "rede_intermunicipal")
            mid = inter_mid if is_inter else cras_mid
            action, _row = _upsert_sla(
                session,
                mid,
                r.unidade_tipo,
                r.unidade_id,
                r.modulo,
                r.etapa,
                r.sla_dias,
                overwrite=overwrite,
            )
            counts[action] += 1

        # Metas
        if incluir_metas:
            for m in META_PADROES.get(perfil_key, []):
                action, _row = _upsert_meta(
                    session,
                    cras_mid,  # metas, por padrão, ficam no escopo do município (ou global se cras_scope=global)
                    None,
                    None,
                    m.modulo,
                    m.kpi,
                    m.periodo,
                    m.valor_meta,
                    overwrite=overwrite,
                )
                counts[action] += 1

        if dry_run:
            session.rollback()
            print("DRY RUN: nada foi gravado.")
        else:
            session.commit()
            print("Padrões gravados.")

    print(f"Resumo: insert={counts['insert']} update={counts['update']} skip={counts['skip']}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Aplica SLAs/Metas padrão no banco (Config).")
    parser.add_argument(
        "--perfil",
        default="media",
        help="pequena|media|consorcio (aliases: prefeitura_pequena, prefeitura_media, consorcio)",
    )
    parser.add_argument(
        "--municipio-id",
        type=int,
        default=1,
        help="Município alvo (para regras do CRAS). Default=1 (demo).",
    )
    parser.add_argument(
        "--cras-scope",
        default="municipal",
        choices=["municipal", "global"],
        help="Escopo das regras CRAS: municipal (padrão) ou global.",
    )
    parser.add_argument(
        "--inter-scope",
        default="global",
        choices=["global", "municipal"],
        help="Escopo das regras intermunicipais: global (padrão) ou municipal.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Sobrescreve regras/metas existentes (cuidado).",
    )
    parser.add_argument(
        "--sem-metas",
        action="store_true",
        help="Não aplica metas (só SLA).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simula sem gravar (rollback).",
    )

    args = parser.parse_args()

    aplicar_padroes(
        perfil=str(args.perfil),
        municipio_id=int(args.municipio_id) if args.municipio_id is not None else None,
        cras_scope=str(args.cras_scope),
        inter_scope=str(args.inter_scope),
        overwrite=bool(args.overwrite),
        incluir_metas=(not bool(args.sem_metas)),
        dry_run=bool(args.dry_run),
    )


if __name__ == "__main__":
    main()
