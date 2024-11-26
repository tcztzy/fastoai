from datetime import datetime
from typing import Annotated, Literal

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, EmailStr
from sqlmodel import JSON, Field, Relationship, SQLModel

from ..dependencies import SessionDependency, SettingsDependency
from ._utils import now, random_id_with_prefix

security = HTTPBearer()


class UserSettings(BaseModel):
    """User Settings."""

    object: Literal["user.settings"] = "user.settings"


class User(SQLModel, table=True):
    """User model."""

    id: str = Field(default_factory=random_id_with_prefix("user_"), primary_key=True)
    name: str = Field(max_length=150, unique=True, regex=r"^[\w.@+-]+$")
    password: str
    email: EmailStr | None = Field(nullable=True)
    is_superuser: bool = False
    is_active: bool = True
    created_at: datetime = Field(default_factory=now)
    updated_at: datetime = Field(default_factory=now)
    settings: UserSettings = Field(default_factory=dict, sa_type=JSON)
    api_keys: list["APIKey"] = Relationship(back_populates="user")


class APIKey(SQLModel, table=True):
    """API key model.

    API key is used for authenticating the user.
    """

    __tablename__ = "api_key"

    id: str = Field(default_factory=random_id_with_prefix("sk-"), primary_key=True)
    user_id: str = Field(foreign_key="user.id")
    user: "User" = Relationship(back_populates="api_keys")
    name: str = Field(default="New API key", max_length=255)
    created_at: datetime = Field(default_factory=now)


async def get_api_key(
    *,
    api_key: str,
    settings: SettingsDependency,
    session: SessionDependency,
) -> APIKey | None:
    """Get the API key."""
    if not settings.auth_enabled:
        return APIKey(id=api_key, user=User(name="test", password="test"))
    return await session.get(APIKey, api_key)


async def get_current_user(
    *,
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    settings: SettingsDependency,
    session: SessionDependency,
) -> User:
    """Get the current user."""
    api_key = await get_api_key(
        credentials=credentials.credentials,
        settings=settings,
        session=session,
    )
    if api_key is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key"
        )
    return api_key.user


async def get_current_active_user(
    user: User = Depends(get_current_user),
) -> User:
    """Get the current active user."""
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user"
        )
    return user
