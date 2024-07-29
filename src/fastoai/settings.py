from functools import cached_property, lru_cache
from pathlib import Path
from typing import Literal

import orjson
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings
from sqlmodel import Session, SQLModel, create_engine

from .models import OBJECT_TYPES


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

    def model_post_init(self, __context):
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    @cached_property
    def engine(self):
        """Get engine."""

        def serialize_pydantic_model(model: BaseModel) -> str:
            return model.model_dump_json()

        def deserialize_pydantic_model(data: str) -> BaseModel | None:
            # Try deserializing with each model until one works.
            # This is a pretty ugly solution but the deserialization seems to only be possible and reliable at an engine level
            # and we need to know the model to deserialize it properly
            # We would need to keep adding more of these if we add more models with JSON fields.
            json_data = orjson.loads(data)
            if "object" in json_data:
                object_type = json_data["object"]
                if object_type in OBJECT_TYPES:
                    return OBJECT_TYPES[object_type].model_validate(json_data)
            return None

        e = create_engine(
            self.database_url,
            json_serializer=serialize_pydantic_model,
            json_deserializer=deserialize_pydantic_model,
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
