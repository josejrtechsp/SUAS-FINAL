from __future__ import annotations

from datetime import datetime, timedelta

from sqlmodel import Session, select

from app.core.db import engine, init_db
from app.models.creas_unidade import CreasUnidade
from app.models.creas_caso import CreasCaso, CreasCasoHistorico


def seed_creas(municipio_id: int = 1) -> None:
    """Seed simples do CREAS: cria unidade e alguns casos demo (idempotente)."""
    print("Iniciando seed do CREAS...")
    init_db()

    with Session(engine) as session:
        # unidade
        unidade = session.exec(
            select(CreasUnidade).where(CreasUnidade.municipio_id == int(municipio_id)).where(CreasUnidade.nome == "CREAS 1")
        ).first()
        if not unidade:
            unidade = CreasUnidade(municipio_id=int(municipio_id), nome="CREAS 1", ativo=True)
            session.add(unidade)
            session.commit()
            session.refresh(unidade)
            print(f"Criada unidade: {unidade.nome} (id={unidade.id})")
        else:
            print(f"Já existe unidade: {unidade.nome} (id={unidade.id})")

        # casos demo se vazio
        existe_caso = session.exec(select(CreasCaso).where(CreasCaso.municipio_id == int(municipio_id))).first()
        if existe_caso:
            print("Já existem casos CREAS neste município; não vou criar demo.")
            print("Seed CREAS finalizado.")
            return

        now = datetime.utcnow()

        # 1 caso propositalmente em atraso (pra aparecer no /gestao/fila)
        demos = [
            {
                "titulo": "Violência doméstica (exemplo)",
                "tipologia": "violencia",
                "prioridade": "alta",
                "risco": "alto",
                "etapa_atual": "triagem",
                "inicio_etapa": now - timedelta(days=5),  # SLA padrão da triagem = 2 dias
                "prazo_etapa_dias": 2,
            },
            {
                "titulo": "Suspeita de negligência (exemplo)",
                "tipologia": "violacao_direitos",
                "prioridade": "media",
                "risco": "medio",
                "etapa_atual": "acolhimento",
                "inicio_etapa": now - timedelta(days=1),
                "prazo_etapa_dias": 7,
            },
            {
                "titulo": "Trabalho infantil (suspeita)",
                "tipologia": "trabalho_infantil",
                "prioridade": "media",
                "risco": "medio",
                "etapa_atual": "diagnostico",
                "inicio_etapa": now - timedelta(days=3),
                "prazo_etapa_dias": 14,
            },
        ]

        for d in demos:
            caso = CreasCaso(
                municipio_id=int(municipio_id),
                unidade_id=int(unidade.id),
                tipo_caso="familia",
                familia_id=None,
                pessoa_id=None,
                status="em_andamento",
                etapa_atual=d["etapa_atual"],
                prioridade=d["prioridade"],
                risco=d["risco"],
                tecnico_responsavel_id=None,
                titulo=d["titulo"],
                tipologia=d["tipologia"],
                data_abertura=now,
                data_inicio_etapa_atual=d["inicio_etapa"],
                prazo_etapa_dias=int(d["prazo_etapa_dias"]),
                atualizado_em=now,
            )
            session.add(caso)
            session.commit()
            session.refresh(caso)

            session.add(
                CreasCasoHistorico(
                    caso_id=int(caso.id),
                    etapa=caso.etapa_atual,
                    tipo_acao="abertura",
                    usuario_id=None,
                    usuario_nome="seed",
                    observacoes="Caso demo criado automaticamente.",
                    criado_em=datetime.utcnow(),
                )
            )
            session.commit()
            print(f"Criado caso CREAS demo: id={caso.id} etapa={caso.etapa_atual}")

    print("Seed CREAS finalizado.")


if __name__ == "__main__":
    seed_creas()
