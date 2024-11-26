from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr
from sqlmodel import JSON, Field, Relationship, SQLModel

from ._utils import now, random_id_with_prefix


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
