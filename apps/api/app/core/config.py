from functools import lru_cache

from pydantic import AnyHttpUrl, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = Field(default="development", alias="APP_ENV")
    app_name: str = Field(default="SkillGraph", alias="APP_NAME")
    app_host: str = Field(default="0.0.0.0", alias="APP_HOST")
    app_port: int = Field(default=8000, alias="APP_PORT")

    database_url: str = Field(
        default="postgresql+psycopg://skillgraph:skillgraph@localhost:5432/skillgraph",
        alias="DATABASE_URL",
    )

    jwt_secret_key: str = Field(alias="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    jwt_access_expires_minutes: int = Field(default=20, alias="JWT_ACCESS_EXPIRES_MINUTES")
    jwt_refresh_expires_minutes: int = Field(default=60 * 24 * 7, alias="JWT_REFRESH_EXPIRES_MINUTES")

    cookie_secure: bool = Field(default=False, alias="COOKIE_SECURE")
    cookie_domain: str | None = Field(default=None, alias="COOKIE_DOMAIN")

    frontend_admin_url: AnyHttpUrl = Field(default="http://localhost:5173", alias="FRONTEND_ADMIN_URL")
    frontend_web_url: AnyHttpUrl = Field(default="http://localhost:5174", alias="FRONTEND_WEB_URL")

    ai_service_url: str = Field(default="http://ai:8100", alias="AI_SERVICE_URL")
    ai_question_service_url: str | None = Field(default=None, alias="AI_QUESTION_SERVICE_URL")
    ai_tts_service_url: str | None = Field(default=None, alias="AI_TTS_SERVICE_URL")
    ai_stt_service_url: str | None = Field(default=None, alias="AI_STT_SERVICE_URL")
    ai_analysis_service_url: str | None = Field(default=None, alias="AI_ANALYSIS_SERVICE_URL")

    superadmin_bootstrap_email: str = Field(default="superadmin@skillgraph.dev", alias="SUPERADMIN_EMAIL")
    superadmin_bootstrap_password: str = Field(default="SkillGraphAdmin123!", alias="SUPERADMIN_PASSWORD")
    superadmin_bootstrap_company: str = Field(default="SkillGraph Platform", alias="SUPERADMIN_COMPANY")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
