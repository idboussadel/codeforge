from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# apps/api/src/codeforge/config.py → repo root
REPO_ROOT = Path(__file__).resolve().parents[4]


def _default_database_url() -> str:
    return f"sqlite+aiosqlite:///{REPO_ROOT / 'data' / 'codeforge.db'}"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=REPO_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    deepseek_api_key: str
    e2b_api_key: str
    e2b_template: str = "code-interpreter-v1"
    database_url: str = Field(default_factory=_default_database_url)
    cors_origin: str = "http://localhost:3000"
    model: str = "deepseek-chat"


settings = Settings()
