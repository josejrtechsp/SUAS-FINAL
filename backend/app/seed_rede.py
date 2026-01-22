from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import or_  # type: ignore
from sqlmodel import Session, select

from app.core.db import engine, init_db
from app.models.cras_encaminhamento import CrasEncaminhamento, CrasEncaminhamentoEvento
from app.models.cras_unidade import CrasUnidade
from app.models.encaminhamentos import EncaminhamentoEvento, EncaminhamentoIntermunicipal


def seed_rede(municipio_id: int = 1) -> None:
    """Seed simples para demonstrar a REDE na Gestão (encaminhamentos + devolutivas).

    - Cria 2 encaminhamentos CRAS (1 atrasado, 1 em risco)
    - Cria 2 encaminhamentos intermunicipais (1 em risco, 1 atrasado)

    Idempotente: não duplica se já existirem registros no município.
    """
    print("Iniciando seed da Rede (Encaminhamentos)...")
    init_db()

    now = datetime.utcnow()

    with Session(engine) as session:
        # ===== CRAS =====
        unidade = session.exec(
            select(CrasUnidade)
            .where(CrasUnidade.municipio_id == int(municipio_id))
            .order_by(CrasUnidade.id.asc())
        ).first()
        if not unidade:
            unidade = CrasUnidade(municipio_id=int(municipio_id), nome="CRAS 1", ativo=True, criado_em=now)
            session.add(unidade)
            session.commit()
            session.refresh(unidade)

        existe_cras = session.exec(
            select(CrasEncaminhamento).where(CrasEncaminhamento.municipio_id == int(municipio_id))
        ).first()

        if existe_cras:
            print("Já existem encaminhamentos CRAS neste município; não vou criar demo CRAS.")
        else:
            # 1) atrasado (prazo 7 dias, enviado há 10)
            e1 = CrasEncaminhamento(
                municipio_id=int(municipio_id),
                unidade_id=int(unidade.id),
                pessoa_id=None,
                paif_id=None,
                destino_tipo="creas",
                destino_nome="CREAS 1",
                motivo="Acompanhamento especializado (demo)",
                observacao_operacional="Encaminhamento demo para aparecer na Gestão (atrasado).",
                status="enviado",
                enviado_em=now - timedelta(days=10),
                prazo_devolutiva_dias=7,
                criado_por_nome="seed",
                atualizado_por_nome="seed",
                criado_em=now,
                atualizado_em=now,
            )
            session.add(e1)
            session.commit()
            session.refresh(e1)
            session.add(
                CrasEncaminhamentoEvento(
                    encaminhamento_id=int(e1.id),
                    tipo="enviado",
                    detalhe="Encaminhamento demo criado (atrasado).",
                    por_nome="seed",
                    em=now,
                )
            )

            # 2) em risco (prazo 7 dias, enviado há 5 → vence em 2 dias com janela 72h)
            e2 = CrasEncaminhamento(
                municipio_id=int(municipio_id),
                unidade_id=int(unidade.id),
                pessoa_id=None,
                paif_id=None,
                destino_tipo="osc",
                destino_nome="Associação Nova Vida",
                motivo="Vaga em serviço (demo)",
                observacao_operacional="Encaminhamento demo para aparecer na Gestão (em risco).",
                status="enviado",
                enviado_em=now - timedelta(days=5),
                prazo_devolutiva_dias=7,
                criado_por_nome="seed",
                atualizado_por_nome="seed",
                criado_em=now,
                atualizado_em=now,
            )
            session.add(e2)
            session.commit()
            session.refresh(e2)
            session.add(
                CrasEncaminhamentoEvento(
                    encaminhamento_id=int(e2.id),
                    tipo="enviado",
                    detalhe="Encaminhamento demo criado (em risco).",
                    por_nome="seed",
                    em=now,
                )
            )

            session.commit()
            print(f"Criados encaminhamentos CRAS: ids={e1.id},{e2.id}")

        # ===== Intermunicipal =====
        existe_inter = session.exec(
            select(EncaminhamentoIntermunicipal).where(
                or_(
                    EncaminhamentoIntermunicipal.municipio_origem_id == int(municipio_id),
                    EncaminhamentoIntermunicipal.municipio_destino_id == int(municipio_id),
                )
            )
        ).first()

        if existe_inter:
            print("Já existem encaminhamentos intermunicipais envolvendo este município; não vou criar demo intermunicipal.")
        else:
            # 1) em risco (due = criado + 15d). criado há 13d -> vence em 2d
            i1 = EncaminhamentoIntermunicipal(
                pessoa_id=1,
                caso_id=None,
                municipio_origem_id=int(municipio_id),
                municipio_destino_id=2,
                motivo="Retorno assistido (demo)",
                observacoes="Intermunicipal demo (em risco).",
                consentimento_registrado=True,
                status="solicitado",
                criado_em=now - timedelta(days=13),
                atualizado_em=now - timedelta(days=13),
            )
            session.add(i1)
            session.commit()
            session.refresh(i1)
            session.add(
                EncaminhamentoEvento(
                    encaminhamento_id=int(i1.id),
                    tipo="solicitado",
                    detalhe="Solicitação demo registrada.",
                    por_nome="seed",
                    em=now - timedelta(days=13),
                )
            )

            # 2) atrasado (criado há 20d -> venceu há 5d)
            i2 = EncaminhamentoIntermunicipal(
                pessoa_id=2,
                caso_id=None,
                municipio_origem_id=int(municipio_id),
                municipio_destino_id=3,
                motivo="Reintegração familiar (demo)",
                observacoes="Intermunicipal demo (atrasado).",
                consentimento_registrado=True,
                status="solicitado",
                criado_em=now - timedelta(days=20),
                atualizado_em=now - timedelta(days=20),
            )
            session.add(i2)
            session.commit()
            session.refresh(i2)
            session.add(
                EncaminhamentoEvento(
                    encaminhamento_id=int(i2.id),
                    tipo="solicitado",
                    detalhe="Solicitação demo registrada.",
                    por_nome="seed",
                    em=now - timedelta(days=20),
                )
            )

            session.commit()
            print(f"Criados encaminhamentos intermunicipais: ids={i1.id},{i2.id}")

    print("Seed Rede finalizado.")


if __name__ == "__main__":
    seed_rede()
