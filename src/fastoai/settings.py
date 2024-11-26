from pathlib import Path

from pydantic import Field, HttpUrl
from pydantic_settings import BaseSettings


class OpenAISettings(BaseSettings, env_prefix="openai_"):
    """OpenAI settings."""

    api_key: str
    base_url: str = "https://api.openai.com/v1"


class Settings(BaseSettings, env_prefix="fastoai_"):
    """Settings."""

    openai: OpenAISettings = Field(default_factory=OpenAISettings)
    base_url: HttpUrl = HttpUrl("http://127.0.0.1:8000")
    database_url: str = "sqlite+aiosqlite:///"
    upload_dir: Path = Path.home() / ".fastoai" / "uploads"
    auth_enabled: bool = False

    def model_post_init(self, __context):
        self.upload_dir.mkdir(parents=True, exist_ok=True)
