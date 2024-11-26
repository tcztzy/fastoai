from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession

from .settings import Settings


@lru_cache
def get_settings() -> Settings:
    """Get settings."""
    return Settings()


SettingsDependency = Annotated[Settings, Depends(get_settings)]


async def get_session(settings: SettingsDependency):
    """Get session."""
    engine = create_async_engine(settings.database_url)
    async with AsyncSession(engine) as session:
        yield session


SessionDependency = Annotated[AsyncSession, Depends(get_session)]


@lru_cache
async def get_openai(settings: SettingsDependency):
    """Get OpenAI client."""
    return AsyncOpenAI(**settings.openai.model_dump())


OpenAIDependency = Annotated[AsyncOpenAI, Depends(get_openai)]
