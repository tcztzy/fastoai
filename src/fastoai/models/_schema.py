from typing import Any, Literal, Mapping, Self

from openai.types.beta.assistant import Assistant
from openai.types.beta.thread import Thread
from openai.types.beta.threads.message import Message
from openai.types.beta.threads.run import Run
from openai.types.beta.threads.runs.run_step import RunStep
from pydantic import BaseModel
from pydantic import BaseModel
from sqlalchemy.ext.mutable import Mutable


class MutableModel(BaseModel, Mutable):
    def __setattr__(self, name: str, value: Any) -> None:
        """Allows SQLAlchmey Session to track mutable behavior when updating any field"""
        self.changed()
        return super().__setattr__(name, value)

    @classmethod
    def coerce(cls, key: str, value: Any) -> Self | None:
        """Convert JSON to MeetupLocation object allowing for mutable behavior"""
        if isinstance(value, cls) or value is None:
            return value

        if isinstance(value, str):
            return cls.model_validate_json(value)

        if isinstance(value, dict):
            return cls(**value)

        super().coerce(key, value)


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


class MutableAssistant(MutableModel, Assistant):
    """Mutable Assistant object."""


class MutableThread(MutableModel, Thread):
    """Mutable Thread object."""


class MutableMessage(MutableModel, Message):
    """Mutable Message object."""


class MutableRun(MutableModel, Run):
    """Mutable Run object."""


class MutableRunStep(MutableModel, RunStep):
    """Mutable RunStep object."""


OBJECT_TYPES: Mapping[str, type[BaseModel]] = {
    "assistant": MutableAssistant,
    "thread": MutableThread,
    "thread.message": MutableMessage,
    "thread.run": MutableRun,
    "thread.run.step": MutableRunStep,
    "user.settings": UserSettings,
}
