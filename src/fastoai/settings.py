import asyncio
from functools import lru_cache
from pathlib import Path
from typing import Sequence

from loguru import logger
from openai import AsyncClient, OpenAIError
from openai.types import Model
from pydantic import Field
from pydantic_settings import BaseSettings

from ._client import AsyncOpenAI

FASTOAI_DIR = Path.home() / ".fastoai"


class OpenAISettings(BaseSettings, env_prefix="openai_"):
    """OpenAI settings."""

    api_key: str = ""
    base_url: str = "https://api.openai.com/v1"


async def list_models(client: AsyncClient) -> list[Model]:
    return (await client.models.list()).data


class Settings(
    BaseSettings,
    env_prefix="fastoai_",
    json_file=FASTOAI_DIR / "settings.json",
):
    """Settings."""

    base_url: str = "http://127.0.0.1:8000"
    database_url: str = ""
    upload_dir: Path = FASTOAI_DIR / "uploads"
    generate_models: bool = False
    endpoints: list[OpenAISettings] = Field(default_factory=lambda: [OpenAISettings()])

    def model_post_init(self, __context):
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        if not self.database_url:
            self.database_url = f"sqlite+aiosqlite:///{FASTOAI_DIR / 'fastoai.db'}"

    def save(self):
        """Save settings."""
        json_file = self.model_config.get("json_file")
        if json_file is None:
            raise ValueError("No JSON file configured")
        if isinstance(json_file, Sequence):
            json_file = json_file[0]
        Path(json_file).write_text(
            self.model_dump_json(
                indent=4,
                exclude_unset=True,
                exclude_defaults=True,
                exclude_none=True,
            )
        )

    async def get_openai_client(self) -> AsyncOpenAI:
        results: dict[tuple[str, str], list[Model]] = {}
        try:
            tasks: dict[tuple[str, str], asyncio.Task[list[Model]]] = {}
            async with asyncio.TaskGroup() as tg:
                for endpoint in self.endpoints:
                    client = AsyncClient(**endpoint.model_dump())
                    tasks[(endpoint.api_key, endpoint.base_url)] = tg.create_task(
                        list_models(client)
                    )
            results |= {
                (api_key, base_url): task.result()
                for (api_key, base_url), task in tasks.items()
            }
        except* OpenAIError as excgroup:
            for exc in excgroup.exceptions:
                logger.error(exc)
        return AsyncOpenAI(endpoints=results)


@lru_cache
def get_settings() -> Settings:
    """Get settings."""
    return Settings()
