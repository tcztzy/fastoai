from datetime import datetime
from enum import StrEnum, auto
from typing import TYPE_CHECKING, Literal

from openai import BaseModel
from pydantic import EmailStr
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlmodel import Field, Relationship, SQLModel

from ._utils import now
from .project_user import ProjectUser

if TYPE_CHECKING:
    from .key import Key
    from .project import Project


class OrganizationUserRole(StrEnum):
    OWNER = auto()
    READER = auto()


class OrganizationUserPublic(BaseModel):
    object: Literal["organization.user"] = "organization.user"
    id: str
    name: str
    email: EmailStr
    role: OrganizationUserRole
    added_at: int


class OrganizationUser(SQLModel, AsyncAttrs, table=True):
    __tablename__ = "organization_user"  # type: ignore

    organization_id: str = Field(foreign_key="organization.id", primary_key=True)
    id: str = Field(foreign_key="user.id", primary_key=True)
    role: OrganizationUserRole
    added_at: datetime = Field(default_factory=now)
    projects: list["Project"] = Relationship(
        back_populates="users", link_model=ProjectUser
    )
    admin_api_keys: list["Key"] = Relationship(back_populates="admin")

    async def to_openai_model(self) -> OrganizationUserPublic:
        user = await self.awaitable_attrs.user
        return OrganizationUserPublic(
            id=self.id,
            name=user.name,
            email=user.email,
            role=self.role,
            added_at=int(self.added_at.timestamp()),
        )
