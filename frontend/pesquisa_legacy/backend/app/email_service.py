import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict

from .config import settings


def send_contact_email(data: Dict[str, str]) -> None:
    """
    Envia e-mail de contato usando SMTP (Gmail).
    data deve conter: nome, email, telefone, tipo, mensagem, municipio.
    """

    subject = f"[Site Ideal] Novo contato de {data.get('nome')}"
    from_email = settings.email_user
    to_email = settings.email_to

    body = f"""
Novo contato recebido pelo site da Ideal:

Nome: {data.get('nome')}
E-mail: {data.get('email')}
Telefone: {data.get('telefone')}
Município: {data.get('municipio')}
Tipo de cliente: {data.get('tipo')}

Mensagem:
{data.get('mensagem')}
"""

    msg = MIMEMultipart()
    msg["From"] = from_email
    msg["To"] = to_email
    msg["Subject"] = subject

    msg.attach(MIMEText(body, "plain", "utf-8"))

    with smtplib.SMTP(settings.email_host, settings.email_port) as server:
        server.starttls()
        server.login(settings.email_user, settings.email_password)
        server.sendmail(from_email, [to_email], msg.as_string())