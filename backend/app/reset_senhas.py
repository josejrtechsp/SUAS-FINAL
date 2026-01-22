from sqlmodel import Session, select

from app.core.db import engine, init_db
from app.core.security import hash_senha
from app.models.usuario import Usuario


USUARIOS_PARA_RESET = [
    ("admin@poprua.local", "admin123"),
    ("operador.araraquara@poprua.local", "operador123"),
]


def reset_senhas():
    """
    Reseta as senhas dos usuários informados, sem apagar banco.
    Útil quando mudamos o algoritmo de hash (ex.: bcrypt -> pbkdf2_sha256).
    """
    print("Resetando senhas...")

    # garante tabelas
    init_db()

    with Session(engine) as session:
        for email, senha in USUARIOS_PARA_RESET:
            stmt = select(Usuario).where(Usuario.email == email)
            usuario = session.exec(stmt).first()

            if not usuario:
                print(f"Usuário NÃO encontrado: {email}")
                continue

            usuario.senha_hash = hash_senha(senha)
            session.add(usuario)
            print(f"Senha resetada: {email}")

        session.commit()

    print("Reset finalizado.")


if __name__ == "__main__":
    reset_senhas()