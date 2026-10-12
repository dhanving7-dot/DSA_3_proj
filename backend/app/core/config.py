"""Application configuration loaded from environment variables."""
from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    PROJECT_NAME: str = "Student-Laboratory Allocation Engine"
    API_V1_PREFIX: str = "/api/v1"

    # Database
    DATABASE_URL: str = "sqlite:///./dev.db"

    # Redis (used for rate-limiting / caching of analytics; optional)
    REDIS_URL: str = "redis://localhost:6379/0"

    # Auth
    SECRET_KEY: str = "dev-secret-key-change-me-in-production-please"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 12

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    # AI
    ANTHROPIC_API_KEY: str | None = None
    AI_MODEL: str = "claude-sonnet-5"

    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int = 120

    ENV: str = "development"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
