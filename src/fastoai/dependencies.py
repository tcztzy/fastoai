from typing import Annotated

import asyncstdlib as a
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from ._client import AsyncOpenAI
from .models import User
from .models.key import Key
from .models.project_user import ProjectUser
from .models.service_account import ServiceAccount
from .settings import Settings, get_settings

SettingsDependency = Annotated[Settings, Depends(get_settings)]


async def get_session(settings: SettingsDependency):
    """Get session."""
    engine = create_async_engine(settings.database_url)
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    async with AsyncSession(engine) as session:
        yield session


SessionDependency = Annotated[AsyncSession, Depends(get_session)]


@a.lru_cache
async def get_openai(settings: SettingsDependency):
    """Get OpenAI client."""
    return await settings.get_openai_client()


ClientDependency = Annotated[AsyncOpenAI, Depends(get_openai)]

security = HTTPBearer()


async def get_user(
    *,
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    session: SessionDependency,
) -> ProjectUser | ServiceAccount | None:
    """Get the current user."""
    api_key = await session.get(Key, credentials.credentials)
    if api_key is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key"
        )
    await session.refresh(api_key, ["user"])
    return api_key.user or api_key.service_account


UserDependency = Annotated[User, Depends(get_user)]
