from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuración global de la aplicación, leída desde variables de entorno / .env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    APP_ENV: str = "development"
    LOG_LEVEL: str = "INFO"
    PORT: int = 8000

    # Supabase
    SUPABASE_URL: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""
    SUPABASE_ANON_KEY: str = ""
    SUPABASE_JWT_SECRET: str = ""
    SUPABASE_DB_URL: str = ""

    BUCKET_RESUMES: str = "resumes"

    # CORS y cron
    CORS_ALLOWED_ORIGINS: str = "http://localhost:4200"
    CRON_SECRET: str = ""

    # Credenciales del admin para tests de integración (dev). No usar en prod.
    ADMIN_EMAIL: str = ""
    ADMIN_PASSWORD: str = ""

    # Notificaciones por email (Resend). Sin API key o destinatario, no se envía nada.
    RESEND_API_KEY: str = ""
    NOTIFY_FROM_EMAIL: str = "onboarding@resend.dev"
    NOTIFY_EMAIL_TO: str = ""

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ALLOWED_ORIGINS.split(",") if origin.strip()]

    @property
    def notify_enabled(self) -> bool:
        return bool(self.RESEND_API_KEY and self.NOTIFY_EMAIL_TO)


@lru_cache
def get_settings() -> Settings:
    return Settings()