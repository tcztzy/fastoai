from functools import cached_property, lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings
from sqlmodel import Session, SQLModel, create_engine


class OpenAISettings(BaseSettings, env_prefix="openai_"):
    """OpenAI settings."""

    api_key: str
    base_url: str = "https://api.openai.com/v1"


class Settings(BaseSettings):
    """Settings."""

    openai: list[OpenAISettings] = []
    database_url: str = "sqlite:///"
    upload_dir: Path = Path.home() / ".fastoai" / "uploads"
    auth_enabled: bool = False
    generate_models: bool = True
    generate_requests: bool = True

    def model_post_init(self, __context):
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    @cached_property
    def engine(self):
        """Get engine."""
        e = create_engine(self.database_url)
        SQLModel.metadata.create_all(e)
        return e

    @cached_property
    def session(self):
        """Get session."""
        return Session(self.engine)


@lru_cache
def get_settings() -> Settings:
    """Get settings."""
    return Settings()


settings = get_settings()
