from functools import cached_property, lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings
from sqlmodel import Session, SQLModel, create_engine

from .serde import json_deserializer, json_serializer


class AnthropicSettings(BaseSettings, env_prefix="anthropic_"):
    """Anthropic settings."""

    api_key: str
    base_url: str = "https://api.anthropic.com"


class GoogleSetting(BaseSettings, env_prefix="google_"):
    """Google Gemini settings."""

    api_key: str
    base_url: str = "https://generativelanguage.googleapis.com"


class OpenAISettings(BaseSettings, env_prefix="openai_"):
    """OpenAI settings."""

    api_key: str
    base_url: str = "https://api.openai.com/v1"


class OllamaSettings(BaseSettings, env_prefix="ollama_"):
    """Ollama settings."""

    api_key: Literal["ollama"] = "ollama"
    base_url: str = Field(default="https://api.ollama.com", alias="ollama_host")


class Settings(BaseSettings):
    """Settings."""

    openai: list[OpenAISettings] = []
    anthropic: list[AnthropicSettings] = []
    google: list[GoogleSetting] = []
    ollama: list[OllamaSettings] = []
    database_url: str = "sqlite:///"
    upload_dir: Path = Path.home() / ".fastoai" / "uploads"
    auth_enabled: bool = False
    generate_models: bool = True

    def model_post_init(self, __context):
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    @cached_property
    def engine(self):
        """Get engine."""
        e = create_engine(
            self.database_url,
            json_serializer=json_serializer,
            json_deserializer=json_deserializer,
        )
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
