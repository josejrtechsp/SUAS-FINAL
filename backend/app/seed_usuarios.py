from sqlmodel import Session, select

from app.core.db import engine, init_db
from app.core.security import hash_senha
from app.models.usuario import Usuario


USUARIOS_BASE = [
    {
        "nome": "Admin Pop Rua",
        "email": "admin@poprua.local",
        "perfil": "admin",
        "municipio_id": None,
        "ativo": True,
        "senha_plana": "admin123",
    },
    {
        "nome": "Operador Araraquara",
        "email": "operador.araraquara@poprua.local",
        "perfil": "operador",
        "municipio_id": 3,  # ajuste para o ID real de Araraquara no seu banco
        "ativo": True,
        "senha_plana": "operador123",
    },
]


def seed_usuarios():
    """
    Cria usuários básicos no banco, se ainda não existirem.
    Pode rodar quantas vezes quiser: não duplica e-mail.
    """
    print("Iniciando seed de usuários...")

    # garante criação das tabelas
    init_db()

    with Session(engine) as session:
        for dados in USUARIOS_BASE:
            email = dados["email"]

            stmt = select(Usuario).where(Usuario.email == email)
            existente = session.exec(stmt).first()

            if existente:
                print(f"Já existe usuário: {email} (id={existente.id})")
                continue

            usuario = Usuario(
                nome=dados["nome"],
                email=dados["email"],
                perfil=dados["perfil"],
                municipio_id=dados["municipio_id"],
                ativo=dados["ativo"],
                senha_hash=hash_senha(dados["senha_plana"]),
            )

            session.add(usuario)
            session.commit()
            session.refresh(usuario)

            print(
                f"Criado usuário: {usuario.nome} "
                f"({usuario.email}) perfil={usuario.perfil} id={usuario.id}"
            )

    print("Seed de usuários finalizado.")


if __name__ == "__main__":
    seed_usuarios()