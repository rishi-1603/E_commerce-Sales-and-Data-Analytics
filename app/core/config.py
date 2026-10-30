from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List
import os
import secrets
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]

class Settings(BaseSettings):
    PROJECT_NAME: str = "Commerce Intelligence API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        f"sqlite+aiosqlite:///{BASE_DIR / 'data' / 'ecommerce.db'}"
    )

    SYNC_DATABASE_URL: str = os.getenv(
        "SYNC_DATABASE_URL",
        f"sqlite:///{BASE_DIR / 'data' / 'ecommerce.db'}"
    )

    # No hardcoded fallback: a missing SECRET_KEY yields an ephemeral per-process
    # key so a shipped default can never be mistaken for a production secret.
    SECRET_KEY: str = os.getenv("SECRET_KEY") or secrets.token_urlsafe(48)
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost",
        "http://localhost:3000",
        "http://localhost:8000",
        "https://ecomanalytics-dashboard.vercel.app",
        "*"
    ]

    model_config = SettingsConfigDict(env_file=".env", extra="allow")

settings = Settings()
