from pydantic import BaseSettings, EmailStr, Field
from typing import List


class Settings(BaseSettings):
    email_host: str = Field("smtp.gmail.com", env="EMAIL_HOST")
    email_port: int = Field(587, env="EMAIL_PORT")
    email_user: EmailStr = Field(..., env="EMAIL_USER")
    email_password: str = Field(..., env="EMAIL_PASSWORD")
    email_to: EmailStr = Field(..., env="EMAIL_TO")
    allowed_origins: List[str] = Field(
        default=["http://localhost:5173"],
        env="ALLOWED_ORIGINS",
    )

    class Config:
        env_file = ".env"


settings = Settings()