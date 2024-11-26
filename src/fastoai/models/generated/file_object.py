# Generated by FastOAI, DON'T EDIT
from datetime import datetime
from typing import Annotated, Literal

from pydantic import field_serializer
from sqlmodel import Enum, Field, SQLModel

from .._utils import now, random_id_with_prefix


class FileObject(SQLModel, table=True):
    __tablename__ = "file"

    id: Annotated[str, Field(primary_key=True, default_factory=random_id_with_prefix("file-"))]
    """The file identifier, which can be referenced in the API endpoints."""

    bytes: int
    """The size of the file, in bytes."""

    created_at: Annotated[datetime, Field(default_factory=now)]
    """The Unix timestamp (in seconds) for when the file was created."""

    filename: str
    """The name of the file."""

    purpose: Annotated[Literal[
        "assistants", "assistants_output", "batch", "batch_output", "fine-tune", "fine-tune-results", "vision"
    ], Field(sa_type=Enum("assistants", "assistants_output", "batch", "batch_output", "fine-tune", "fine-tune-results", "vision"))]
    """The intended purpose of the file.

    Supported values are `assistants`, `assistants_output`, `batch`, `batch_output`,
    `fine-tune`, `fine-tune-results` and `vision`.
    """
    status: Annotated[Literal["uploaded", "processed", "error"], Field(sa_type=Enum("uploaded", "processed", "error"))]
    """Deprecated.

    The current status of the file, which can be either `uploaded`, `processed`, or
    `error`.
    """
    status_details: str | None = None
    """Deprecated.

    For details on why a fine-tuning training file failed validation, see the
    `error` field on `fine_tuning.job`.
    """

    @field_serializer("created_at")
    def serialize_datetime(self, dt: datetime, _) -> int:
        return int(dt.timestamp())
