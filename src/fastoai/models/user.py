from datetime import datetime
from typing import Annotated, Any, Literal, Self

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, EmailStr
from sqlmodel import JSON, Field, Relationship, SQLModel

from ..settings import settings
from ..utils import now, random_id_with_prefix

security = HTTPBearer()


class WithMetadata(SQLModel):
    metadata_: (
        dict[
            Annotated[str, Field(max_length=64)],
            Annotated[str, Field(max_length=512)] | int | float | bool | None,
        ]
        | None
    ) = Field(
        None, alias="metadata", sa_type=JSON, sa_column_kwargs={"name": "metadata"}
    )
    """Set of 16 key-value pairs that can be attached to an object.

    This can be useful for storing additional information about the object in a
    structured format. Keys can be a maximum of 64 characters long and values can be
    a maximum of 512 characters long.
    """

    def __init__(self, **kwargs):
        if "metadata" in kwargs:
            kwargs["metadata_"] = kwargs.pop("metadata")
        return super().__init__(**kwargs)

    @classmethod
    def model_validate(
        cls,
        obj: Any,
        *,
        strict: bool | None = None,
        from_attributes: bool | None = None,
        context: dict[str, Any] | None = None,
        update: dict[str, Any] | None = None,
    ) -> Self:
        if "metadata" in obj:
            obj["metadata_"] = obj.pop("metadata")
        return super().model_validate(
            obj,
            strict=strict,
            from_attributes=from_attributes,
            context=context,
            update=update,
        )

    def model_dump(self, **kwargs):
        result = super().model_dump(**kwargs)
        if "metadata_" in result and kwargs.get("by_alias", False):
            result["metadata"] = result.pop("metadata_")
        return result

    def model_dump_json(self, **kwargs):
        result = super().model_dump_json(**kwargs)
        if "metadata_" in result:
            result.replace("metadata_", "metadata")
        return result


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
    updated_at: datetime = Field(
        default_factory=now, sa_column_kwargs={"onupdate": now}
    )
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


def get_api_key(api_key: str) -> APIKey | None:
    """Get the API key."""
    if not settings.auth_enabled:
        return APIKey(id=api_key, user=User(name="test", password="test"))
    return settings.session.get(APIKey, api_key)


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
) -> User:
    """Get the current user."""
    api_key = get_api_key(credentials.credentials)
    if api_key is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key"
        )
    return api_key.user


def get_current_active_user(
    user: User = Depends(get_current_user),
) -> User:
    """Get the current active user."""
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user"
        )
    return user
