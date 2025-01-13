from datetime import datetime
from enum import StrEnum, auto
from typing import TYPE_CHECKING

from pydantic import EmailStr, field_serializer
from sqlmodel import Field, Relationship, SQLModel

from ._utils import now

if TYPE_CHECKING:
    from .key import Key


class ProjectUserRole(StrEnum):
    OWNER = auto()
    MEMBER = auto()


class ProjectUserBase(SQLModel):
    name: str
    email: EmailStr
    role: ProjectUserRole
    added_at: datetime = Field(default_factory=now)


class ProjectUserPublic(ProjectUserBase):
    object: str = "organization.project.user"
    id: str

    @field_serializer("added_at")
    def serialize_datetime(self, value: datetime) -> int:
        return int(value.timestamp())


class ProjectUser(ProjectUserBase, table=True):
    __tablename__ = "project_user"  # type: ignore

    id: str = Field(foreign_key="organization_user.id", primary_key=True)
    project_id: str = Field(foreign_key="project.id", primary_key=True)
    api_keys: list["Key"] = Relationship(back_populates="user")
