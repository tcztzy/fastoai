from functools import cached_property, lru_cache
from pathlib import Path

from pydantic import HttpUrl
from pydantic_settings import BaseSettings
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession


class OpenAISettings(BaseSettings, env_prefix="openai_"):
    """OpenAI settings."""

    api_key: str
    base_url: str = "https://api.openai.com/v1"


class Settings(BaseSettings, env_prefix="fastoai_"):
    """Settings."""

    openai: list[OpenAISettings] = []
    base_url: HttpUrl = HttpUrl("http://127.0.0.1:8000")
    database_url: str = "sqlite+aiosqlite:///"
    upload_dir: Path = Path.home() / ".fastoai" / "uploads"
    auth_enabled: bool = False
    generate_models: bool = False

    def model_post_init(self, __context):
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    @cached_property
    def engine(self):
        """Get engine."""
        return create_async_engine(self.database_url)

    @cached_property
    def session(self):
        """Get session."""
        return AsyncSession(self.engine)


@lru_cache
def get_settings() -> Settings:
    """Get settings."""
    return Settings()


settings = get_settings()
