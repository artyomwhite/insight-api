"""Application settings loaded from environment variables."""

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.db.database_url import normalize_database_url


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # App
    app_name: str = Field(default="Insight API", alias="APP_NAME")
    app_version: str = Field(default="1.0.0", alias="APP_VERSION")
    environment: Literal["development", "staging", "production"] = Field(
        default="development", alias="ENVIRONMENT"
    )
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://insight:insight@localhost:5432/insight",
        alias="DATABASE_URL",
    )

    # Security
    secret_key: str = Field(default="change-me", alias="SECRET_KEY")
    algorithm: str = Field(default="HS256", alias="ALGORITHM")
    access_token_expire_hours: int = Field(default=2, alias="ACCESS_TOKEN_EXPIRE_HOURS")

    # CORS
    cors_origins: str = Field(
        default="http://localhost:3000,http://localhost:8000",
        alias="CORS_ORIGINS",
    )

    # Admin seed
    admin_email: str = Field(default="admin@insight.dev", alias="ADMIN_EMAIL")
    admin_password: str = Field(default="changeme123!", alias="ADMIN_PASSWORD")

    # Limits
    max_analytics_range_days: int = Field(default=365, alias="MAX_ANALYTICS_RANGE_DAYS")
    max_batch_events: int = Field(default=100, alias="MAX_BATCH_EVENTS")
    max_event_properties_size_kb: int = Field(default=10, alias="MAX_EVENT_PROPERTIES_SIZE_KB")

    @field_validator("database_url", mode="before")
    @classmethod
    def fix_database_url(cls, v: str) -> str:
        """Normalize to postgresql+asyncpg (never psycopg2)."""
        return normalize_database_url(v)

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def docs_enabled(self) -> bool:
        return not self.is_production


@lru_cache
def get_settings() -> Settings:
    return Settings()
