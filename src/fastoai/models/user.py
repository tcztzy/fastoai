from datetime import datetime
from typing import TYPE_CHECKING

from pydantic import EmailStr
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlmodel import Field, Relationship, SQLModel

from ._utils import now, random_id_with_prefix
from .organization_user import OrganizationUser

if TYPE_CHECKING:
    from .organization import Organization


class User(AsyncAttrs, SQLModel, table=True):
    """User model."""

    id: str = Field(default_factory=random_id_with_prefix("user_"), primary_key=True)
    name: str
    password: str
    email: EmailStr
    phone: str | None = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=now)
    organizations: list["Organization"] = Relationship(
        back_populates="users", link_model=OrganizationUser
    )
