import secrets
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "sqlite:///./cloud_portal.db"
    secret_key: str = secrets.token_urlsafe(32)
    access_token_expire_minutes: int = 60 * 24 * 7  # 7 giorni

    # Bootstrap: creato automaticamente al primo avvio se non esiste alcun utente
    bootstrap_admin_username: str = "admin"
    bootstrap_admin_password: str = "changeme"

    cors_origins: list[str] = ["*"]


settings = Settings()
