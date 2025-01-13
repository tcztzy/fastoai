from typing import TYPE_CHECKING

from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlmodel import Field, Relationship, SQLModel

from ._utils import random_id_with_prefix
from .organization_user import OrganizationUser
from .user import User

if TYPE_CHECKING:
    from .project import Project
    from .service_account import ServiceAccount


class Organization(SQLModel, AsyncAttrs, table=True):
    id: str = Field(default_factory=random_id_with_prefix("org-"), primary_key=True)
    name: str = "Personal"
    users: list["User"] = Relationship(
        back_populates="organizations", link_model=OrganizationUser
    )
    projects: list["Project"] = Relationship(back_populates="organization")
    service_accounts: list["ServiceAccount"] = Relationship(
        back_populates="organization"
    )

    async def get_members(self):
        return (
            await self.awaitable_attrs.users
            + await self.awaitable_attrs.service_accounts
        )
