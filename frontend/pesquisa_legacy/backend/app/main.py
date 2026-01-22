from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, constr

from .config import settings
from .email_service import send_contact_email


app = FastAPI(title="Ideal API")


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ContactRequest(BaseModel):
    nome: constr(strip_whitespace=True, min_length=2)
    email: EmailStr
    telefone: str | None = None
    municipio: str | None = None
    tipo: str | None = None
    mensagem: constr(strip_whitespace=True, min_length=5)


class ContactResponse(BaseModel):
    ok: bool
    message: str


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/contact", response_model=ContactResponse)
def contact(request: ContactRequest):
    try:
        send_contact_email(request.dict())
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="Não foi possível enviar o e-mail. Tente novamente em alguns minutos.",
        ) from e

    return ContactResponse(
        ok=True,
        message="Mensagem enviada com sucesso. A equipe da Ideal entrará em contato.",
    )