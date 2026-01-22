from __future__ import annotations

from datetime import date, datetime, timedelta

from sqlmodel import Session, select

from app.core.db import engine, init_db
from app.models.osc import Osc, OscParceria, OscPrestacaoContas


def seed_osc(municipio_id: int = 1) -> None:
    """Seed simples do Terceiro Setor (OSC) para demo da Gestão.

    - Cria 2 OSCs
    - Cria 2 parcerias
    - Cria prestações (uma em atraso para aparecer como "crítica")
    """

    print("Iniciando seed do Terceiro Setor (OSC)...")
    init_db()

    with Session(engine) as session:
        # não duplica seed se já existir OSC no município
        existe = session.exec(select(Osc).where(Osc.municipio_id == int(municipio_id))).first()
        if existe:
            print("Já existem OSCs neste município; não vou criar demo.")
            print("Seed OSC finalizado.")
            return

        osc1 = Osc(
            municipio_id=int(municipio_id),
            nome="Associação Nova Vida",
            cnpj="12.345.678/0001-90",
            tipo="associacao",
            areas_atuacao="Assistência social, crianças e adolescentes",
            contato_nome="Coordenação",
            contato_email="contato@novavida.org",
            contato_telefone="(16) 99999-0000",
            ativo=True,
            criado_em=datetime.utcnow(),
        )
        osc2 = Osc(
            municipio_id=int(municipio_id),
            nome="Instituto Caminhos",
            cnpj="98.765.432/0001-10",
            tipo="fundacao",
            areas_atuacao="SCFV, juventude",
            contato_nome="Diretoria",
            contato_email="contato@caminhos.org",
            contato_telefone="(16) 98888-1111",
            ativo=True,
            criado_em=datetime.utcnow(),
        )
        session.add(osc1)
        session.add(osc2)
        session.commit()
        session.refresh(osc1)
        session.refresh(osc2)
        print(f"Criadas OSCs: {osc1.nome} (id={osc1.id}), {osc2.nome} (id={osc2.id})")

        p1 = OscParceria(
            municipio_id=int(municipio_id),
            osc_id=int(osc1.id),
            instrumento="termo_fomento",
            numero="TF-001/2026",
            objeto="Execução de serviço de convivência (SCFV)",
            valor_total=180000.0,
            data_inicio=date.today() - timedelta(days=60),
            data_fim=date.today() + timedelta(days=300),
            status="ativa",
            gestor_responsavel_id=None,
            gestor_responsavel_nome=None,
            criado_em=datetime.utcnow(),
            atualizado_em=datetime.utcnow(),
        )
        p2 = OscParceria(
            municipio_id=int(municipio_id),
            osc_id=int(osc2.id),
            instrumento="termo_colaboracao",
            numero="TC-002/2026",
            objeto="Acolhimento e acompanhamento familiar",
            valor_total=240000.0,
            data_inicio=date.today() - timedelta(days=30),
            data_fim=date.today() + timedelta(days=330),
            status="ativa",
            gestor_responsavel_id=None,
            gestor_responsavel_nome=None,
            criado_em=datetime.utcnow(),
            atualizado_em=datetime.utcnow(),
        )
        session.add(p1)
        session.add(p2)
        session.commit()
        session.refresh(p1)
        session.refresh(p2)
        print(f"Criadas parcerias: id={p1.id}, id={p2.id}")

        # prestação crítica (em atraso)
        pc1 = OscPrestacaoContas(
            municipio_id=int(municipio_id),
            parceria_id=int(p1.id),
            competencia="2025-12",
            prazo_entrega=date.today() - timedelta(days=10),
            status="pendente",
            entregue_em=None,
            responsavel_id=None,
            responsavel_nome=None,
            observacao="Prestação mensal pendente.",
            criado_em=datetime.utcnow(),
            atualizado_em=datetime.utcnow(),
        )
        # prestação pendente (a vencer)
        pc2 = OscPrestacaoContas(
            municipio_id=int(municipio_id),
            parceria_id=int(p2.id),
            competencia="2026-01",
            prazo_entrega=date.today() + timedelta(days=15),
            status="pendente",
            entregue_em=None,
            responsavel_id=None,
            responsavel_nome=None,
            observacao="Prestação mensal a vencer.",
            criado_em=datetime.utcnow(),
            atualizado_em=datetime.utcnow(),
        )
        session.add(pc1)
        session.add(pc2)
        session.commit()
        session.refresh(pc1)
        session.refresh(pc2)
        print(f"Criadas prestações: id={pc1.id} (atrasada), id={pc2.id} (a vencer)")

    print("Seed OSC finalizado.")


if __name__ == "__main__":
    seed_osc()
