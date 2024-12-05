from datetime import datetime
from enum import StrEnum, auto
from typing import Literal, cast

from openai import BaseModel
from pydantic import EmailStr
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlmodel import Field, Relationship, SQLModel

from ._utils import now, random_id_with_prefix


class OrganizationUserRole(StrEnum):
    OWNER = auto()
    READER = auto()


class _OrganizationUser(BaseModel):
    object: Literal["organization.user"] = "organization.user"
    id: str
    name: str
    email: EmailStr
    role: OrganizationUserRole
    added_at: int


class OrganizationUser(AsyncAttrs, SQLModel, table=True):
    organization_id: str = Field(foreign_key="organization.id", primary_key=True)
    organization: "Organization" = Relationship(back_populates="members")
    user_id: str = Field(foreign_key="user.id", primary_key=True)
    user: "User" = Relationship(back_populates="organization_users")
    role: OrganizationUserRole
    added_at: datetime = Field(default_factory=now)

    async def to_openai_model(self) -> _OrganizationUser:
        user = cast(User, await self.awaitable_attrs.user)
        return _OrganizationUser(
            id=self.user_id,
            name=user.name,
            email=user.email,
            role=self.role,
            added_at=int(self.added_at.timestamp()),
        )


class User(AsyncAttrs, SQLModel, table=True):
    """User model."""

    id: str = Field(default_factory=random_id_with_prefix("user_"), primary_key=True)
    name: str
    password: str
    email: EmailStr
    phone: str | None = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=now)
    api_keys: list["APIKey"] = Relationship(back_populates="user")
    organization_users: OrganizationUser = Relationship(back_populates="user")


class Organization(AsyncAttrs, SQLModel, table=True):
    id: str = Field(default_factory=random_id_with_prefix("org-"), primary_key=True)
    name: str = "Personal"
    members: list[OrganizationUser] = Relationship(back_populates="organization")


class Project(AsyncAttrs, SQLModel, table=True):
    id: str = Field(default_factory=random_id_with_prefix("proj_"), primary_key=True)
    name: str = "Default project"


class APIKey(AsyncAttrs, SQLModel, table=True):
    """API key model.

    API key is used for authenticating the user.
    """

    __tablename__ = "api_key"  # type: ignore

    id: str = Field(default_factory=random_id_with_prefix("sk-"), primary_key=True)
    user_id: str = Field(foreign_key="user.id")
    user: User = Relationship(back_populates="api_keys")
    name: str = Field(default="New API key", max_length=255)
    created_at: datetime = Field(default_factory=now)
