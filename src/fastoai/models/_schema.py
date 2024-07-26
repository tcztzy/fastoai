from typing import Literal, Mapping

from openai.types.beta.assistant import Assistant
from openai.types.beta.thread import Thread
from openai.types.beta.threads.message import Message
from openai.types.beta.threads.run import Run
from openai.types.beta.threads.runs.run_step import RunStep
from pydantic import BaseModel


class AnthropicSettings(BaseModel):
    """Anthropic settings."""

    api_key: str
    base_url: str = "https://api.anthropic.com"


class GoogleSettings(BaseModel):
    """Google Gemini settings."""

    api_key: str
    base_url: str = "https://generativelanguage.googleapis.com"


class OpenAISettings(BaseModel):
    """OpenAI settings."""

    api_key: str
    base_url: str = "https://api.openai.com/v1"


class OllamaSettings(BaseModel):
    """Ollama settings."""

    api_key: Literal["ollama"] = "ollama"
    base_url: str = "http://localhost:14434/v1"


class UserSettings(BaseModel):
    """User Settings."""

    object: Literal["user.settings"] = "user.settings"
    openai: list[OpenAISettings] = []
    anthropic: list[AnthropicSettings] = []
    google: list[GoogleSettings] = []
    ollama: list[OllamaSettings] = []


OBJECT_TYPES: Mapping[str, type[BaseModel]] = {
    "assistant": Assistant,
    "thread": Thread,
    "thread.message": Message,
    "thread.run": Run,
    "thread.run.step": RunStep,
    "user.settings": UserSettings,
}
