from datetime import datetime
from typing import TYPE_CHECKING, Literal

from pydantic import computed_field, field_serializer
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlmodel import Field, Relationship, SQLModel

from ._utils import now, random_id_with_prefix
from .project_user import ProjectUser

if TYPE_CHECKING:
    from .organization import Organization
    from .organization_user import OrganizationUser


class ProjectBase(SQLModel):
    name: str = "Default project"
    created_at: datetime = Field(default_factory=now)
    archived_at: datetime | None = None

    @computed_field
    def status(self) -> Literal["active", "archived"]:
        return "archived" if self.archived_at else "active"


class ProjectPublic(ProjectBase):
    id: str
    object: Literal["organization.project"] = "organization.project"

    @field_serializer("created_at", "archived_at")
    def serialize_datetime(self, value: datetime | None) -> int | None:
        return int(value.timestamp()) if value else None


class Project(ProjectBase, AsyncAttrs, table=True):
    id: str = Field(default_factory=random_id_with_prefix("proj_"), primary_key=True)
    organization_id: str = Field(foreign_key="organization.id")
    organization: "Organization" = Relationship(back_populates="projects")
    users: list["OrganizationUser"] = Relationship(
        back_populates="projects", link_model=ProjectUser
    )
