from functools import lru_cache
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession

from .models import APIKey, User
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

security = HTTPBearer()


async def get_user(
    *,
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    settings: SettingsDependency,
    session: SessionDependency,
) -> User:
    """Get the current user."""
    if not settings.auth_enabled:
        return APIKey(
            id=credentials.credentials, user=User(name="test", password="test")
        )
    api_key = await session.get(APIKey, credentials.credentials)
    if api_key is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key"
        )
    if not api_key.user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user"
        )
    return api_key.user


UserDependency = Annotated[User, Depends(get_user)]
