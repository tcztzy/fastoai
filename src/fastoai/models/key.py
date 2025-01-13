from datetime import datetime
from secrets import token_urlsafe
from typing import Annotated, Literal, TypedDict

from pydantic import computed_field, field_serializer
from sqlmodel import Field, Relationship, SQLModel

from ._types import MutableBaseModel, as_sa_type
from ._utils import now, random_id_with_prefix
from .organization_user import OrganizationUser, OrganizationUserPublic
from .project_user import ProjectUser, ProjectUserPublic
from .service_account import (
    OrganizationServiceAccount,
    ProjectServiceAccount,
    ServiceAccount,
)


class Permissions(MutableBaseModel):
    models: Literal["read"] | None
    """List models this organization has access to."""

    model_capabilities: Literal["write"] | None
    """Create chat completions, audio, embeddings and images."""

    assistants: Literal["read", "write"] | None
    """Create and retrieve assistants"""

    threads: Literal["read", "write"] | None
    """Create and retrieve Threads/Messages/Runs."""

    fine_tuning: Literal["read", "write"] | None
    """Create and retrieve fine-tuning jobs."""

    files: Literal["read", "write"] | None
    """Create and retrieve files."""


class KeyBase(SQLModel):
    name: str = "Secret key"
    created_at: datetime = Field(default_factory=now)


class UserOwner(TypedDict):
    type: Literal["user"]
    user: ProjectUser


class ServiceAccountOwner(TypedDict):
    type: Literal["service_account"]
    service_account: ServiceAccount


class Key(KeyBase, table=True):
    id: str = Field(primary_key=True, default_factory=random_id_with_prefix("key_", 16))
    value: str = ""
    permissions: Annotated[
        Permissions | Literal["all", "read_only"],
        Field(sa_type=as_sa_type(Permissions | Literal["all", "read_only"])),
    ] = "all"
    admin_id: str | None = Field(default=None, foreign_key="organization_user.id")
    admin: OrganizationUser | None = Relationship(back_populates="admin_api_keys")
    project_id: str | None = Field(default=None, foreign_key="project.id")
    user_id: str | None = Field(default=None, foreign_key="project_user.id")
    user: ProjectUser | None = Relationship(back_populates="api_keys")
    service_account_id: str | None = Field(
        default=None, foreign_key="service_account.id"
    )
    service_account: ServiceAccount | None = Relationship(back_populates="api_key")

    def model_post_init(self, __context):
        self.value = "sk-proj-" + token_urlsafe(117)

    @computed_field
    @property
    def redacted_value(self) -> str:
        return self.value[:8] + "*" * (len(self.value) - 12) + self.value[-4:]

    @computed_field
    @property
    def owner(self) -> UserOwner | ServiceAccountOwner:
        if self.user is not None:
            return UserOwner({"type": "user", "user": self.user})
        if self.service_account is not None:
            return ServiceAccountOwner(
                {"type": "service_account", "service_account": self.service_account}
            )
        raise ValueError("API key does not have an owner")


class _OrganizationUser(OrganizationUserPublic):
    type: Literal["user"] = "user"


class AdminAPIKey(KeyBase):
    id: str
    object: Literal["organization.admin_api_key"] = "organization.admin_api_key"
    redacted_value: str
    owner: _OrganizationUser | OrganizationServiceAccount

    @field_serializer("created_at")
    def serialize_datetime(self, value: datetime) -> int:
        return int(value.timestamp())


class UserOwnerPublic(TypedDict):
    type: Literal["user"]
    user: ProjectUserPublic


class ServiceAccountOwnerPublic(TypedDict):
    type: Literal["service_account"]
    service_account: ProjectServiceAccount


class ProjectAPIKey(KeyBase):
    id: str
    object: Literal["organization.project.api_key"] = "organization.project.api_key"
    redacted_value: str
    owner: UserOwnerPublic | ServiceAccountOwnerPublic

    @field_serializer("created_at")
    def serialize_datetime(self, value: datetime) -> int:
        return int(value.timestamp())
