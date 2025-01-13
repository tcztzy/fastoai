from datetime import datetime
from enum import StrEnum, auto
from typing import TYPE_CHECKING, Literal

from pydantic import field_serializer
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlmodel import Field, Relationship, SQLModel, UniqueConstraint, col

from ._utils import now, random_id_with_prefix
from .organization import Organization

if TYPE_CHECKING:
    from .key import Key


class ServiceAccountRole(StrEnum):
    OWNER = auto()
    MEMBER = auto()


class ServiceAccountBase(SQLModel):
    name: str = "Service account"
    created_at: datetime = Field(default_factory=now)
    role: ServiceAccountRole = ServiceAccountRole.MEMBER


class ServiceAccount(ServiceAccountBase, AsyncAttrs, table=True):
    __tablename__ = "service_account"  # type: ignore

    id: str = Field(
        default_factory=random_id_with_prefix("svc_acct_"), primary_key=True
    )
    organization_id: str = Field(foreign_key="organization.id", primary_key=True)
    organization: Organization = Relationship(back_populates="service_accounts")
    api_key: "Key" = Relationship(
        back_populates="service_account", sa_relationship_kwargs={"uselist": False}
    )


class OrganizationServiceAccount(ServiceAccountBase):
    id: str
    object: Literal["organization.service_account"] = "organization.service_account"
    type: Literal["service_account"] = "service_account"

    @field_serializer("created_at")
    def serialize_datetime(self, value: datetime) -> int:
        return int(value.timestamp())


class ProjectServiceAccount(ServiceAccountBase):
    id: str
    object: Literal["organization.project.service_account"] = (
        "organization.project.service_account"
    )

    @field_serializer("created_at")
    def serialize_datetime(self, value: datetime) -> int:
        return int(value.timestamp())


UniqueConstraint(
    col(ServiceAccount.name),
    col(ServiceAccount.organization_id),
)
