from sqlmodel import Session, select

from app.core.db import engine, init_db
from app.models.municipio import Municipio


# Lista de municípios que você passou
MUNICIPIOS_BASE = [
    {"nome": "São Carlos", "uf": "SP"},
    {"nome": "Tabatinga", "uf": "SP"},  # ajuste se o nome correto for outro
    {"nome": "Araraquara", "uf": "SP"},
    {"nome": "Ibaté", "uf": "SP"},
    {"nome": "Porto Ferreira", "uf": "SP"},
    {"nome": "Santa Rita do Passa Quatro", "uf": "SP"},
    {"nome": "Américo Brasiliense", "uf": "SP"},
]


def seed_municipios():
    """
    Cria os municípios básicos no banco, se ainda não existirem.
    Pode rodar quantas vezes quiser: ele não duplica nomes.
    """
    print("Iniciando seed de municípios...")

    # garante que as tabelas existem
    init_db()

    with Session(engine) as session:
        for dados in MUNICIPIOS_BASE:
            nome = dados["nome"]

            # verifica se já existe município com esse nome
            stmt = select(Municipio).where(Municipio.nome == nome)
            existente = session.exec(stmt).first()

            if existente:
                print(f"Já existe município: {nome} (id={existente.id})")
                continue

            municipio = Municipio(**dados)
            session.add(municipio)
            session.commit()
            session.refresh(municipio)

            print(f"Criado município: {nome} (id={municipio.id})")

    print("Seed de municípios finalizado.")


if __name__ == "__main__":
    seed_municipios()