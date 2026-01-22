# app/core/security.py
import os
from datetime import datetime, timedelta
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.models.usuario import UsuarioRead

# ================================
# Configuração de senha (hash)
# ================================
# ✅ IMPORTANTÍSSIMO:
# - coloca pbkdf2_sha256 como padrão (hash novo)
# - mantém bcrypt para verificar hashes antigos sem estourar 500
pwd_context = CryptContext(
    schemes=["pbkdf2_sha256", "bcrypt"],
    deprecated="auto",
)

def hash_senha(senha: str) -> str:
    return pwd_context.hash(senha)

def verificar_senha(senha: str, senha_hash: str) -> bool:
    """
    ✅ Nunca pode quebrar o login com exception.
    Se o hash estiver num formato diferente, retorna False.
    """
    try:
        return pwd_context.verify(senha, senha_hash)
    except Exception:
        return False

# ================================
# Configuração de JWT
# ================================
SECRET_KEY = os.getenv(
    "POPRUA_SECRET_KEY",
    "trocar-essa-chave-por-uma-bem-grande-e-secreta",
)
ALGORITHM = os.getenv("POPRUA_JWT_ALGORITHM", "HS256")

ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv("POPRUA_ACCESS_TOKEN_EXPIRE_MINUTES", str(60 * 8))
)

def criar_token_acesso(
    usuario: UsuarioRead,
    expires_delta: Optional[timedelta] = None,
) -> str:
    agora = datetime.utcnow()

    to_encode = {
        "sub": str(usuario.id),
        "perfil": usuario.perfil,
        "municipio_id": usuario.municipio_id,
        "iat": int(agora.timestamp()),
        "nome": usuario.nome,
        "email": usuario.email,
    }

    expire = agora + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode["exp"] = int(expire.timestamp())

    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decodificar_token(token: str) -> dict:
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])